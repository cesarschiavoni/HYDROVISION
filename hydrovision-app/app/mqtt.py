"""
mqtt.py — Cliente MQTT: consumer de telemetría + publisher de comandos
HydroVision AG

Arquitectura:
  Nodo → LoRa → Gateway → MQTT Broker (buffer persistente)
                              ↓
                    Consumer (este módulo) → DB
                              ↑
                    Publisher (este módulo) ← Dashboard (comandos riego)

Topics:
  hydrovision/{node_id}/telemetry   — nodo publica JSON telemetría (QoS 1)
  hydrovision/{node_id}/command     — app publica comandos al nodo (QoS 1)
  hydrovision/{node_id}/downlink    — app publica respuesta post-ingest (QoS 0)
"""

import json
import logging
import threading

import paho.mqtt.client as mqtt

from app.config import MQTT_BROKER, MQTT_PORT
from app.models import SessionLocal

logger = logging.getLogger("hydrovision.mqtt")

# Tópics
TOPIC_TELEMETRY = "hydrovision/+/telemetry"       # suscripción wildcard
TOPIC_COMMAND   = "hydrovision/{node_id}/command"  # publicación por nodo
TOPIC_DOWNLINK  = "hydrovision/{node_id}/downlink" # respuesta post-ingest

# Cliente global
_client: mqtt.Client | None = None
_thread: threading.Thread | None = None


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def _on_connect(client, userdata, flags, reason_code, properties=None):
    """Al conectar (o reconectar) suscribir a telemetría."""
    logger.info("MQTT conectado al broker %s:%s (rc=%s)", MQTT_BROKER, MQTT_PORT, reason_code)
    client.subscribe(TOPIC_TELEMETRY, qos=1)
    logger.info("Suscrito a %s", TOPIC_TELEMETRY)


def _on_message(client, userdata, msg):
    """
    Recibe telemetría de un nodo vía MQTT.
    Topic: hydrovision/{node_id}/telemetry
    Payload: JSON con misma estructura que NodePayload.
    """
    try:
        # Extraer node_id del topic
        parts = msg.topic.split("/")
        if len(parts) != 3 or parts[2] != "telemetry":
            return

        payload_dict = json.loads(msg.payload.decode("utf-8"))
        node_id = parts[1]

        # Asegurar consistencia: el node_id del topic manda
        payload_dict["node_id"] = node_id

        # Procesar con sesión de DB propia (estamos en hilo background)
        from app.core import process_ingest

        db = SessionLocal()
        try:
            resp = process_ingest(payload_dict, db, ip="mqtt")
            logger.debug("Ingest MQTT %s → %s", node_id, resp.get("status"))

            # Publicar downlink al nodo (respuesta con varietal, sol_sim, etc.)
            if resp.get("status") == "ok":
                topic = TOPIC_DOWNLINK.format(node_id=node_id)
                client.publish(topic, json.dumps(resp), qos=0)
        finally:
            db.close()

    except json.JSONDecodeError:
        logger.warning("MQTT payload inválido (no es JSON): topic=%s", msg.topic)
    except Exception:
        logger.exception("Error procesando mensaje MQTT: topic=%s", msg.topic)


def _on_disconnect(client, userdata, flags, reason_code, properties=None):
    logger.warning("MQTT desconectado (rc=%s). Reconectando automáticamente...", reason_code)


# ---------------------------------------------------------------------------
# Publisher — enviar comandos al nodo
# ---------------------------------------------------------------------------

def publish_command(node_id: str, command: dict) -> bool:
    """
    Publica un comando al nodo vía MQTT.

    Ejemplo:
        publish_command("HV-0042", {"irrigate": True})
        → topic: hydrovision/HV-0042/command
        → payload: {"irrigate": true}

    El gateway LoRa lo recibe y lo transmite al nodo en el siguiente
    downlink LoRa (clase A: después de un uplink del nodo).
    """
    if _client is None or not _client.is_connected():
        logger.warning("MQTT no conectado — comando no enviado a %s", node_id)
        return False

    topic = TOPIC_COMMAND.format(node_id=node_id)
    result = _client.publish(topic, json.dumps(command), qos=1)
    logger.info("Comando MQTT → %s: %s (rc=%s)", topic, command, result.rc)
    return result.rc == mqtt.MQTT_ERR_SUCCESS


# ---------------------------------------------------------------------------
# Lifecycle — start / stop
# ---------------------------------------------------------------------------

def start_mqtt():
    """
    Inicia el cliente MQTT en un hilo background.
    Se llama desde el lifespan de FastAPI.
    Reconecta automáticamente si se pierde la conexión.
    """
    global _client, _thread

    _client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="hydrovision-app",
        clean_session=False,  # sesión persistente — no pierde mensajes QoS 1
    )
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.on_disconnect = _on_disconnect

    # Reconnect automático (backoff 1-30s)
    _client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        _client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except (ConnectionRefusedError, OSError) as e:
        logger.warning(
            "No se pudo conectar al broker MQTT %s:%s (%s). "
            "La app funciona sin MQTT — los nodos pueden usar /ingest HTTP como fallback.",
            MQTT_BROKER, MQTT_PORT, e,
        )
        _client = None
        return

    # loop_start() crea un hilo daemon que maneja reconnect + mensajes
    _client.loop_start()
    _thread = True
    logger.info("MQTT consumer iniciado (broker=%s:%s)", MQTT_BROKER, MQTT_PORT)


def stop_mqtt():
    """Detiene el cliente MQTT limpiamente."""
    global _client, _thread
    if _client:
        _client.loop_stop()
        _client.disconnect()
        logger.info("MQTT consumer detenido")
    _client = None
    _thread = None
