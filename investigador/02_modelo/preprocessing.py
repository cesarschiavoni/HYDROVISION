"""
preprocessing.py — Preprocesamiento de datos de campo para el modelo PINN
HydroVision AG | ML Engineer / 02_modelo

Responsabilidades:
    1. Convertir payload JSON del nodo en tensores listos para el modelo
    2. Calcular VPD a partir de T_air + HR
    3. Aplicar normalización de frame térmico
    4. Preparar el dataset Scholander (labels.json) a partir de mediciones de campo
    5. Exportar batches para inferencia desde telemetría en producción

Uso como módulo:
    from preprocessing import FramePreprocessor, compute_vpd, build_scholander_label

Uso como CLI (construir labels.json desde planilla CSV de campo):
    python preprocessing.py --mode scholander \\
        --input ../data/scholander/mediciones_campo.csv \\
        --frames-dir ../data/scholander/frames/ \\
        --output ../data/scholander/labels.json

    python preprocessing.py --mode infer \\
        --payload payload_ejemplo.json \\
        --frame frame_ejemplo.npy \\
        --checkpoint ../models/checkpoints/best_finetune.pt
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Constantes físicas
# ---------------------------------------------------------------------------
FRAME_H = 120       # altura píxeles del frame térmico (MLX90640 upscaled)
FRAME_W = 160       # ancho
T_NORM_MIN = 5.0    # °C — límite inferior para normalización [0, 1]
T_NORM_RANGE = 50.0 # °C — rango (5–55°C cubre todo el rango operativo del campo)


# ---------------------------------------------------------------------------
# VPD: cálculo desde T_air + HR
# ---------------------------------------------------------------------------
def compute_vpd(t_air_c: float, rh_pct: float) -> float:
    """
    Calcula el Déficit de Presión de Vapor (VPD) en kPa.

    Fórmula de Tetens (FAO-56 Allen et al. 1998):
        e_s = 0.6108 × exp(17.27 × T / (T + 237.3))   [kPa]
        VPD = e_s × (1 − RH/100)

    Args:
        t_air_c: temperatura del aire [°C]
        rh_pct:  humedad relativa [%] (0–100)

    Returns:
        VPD en kPa

    Ejemplos:
        >>> compute_vpd(28.0, 45.0)
        2.12...
        >>> compute_vpd(25.0, 80.0)
        0.634...
    """
    e_s = 0.6108 * np.exp(17.27 * t_air_c / (t_air_c + 237.3))
    return float(e_s * (1.0 - rh_pct / 100.0))


# ---------------------------------------------------------------------------
# Normalización de frame térmico
# ---------------------------------------------------------------------------
def normalize_frame(
    frame_c: np.ndarray,
    t_min: float = T_NORM_MIN,
    t_range: float = T_NORM_RANGE,
) -> np.ndarray:
    """
    Normaliza un frame térmico de °C a [0, 1].

    Rango operativo: [T_NORM_MIN, T_NORM_MIN + T_NORM_RANGE] = [5°C, 55°C].
    Valores fuera de rango se recortan antes de normalizar (no se descartan).

    Args:
        frame_c:  ndarray float32 de forma (H, W) o (1, H, W) en °C
        t_min:    temperatura mínima del rango de normalización [°C]
        t_range:  ancho del rango [°C]

    Returns:
        ndarray float32 normalizado [0, 1], misma forma que la entrada
    """
    return np.clip((frame_c.astype(np.float32) - t_min) / t_range, 0.0, 1.0)


def denormalize_frame(frame_norm: np.ndarray,
                      t_min: float = T_NORM_MIN,
                      t_range: float = T_NORM_RANGE) -> np.ndarray:
    """Invierte normalize_frame: [0, 1] → °C."""
    return frame_norm.astype(np.float32) * t_range + t_min


# ---------------------------------------------------------------------------
# Carga y validación de frame .npy
# ---------------------------------------------------------------------------
def load_frame(path: str | Path) -> np.ndarray:
    """
    Carga un frame térmico desde archivo .npy.

    El frame debe ser float32 (H, W) con temperaturas en °C.
    Si el archivo tiene forma (1, H, W) se elimina la dimensión de canal.

    Args:
        path: ruta al archivo .npy

    Returns:
        ndarray float32 (120, 160) en °C

    Raises:
        FileNotFoundError si el archivo no existe
        ValueError si la forma no es compatible (120×160 o similar)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Frame no encontrado: {path}")

    frame = np.load(path).astype(np.float32)

    # Eliminar dimensión de canal si existe
    if frame.ndim == 3 and frame.shape[0] == 1:
        frame = frame.squeeze(0)

    if frame.ndim != 2:
        raise ValueError(f"Frame con forma inesperada: {frame.shape}. Se espera (H, W).")

    # Advertir si las dimensiones no son las nominales del MLX90640
    if frame.shape != (FRAME_H, FRAME_W):
        # Redimensionar si hay diferencia menor
        import cv2 as _cv2
        frame = _cv2.resize(frame, (FRAME_W, FRAME_H), interpolation=_cv2.INTER_LINEAR)

    return frame


