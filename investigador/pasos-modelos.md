# HydroVision AG — Pasos para generar los modelos

## Entorno de trabajo (obligatorio antes de todo)

El proyecto usa un **entorno virtual Python 3.12** con PyTorch CUDA. Python 3.14 (el sistema) no tiene soporte GPU.

```bat
REM Activar el entorno — hacerlo en CADA terminal nueva antes de correr cualquier script
C:\Temp\Agro\investigador\venv\Scripts\activate
```

El prompt tiene que mostrar `(venv)` al principio:
```
(venv) C:\Temp\Agro\investigador\02_modelo>
```

Sin `(venv)` → PyTorch corre en CPU con Python 3.14. Con `(venv)` → RTX 3070.

### Verificar GPU (una sola vez)
```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
python -c "import torch; print(torch.__version__); print('CUDA:', torch.version.cuda); print('GPU:', torch.cuda.get_device_name(0))"
```
Salida esperada: `2.5.1+cu121` / `CUDA: 12.1` / `GPU: NVIDIA GeForce RTX 3070`

| GPU | Driver | VRAM | Compute | PyTorch |
|-----|--------|------|---------|---------|
| RTX 3070 | 595.97 | 8 GB | 8.6 | 2.5.1+cu121 |

---

## Paso 1 — Generar el dataset sintético (CPU, ~33 min, solo una vez)

> **Para qué sirve:** El modelo necesita miles de ejemplos de imágenes térmicas con su CWSI correcto para aprender. Como todavía no hay imágenes reales del campo, se genera un dataset sintético: el simulador físico crea 1 millón de imágenes térmicas artificiales de canopias bajo distintas condiciones (temperatura, VPD, hora del día, estrés hídrico) y calcula el CWSI teórico de cada una. Este dataset es el "libro de texto" del modelo.

```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
cd C:\Temp\Agro\investigador\01_simulador
python generate_large_dataset.py --total 1000000 --workers 4 --chunk-size 2000
```

- Genera `investigador/data/dataset_sintetico_1M.h5` (**~24.5 GB** — 1M × 120×160 px float16 + gzip)
- **CPU-only** — simulación física, no redes. Normal que la GPU no se use aquí.
- `--workers 4 --chunk-size 2000` evita `WinError 1450` (límite de pipes IPC de Windows con chunks grandes; con `--workers 8` falla)

> **Prueba rápida antes de largar 1M imágenes:**
> ```bat
> python generate_large_dataset.py --total 3000 --workers 4 --chunk-size 500
> ```

---

## Paso 2 — Pre-entrenamiento sintético (GPU, ~2.5 horas)

> **Para qué sirve:** Se entrena la red neuronal usando el dataset del Paso 1. El modelo aprende a mirar una imagen térmica y estimar el CWSI. Como los datos son sintéticos, el modelo no queda listo para producción, pero aprende los patrones generales (dónde está la canopia, cómo varía la temperatura, qué forma tiene una planta estresada). Es el equivalente a estudiar de un libro antes de ir al campo.

```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
cd C:\Temp\Agro\investigador\02_modelo
python train.py --stage synthetic
```

- `--num-workers` **no es necesario** — se auto-detecta (0 en Windows, obligatorio para HDF5)
- Imprime al inicio: `Entrenando stage='synthetic' en cuda` — confirma que usa GPU
- Guarda el mejor checkpoint en `investigador/models/checkpoints/best_synthetic.pt`
- Logs en `investigador/models/logs/history_synthetic.json`
- **~5 min/epoch × 30 epochs ≈ 2.5 horas totales**

### Throughput esperado
```
train:   5%|█▍  | 171/3711 [00:16<04:29, 13.12batch/s, data=0.07s, gpu=0.03s]
```
- `data` = tiempo de I/O HDF5 por batch (normal: 0.05-0.5s)
- `gpu`  = tiempo de forward+backward+optimizer (normal: 0.03-0.1s)
- Si `data` > 1s sostenido → problema de I/O (ver errores conocidos)

**Monitorear GPU** en otra terminal:
```bat
nvidia-smi dmon -s u -d 2
```
`sm%` bajo (1-20%) es normal — modelo pequeño (339K params), cuello de botella es I/O del HDF5.

### Prompts al arrancar

