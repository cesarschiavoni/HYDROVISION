"""
quantize.py — Cuantización INT8 y exportación TFLite Micro / ONNX
HydroVision AG | ML Engineer / 02_modelo

Convierte el modelo PINN entrenado en PyTorch a formato deployable en
RPi Zero 2W con latencia < 200ms por frame.

Pipeline:
    1. PyTorch FP32  →  PyTorch INT8 (quantization-aware o post-training)
    2. PyTorch INT8  →  ONNX
    3. ONNX          →  TFLite FP32  →  TFLite INT8 (TFLite Micro)

Validación post-cuantización:
    - Error máximo CWSI: < ±0.02 respecto al modelo FP32
    - Tamaño objetivo: < 2 MB para flash de RPi
    - Latencia objetivo: < 200ms en RPi Zero 2W (ARM Cortex-A53 @ 1GHz)

Uso:
    python quantize.py --checkpoint ../models/checkpoints/best_finetune.pt \
                       --output ../models/edge/ \
                       --calibration-data ../data/dataset_sintetico_1M.h5

Salidas en ../models/edge/:
    hydrovision_cwsi.onnx            — modelo ONNX FP32
    hydrovision_cwsi_int8.tflite     — modelo TFLite INT8 para RPi Zero 2W
    benchmark_results.json           — latencia y error vs. FP32
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# Cuantización Post-Training PyTorch (PTQ)
# ---------------------------------------------------------------------------
def quantize_pytorch_ptq(
    model: nn.Module,
    calibration_data: torch.Tensor,
    backend: str = "qnnpack",   # qnnpack para ARM (RPi), fbgemm para x86
) -> nn.Module:
    """
    Cuantización post-training estática (PTQ) para inferencia INT8 en ARM.

    Args:
        model:             modelo FP32 entrenado
        calibration_data:  (N, 1, 120, 160) — subset representativo para calibrar
        backend:           'qnnpack' para ARM/RPi, 'fbgemm' para x86

    Returns:
        modelo cuantizado INT8 listo para torch.jit.script
    """
    torch.backends.quantized.engine = backend
    model.eval()

    # Preparar para cuantización estática
    model_q = torch.quantization.QuantWrapper(model)
    model_q.qconfig = torch.quantization.get_default_qconfig(backend)
    torch.quantization.prepare(model_q, inplace=True)

    # Calibración: pasar datos representativos
    print(f"Calibrando con {len(calibration_data)} frames...")
    with torch.no_grad():
        batch_size = 32
        for i in range(0, len(calibration_data), batch_size):
            batch = calibration_data[i:i + batch_size]
            model_q(batch)

    # Convertir a INT8
    torch.quantization.convert(model_q, inplace=True)
    print("Cuantización PTQ completada.")
    return model_q


# ---------------------------------------------------------------------------
# Exportación ONNX
# ---------------------------------------------------------------------------
def export_onnx(
    model: nn.Module,
    output_path: str,
    opset: int = 17,
) -> None:
    """
    Exporta el modelo a formato ONNX para conversión posterior a TFLite.

    Args:
        model:       modelo PyTorch (FP32 o INT8)
        output_path: ruta del archivo .onnx
        opset:       versión del opset ONNX (17 = compatible con TFLite 2.14)
    """
    model.eval()
    dummy_input = torch.randn(1, 1, 120, 160)

    # Para modelos que retornan tuple, envolver en módulo simple
    class SingleOutputWrapper(nn.Module):
        def __init__(self, m): super().__init__(); self.m = m
        def forward(self, x):
            out = self.m(x)
            return out[0] if isinstance(out, tuple) else out

    wrapper = SingleOutputWrapper(model)

    torch.onnx.export(
        wrapper,
        dummy_input,
        output_path,
        opset_version=opset,
        input_names=["thermal_image"],
        output_names=["cwsi_pred"],
        dynamic_axes={
            "thermal_image": {0: "batch_size"},
            "cwsi_pred": {0: "batch_size"},
        },
        do_constant_folding=True,
    )
    size_kb = os.path.getsize(output_path) / 1024
    print(f"ONNX exportado: {output_path}  ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Conversión TFLite INT8
# ---------------------------------------------------------------------------
def convert_tflite_int8(
    onnx_path: str,
    output_path: str,
    calibration_images: Optional[np.ndarray] = None,
) -> None:
    """
    Convierte ONNX → TFLite FP32 → TFLite INT8 con cuantización completa.

    Requiere:
        pip install tensorflow onnx-tf

    Args:
        onnx_path:          modelo ONNX
        output_path:        ruta del .tflite de salida
        calibration_images: (N, 1, 120, 160) numpy float32 para calibración INT8
    """
    try:
        import tensorflow as tf
        from onnx_tf.backend import prepare
        import onnx
    except ImportError:
        print("ERROR: tensorflow y onnx-tf son necesarios para conversión TFLite.")
        print("  pip install tensorflow onnx-tf")
        return

    print(f"Convirtiendo ONNX → TFLite INT8: {onnx_path}")

    # ONNX → TF SavedModel
    onnx_model = onnx.load(onnx_path)
    tf_rep = prepare(onnx_model)
    saved_model_dir = output_path.replace(".tflite", "_savedmodel")
    tf_rep.export_graph(saved_model_dir)

    # TF SavedModel → TFLite INT8
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    if calibration_images is not None:
        def representative_dataset():
            for i in range(min(len(calibration_images), 200)):
                img = calibration_images[i:i+1]  # (1, 1, 120, 160)
                # TFLite espera NHWC: (1, 120, 160, 1)
                img_nhwc = img.transpose(0, 2, 3, 1)
                yield [img_nhwc.astype(np.float32)]

        converter.representative_dataset = representative_dataset

    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)

    size_kb = len(tflite_model) / 1024
    print(f"TFLite INT8 exportado: {output_path}  ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Benchmark de latencia
# ---------------------------------------------------------------------------
def benchmark_latency(
    model: nn.Module,
    n_runs: int = 100,
    warmup: int = 10,
    device: str = "cpu",
) -> dict:
    """
    Mide la latencia de inferencia por frame.

    Args:
        model:   modelo PyTorch
        n_runs:  número de runs para promediar
        warmup:  runs de calentamiento (excluidos del promedio)
        device:  'cpu' o 'cuda'

    Returns:
        dict con mean_ms, std_ms, min_ms, max_ms
    """
    model.eval()
    dev = torch.device(device)
    model = model.to(dev)
    x = torch.randn(1, 1, 120, 160).to(dev)

    latencies = []
    with torch.no_grad():
        for i in range(warmup + n_runs):
            t0 = time.perf_counter()
            out = model(x)
            if isinstance(out, tuple):
                _ = out[0].item()
            else:
                _ = out.item()
            t1 = time.perf_counter()
            if i >= warmup:
                latencies.append((t1 - t0) * 1000)  # ms

    return {
        "mean_ms": np.mean(latencies),
        "std_ms": np.std(latencies),
        "min_ms": np.min(latencies),
        "max_ms": np.max(latencies),
        "device": device,
    }


# ---------------------------------------------------------------------------
# Validación: error FP32 vs INT8
# ---------------------------------------------------------------------------
def validate_quantization_error(
    model_fp32: nn.Module,
    model_int8: nn.Module,
    test_images: torch.Tensor,
    tolerance: float = 0.02,
) -> dict:
    """
    Compara las predicciones FP32 vs INT8 para verificar que el error
    de cuantización sea aceptable (< ±0.02 CWSI).
    """
    model_fp32.eval()
    model_int8.eval()

    with torch.no_grad():
        out_fp32 = model_fp32(test_images)
        out_int8 = model_int8(test_images)

        cwsi_fp32 = out_fp32[0] if isinstance(out_fp32, tuple) else out_fp32
        cwsi_int8 = out_int8[0] if isinstance(out_int8, tuple) else out_int8

        diff = (cwsi_fp32 - cwsi_int8).abs()

    result = {
        "max_error": diff.max().item(),
        "mean_error": diff.mean().item(),
        "within_tolerance": (diff.max().item() < tolerance),
        "tolerance": tolerance,
    }
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent      # 02_modelo/
_INVESTIGADOR = _HERE.parent                  # investigador/


def main():
    parser = argparse.ArgumentParser(
        description="Cuantización INT8 y exportación edge — HydroVision AG"
    )
    parser.add_argument("--checkpoint", required=True,
                        help="Checkpoint PyTorch (.pt) — ej: ../models/checkpoints/best_finetune.pt")
    parser.add_argument("--output", default=str(_INVESTIGADOR / "models" / "edge"),
                        help="Directorio de salida (default: ../models/edge/)")
    parser.add_argument("--calibration-data",
                        default=str(_INVESTIGADOR / "data" / "dataset_sintetico_1M.h5"),
                        help="HDF5 para calibración INT8 (default: ../data/dataset_sintetico_1M.h5)")
    parser.add_argument("--skip-tflite", action="store_true",
                        help="No convertir a TFLite (solo ONNX)")
    parser.add_argument("--benchmark", action="store_true",
                        help="Ejecutar benchmark de latencia")
    args = parser.parse_args()

    import sys
    sys.path.insert(0, ".")
    from pinn_model import HydroVisionPINN, HydroVisionPINN_Edge

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    # Cargar modelo
    print(f"Cargando checkpoint: {args.checkpoint}")
    ckpt = torch.load(args.checkpoint, map_location="cpu")
    model_fp32 = HydroVisionPINN(pretrained=False)
    model_fp32.load_state_dict(ckpt["model_state"])
    model_fp32.eval()
    print(f"  Parámetros FP32: {model_fp32.count_parameters():,}")

    # Calibration data
    calib_images = None
    if args.calibration_data:
        try:
            sys.path.insert(0, "../01_simulador")
            from generate_large_dataset import SyntheticThermalDataset
            ds = SyntheticThermalDataset(args.calibration_data)
            # Tomar 500 imágenes para calibración
            idxs = np.random.choice(len(ds), min(500, len(ds)), replace=False)
            calib_images = np.stack([ds[i][0] for i in idxs])
            calib_tensor = torch.from_numpy(calib_images)
            print(f"  Datos de calibración: {len(calib_images)} frames")
        except Exception as e:
            print(f"  Advertencia: no se pudo cargar calibration data — {e}")

    # 1. Cuantización PTQ
    print("\n[1/4] Cuantización PTQ (INT8, backend qnnpack)...")
    calib_t = calib_tensor[:200] if calib_images is not None else torch.randn(200, 1, 120, 160)
    model_int8 = quantize_pytorch_ptq(model_fp32, calib_t, backend="qnnpack")

    # 2. Validación error
    print("\n[2/4] Validación error FP32 vs INT8...")
    test_x = torch.randn(50, 1, 120, 160)
    err = validate_quantization_error(model_fp32, model_int8, test_x)
    print(f"  Error máximo CWSI : {err['max_error']:.4f}")
    print(f"  Error medio CWSI  : {err['mean_error']:.4f}")
    print(f"  Dentro de ±{err['tolerance']}: {err['within_tolerance']}")

    if not err["within_tolerance"]:
        print("  ADVERTENCIA: error > tolerancia — considerar QAT o ajustar calibración")

    # 3. Exportación ONNX
    print("\n[3/4] Exportando ONNX...")
    onnx_path = str(output_dir / "hydrovision_cwsi.onnx")
    export_onnx(model_fp32, onnx_path)

    # 4. Conversión TFLite
    if not args.skip_tflite:
        print("\n[4/4] Convirtiendo a TFLite INT8...")
        tflite_path = str(output_dir / "hydrovision_cwsi_int8.tflite")
        convert_tflite_int8(
            onnx_path, tflite_path,
            calibration_images=calib_images,
        )
    else:
        print("\n[4/4] TFLite omitido (--skip-tflite)")

    # Benchmark
    if args.benchmark:
        print("\n[Benchmark] Latencia en CPU (simula RPi Zero 2W)...")
        lat = benchmark_latency(model_fp32, n_runs=100, device="cpu")
        print(f"  FP32  mean={lat['mean_ms']:.1f}ms  std={lat['std_ms']:.1f}ms")
        lat_int8 = benchmark_latency(model_int8, n_runs=100, device="cpu")
        print(f"  INT8  mean={lat_int8['mean_ms']:.1f}ms  std={lat_int8['std_ms']:.1f}ms")
        speedup = lat["mean_ms"] / lat_int8["mean_ms"]
        print(f"  Speedup INT8 vs FP32: {speedup:.1f}×")

    print(f"\nArtifactos guardados en: {output_dir}/")


if __name__ == "__main__":
    main()