# ---------------------------------------------------------------------------
# Preprocesador de frames para el modelo
# ---------------------------------------------------------------------------
class FramePreprocessor:
    """
    Convierte un frame térmico + metadatos en el tensor de entrada del modelo PINN.

    Uso típico (inferencia en producción):
        prep = FramePreprocessor()
        tensor, meta = prep.from_npy("frame_001.npy", vpd=2.3, ta=28.5)
        cwsi_pred, dt_pred = model(tensor.to(device))

    Uso desde payload del nodo:
        tensor, meta = prep.from_payload(payload_json, frames_dir)
    """

    def __init__(
        self,
        t_min: float = T_NORM_MIN,
        t_range: float = T_NORM_RANGE,
    ):
        self.t_min = t_min
        self.t_range = t_range

    def from_npy(
        self,
        frame_path: str | Path,
        vpd: Optional[float] = None,
        ta: Optional[float] = None,
        rh: Optional[float] = None,
    ) -> Tuple[torch.Tensor, dict]:
        """
        Carga y preprocesa un frame .npy en un tensor listo para el modelo.

        Args:
            frame_path: ruta al archivo .npy
            vpd:        VPD en kPa. Si es None, se calcula desde ta+rh.
            ta:         temperatura del aire [°C] (requerido si vpd es None)
            rh:         humedad relativa [%] (requerido si vpd es None)

        Returns:
            tensor:  torch.Tensor (1, 1, 120, 160) float32 normalizado — listo para model()
            meta:    dict con vpd, ta, rh, t_min, t_range para logging
        """
        frame = load_frame(frame_path)
        frame_norm = normalize_frame(frame, self.t_min, self.t_range)

        # Calcular VPD si no se proporcionó directamente
        if vpd is None:
            if ta is None or rh is None:
                raise ValueError("Proporcionar vpd ó (ta + rh) para calcular VPD")
            vpd = compute_vpd(ta, rh)

        tensor = torch.from_numpy(frame_norm).unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)

        meta = {
            "vpd": round(vpd, 4),
            "ta": ta,
            "rh": rh,
            "frame_min_c": float(frame.min()),
            "frame_max_c": float(frame.max()),
            "frame_mean_c": float(frame.mean()),
        }
        return tensor, meta

    def from_payload(
        self,
        payload: dict,
        frames_dir: str | Path,
        frame_filename: Optional[str] = None,
    ) -> Tuple[torch.Tensor, dict]:
        """
        Preprocesa desde un payload JSON de telemetría del nodo HydroVision.

        El payload sigue el contrato definido en diagrama-arquitectura-datos.md:
            payload["env"]["t_air"], payload["env"]["rh"]
            payload["thermal"]["tc_mean"] (o frame .npy separado)

        Args:
            payload:        dict con el payload completo del nodo
            frames_dir:     directorio donde están los .npy del nodo
            frame_filename: nombre del .npy. Si es None, intenta inferir desde
                            payload["ts"] + payload["node_id"].

        Returns:
            tensor, meta (mismo formato que from_npy)
        """
        env = payload.get("env", {})
        ta = float(env.get("t_air", 25.0))
        rh = float(env.get("rh", 50.0))
        vpd = compute_vpd(ta, rh)

        # Inferir nombre del frame si no se especifica
        if frame_filename is None:
            ts = payload.get("ts", 0)
            node_id = payload.get("node_id", "unknown")
            frame_filename = f"{node_id}_{ts}.npy"

        frame_path = Path(frames_dir) / frame_filename
        return self.from_npy(frame_path, vpd=vpd, ta=ta, rh=rh)

    def batch_from_dir(
        self,
        frames_dir: str | Path,
        metadata_list: List[dict],
    ) -> Tuple[torch.Tensor, List[dict]]:
        """
        Preprocesa múltiples frames en un solo batch.

        Args:
            frames_dir:     directorio con los .npy
            metadata_list:  lista de dicts, cada uno con {filename, vpd, ta, rh}

        Returns:
            batch_tensor: (N, 1, 120, 160) float32
            metas:        lista de dicts con metadatos de cada frame
        """
        tensors, metas = [], []
        for m in metadata_list:
            t, meta = self.from_npy(
                Path(frames_dir) / m["filename"],
                vpd=m.get("vpd"),
                ta=m.get("ta"),
                rh=m.get("rh"),
            )
            tensors.append(t.squeeze(0))  # (1, H, W)
            metas.append(meta)

        batch = torch.stack(tensors)  # (N, 1, H, W)
        return batch, metas


