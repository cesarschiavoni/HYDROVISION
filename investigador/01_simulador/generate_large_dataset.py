"""
generate_large_dataset.py — Generador del dataset sintético de 1.000.000 imágenes
HydroVision AG | ML Engineer / 01_simulador

Genera el dataset de entrenamiento del modelo PINN en chunks de 10.000 imágenes,
guardando en formato HDF5 para acceso eficiente desde PyTorch DataLoader.

Estructura del HDF5:
  /images   — float16 (N, 120, 160)   — imágenes térmicas [°C]
  /cwsi     — float32 (N,)            — CWSI ground truth [0-1]
  /metadata — JSON strings (N,)       — contexto completo de cada frame

Tiempo estimado en RTX 3070 (CPU-bound): ~40h para 1.000.000 imágenes
En CPU de 8 cores con paralelización: ~6-8h

Uso:
    # Desde investigador/01_simulador/ o desde investigador/:
    python generate_large_dataset.py --total 1000000 --workers 8
    python generate_large_dataset.py --total 3000  # prueba rápida (3000 frames)

    # Salida por defecto: investigador/data/dataset_sintetico_1M.h5
    # El HDF5 (~11-15 GB) va en investigador/data/ — NO en el directorio de código.

    # Si el disco C: no tiene espacio, redirigir con --output:
    python generate_large_dataset.py --output D:/dataset_sintetico_1M.h5
"""

from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple

import h5py
import numpy as np
from tqdm import tqdm

from simulator import ThermalSimulator, ETC_REGIMES
from weather import sample_colonia_caroya

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
CHUNK_SIZE = 10_000       # imágenes por chunk HDF5
DEFAULT_TOTAL = 1_000_000
# Salida en investigador/data/ — relativo al repo, no hardcodeado a ninguna máquina.
# Espacio estimado: ~11–15 GB (float16 + gzip level 4).
# Si C: no tiene espacio, usar: python generate_large_dataset.py --output D:/dataset.h5
_HERE = os.path.dirname(os.path.abspath(__file__))   # 01_simulador/
_DATA_DIR = os.path.join(_HERE, "..", "data")        # investigador/data/
DEFAULT_OUTPUT = os.path.join(_DATA_DIR, "dataset_sintetico_1M.h5")
HOURS = (8.5, 12.0, 16.0)   # ventanas de captura del protocolo


