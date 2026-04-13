"""
Calibración dinámica del baseline CWSI — HydroVision AG
========================================================
Gestiona los baselines Tc_wet y Tc_dry del CWSI y los actualiza
automáticamente usando eventos de campo sin intervención humana.

Eventos que disparan recalibración:
1. Lluvia significativa (MDS ≈ 0): planta al máximo de hidratación →
   la captura térmica inmediata provee el Tc_wet real de ESE nodo.
2. Deriva térmica detectada: CWSI consistentemente < 0 o > 1 por
   varias horas → el baseline se desplazó (cambio fenológico, sensor).
3. Actualización periódica (Mes 4–9): promedio rodante de capturas
   con MDS < umbral_bienestar.

Baselines de fábrica (inicialización):
- Tc_wet = Ta + (a - b*VPD)  donde a=1.5, b=1.8 (NWSB Jackson 1981, adaptado vid)
- Tc_dry = Ta + dT_dry        donde dT_dry ≈ 4.5°C (hoja sin transpiración)
"""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Baseline NWSB de fábrica (Jackson 1981 — adaptado vid Malbec)
# ---------------------------------------------------------------------------
# dT_wet = Tc_wet - Ta = A - B * VPD
NWSB_A = 1.5   # [°C] intercepto — calibrado para vid en Argentina
NWSB_B = 1.8   # [°C/kPa] pendiente VPD
DT_DRY = 4.5   # [°C] Tc_dry - Ta para hoja sin transpiración


def nwsb_tc_wet(ta: float, vpd_kpa: float) -> float:
    """Baseline inferior de fábrica: temperatura de hoja bien regada."""
    return ta + NWSB_A - NWSB_B * vpd_kpa


def nwsb_tc_dry(ta: float) -> float:
    """Baseline superior de fábrica: hoja sin transpiración."""
    return ta + DT_DRY


# ---------------------------------------------------------------------------
# Snapshot de calibración
# ---------------------------------------------------------------------------
@dataclass
class CalibrationSnapshot:
    """
    Un punto de calibración capturado en campo.
    Cada snapshot representa la temperatura media de canopia medida
    por el nodo en condiciones conocidas.
    """
    timestamp_iso: str          # ISO 8601
    tc_measured: float          # Temperatura canopia medida [°C]
    ta: float                   # Temperatura aire [°C]
    vpd_kpa: float              # VPD [kPa]
    mds_um: float               # MDS del extensómetro [µm] en ese momento
    trigger: str                # "rain", "schedule", "manual"
    confidence: float           # 0-1, qué tan confiable es este punto


