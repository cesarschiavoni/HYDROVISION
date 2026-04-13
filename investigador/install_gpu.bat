@echo off
REM ============================================================
REM HydroVision AG — Setup GPU (RTX 3070, CUDA 12.1, Windows)
REM ============================================================
REM Ejecutar UNA VEZ antes de entrenar.
REM Requiere: Python 3.10+ en PATH, pip actualizado.

echo.
echo === HydroVision AG — Instalacion GPU ===
echo RTX 3070 / CUDA 12.1
echo.

REM Verificar que nvidia-smi esta disponible
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo ERROR: nvidia-smi no encontrado.
    echo Instalar drivers NVIDIA desde: https://www.nvidia.com/drivers
    pause
    exit /b 1
)

echo Driver NVIDIA detectado:
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
echo.

REM Actualizar pip
python -m pip install --upgrade pip

REM Instalar PyTorch con CUDA 12.1
echo Instalando PyTorch 2.x con CUDA 12.1...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

REM Resto de dependencias
echo.
echo Instalando dependencias del proyecto...
pip install numpy>=1.24 scipy>=1.11 pandas>=2.0 matplotlib>=3.7 ^
            scikit-learn>=1.3 Pillow>=10.0 tqdm>=4.66 h5py>=3.9 ^
            timm>=0.9.12 segmentation-models-pytorch>=0.3.3 ^
            onnx>=1.15 onnxruntime>=1.16 wandb>=0.16

echo.
echo === Verificando GPU ===
python verify_gpu.py

echo.
echo Listo. Para entrenar:
echo   cd 02_modelo
echo   python train.py --stage synthetic --dataset ..\data\dataset_sintetico_1M.h5
pause