# ---------------------------------------------------------------------------
# Construcción del dataset Scholander
# ---------------------------------------------------------------------------
@dataclass
class ScholanderEntry:
    """
    Un par de calibración CWSI + ψ_stem medido con cámara de presión Scholander.

    Corresponds al contrato labels.json descrito en pasos-modelos.md.
    """
    filename: str       # nombre del .npy del frame
    cwsi: float         # CWSI calculado en campo: (Tc_mean - Tc_wet) / (Tc_dry - Tc_wet)
    psi_stem: float     # potencial hídrico de tallo [MPa] (negativo: -0.3 a -2.0)
    vpd: float          # VPD [kPa]
    ta: float           # temperatura del aire [°C]
    etc_regime: float   # fracción de ETc de la zona (0.0, 0.15, 0.40, 0.65, 1.0)
    session: int = 1    # número de sesión Scholander (1–4)
    zone: str = "A"     # zona de riego (A, B, C, D, E)
    fecha: str = ""     # fecha ISO YYYY-MM-DD
    gdd: float = 0.0    # grados-día acumulados al momento de la medición


def build_scholander_label(
    filename: str,
    cwsi: float,
    psi_stem: float,
    vpd: float,
    ta: float,
    etc_regime: float,
    session: int = 1,
    zone: str = "A",
    fecha: str = "",
    gdd: float = 0.0,
) -> dict:
    """
    Construye una entrada de labels.json para el dataset Scholander.

    Usado para armar el dataset a partir de las planillas de campo.

    Args:
        filename:    nombre del archivo .npy del frame (ej: "HV-A4CF12B3E7_1743980400.npy")
        cwsi:        CWSI calculado en campo [0-1]
        psi_stem:    potencial hídrico medido con Scholander [MPa] (negativo)
        vpd:         VPD en kPa
        ta:          temperatura del aire [°C]
        etc_regime:  fracción de ETc asignada a la zona (0.0, 0.15, 0.40, 0.65, 1.0)
        session:     número de sesión (1=post-brotación, 2=pre-envero, etc.)
        zone:        zona de riego ('A'–'E')
        fecha:       fecha de medición ISO (YYYY-MM-DD)
        gdd:         grados-día acumulados al momento de la medición

    Returns:
        dict con el formato exacto esperado por ScholanderDataset en train.py
    """
    entry = ScholanderEntry(
        filename=filename,
        cwsi=round(float(cwsi), 4),
        psi_stem=round(float(psi_stem), 4),
        vpd=round(float(vpd), 4),
        ta=round(float(ta), 2),
        etc_regime=round(float(etc_regime), 3),
        session=session,
        zone=zone,
        fecha=fecha,
        gdd=round(float(gdd), 1),
    )
    return asdict(entry)


def export_scholander_dataset(
    entries: List[dict],
    output_path: str | Path,
    overwrite: bool = False,
) -> None:
    """
    Guarda la lista de entradas como labels.json para ScholanderDataset.

    Si output_path ya existe y overwrite=False, lanza FileExistsError.

    Args:
        entries:     lista de dicts (output de build_scholander_label)
        output_path: ruta al labels.json de salida
        overwrite:   si True, sobreescribe el archivo existente
    """
    path = Path(output_path)
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"{path} ya existe. Usar overwrite=True para sobreescribir."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Dataset Scholander guardado: {path}  ({len(entries)} entradas)")