# ---------------------------------------------------------------------------
# Gestor de baseline dinámico
# ---------------------------------------------------------------------------
class CWSIBaseline:
    """
    Baseline dinámico del CWSI con auto-calibración por eventos de campo.

    Mantiene:
    - tc_wet_offset: corrección aditiva al NWSB (se actualiza con eventos)
    - tc_dry_offset: corrección al baseline superior
    - buffer de snapshots recientes para estimación robusta

    El offset parte en 0 (usa el NWSB de Jackson 1981 sin modificar).
    Con cada evento de calibración, el offset se acerca al valor real del nodo.
    """

    # MDS por debajo del cual consideramos que la planta está bien hidratada [µm]
    MDS_WELLWATERED_THRESHOLD = 50.0

    # Ventana de snapshots para estimación rodante
    SNAPSHOT_BUFFER = 30

    # Factor de aprendizaje para actualización del offset (EMA)
    LEARNING_RATE = 0.25

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.tc_wet_offset: float = 0.0   # corrección al NWSB (°C)
        self.tc_dry_offset: float = 0.0   # corrección al DT_DRY (°C)
        self.snapshots: deque[CalibrationSnapshot] = deque(maxlen=self.SNAPSHOT_BUFFER)
        self.calibration_count: int = 0
        self.last_rain_calibration: Optional[str] = None

    # --- Getters de baseline ---

    def tc_wet(self, ta: float, vpd_kpa: float) -> float:
        """Baseline inferior calibrado para este nodo."""
        return nwsb_tc_wet(ta, vpd_kpa) + self.tc_wet_offset

    def tc_dry(self, ta: float) -> float:
        """Baseline superior calibrado para este nodo."""
        return nwsb_tc_dry(ta) + self.tc_dry_offset

    def compute_cwsi(self, tc: float, ta: float, vpd_kpa: float) -> float:
        """
        CWSI usando los baselines calibrados de este nodo.
        Retorna NaN si los baselines son degenerados (Tc_dry ≈ Tc_wet).
        """
        wet = self.tc_wet(ta, vpd_kpa)
        dry = self.tc_dry(ta)
        denom = dry - wet
        if abs(denom) < 0.2:
            logger.warning(f"[{self.node_id}] Baselines degenerados: Tc_wet={wet:.2f}, Tc_dry={dry:.2f}")
            return float("nan")
        return float(np.clip((tc - wet) / denom, 0.0, 1.0))

    # --- Actualización de baseline por eventos ---

    def update_rain(
        self,
        tc_measured: float,
        ta: float,
        vpd_kpa: float,
        mds_um: float,
        timestamp_iso: str,
    ) -> bool:
        """
        Evento de lluvia: si MDS ≈ 0 la planta está al máximo de hidratación.
        Tc_measured en ese momento es el Tc_wet real del nodo → recalibrar.

        Returns:
            True si se aplicó la calibración, False si MDS era demasiado alto.
        """
        if mds_um > self.MDS_WELLWATERED_THRESHOLD:
            logger.debug(
                f"[{self.node_id}] Rain event ignorado: MDS={mds_um:.1f}µm > umbral"
            )
            return False

        expected_wet = nwsb_tc_wet(ta, vpd_kpa)
        error = tc_measured - expected_wet

        # EMA del offset
        self.tc_wet_offset = (
            (1 - self.LEARNING_RATE) * self.tc_wet_offset
            + self.LEARNING_RATE * error
        )

        snap = CalibrationSnapshot(
            timestamp_iso=timestamp_iso,
            tc_measured=tc_measured,
            ta=ta,
            vpd_kpa=vpd_kpa,
            mds_um=mds_um,
            trigger="rain",
            confidence=min(1.0, (self.MDS_WELLWATERED_THRESHOLD - mds_um) / self.MDS_WELLWATERED_THRESHOLD + 0.5),
        )
        self.snapshots.append(snap)
        self.calibration_count += 1
        self.last_rain_calibration = timestamp_iso

        logger.info(
            f"[{self.node_id}] Calibración por lluvia: tc_wet_offset={self.tc_wet_offset:+.3f}°C "
            f"(error={error:+.3f}°C, MDS={mds_um:.1f}µm)"
        )
        return True

    def update_scheduled(
        self,
        tc_measured: float,
        ta: float,
        vpd_kpa: float,
        mds_um: float,
        timestamp_iso: str,
    ) -> None:
        """
        Actualización periódica (cada sesión Scholander).
        Solo actualiza si la planta está razonablemente hidratada (MDS bajo).
        """
        confidence = max(0.0, 1.0 - mds_um / 500.0)
        if confidence < 0.2:
            return

        expected_wet = nwsb_tc_wet(ta, vpd_kpa)
        error = tc_measured - expected_wet

        # Aprendizaje más lento que el evento de lluvia
        lr = self.LEARNING_RATE * confidence * 0.5
        self.tc_wet_offset = (1 - lr) * self.tc_wet_offset + lr * error

        snap = CalibrationSnapshot(
            timestamp_iso=timestamp_iso,
            tc_measured=tc_measured,
            ta=ta,
            vpd_kpa=vpd_kpa,
            mds_um=mds_um,
            trigger="schedule",
            confidence=confidence,
        )
        self.snapshots.append(snap)
        self.calibration_count += 1

    def detect_drift(self, cwsi_history: list[float]) -> Tuple[bool, str]:
        """
        Detecta deriva del baseline a partir del historial de CWSI.

        Señales de deriva:
        - CWSI < 0 consistentemente: Tc_wet está sobrestimado (muy alto)
        - CWSI > 1 consistentemente: Tc_wet está subestimado (muy bajo)
        - CWSI = constante durante días: sensor con ruido o baseline fijo incorrecto

        Args:
            cwsi_history: lista de valores CWSI de las últimas sesiones

        Returns:
            (hay_deriva, descripción)
        """
        if len(cwsi_history) < 5:
            return False, "sin datos suficientes"

        arr = np.array([v for v in cwsi_history if not np.isnan(v)])
        if len(arr) < 5:
            return False, "sin datos válidos"

        mean_cwsi = arr.mean()
        if mean_cwsi < 0.02:
            return True, f"CWSI sistemáticamente bajo ({mean_cwsi:.3f}) — Tc_wet sobreestimado"
        if mean_cwsi > 0.98:
            return True, f"CWSI sistemáticamente alto ({mean_cwsi:.3f}) — Tc_wet subestimado"
        if arr.std() < 0.01 and len(arr) > 10:
            return True, f"CWSI sin variación (std={arr.std():.4f}) — posible falla de sensor"

        return False, "sin deriva detectada"

    # --- Persistencia ---

    def save(self, path: Path) -> None:
        """Guarda el estado de calibración en JSON para recuperación ante reinicio."""
        state = {
            "node_id": self.node_id,
            "tc_wet_offset": self.tc_wet_offset,
            "tc_dry_offset": self.tc_dry_offset,
            "calibration_count": self.calibration_count,
            "last_rain_calibration": self.last_rain_calibration,
            "snapshots": [asdict(s) for s in list(self.snapshots)[-10:]],
        }
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        logger.info(f"[{self.node_id}] Baseline guardado en {path}")

    @classmethod
    def load(cls, path: Path) -> "CWSIBaseline":
        """Carga estado de calibración desde JSON."""
        state = json.loads(path.read_text())
        obj = cls(node_id=state["node_id"])
        obj.tc_wet_offset = state["tc_wet_offset"]
        obj.tc_dry_offset = state["tc_dry_offset"]
        obj.calibration_count = state["calibration_count"]
        obj.last_rain_calibration = state.get("last_rain_calibration")
        for snap_dict in state.get("snapshots", []):
            obj.snapshots.append(CalibrationSnapshot(**snap_dict))
        return obj

    def summary(self) -> dict:
        return {
            "node_id": self.node_id,
            "tc_wet_offset": round(self.tc_wet_offset, 4),
            "tc_dry_offset": round(self.tc_dry_offset, 4),
            "calibration_count": self.calibration_count,
            "last_rain_calibration": self.last_rain_calibration,
            "n_snapshots": len(self.snapshots),
        }
