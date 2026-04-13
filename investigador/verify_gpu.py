"""
verify_gpu.py — Verificación del entorno GPU para HydroVision AG
Ejecutar antes del primer entrenamiento para confirmar que CUDA está disponible.

Uso:
    python verify_gpu.py
"""

import sys

def check():
    print("=== HydroVision AG — Verificación GPU ===\n")

    # Python
    print(f"Python : {sys.version.split()[0]}")

    # PyTorch
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
    except ImportError:
        print("ERROR: PyTorch no instalado. Ejecutar install_gpu.bat")
        sys.exit(1)

    # CUDA disponible
    cuda_ok = torch.cuda.is_available()
    print(f"CUDA   : {'OK — disponible' if cuda_ok else 'NO DISPONIBLE — se usará CPU'}")

    if not cuda_ok:
        print("\nPosibles causas:")
        print("  1. PyTorch instalado sin CUDA: pip install torch (CPU-only)")
        print("     Solución: ejecutar install_gpu.bat")
        print("  2. Driver NVIDIA desactualizado")
        print("     Solución: actualizar desde https://www.nvidia.com/drivers")
        sys.exit(1)

    # Detalles GPU
    n_gpus = torch.cuda.device_count()
    print(f"GPUs   : {n_gpus}")
    for i in range(n_gpus):
        props = torch.cuda.get_device_properties(i)
        mem_gb = props.total_memory / 1024**3
        print(f"  [{i}] {props.name} — {mem_gb:.1f} GB VRAM — SM {props.major}.{props.minor}")

    # Test tensor en GPU
    x = torch.randn(1000, 1000, device="cuda")
    y = x @ x.T
    print(f"\nTest   : multiplicación 1000×1000 en GPU — OK ({y.shape})")

    # cuDNN
    print(f"cuDNN  : {torch.backends.cudnn.version()} — enabled={torch.backends.cudnn.enabled}")

    # Memoria disponible
    free, total = torch.cuda.mem_get_info(0)
    print(f"VRAM   : {free/1024**3:.1f} GB libres / {total/1024**3:.1f} GB total")

    # Estimación batch size PINN en RTX 3070 (8 GB)
    # Modelo ~50MB, batch 256 × (1, 120, 160) float32 = ~6 MB → cabe con margen
    print("\n=== Estimación para entrenamiento PINN ===")
    print(f"  Batch size recomendado (sintético): 256  (~6 MB por batch)")
    print(f"  Batch size recomendado (finetune) : 16   (dataset pequeño)")
    print(f"  Tiempo estimado entrenamiento sintético (30 epochs, 1M imgs): ~40h")
    print(f"  Tiempo estimado finetune (50 epochs, 680 frames): ~10 min")

    print("\n=== TODO OK — listo para entrenar ===")

if __name__ == "__main__":
    check()
