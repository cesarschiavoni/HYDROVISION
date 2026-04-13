"""
mqtt_ingester.py — Suscriptor MQTT → PostgreSQL
HydroVision AG | TRL 4

Escucha los topics MQTT del gateway LoRa y persiste telemetría
directamente en PostgreSQL, sin pasar por el endpoint HTTP /ingest.

Esto es el "pegamento" entre Mosquitto y la base de datos para el
flujo principal: nodo → LoRa → gateway → MQTT → este módulo → PostgreSQL.

Uso:
    python mqtt_ingester.py                    # con defaults
    MQTT_BROKER=10.0.0.5 python mqtt_ingester.py  # broker remoto

Requiere:
    pip install paho-mqtt psycopg2-binary

Topics suscritos:
    hydrovision/+/telemetry   — payloads de medición
    hydrovision/+/alert       — alertas HSI
    hydrovision/+/status      — heartbeat / estado
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import execute_values

# ── Configuración ────────────────────────────────────────────────
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPICS = [
    ("hydrovision/+/telemetry", 1),
    ("hydrovision/+/alert", 1),
    ("hydrovision/+/status", 0),
]

DB_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://hydrovision:hydro_dev_2026@localhost:5432/hydrovision",
)

# Calidad de captura que descarta el frame térmico
CALIDAD_DESCARTE = {"fumigacion", "lluvia", "nocturno", "lente_sucio"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("mqtt_ingester")


# ── PostgreSQL ───────────────────────────────────────────────────

def get_db_conn():
    """Crea conexión a PostgreSQL con autocommit para INSERTs simples."""
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    return conn


def insert_telemetry(conn, p: dict):
    """Inserta un payload de telemetría completo en la tabla telemetry."""
    env = p.get("env", {})
    thermal = p.get("thermal", {})
    dendro = p.get("dendro", {})
    hsi = p.get("hsi", {})
    gps = p.get("gps", {})
    gdd = p.get("gdd", {})
    sol = p.get("solenoid", {})

    sql = """
    INSERT INTO telemetry (
        node_id, ts, cwsi, hsi, mds_mm,
        t_air, rh, wind_ms, rain_mm, bat_pct,
        calidad, origen, lat, lon,
        rad_wm2, tc_mean, tc_max, tc_wet, tc_dry,
        pm2_5, iso_nodo, gdd_acum, estadio, varietal,
        valid_px, n_frames, w_cwsi, w_mds, wind_ovr,
        sol_canal, sol_active, sol_reason
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s
    )
    """
    values = (
        p.get("node_id"),
        p.get("ts"),
        thermal.get("cwsi"),
        hsi.get("value"),
        dendro.get("mds_mm"),
        # env
        env.get("t_air"),
        env.get("rh"),
        env.get("wind_ms"),
        env.get("rain_mm"),
        p.get("bat_pct"),
        # calidad
        p.get("calidad_captura", "ok"),
        "real",
        gps.get("lat"),
        gps.get("lon"),
        # campos ampliados
        env.get("rad_wm2"),
        thermal.get("tc_mean"),
        thermal.get("tc_max"),
        thermal.get("tc_wet"),
        thermal.get("tc_dry"),
        p.get("pm2_5"),
        p.get("iso_nodo"),
        gdd.get("acum"),
        gdd.get("estadio"),
        p.get("varietal"),
        thermal.get("valid_pixels"),
        thermal.get("n_frames"),
        hsi.get("w_cwsi"),
        hsi.get("w_mds"),
        hsi.get("wind_override", False),
        sol.get("canal"),
        sol.get("active", False),
        sol.get("reason"),
    )
    with conn.cursor() as cur:
        cur.execute(sql, values)


def insert_audit(conn, event: str, node_id: str = None, detail: str = None):
    """Registra evento en audit_log."""
    sql = "INSERT INTO audit_log (event, node_id, detail) VALUES (%s, %s, %s)"
    with conn.cursor() as cur:
        cur.execute(sql, (event, node_id, detail))


def upsert_node_config(conn, node_id: str, lat: float = None, lon: float = None,
                       solenoid: int = None):
    """Crea registro en node_config si no existe (primer contacto)."""
    sql = """
    INSERT INTO node_config (node_id, solenoid)
    VALUES (%s, %s)
    ON CONFLICT (node_id) DO NOTHING
    """
    with conn.cursor() as cur:
        cur.execute(sql, (node_id, solenoid))


def insert_irrigation_change(conn, node_id: str, zona_id: int, active: bool,
                             ciclos: int):
    """Registra cambio de estado de riego."""
    sql = """
    INSERT INTO irrigation_log (node_id, zona, duration_min, active)
    VALUES (%s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (node_id, zona_id, ciclos * 15, active))


# ── MQTT Callbacks ───────────────────────────────────────────────