**1. Hugging Face — descarga backbone MobileNetV3:**
```
Warning: You are sending unauthenticated requests to the HF Hub...
Unexpected keys (classifier.bias, ...) found while loading pretrained weights.
model.safetensors: 100% 6.42M/6.42M
```
Normal. Las `Unexpected keys` son capas del clasificador ImageNet que no se usan (se reemplazan por los heads CWSI/ΔT). Descarga una sola vez a `~/.cache/huggingface/`. No hace falta cuenta HF.

**2. Warning de symlinks:**
```
UserWarning: your machine does not support symlinks in C:\Users\...\huggingface\hub\...
```
Ignorar. No afecta el entrenamiento.

**3. Weights & Biases:**
```
wandb: (1) Create a W&B account
wandb: (2) Use an existing W&B account
wandb: (3) Don't visualize my results
wandb: Enter your choice:
```
**Ingresar `3`** — logs quedan en `investigador/models/logs/` de forma local.

---

## Paso 3 — Fine-tuning con datos reales (GPU, cuando haya datos Scholander)

> **Para qué sirve:** Se ajusta el modelo entrenado en sintético usando imágenes reales del campo junto con mediciones de potencial hídrico (cámara de presión Scholander). Con unos pocos cientos de ejemplos reales el modelo se calibra a las condiciones reales: variedad específica, suelo local, condiciones de luz de Mendoza/San Juan. Sin este paso el modelo funciona, pero con menos precisión. Es el equivalente a la práctica de campo después de estudiar el libro.

```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
cd C:\Temp\Agro\investigador\02_modelo
python train.py --stage finetune ^
    --checkpoint ..\models\checkpoints\best_synthetic.pt ^
    --real-data ..\data\scholander\ ^
    --cultivar malbec
```

- Requiere `investigador/data/scholander/frames/*.npy` + `labels.json`
- Guarda `investigador/models/checkpoints/best_finetune.pt`

### Cultivar y parametros fisicos (importante)

El modelo PINN usa parametros fisicos especificos de cada variedad de vid para calcular el CWSI teorico. Estos parametros se cargan automaticamente desde `investigador/config/cultivares.json`:

| Cultivar | NWSB intercept a (°C) | NWSB slope b (°C/kPa) | DT_UL (°C) | ΔT_LL a VPD=2.0 | Umbral alerta CWSI |
|----------|----------------------|-----------------------|-----------|-----------------|-------------------|
| `malbec` | 1.5 | -1.80 | 3.50 | -2.1°C | 0.30 |
| `cabernet_sauvignon` | 1.5 | -1.875 | 3.20 | -2.25°C | 0.35 |
| `syrah` | 1.5 | -2.00 | 3.00 | -2.5°C | 0.40 |
| `bonarda` | 1.5 | -1.65 | 3.00 | -1.8°C | 0.28 |
| `chardonnay` | 1.5 | -1.925 | 3.20 | -2.35°C | 0.35 |
| `olivo` | 1.0 | -1.40 | 6.00 | -1.8°C | 0.40 |
| `cerezo` | 1.2 | -1.50 | 2.50 | -1.8°C | 0.30 |
| `arandano` | 1.5 | -1.80 | 2.00 | -2.1°C | 0.25 |
*(ver config/cultivares.json para la lista completa — 14 cultivares)*

**Donde importa:**
- **NWSB a + slope** (Non-Water Stressed Baseline): formula completa ΔT_LL = a + slope × VPD (Jackson 1981). El intercepto `a` representa el diferencial termico a VPD=0 (generalmente positivo: la planta transpira incluso sin deficit de vapor). El `slope` (negativo) capta que a mayor VPD la planta se enfria mas activamente. Ambos parametros varian por variedad.
- **DT_UL**: temperatura diferencial maxima de una hoja sin transpirar (estomas cerrados). Depende de la anatomia foliar del cultivar.

**BUG CORREGIDO (Abril 2026):** La version anterior usaba solo `ΔT_LL = slope × VPD` sin intercepto, lo que daba `-0.90°C` a VPD=2.0 kPa para Malbec. El valor correcto (Bellvert 2016) es `-2.1°C`. La formula ahora incluye el intercepto `a`: `ΔT_LL = nwsb_a + nwsb_slope × VPD`. Los checkpoints entrenados con la version anterior deben descartarse si el termino de fisica estaba activo (stage finetune).

**Cuando importa:**
- **Paso 2 (synthetic):** NO importa. El peso del termino de fisica es 0.0 porque los datos sinteticos no tienen VPD real. El modelo solo aprende patrones visuales. No hace falta especificar `--cultivar`.
- **Paso 3 (finetune):** SI importa. El termino de fisica se activa (`physics=0.3`) y usa estos parametros para regularizar el modelo. Especificar `--cultivar` es obligatorio para que los parametros fisicos coincidan con la variedad del campo real.

