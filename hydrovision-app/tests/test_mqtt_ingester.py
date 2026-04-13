"""
test_mqtt_ingester.py — Tests unitarios para mqtt_ingester.py
HydroVision AG | TRL 4

Testea el parsing y procesamiento de payloads MQTT sin necesidad
de un broker real ni una base de datos PostgreSQL.

Ejecutar:
    cd mvc && python -m pytest tests/test_mqtt_ingester.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Ajustar path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock psycopg2 y paho.mqtt antes del import
sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.extras"] = MagicMock()
sys.modules["paho"] = MagicMock()
sys.modules["paho.mqtt"] = MagicMock()
sys.modules["paho.mqtt.client"] = MagicMock()

import mqtt_ingester as ingester


# ── Fixtures ─────────────────────────────────────────────────────

def _sample_payload() -> dict:
    """Payload v1 completo como lo envía el nodo."""
    return {
        "v": 1,
        "node_id": "HV-A1B2C3D4",
        "ts": 1712678400,
        "cycle": 142,
        "env": {
            "t_air": 28.5,
            "rh": 45.2,
            "wind_ms": 2.3,
            "rain_mm": 0.0,
            "rad_wm2": 850,
        },
        "thermal": {
            "tc_mean": 31.24,
            "tc_max": 33.10,
            "tc_wet": 25.80,
            "tc_dry": 38.50,
            "cwsi": 0.425,
            "valid_pixels": 180,
            "n_frames": 5,
        },
        "dendro": {
            "mds_mm": 0.0832,
            "mds_norm": 0.620,
        },
        "hsi": {
            "value": 0.523,
            "w_cwsi": 0.35,
            "w_mds": 0.65,
            "wind_override": False,
        },
        "gps": {
            "lat": -31.201345,
            "lon": -64.092678,
        },
        "bat_pct": 87,
        "pm2_5": 12,
        "calidad_captura": "ok",
        "gdd": {
            "acum": 1245.5,
            "estadio": "envero",
        },
        "iso_nodo": 92,
        "solenoid": {
            "canal": 1,
            "active": False,
            "reason": "off",
            "ciclos_activo": 0,
        },
        "varietal": "malbec",
    }


def _make_mqtt_msg(topic: str, payload: dict):
    """Simula un mensaje MQTT."""
    msg = MagicMock()
    msg.topic = topic
    msg.payload = json.dumps(payload).encode("utf-8")
    return msg


# ── Tests ────────────────────────────────────────────────────────

class TestPayloadParsing:
    """Verifica que el ingester extrae correctamente los campos del payload."""

    def test_telemetry_inserts_all_fields(self):
        """insert_telemetry debe generar un INSERT con todos los campos del payload v1."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        p = _sample_payload()
        ingester.insert_telemetry(conn, p)

        cursor.execute.assert_called_once()
        sql, values = cursor.execute.call_args[0]

        # Verificar que los valores clave estan en la tupla
        assert "HV-A1B2C3D4" in values  # node_id
        assert 1712678400 in values       # ts
        assert 0.425 in values            # cwsi
        assert 0.523 in values            # hsi value
        assert 0.0832 in values           # mds_mm
        assert 28.5 in values             # t_air
        assert 87 in values               # bat_pct
        assert "ok" in values             # calidad
        assert "real" in values           # origen
        assert 850 in values              # rad_wm2
        assert 92 in values               # iso_nodo
        assert 1245.5 in values           # gdd_acum
        assert "envero" in values         # estadio
        assert "malbec" in values         # varietal

    def test_audit_insert(self):
        """insert_audit debe insertar un registro de auditoría."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        ingester.insert_audit(conn, "ingest_ok", "HV-TEST", "detail")

        cursor.execute.assert_called_once()
        _, values = cursor.execute.call_args[0]
        assert values == ("ingest_ok", "HV-TEST", "detail")


class TestCalidadDescarte:
    """Verifica que payloads con calidad no ok se descartan correctamente."""

    @pytest.mark.parametrize("calidad", ["fumigacion", "lluvia", "nocturno", "lente_sucio"])
    def test_descarte_por_calidad(self, calidad):
        """Payloads con calidad de descarte no deben insertarse en telemetry."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        p = _sample_payload()
        p["calidad_captura"] = calidad

        ingester._handle_telemetry(conn, "HV-TEST", p)

        # Solo debe haber llamado insert_audit (descartado), no insert_telemetry
        calls = [c[0][0] for c in cursor.execute.call_args_list]
        sql_calls = " ".join(str(c) for c in calls)
        assert "INSERT INTO telemetry" not in sql_calls

    def test_calidad_ok_si_inserta(self):
        """Payloads con calidad=ok deben insertarse normalmente."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        p = _sample_payload()
        ingester._handle_telemetry(conn, "HV-TEST", p)

        all_sql = " ".join(str(c[0][0]) for c in cursor.execute.call_args_list)
        assert "INSERT INTO telemetry" in all_sql


class TestTopicRouting:
    """Verifica que on_message rutea correctamente por tipo de topic."""

    def test_telemetry_topic(self):
        """Topic hydrovision/NODE/telemetry debe llamar _handle_telemetry."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = MagicMock()
        userdata = {"db": conn}
        msg = _make_mqtt_msg("hydrovision/HV-TEST/telemetry", _sample_payload())

        with patch.object(ingester, "_handle_telemetry") as mock_t:
            ingester.on_message(client, userdata, msg)
            mock_t.assert_called_once()
            assert mock_t.call_args[0][1] == "HV-TEST"

    def test_alert_topic(self):
        """Topic hydrovision/NODE/alert debe llamar _handle_alert."""
        conn = MagicMock()
        client = MagicMock()
        userdata = {"db": conn}
        msg = _make_mqtt_msg("hydrovision/HV-TEST/alert", _sample_payload())

        with patch.object(ingester, "_handle_alert") as mock_a:
            ingester.on_message(client, userdata, msg)
            mock_a.assert_called_once()

    def test_status_topic(self):
        """Topic hydrovision/NODE/status debe llamar _handle_status."""
        conn = MagicMock()
        client = MagicMock()
        userdata = {"db": conn}
        msg = _make_mqtt_msg("hydrovision/HV-TEST/status", {"bat_pct": 85, "iso_nodo": 95})

        with patch.object(ingester, "_handle_status") as mock_s:
            ingester.on_message(client, userdata, msg)
            mock_s.assert_called_once()

    def test_invalid_json_no_crash(self):
        """Payload JSON invalido no debe crashear el ingester."""
        conn = MagicMock()
        client = MagicMock()
        userdata = {"db": conn}
        msg = MagicMock()
        msg.topic = "hydrovision/HV-TEST/telemetry"
        msg.payload = b"not json at all"

        # No debe lanzar excepcion
        ingester.on_message(client, userdata, msg)

    def test_short_topic_ignored(self):
        """Topics con menos de 3 partes deben ignorarse."""
        conn = MagicMock()
        client = MagicMock()
        userdata = {"db": conn}
        msg = _make_mqtt_msg("hydrovision/only", {})

        with patch.object(ingester, "_handle_telemetry") as mock_t:
            ingester.on_message(client, userdata, msg)
            mock_t.assert_not_called()


class TestIrrigationStateChange:
    """Verifica detección de cambios de estado de riego."""

    def test_irrigation_on_detected(self):
        """Cambio de active=False a active=True debe registrar irrigate_on."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # Reset state
        ingester._irrigation_state.clear()

        p = _sample_payload()
        p["solenoid"]["active"] = True
        p["solenoid"]["reason"] = "hsi"

        ingester._handle_telemetry(conn, "HV-TEST", p)

        all_sql = " ".join(str(c[0][0]) for c in cursor.execute.call_args_list)
        assert "INSERT INTO irrigation_log" in all_sql

    def test_no_change_no_log(self):
        """Sin cambio de estado no debe registrar en irrigation_log."""
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        ingester._irrigation_state["HV-STABLE"] = False
        p = _sample_payload()
        p["node_id"] = "HV-STABLE"
        p["solenoid"]["active"] = False

        ingester._handle_telemetry(conn, "HV-STABLE", p)

        all_sql = " ".join(str(c[0][0]) for c in cursor.execute.call_args_list)
        assert "INSERT INTO irrigation_log" not in all_sql