def import_from_csv(csv_path: str | Path) -> List[dict]:
    """
    Importa mediciones de campo desde un CSV y las convierte a formato labels.json.

    Formato del CSV esperado (puede tener columnas adicionales, se ignoran):
        filename, cwsi, psi_stem, vpd, ta, etc_regime, session, zone, fecha, gdd

    La columna 'vpd' es opcional si hay columnas 'ta' y 'rh' (VPD se calcula).

    Args:
        csv_path: ruta al archivo CSV de campo

    Returns:
        lista de dicts en formato labels.json
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {path}")

    entries = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # línea 2 = primera de datos
            try:
                # VPD: usar columna vpd si existe, sino calcular desde ta+rh
                if "vpd" in row and row["vpd"].strip():
                    vpd = float(row["vpd"])
                elif "ta" in row and "rh" in row:
                    vpd = compute_vpd(float(row["ta"]), float(row["rh"]))
                else:
                    raise ValueError("Se necesita columna 'vpd' o ('ta' y 'rh')")

                entry = build_scholander_label(
                    filename=row["filename"].strip(),
                    cwsi=float(row["cwsi"]),
                    psi_stem=float(row["psi_stem"]),
                    vpd=vpd,
                    ta=float(row.get("ta", 25.0)),
                    etc_regime=float(row.get("etc_regime", 0.5)),
                    session=int(row.get("session", 1)),
                    zone=row.get("zone", "A").strip(),
                    fecha=row.get("fecha", "").strip(),
                    gdd=float(row.get("gdd", 0.0)),
                )
                entries.append(entry)

            except (KeyError, ValueError) as e:
                print(f"  Advertencia línea {i}: {e} — fila ignorada: {dict(row)}")
                continue

    print(f"CSV importado: {len(entries)} entradas válidas desde {path.name}")
    return entries


# ---------------------------------------------------------------------------
# Inferencia rápida desde CLI (un solo frame)
# ---------------------------------------------------------------------------
def run_inference(
    frame_path: str,
    checkpoint_path: str,
    payload_path: Optional[str] = None,
    vpd: float = 2.0,
    ta: float = 25.0,
) -> dict:
    """
    Corre el modelo PINN sobre un frame .npy y devuelve CWSI + ΔT predichos.

    Args:
        frame_path:      path al .npy del frame
        checkpoint_path: path al checkpoint .pt del modelo
        payload_path:    path al payload JSON del nodo (opcional, para extraer VPD real)
        vpd:             VPD fallback si no hay payload [kPa]
        ta:              temperatura del aire fallback [°C]

    Returns:
        dict con cwsi_pred, delta_t_pred, vpd_usado, frame_stats
    """
    # Import local para evitar dependencia en módulos que no usan PyTorch
    sys.path.insert(0, str(Path(__file__).parent))
    from pinn_model import HydroVisionPINN

    # Cargar payload para VPD real si está disponible
    if payload_path:
        with open(payload_path) as f:
            payload = json.load(f)
        env = payload.get("env", {})
        ta = float(env.get("t_air", ta))
        rh = float(env.get("rh", 50.0))
        vpd = compute_vpd(ta, rh)

    prep = FramePreprocessor()
    tensor, meta = prep.from_npy(frame_path, vpd=vpd, ta=ta)

    # Cargar modelo
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(checkpoint_path, map_location=device)
    model = HydroVisionPINN(pretrained=False)
    model.load_state_dict(ckpt["model_state"])
    model.eval().to(device)

    with torch.no_grad():
        t = tensor.to(device)
        cwsi_pred, delta_t_pred = model(t)

    return {
        "cwsi_pred": round(float(cwsi_pred.item()), 4),
        "delta_t_pred_c": round(float(delta_t_pred.item()), 3),
        "vpd_kpa": round(vpd, 3),
        "ta_c": ta,
        "frame_mean_c": meta["frame_mean_c"],
        "frame_min_c": meta["frame_min_c"],
        "frame_max_c": meta["frame_max_c"],
        "model_epoch": ckpt.get("epoch", "?"),
        "device": str(device),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cli_scholander(args):
    """Modo: construir labels.json desde CSV de campo."""
    entries = import_from_csv(args.input)

    # Validar que los .npy existen en frames_dir
    if args.frames_dir:
        frames_dir = Path(args.frames_dir)
        missing = [e["filename"] for e in entries
                   if not (frames_dir / e["filename"]).exists()]
        if missing:
            print(f"  ADVERTENCIA: {len(missing)} frames no encontrados en {frames_dir}:")
            for fn in missing[:5]:
                print(f"    {fn}")
            if len(missing) > 5:
                print(f"    ... y {len(missing) - 5} más")

    export_scholander_dataset(entries, args.output, overwrite=getattr(args, "overwrite", False))


def _cli_infer(args):
    """Modo: inferencia sobre un frame único."""
    result = run_inference(
        frame_path=args.frame,
        checkpoint_path=args.checkpoint,
        payload_path=getattr(args, "payload", None),
        vpd=float(getattr(args, "vpd", 2.0)),
        ta=float(getattr(args, "ta", 25.0)),
    )
    print("\nResultado de inferencia:")
    for k, v in result.items():
        print(f"  {k:<22} = {v}")


def main():
    parser = argparse.ArgumentParser(
        description="Preprocesamiento de datos de campo — HydroVision AG"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # --- Modo: construir labels.json desde CSV ---
    p_sch = subparsers.add_parser("scholander",
        help="Construir labels.json para entrenamiento desde CSV de campo")
    p_sch.add_argument("--input", required=True,
        help="CSV de mediciones de campo (filename, cwsi, psi_stem, vpd, ta, etc.)")
    p_sch.add_argument("--frames-dir", default=None,
        help="Directorio de frames .npy para validar que existen")
    p_sch.add_argument("--output", required=True,
        help="Ruta de salida del labels.json")
    p_sch.add_argument("--overwrite", action="store_true",
        help="Sobreescribir labels.json si ya existe")

    # --- Modo: inferencia sobre un frame ---
    p_inf = subparsers.add_parser("infer",
        help="Correr inferencia PINN sobre un frame .npy")
    p_inf.add_argument("--frame", required=True,
        help="Frame térmico .npy")
    p_inf.add_argument("--checkpoint", required=True,
        help="Checkpoint del modelo .pt")
    p_inf.add_argument("--payload", default=None,
        help="Payload JSON del nodo (opcional, para extraer T_air y RH reales)")
    p_inf.add_argument("--vpd", type=float, default=2.0,
        help="VPD fallback en kPa (si no hay payload)")
    p_inf.add_argument("--ta", type=float, default=25.0,
        help="Temperatura del aire fallback [°C]")

    args = parser.parse_args()

    if args.mode == "scholander":
        _cli_scholander(args)
    elif args.mode == "infer":
        _cli_infer(args)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("HydroVision AG — Preprocessing demo")
        print("=" * 50)

        # Demo: compute_vpd
        for t, rh in [(25.0, 80.0), (28.0, 45.0), (35.0, 30.0)]:
            v = compute_vpd(t, rh)
            print(f"  VPD(T={t}°C, RH={rh}%) = {v:.3f} kPa")

        # Demo: normalize_frame
        fake_frame = np.random.uniform(20.0, 40.0, (FRAME_H, FRAME_W)).astype(np.float32)
        norm = normalize_frame(fake_frame)
        print(f"\n  Frame sintético (120×160):")
        print(f"    Original: min={fake_frame.min():.1f}°C, max={fake_frame.max():.1f}°C")
        print(f"    Normed:   min={norm.min():.3f},       max={norm.max():.3f}")

        # Demo: FramePreprocessor
        prep = FramePreprocessor()
        # Guardar frame temporal y procesarlo
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as tmp:
            np.save(tmp.name, fake_frame)
            tensor, meta = prep.from_npy(tmp.name, vpd=2.3, ta=28.0)
            os.unlink(tmp.name)

        print(f"\n  FramePreprocessor:")
        print(f"    Tensor shape: {tuple(tensor.shape)}")
        print(f"    dtype:        {tensor.dtype}")
        print(f"    Meta:         {meta}")

        # Demo: build_scholander_label
        label = build_scholander_label(
            filename="HV-A4CF12B3E7_1743980400.npy",
            cwsi=0.42, psi_stem=-1.2, vpd=2.3, ta=28.0,
            etc_regime=0.65, session=2, zone="B",
            fecha="2027-01-07", gdd=485.0,
        )
        print(f"\n  Scholander label ejemplo:")
        for k, v in label.items():
            print(f"    {k}: {v}")

        print("\nUso CLI:")
        print("  python preprocessing.py scholander --input mediciones.csv --output labels.json")
        print("  python preprocessing.py infer --frame frame.npy --checkpoint best.pt")