**Ejemplo para otro campo:**
```bat
REM Campo de Cabernet Sauvignon en Mendoza
python train.py --stage finetune ^
    --checkpoint ..\models\checkpoints\best_synthetic.pt ^
    --real-data ..\data\scholander_mendoza\ ^
    --cultivar cabernet_sauvignon
```

**Agregar un cultivar nuevo:** Editar `investigador/config/cultivares.json` con los parametros NWSB y DT_upper de la variedad. Fuentes: Jackson (1981), Bellvert et al. (2016), FAO-56. Para variedades sin datos publicados, usar los valores mas cercanos y ajustar con los datos Scholander del Paso 3 (el finetune compensa diferencias moderadas).

### Formato de labels.json
```json
[
  {
    "filename":   "frame_001.npy",
    "cwsi":       0.42,
    "psi_stem":  -1.2,
    "vpd":        2.8,
    "ta":         28.5,
    "etc_regime": 1.0
  }
]
```

| Campo | Fuente | Requerido |
|-------|--------|-----------|
| `filename` | nombre del .npy grabado por el nodo | Sí |
| `cwsi` | calculado de la imagen: `(Tc_mean − Tc_wet) / (Tc_dry − Tc_wet)` | Sí |
| `psi_stem` | cámara de presión Scholander | No (recomendado) |
| `vpd` | estación meteorológica | No (default 2.0) |
| `ta` | temperatura de aire | No |
| `etc_regime` | 0 = sin riego, 1 = riego pleno | No |

Mínimo útil: ~200-500 pares frame/psi_stem.

---

## Paso 3.5 — Preparar dataset Scholander desde planilla CSV (nuevo)

> **Para qué sirve:** Convierte la planilla de campo (CSV con columnas filename, cwsi, psi_stem, vpd, ta, etc_regime, zone, session) al formato `labels.json` que espera el DataLoader del Paso 3. Usa `preprocessing.py`.

```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
cd C:\Temp\Agro\investigador\02_modelo
python preprocessing.py scholander ^
    --input ..\data\scholander\mediciones_campo.csv ^
    --frames-dir ..\data\scholander\frames\ ^
    --output ..\data\scholander\labels.json
```

**Formato del CSV** (columnas mínimas requeridas):
```
filename,cwsi,psi_stem,vpd,ta,etc_regime,zone,session,fecha,gdd
HV-A4CF12B3E7_1746000000.npy,0.42,-1.2,2.3,28.5,0.65,B,2,2027-01-07,485.0
```
- `vpd` puede omitirse si hay columnas `ta` y `rh` (se calcula automáticamente)
- `psi_stem` puede omitirse si no hay medición Scholander para ese frame (se guarda como null)

**Inferencia rápida sobre un frame individual:**
```bat
python preprocessing.py infer ^
    --frame ..\data\scholander\frames\HV-A4CF12B3E7_1746000000.npy ^
    --checkpoint ..\models\checkpoints\best_finetune.pt ^
    --payload ..\data\payloads\payload_ejemplo.json
```

---

## Paso 3.6 — Validar el modelo (nuevo)

> **Para qué sirve:** Evalúa el checkpoint entrenado contra el dataset Scholander y genera métricas (MAE, RMSE, R²) + gráficos (scatter CWSI, Bland-Altman, scatter ψ_stem, error por sesión). Target TRL 4: MAE ≤ 0.08, R² ≥ 0.75 vs CWSI real, R² ≥ 0.75 vs ψ_stem.

```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
cd C:\Temp\Agro\investigador\03_fusion
python validate_pinn.py ^
    --checkpoint ..\models\checkpoints\best_finetune.pt ^
    --data-dir ..\data\scholander\ ^
    --output-dir ..\models\logs\validation_S4\
```

Salidas en `investigador/models/logs/validation_S4/`:
- `metrics.json` — todas las métricas en formato JSON
- `metrics_summary.txt` — resumen legible con indicadores ✓/✗ de TRL 4
- `scatter_cwsi.png` — scatter CWSI pred vs real coloreado por zona RDI
- `bland_altman.png` — diagrama de Bland-Altman
- `scatter_psi_stem.png` — scatter CWSI pred vs ψ_stem Scholander (si hay datos)
- `error_by_session.png` — boxplot de error por sesión S1–S4

