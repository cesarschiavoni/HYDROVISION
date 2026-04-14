"""
routers/inference.py — Endpoints de inferencia PINN y validacion
HydroVision AG
"""

import csv
import datetime
import io
import json
import math
import random
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import (
    ZONES, _NODE_IRRIGATION, _NODE_SOL_SIM,
    CWSI_MEDIO, CWSI_ALTO, CWSI_IRRIGATE,
    _fusion, _vpd_kpa, _stress_label, _fenologia_zona,
    _ky_para_varietal, _ensure_node_config, _zona_para_punto,
    _reload_zones, _check_overlap, _zone_bounds, _zone_bounds_from_vertices,
    _zone_centroid_from_vertices, _area_ha_zona, _calcular_superficie_ha,
    _nodos_recomendados_zona, _resumen_varietales, _seed_defaults,
    _autoasignar_zonas_nodos,
)
from app.deps import get_db, check_rate_limit as _check_rate_limit, verify_hmac as _verify_hmac, audit as _audit
from app.models import (
    AppConfig, AuditLog, Base, IrrigationLog, NodeConfig,
    SessionLocal, Telemetry, ZoneConfig, engine,
    APP_CONFIG_DEFAULTS, ZONE_DEFAULTS,
)
from app.schemas import (
    NodePayload, ZoneIn, NodeConfigIn, ConfigIn,
    InferenceRequest, InferenceResponse,
)


router = APIRouter()

# ═══════════════════════════════════════════════════════════════════════════
# PINN model — lazy load
# ═══════════════════════════════════════════════════════════════════════════
_PINN_MODEL = None
_PINN_AVAILABLE = False

try:
    import torch
    _TORCH_OK = True
except ImportError:
    _TORCH_OK = False


def _load_pinn_model():
    """Carga lazy del modelo PINN (INT8 o FP32 según disponibilidad)."""
    global _PINN_MODEL, _PINN_AVAILABLE
    if not _TORCH_OK:
        return

    _INVESTIGADOR_PATH = Path(__file__).parent.parent / "investigador"
    model_paths = [
        _INVESTIGADOR_PATH / "models" / "edge" / "hydrovision_cwsi_int8.tflite",
        _INVESTIGADOR_PATH / "models" / "checkpoints" / "best_finetune.pt",
        _INVESTIGADOR_PATH / "models" / "checkpoints" / "best_synthetic.pt",
    ]

    for mp in model_paths:
        if mp.exists():
            try:
                if str(_INVESTIGADOR_PATH / "02_modelo") not in sys.path:
                    sys.path.insert(0, str(_INVESTIGADOR_PATH / "02_modelo"))
                from pinn_model import HydroVisionPINN

                if mp.suffix == ".pt":
                    ckpt = torch.load(mp, map_location="cpu", weights_only=False)
                    model = HydroVisionPINN(pretrained=False)
                    model.load_state_dict(ckpt.get("model_state", ckpt))
                    model.eval()
                    _PINN_MODEL = model
                    _PINN_AVAILABLE = True
                    return
            except Exception:
                continue


@router.post("/api/inference", response_model=InferenceResponse)
def post_inference(req: InferenceRequest):
    """
    Inferencia PINN: recibe imagen térmica 120×160 y retorna CWSI estimado.
    Latencia objetivo: < 1s en CPU (< 200ms en ESP32-S3 con INT8).
    """
    if not _TORCH_OK:
        raise HTTPException(503, "PyTorch no disponible en este servidor")

    if _PINN_MODEL is None:
        _load_pinn_model()

    if not _PINN_AVAILABLE:
        raise HTTPException(503, "Modelo PINN no encontrado — ejecutar train.py primero")

    import time as _time
    try:
        img = torch.tensor(req.thermal_image, dtype=torch.float32)
        if img.shape != (120, 160):
            raise HTTPException(
                422, f"Imagen debe ser 120x160, recibida: {list(img.shape)}"
            )
        img = img.unsqueeze(0).unsqueeze(0)  # (1, 1, 120, 160)

        t0 = _time.perf_counter()
        with torch.no_grad():
            out = _PINN_MODEL(img)
        t1 = _time.perf_counter()

        cwsi_val = out[0].item() if isinstance(out, tuple) else out.item()
        delta_t = out[1].item() if isinstance(out, tuple) and len(out) > 1 else 0.0

        return InferenceResponse(
            cwsi=round(cwsi_val, 4),
            delta_t=round(delta_t, 2),
            latency_ms=round((t1 - t0) * 1000, 1),
            model_type="PINN-FP32-CPU",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error en inferencia: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# Validation report endpoint — César #3
# GET /api/validacion/reporte: CSV con HSI vs ψ_stem para validación TRL 4
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/api/validacion/reporte")
def get_validacion_reporte(
    days: int = Query(default=30, ge=1, le=365),
    node_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Genera CSV de validación HSI vs telemetría para correlación con ψ_stem Scholander.

    Columnas: timestamp, node_id, cwsi, hsi, mds_mm, t_air, rh, wind_ms,
              bat_pct, calidad, origen, estadio_fenologico, ky,
              psi_stem_estimado (MPa, estimado por HSI→ψ_stem calibración Malbec)

    La columna psi_stem_estimado se calcula como:
      ψ_stem ≈ -0.2 - 1.8 × HSI  (R² ≈ 0.80, Scholander Malbec Colonia Caroya)
    Este valor es la estimación del nodo — la validación requiere medir ψ_stem
    real con bomba de presión en campo y comparar.
    """
    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    q = db.query(Telemetry).filter(Telemetry.created_at >= since)
    if node_id:
        q = q.filter(Telemetry.node_id == node_id)
    q = q.order_by(Telemetry.created_at.asc())
    rows = q.all()

    if not rows:
        raise HTTPException(404, "Sin datos de telemetría en el período")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "timestamp", "node_id", "cwsi", "hsi", "mds_mm",
        "t_air", "rh", "wind_ms", "bat_pct", "calidad", "origen",
        "psi_stem_estimado_MPa",
    ])
    for r in rows:
        # Estimación ψ_stem desde HSI (calibración lineal Malbec)
        psi_stem_est = round(-0.2 - 1.8 * r.hsi, 3) if r.hsi is not None else ""
        writer.writerow([
            r.created_at.isoformat() if r.created_at else "",
            r.node_id, r.cwsi, r.hsi, r.mds_mm,
            r.t_air, r.rh, r.wind_ms, r.bat_pct, r.calidad, r.origen,
            psi_stem_est,
        ])

    buf.seek(0)
    filename = f"validacion_hsi_psi_stem_{days}d.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Nodo latest endpoint — César #3
# GET /api/nodos/{node_id}/latest: última lectura de un nodo específico
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/api/nodos/{node_id}/latest")
def get_nodo_latest(node_id: str, db: Session = Depends(get_db)):
    """Última lectura de telemetría de un nodo específico."""
    row = (
        db.query(Telemetry)
        .filter(Telemetry.node_id == node_id)
        .order_by(Telemetry.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(404, f"Nodo '{node_id}' sin datos")
    return {
        "node_id": row.node_id,
        "timestamp": row.created_at.isoformat() if row.created_at else None,
        "cwsi": row.cwsi,
        "hsi": row.hsi,
        "mds_mm": row.mds_mm,
        "t_air": row.t_air,
        "rh": row.rh,
        "wind_ms": row.wind_ms,
        "rain_mm": row.rain_mm,
        "bat_pct": row.bat_pct,
        "calidad": row.calidad,
        "origen": row.origen,
    }