# ---------------------------------------------------------------------------
# Worker — se ejecuta en proceso separado
# ---------------------------------------------------------------------------
def _generate_chunk(args: Tuple[int, int, int]) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Genera un chunk de imágenes sintéticas.
    Función de nivel módulo para ser serializable por multiprocessing.

    Args:
        args: (chunk_id, n_images, base_seed)

    Returns:
        images: float16 (n_images, 120, 160)
        cwsi:   float32 (n_images,)
        metas:  lista de dicts JSON-serializables
    """
    chunk_id, n_images, base_seed = args
    seed = base_seed + chunk_id * 9973   # semilla única por chunk (primo)
    rng = np.random.default_rng(seed)
    sim = ThermalSimulator(seed=seed)

    regimes = list(ETC_REGIMES.keys())
    etc_values = list(ETC_REGIMES.values())

    images = np.empty((n_images, 120, 160), dtype=np.float16)
    cwsi_arr = np.empty(n_images, dtype=np.float32)
    metas = []

    for i in range(n_images):
        # Selección aleatoria de régimen y hora (uniforme dentro del chunk)
        regime_idx = int(rng.integers(0, len(regimes)))
        regime = regimes[regime_idx]
        etc = etc_values[regime_idx]
        hour = float(rng.choice(HOURS))
        doy = int(rng.integers(305, 395) % 365)   # nov-mar (temporada)
        rain = float(rng.choice([0, 0, 0, 3, 8, 15],
                                p=[0.60, 0.10, 0.10, 0.10, 0.05, 0.05]))

        weather = sample_colonia_caroya(
            hour=hour, day_of_year=doy, rain_48h=rain, rng=rng
        )
        img, meta = sim.generate(weather, etc_fraction=etc)

        images[i] = img.astype(np.float16)
        cwsi_arr[i] = meta["cwsi"]
        meta["regime"] = regime
        meta["chunk_id"] = chunk_id
        meta["sample_idx"] = i
        metas.append(meta)

    return images, cwsi_arr, metas


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def generate_large_dataset(
    total: int = DEFAULT_TOTAL,
    output_path: str = DEFAULT_OUTPUT,
    workers: int = 4,
    seed: int = 42,
    chunk_size: int = CHUNK_SIZE,
) -> None:
    """
    Genera el dataset sintético completo y lo guarda en HDF5.

    Args:
        total:       número total de imágenes a generar
        output_path: ruta del archivo HDF5 de salida
        workers:     procesos paralelos (óptimo: número de cores físicos)
        seed:        semilla base para reproducibilidad
        chunk_size:  imágenes por chunk de procesamiento
    """
    n_chunks = (total + chunk_size - 1) // chunk_size
    chunk_sizes = [chunk_size] * (n_chunks - 1) + [total - chunk_size * (n_chunks - 1)]

    print(f"HydroVision AG — Generador de Dataset Sintético")
    print(f"  Total imágenes : {total:,}")
    print(f"  Chunks         : {n_chunks} × {chunk_size:,}")
    print(f"  Workers        : {workers}")
    print(f"  Output         : {output_path}")
    print(f"  Seed           : {seed}")
    print()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    t0 = time.time()
    images_written = 0

    with h5py.File(output_path, "w") as hf:
        # Crear datasets con compresión gzip
        ds_images = hf.create_dataset(
            "images",
            shape=(total, 120, 160),
            dtype=np.float16,
            chunks=(min(chunk_size, 1000), 120, 160),
            compression="gzip",
            compression_opts=4,
        )
        ds_cwsi = hf.create_dataset(
            "cwsi",
            shape=(total,),
            dtype=np.float32,
            chunks=(min(chunk_size, 10000),),
        )
        ds_meta = hf.create_dataset(
            "metadata",
            shape=(total,),
            dtype=h5py.special_dtype(vlen=str),
        )

        # Atributos globales del dataset
        hf.attrs["total_images"] = total
        hf.attrs["seed"] = seed
        hf.attrs["regimes"] = json.dumps(ETC_REGIMES)
        hf.attrs["hours"] = json.dumps(list(HOURS))
        hf.attrs["sensor"] = "FLIR Lepton 3.5 (160×120 px, NETD 50mK)"
        hf.attrs["cultivar"] = "Malbec (Colonia Caroya, Córdoba)"
        hf.attrs["protocol"] = "ANPCyT Startup 2025 TRL 3-4"

        chunk_args = [(i, sz, seed) for i, sz in enumerate(chunk_sizes)]

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_generate_chunk, args): (i, chunk_sizes[i])
                for i, args in enumerate(chunk_args)
            }

            pbar = tqdm(total=total, unit="img", desc="Generando")
            for future in as_completed(futures):
                chunk_idx, chunk_n = futures[future]
                images_chunk, cwsi_chunk, metas_chunk = future.result()

                start = sum(chunk_sizes[:chunk_idx])
                end = start + len(images_chunk)

                ds_images[start:end] = images_chunk
                ds_cwsi[start:end] = cwsi_chunk
                ds_meta[start:end] = [json.dumps(m) for m in metas_chunk]

                images_written += len(images_chunk)
                pbar.update(len(images_chunk))

                elapsed = time.time() - t0
                rate = images_written / elapsed
                remaining = (total - images_written) / rate if rate > 0 else 0
                pbar.set_postfix({
                    "rate": f"{rate:.0f} img/s",
                    "ETA": f"{remaining/3600:.1f}h",
                })

            pbar.close()

    elapsed = time.time() - t0
    size_gb = os.path.getsize(output_path) / 1e9
    print(f"\nDataset generado en {elapsed/3600:.2f}h")
    print(f"  Archivo : {output_path}")
    print(f"  Tamaño  : {size_gb:.2f} GB")
    print(f"  Rate    : {total / elapsed:.0f} imágenes/segundo")


# ---------------------------------------------------------------------------
# PyTorch Dataset para cargar el HDF5 en entrenamiento
# ---------------------------------------------------------------------------
class SyntheticThermalDataset:
    """
    PyTorch-compatible Dataset que lee el HDF5 en modo lazy.
    Compatible con torch.utils.data.DataLoader.

    Uso:
        dataset = SyntheticThermalDataset("dataset_sintetico_1M.h5")
        loader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=4)
    """

    def __init__(self, h5_path: str, transform=None):
        self.h5_path = h5_path
        self.transform = transform
        self._hf = None   # abierto lazy por worker

        # Leer metadatos sin mantener el archivo abierto
        with h5py.File(h5_path, "r") as hf:
            self._len = hf["images"].shape[0]
            self.attrs = dict(hf.attrs)

    def __len__(self) -> int:
        return self._len

    def _open(self):
        if self._hf is None:
            # rdcc_nbytes=512 MB: caben ~6 chunks de 77 MB (chunk_size=2000, float16)
            # Default h5py = 1 MB → fuerza releer el chunk en cada acceso aleatorio
            # Con ChunkedSampler el acceso es secuencial → un chunk se descomprime 1 vez
            self._hf = h5py.File(
                self.h5_path, "r",
                rdcc_nbytes=512 * 1024 * 1024,
                rdcc_nslots=521,
            )

    def __getitem__(self, idx: int):
        self._open()
        # float16 → float32 para PyTorch
        image = self._hf["images"][idx].astype(np.float32)
        cwsi = float(self._hf["cwsi"][idx])

        # Normalización: mapear rango [5°C, 55°C] a [0, 1]
        image = np.clip((image - 5.0) / 50.0, 0.0, 1.0)
        # Agregar canal: (1, 120, 160) para Conv2d
        image = image[np.newaxis, :, :]

        if self.transform is not None:
            image = self.transform(image)

        return image, np.float32(cwsi)

    def __del__(self):
        if self._hf is not None:
            try:
                self._hf.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera dataset sintético de imágenes térmicas HydroVision AG"
    )
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL,
                        help=f"Total de imágenes (default: {DEFAULT_TOTAL:,})")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT,
                        help="Ruta del archivo HDF5 de salida")
    parser.add_argument("--workers", type=int, default=4,
                        help="Procesos paralelos (default: 4)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    args = parser.parse_args()

    generate_large_dataset(
        total=args.total,
        output_path=args.output,
        workers=args.workers,
        seed=args.seed,
        chunk_size=args.chunk_size,
    )