**Validar en dataset sintético** (sin datos de campo):
```bat
python validate_pinn.py ^
    --checkpoint ..\models\checkpoints\best_synthetic.pt ^
    --synthetic ..\data\dataset_sintetico_1M.h5 ^
    --n-synthetic 5000
```

---

## Paso 4 — Exportar a edge / ESP32-S3

> **Para qué sirve:** El modelo entrenado en PyTorch no puede correr directamente en el ESP32-S3 del nodo (512KB SRAM + 8MB PSRAM, dual-core 240MHz). Este paso lo convierte a dos formatos optimizados: ONNX (portátil, puede correr en cualquier hardware) y TFLite INT8 (cuantizado a enteros de 8 bits, 4× más liviano, diseñado para microcontroladores como ESP32-S3). El resultado es el archivo que se copia al nodo de campo.

```bat
C:\Temp\Agro\investigador\venv\Scripts\activate
cd C:\Temp\Agro\investigador\02_modelo
python quantize.py --checkpoint ..\models\checkpoints\best_finetune.pt --benchmark
```

- Genera `investigador/models/edge/hydrovision_cwsi.onnx`
- Genera `investigador/models/edge/hydrovision_cwsi_int8.tflite` (cuantizado INT8 para ESP32-S3)

---

## Dónde quedan los archivos

```
investigador/
├── config/
│   └── cultivares.json              ← 14 cultivares con parámetros NWSB correctos
├── data/
│   ├── dataset_sintetico_1M.h5      ← Paso 1 (~24.5 GB)
│   └── scholander/
│       ├── frames/*.npy             ← frames del campo (Pasos 3, 3.5)
│       └── labels.json              ← generado por preprocessing.py (Paso 3.5)
├── 02_modelo/
│   └── preprocessing.py            ← CSV/payload → labels.json + inferencia rápida
├── 03_fusion/
│   └── validate_pinn.py            ← validación completa vs Scholander
└── models/
    ├── checkpoints/
    │   ├── best_synthetic.pt        ← Paso 2
    │   └── best_finetune.pt         ← Paso 3
    ├── logs/
    │   ├── history_synthetic.json
    │   ├── history_finetune.json
    │   └── validation_S4/           ← Paso 3.6 (métricas + gráficos)
    └── edge/
        ├── hydrovision_cwsi.onnx    ← Paso 4
        └── hydrovision_cwsi_int8.tflite
```

> **Redirigir salidas a otro disco (opcional):**
> ```bat
> python train.py --stage synthetic --output-dir D:\Models\hydrovision
> ```
> El dataset debe seguir en C: NVMe para máxima velocidad de lectura. Checkpoints y logs sí pueden ir a D:.

---

## Errores conocidos y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `Entrenando en cpu` + warning `pin_memory` | venv no activado, corre Python 3.14 | Activar venv antes de correr |
| `WinError 1450` en generación | `--workers 8` satura pipes IPC Windows | Usar `--workers 4 --chunk-size 2000` |
| `TypeError: conv2d() received list` | Bug timm 1.0+ con `features_only=True` | Ya corregido en `pinn_model.py` |
| `CUDA: None` con Python 3.14 | PyTorch no tiene wheels CUDA para 3.14 | Usar venv Python 3.12 |
| `data=38s/batch` sostenido | Acceso individual al HDF5 gzip (bug anterior) | Ya corregido — usa `SyntheticHDF5IterDataset` con slices |
| `data` alto solo en primeros batches | Primer slice del chunk descomprime 77 MB | Normal — se estabiliza en <0.1s/batch |
| `ValueError: Cultivar 'X' no encontrado` | Nombre de cultivar no coincide con clave JSON | Ver lista en `config/cultivares.json` — claves en minúsculas con guión bajo |
| `ΔT_LL negativo incorrecto en physics term` | Checkpoints entrenados con `nwsb_slope=-0.45` (bug corregido) | Reentrenar desde Paso 2 — descartar checkpoints previos al 7-abr-2026 |
| `AssertionError: N etiquetas vs M predicciones` en validate_pinn | Labels.json desincronizado con DataLoader | Regenerar labels.json con preprocessing.py |

---

## Orden obligatorio

```
Paso 1 (CPU) → Paso 2 (GPU) → Paso 3 (GPU) → Paso 4 (GPU)
```

Sin datos Scholander todavía: completar Paso 1 + Paso 2. Ya hay un modelo funcional para probar.