# Estado de riego por nodo (para detectar cambios on↔off)
_irrigation_state: dict[str, bool] = {}


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("Conectado a MQTT broker %s:%d", MQTT_BROKER, MQTT_PORT)
        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos)
            log.info("  Suscrito a %s (QoS %d)", topic, qos)
    else:
        log.error("Error de conexión MQTT, rc=%d", rc)


def on_message(client, userdata, msg):
    conn = userdata["db"]

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log.warning("Payload inválido en %s: %s", msg.topic, e)
        return

    # Extraer node_id del topic: hydrovision/{node_id}/{type}
    parts = msg.topic.split("/")
    if len(parts) < 3:
        log.warning("Topic inesperado: %s", msg.topic)
        return

    node_id = parts[1]
    msg_type = parts[2]

    try:
        if msg_type == "telemetry":
            _handle_telemetry(conn, node_id, payload)
        elif msg_type == "alert":
            _handle_alert(conn, node_id, payload)
        elif msg_type == "status":
            _handle_status(conn, node_id, payload)
        else:
            log.debug("Tipo de mensaje desconocido: %s", msg_type)
    except Exception as e:
        log.error("Error procesando %s de %s: %s", msg_type, node_id, e)
        # Reconectar DB si la conexión se perdió
        try:
            conn.reset()
        except Exception:
            userdata["db"] = get_db_conn()


def _handle_telemetry(conn, node_id: str, p: dict):
    """Procesa payload de telemetría."""
    calidad = p.get("calidad_captura", "ok")

    # Descartar frames con calidad no válida (pero registrar recepción)
    if calidad in CALIDAD_DESCARTE:
        insert_audit(conn, "ingest_descartado", node_id, f"calidad={calidad}")
        log.info("↓ %s descartado (calidad=%s)", node_id, calidad)
        return

    # Asegurar que el nodo existe en node_config
    gps = p.get("gps", {})
    sol = p.get("solenoid", {})
    upsert_node_config(conn, node_id, gps.get("lat"), gps.get("lon"),
                       sol.get("canal"))

    # Insertar telemetría
    insert_telemetry(conn, p)

    # Detectar cambio de estado de riego
    sol_active = sol.get("active", False)
    prev_active = _irrigation_state.get(node_id, False)
    if sol_active != prev_active:
        _irrigation_state[node_id] = sol_active
        insert_irrigation_change(conn, node_id, zona_id=0,
                                 active=sol_active,
                                 ciclos=sol.get("ciclos_activo", 0))
        evt = "irrigate_on" if sol_active else "irrigate_off"
        insert_audit(conn, evt, node_id,
                     f"canal={sol.get('canal')} reason={sol.get('reason')}")
        log.info("💧 %s riego %s (canal=%s)", node_id,
                 "ON" if sol_active else "OFF", sol.get("canal"))

    insert_audit(conn, "ingest_ok", node_id)

    hsi_val = p.get("hsi", {}).get("value", 0)
    bat = p.get("bat_pct", 0)
    log.info("✓ %s HSI=%.3f bat=%d%% calidad=%s", node_id, hsi_val, bat, calidad)


def _handle_alert(conn, node_id: str, p: dict):
    """Procesa alerta HSI del nodo."""
    hsi_val = p.get("hsi", {}).get("value", 0)
    estadio = p.get("gdd", {}).get("estadio", "?")
    insert_audit(conn, "alert_hsi", node_id,
                 f"hsi={hsi_val:.3f} estadio={estadio}")
    log.warning("⚠ ALERTA %s: HSI=%.3f estadio=%s", node_id, hsi_val, estadio)


def _handle_status(conn, node_id: str, p: dict):
    """Procesa heartbeat de estado."""
    bat = p.get("bat_pct", 0)
    iso = p.get("iso_nodo", 100)
    insert_audit(conn, "heartbeat", node_id, f"bat={bat}% iso={iso}")
    log.debug("♥ %s bat=%d%% iso=%d", node_id, bat, iso)


# ── Main ─────────────────────────────────────────────────────────

def main():
    log.info("Iniciando MQTT ingester → PostgreSQL")
    log.info("  Broker: %s:%d", MQTT_BROKER, MQTT_PORT)
    log.info("  DB: %s", DB_DSN.split("@")[-1])  # no loguear credenciales

    conn = get_db_conn()
    log.info("  PostgreSQL conectado")

    client = mqtt.Client(
        client_id="hydrovision-ingester",
        protocol=mqtt.MQTTv5,
        userdata={"db": conn},
    )
    client.on_connect = on_connect
    client.on_message = on_message

    # Reconexión automática
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        log.info("Detenido por usuario")
    finally:
        client.disconnect()
        conn.close()


if __name__ == "__main__":
    main()
