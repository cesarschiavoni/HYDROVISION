"""
train.py — Pipeline de entrenamiento completo del modelo PINN
HydroVision AG | ML Engineer / 02_modelo

Etapas:
    1. Pre-entrenamiento en dataset sintético (1M imágenes) — transfer learning
    2. Fine-tuning en frames reales Scholander (680 frames)
    3. Validación en hold-out independiente (120 frames)

Uso (ejecutar desde la raíz investigador/ o desde 02_modelo/):
    # Etapa 1: sintético
    python train.py --stage synthetic --dataset ../data/dataset_sintetico_1M.h5

    # Etapa 2: fine-tuning
    python train.py --stage finetune \
                    --checkpoint ../models/checkpoints/best_synthetic.pt \
                    --real-data ../data/scholander/

    # Evaluación
    python train.py --stage eval \
                    --checkpoint ../models/checkpoints/best_finetune.pt \
                    --real-data ../data/scholander/

Salidas:
    ../models/checkpoints/best_synthetic.pt   — mejor modelo etapa 1
    ../models/checkpoints/best_finetune.pt    — mejor modelo etapa 2
    ../models/logs/history_synthetic.json     — métricas por epoch etapa 1
    ../models/logs/history_finetune.json      — métricas por epoch etapa 2
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import time
from pathlib import Path
from typing import Optional

import h5py
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm

from pinn_model import HydroVisionPINN, HydroVisionPINN_Edge
from pinn_loss import PINNLoss, PINNLossWeights

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CONFIG = {
    "synthetic": {
        "epochs": 50,
        "batch_size": 256,
        "lr": 3e-4,
        "lr_min": 1e-6,
        "weight_decay": 1e-4,
        # physics=0.0: en stage sintético VPD=0 siempre, lo que hace que el
        # término físico fuerce cwsi ≈ ΔT/3.5 incorrectamente. Se activa en finetune
        # donde se tienen VPD reales de campo.
        "loss_weights": PINNLossWeights(mse=1.0, physics=0.0, monotone=0.0),
        "workers": 8,
        "val_split": 0.05,
    },
    "finetune": {
        "epochs": 50,
        "batch_size": 16,   # dataset pequeño (680 frames)
        "lr": 5e-5,         # LR bajo para no destruir features aprendidas
        "lr_min": 1e-6,
        "weight_decay": 1e-5,
        "loss_weights": PINNLossWeights(mse=1.0, physics=0.3, monotone=0.05),
        "workers": 2,
        "val_split": 0.15,  # ~102 frames de validación interna
    },
}

# Rutas relativas al directorio del repo — funcionan en cualquier máquina.
# Estructura: investigador/models/checkpoints/, investigador/models/logs/
_HERE = Path(__file__).resolve().parent          # 02_modelo/
_REPO_ALEXIS = _HERE.parent                      # investigador/
CHECKPOINT_DIR = _REPO_ALEXIS / "models" / "checkpoints"
LOG_DIR        = _REPO_ALEXIS / "models" / "logs"


# ---------------------------------------------------------------------------
# Sampler eficiente para HDF5 gzip
# ---------------------------------------------------------------------------
class ChunkedSampler(torch.utils.data.Sampler):
    """
    Sampler que mezcla a nivel de chunk en vez de imagen a imagen.

    Con shuffle=True y HDF5 gzip:
      - Shuffle normal: cada imagen en un chunk distinto → descomprimir N chunks
        por batch → ~40s/batch con 1M imágenes y gzip
      - ChunkedSampler: mezcla el orden de los 500 chunks, lee cada uno en
        secuencia → cada chunk se descomprime UNA vez para ~8 batches → ~1-3s/batch

    Requiere que el dataset use split contiguo (no random_split) para que los
    índices del Subset estén alineados con los chunks del HDF5.

    Args:
        dataset_size: número total de muestras en el split
        chunk_size:   tamaño de chunk usado al generar el HDF5 (default 2000)
        shuffle:      mezclar orden de chunks (True) o leer secuencial (False)
    """

    def __init__(self, dataset_size: int, chunk_size: int = 2000, shuffle: bool = True):
        self.n = dataset_size
        self.chunk_size = chunk_size
        self.shuffle = shuffle

    def __iter__(self):
        chunks = [list(range(i, min(i + self.chunk_size, self.n)))
                  for i in range(0, self.n, self.chunk_size)]
        if self.shuffle:
            random.shuffle(chunks)
        for chunk in chunks:
            yield from chunk

    def __len__(self) -> int:
        return self.n


# ---------------------------------------------------------------------------
# Dataset HDF5 de alto rendimiento — lectura por slices completos
# ---------------------------------------------------------------------------
class SyntheticHDF5IterDataset(torch.utils.data.IterableDataset):
    """
    IterableDataset que lee el HDF5 gzip en slices completos de chunk.

    Diferencia clave vs acceso por índice individual:
      - hf["images"][start:end]  → 1 llamada h5py, descomprime el chunk UNA vez
      - hf["images"][i] × 2000  → 2000 llamadas h5py, cada una re-descomprime
                                   el chunk desde cero (cache de 1 MB demasiado
                                   chico para chunks de 77 MB)

    Con chunk_size=2000 y batch_size=256: ~8 batches por lectura de disco.
    Speedup esperado: 100-500x vs acceso individual con gzip.

    Args:
        h5_path:          path al archivo HDF5
        chunk_starts:     lista de índices de inicio de cada chunk del split
                          (e.g. [0, 2000, 4000, ...] para train)
        dataset_total:    número total de muestras en el HDF5 (para calcular end)
        hdf5_chunk_size:  tamaño de chunk usado al generar el HDF5 (default 2000)
        shuffle:          mezclar orden de chunks por epoch (True en train)
    """

    def __init__(
        self,
        h5_path: str,
        chunk_starts: list,
        dataset_total: int,
        hdf5_chunk_size: int = 2000,
        shuffle: bool = True,
        augment: bool = False,
    ):
        self.h5_path = h5_path
        self.chunk_starts = chunk_starts
        self.dataset_total = dataset_total
        self.hdf5_chunk_size = hdf5_chunk_size
        self.shuffle = shuffle
        self.augment = augment
        self._len = sum(
            min(s + hdf5_chunk_size, dataset_total) - s for s in chunk_starts
        )

    def __iter__(self):
        chunks = list(self.chunk_starts)
        if self.shuffle:
            random.shuffle(chunks)

        with h5py.File(self.h5_path, "r") as hf:
            for start in chunks:
                end = min(start + self.hdf5_chunk_size, self.dataset_total)

                # UNA sola llamada: lee + descomprime todo el chunk gzip
                images_chunk = hf["images"][start:end].astype(np.float32)
                cwsi_chunk   = hf["cwsi"][start:end].astype(np.float32)

                # Normalización vectorizada sobre todo el chunk
                images_chunk = np.clip((images_chunk - 5.0) / 50.0, 0.0, 1.0)
                images_chunk = images_chunk[:, np.newaxis, :, :]  # (N, 1, 120, 160)

                for i in range(end - start):
                    img = images_chunk[i]
                    if self.augment:
                        # Flip horizontal: la cámara puede estar en cualquier orientación
                        if random.random() > 0.5:
                            img = img[:, :, ::-1].copy()
                        # Flip vertical (menos frecuente)
                        if random.random() > 0.8:
                            img = img[:, ::-1, :].copy()
                        # Jitter de temperatura ±2% (variación de calibración del sensor)
                        img = np.clip(img + np.float32(random.uniform(-0.02, 0.02)), 0.0, 1.0)
                    yield img, cwsi_chunk[i]

    def __len__(self) -> int:
        return self._len


# ---------------------------------------------------------------------------
# Auto-detección de workers óptimos para DataLoader
# ---------------------------------------------------------------------------
def _auto_workers(stage: str) -> int:
    """
    Detecta el número de workers óptimo según el sistema operativo y la etapa.

    - Windows + stage=synthetic: h5py no es fork-safe → workers=0 (obligatorio)
    - Windows + stage=finetune: archivos .npy son fork-safe → hasta 2 workers
    - Linux/Mac: hasta 4 workers (min(4, cpu_count // 4))
    """
    cpu_count = os.cpu_count() or 1
    if platform.system() == "Windows":
        if stage == "synthetic":
            return 0   # h5py + multiprocessing Windows → cuelgue garantizado
        return min(2, max(1, cpu_count // 8))
    return min(4, max(1, cpu_count // 4))


# ---------------------------------------------------------------------------
# Dataset para datos reales Scholander
# ---------------------------------------------------------------------------
class ScholanderDataset(torch.utils.data.Dataset):
    """
    Dataset de frames reales etiquetados con ψ_stem Scholander.

    Estructura esperada del directorio:
        real_data/
            frames/       — NPY float32 (120, 160) por frame
            labels.json   — [{filename, cwsi, psi_stem, vpd, ta, etc_regime}, ...]

    El CWSI real se calcula en campo a partir de T_canopeo medido con la
    cámara + T_wet del panel Wet Ref + T_dry del panel Dry Ref.
    """

    def __init__(self, data_dir: str, augment: bool = False):
        self.data_dir = Path(data_dir)
        self.augment = augment

        labels_path = self.data_dir / "labels.json"
        if not labels_path.exists():
            raise FileNotFoundError(f"No se encontró labels.json en {data_dir}")

        with open(labels_path) as f:
            self.labels = json.load(f)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        entry = self.labels[idx]
        frame_path = self.data_dir / "frames" / entry["filename"]
        image = np.load(frame_path).astype(np.float32)

        # Normalizar: [5°C, 55°C] → [0, 1]
        image = np.clip((image - 5.0) / 50.0, 0.0, 1.0)
        image = image[np.newaxis, :, :]  # (1, 120, 160)

        if self.augment:
            image = self._augment(image)

        cwsi = np.float32(entry["cwsi"])
        vpd = np.float32(entry.get("vpd", 2.0))
        etc = np.float32(entry.get("etc_fraction", 0.5))

        return (
            torch.from_numpy(image),
            torch.tensor([cwsi]),
            torch.tensor([vpd]),
            torch.tensor(etc),
        )

    @staticmethod
    def _augment(image: np.ndarray) -> np.ndarray:
        """Augmentaciones conservadoras que preservan la física térmica."""
        # Flip horizontal (la cámara puede estar orientada en cualquier dirección)
        if np.random.rand() > 0.5:
            image = image[:, :, ::-1].copy()
        # Pequeño jitter de temperatura (±0.1°C / 50°C rango = ±0.002)
        image = image + np.random.normal(0, 0.002, image.shape).astype(np.float32)
        return np.clip(image, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Entrenador
# ---------------------------------------------------------------------------
class Trainer:

    def __init__(self, model: nn.Module, config: dict, stage: str, cultivar: str = "malbec"):
        self.model = model.to(DEVICE)
        self.config = config
        self.stage = stage
        self.cultivar = cultivar

        self.criterion = PINNLoss(config["loss_weights"], cultivar=cultivar)
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config["lr"],
            weight_decay=config["weight_decay"],
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config["epochs"],
            eta_min=config["lr_min"],
        )

        CHECKPOINT_DIR.mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)

        self.best_val_loss = float("inf")
        self.history = []

        # W&B opcional
        try:
            import wandb
            wandb.init(
                project="hydrovision-ag",
                name=f"pinn_{stage}_{time.strftime('%Y%m%d_%H%M')}",
                config={**config, "stage": stage, "device": str(DEVICE)},
            )
            self.wandb = wandb
        except ImportError:
            self.wandb = None

    def _train_epoch_synthetic(self, loader: DataLoader) -> dict:
        """Epoch de entrenamiento en dataset sintético."""
        self.model.train()
        total_loss = 0.0
        total_mse = 0.0
        n_batches = 0
        t_data_total = 0.0
        t_gpu_total  = 0.0

        pbar = tqdm(loader, desc="  train", unit="batch", leave=False)
        t_start_data = time.perf_counter()
        for images, cwsi_real in pbar:
            t_data_total += time.perf_counter() - t_start_data

            t_gpu0 = time.perf_counter()
            images = images.to(DEVICE)
            cwsi_real = cwsi_real.unsqueeze(1).to(DEVICE)

            # VPD no disponible directamente → se estima como 0 para el batch
            # (el término físico se activa solo cuando VPD está disponible)
            vpd = torch.zeros(len(images), 1, device=DEVICE)

            self.optimizer.zero_grad()
            cwsi_pred, delta_t_pred = self.model(images)
            loss, comps = self.criterion(cwsi_pred, delta_t_pred, cwsi_real, vpd)
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            t_gpu_total += time.perf_counter() - t_gpu0

            total_loss += comps["loss_total"]
            total_mse += comps["loss_mse"]
            n_batches += 1
            pbar.set_postfix(
                loss=f"{comps['loss_total']:.4f}",
                data=f"{t_data_total/n_batches:.2f}s",
                gpu=f"{t_gpu_total/n_batches:.3f}s",
            )
            t_start_data = time.perf_counter()

            # Log detallado primeros 3 batches
            if n_batches <= 3:
                print(
                    f"\n  [batch {n_batches}] "
                    f"data={t_data_total:.2f}s  gpu={t_gpu_total:.3f}s  "
                    f"shapes: img={tuple(images.shape)} cwsi={tuple(cwsi_real.shape)}"
                )

        return {
            "train_loss": total_loss / n_batches,
            "train_mse": total_mse / n_batches,
        }

    def _train_epoch_real(self, loader: DataLoader) -> dict:
        """Epoch de entrenamiento en datos reales Scholander."""
        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for images, cwsi_real, vpd, etc in loader:
            images = images.to(DEVICE)
            cwsi_real = cwsi_real.to(DEVICE)
            vpd = vpd.to(DEVICE)
            etc = etc.to(DEVICE)

            self.optimizer.zero_grad()
            cwsi_pred, delta_t_pred = self.model(images)
            loss, comps = self.criterion(cwsi_pred, delta_t_pred, cwsi_real, vpd, etc)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=0.5)
            self.optimizer.step()

            total_loss += comps["loss_total"]
            n_batches += 1

        return {"train_loss": total_loss / n_batches}

    @torch.no_grad()
    def _validate(self, loader: DataLoader) -> dict:
        """Validación: MSE + MAE + R²."""
        self.model.eval()
        preds, truths = [], []

        for batch in loader:
            if len(batch) == 2:
                images, cwsi_real = batch
                images = images.to(DEVICE)
            else:
                images, cwsi_real, _, _ = batch
                images = images.to(DEVICE)

            cwsi_pred, _ = self.model(images)
            preds.append(cwsi_pred.cpu().squeeze(1))
            truths.append(cwsi_real.cpu().reshape(-1))

        preds = torch.cat(preds)
        truths = torch.cat(truths)

        mse = ((preds - truths) ** 2).mean().item()
        mae = (preds - truths).abs().mean().item()
        ss_res = ((preds - truths) ** 2).sum().item()
        ss_tot = ((truths - truths.mean()) ** 2).sum().item()
        r2 = 1.0 - ss_res / (ss_tot + 1e-8)

        return {"val_mse": mse, "val_mae": mae, "val_r2": r2}

    def train(self, train_loader: DataLoader, val_loader: DataLoader) -> None:
        """Loop de entrenamiento completo."""
        use_real = self.stage == "finetune"
        print(f"\nEntrenando stage='{self.stage}' en {DEVICE}")
        print(f"  Cultivar    : {self.cultivar} (parámetros FAO-56 desde config/cultivares.json)")
        print(f"  Epochs      : {self.config['epochs']}")
        print(f"  Batch size  : {self.config['batch_size']}")
        print(f"  LR inicial  : {self.config['lr']}")
        print(f"  Muestras tr.: {len(train_loader.dataset):,}")
        print(f"  Muestras val: {len(val_loader.dataset):,}")

        for epoch in range(1, self.config["epochs"] + 1):
            t0 = time.time()

            if use_real:
                train_metrics = self._train_epoch_real(train_loader)
            else:
                train_metrics = self._train_epoch_synthetic(train_loader)

            val_metrics = self._validate(val_loader)
            self.scheduler.step()

            elapsed = time.time() - t0
            metrics = {**train_metrics, **val_metrics,
                       "epoch": epoch, "lr": self.scheduler.get_last_lr()[0]}

            # Imprimir
            print(
                f"Epoch {epoch:3d}/{self.config['epochs']}  "
                f"loss={train_metrics['train_loss']:.4f}  "
                f"val_mse={val_metrics['val_mse']:.4f}  "
                f"val_r2={val_metrics['val_r2']:.3f}  "
                f"val_mae={val_metrics['val_mae']:.4f}  "
                f"[{elapsed:.1f}s]"
            )

            # W&B logging
            if self.wandb:
                self.wandb.log(metrics)

            self.history.append(metrics)

            # Guardar mejor checkpoint
            if val_metrics["val_mse"] < self.best_val_loss:
                self.best_val_loss = val_metrics["val_mse"]
                ckpt_path = CHECKPOINT_DIR / f"best_{self.stage}.pt"
                torch.save({
                    "epoch": epoch,
                    "model_state": self.model.state_dict(),
                    "optimizer_state": self.optimizer.state_dict(),
                    "metrics": val_metrics,
                    "config": self.config,
                }, ckpt_path)
                print(f"  → Checkpoint guardado: {ckpt_path}")

        # Guardar historial
        history_path = LOG_DIR / f"history_{self.stage}.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)
        print(f"\nHistorial guardado: {history_path}")
        print(f"Mejor val_mse: {self.best_val_loss:.4f}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Entrenamiento PINN HydroVision AG")
    parser.add_argument("--stage", choices=["synthetic", "finetune", "eval"],
                        required=True)
    parser.add_argument("--dataset", type=str, default=None,
                        help="Path al HDF5 del dataset sintético")
    parser.add_argument("--real-data", type=str, default=None,
                        help="Path al directorio de datos reales Scholander")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Checkpoint a cargar (para finetune o eval)")
    parser.add_argument("--edge", action="store_true",
                        help="Usar modelo edge (HydroVisionPINN_Edge)")
    parser.add_argument("--num-workers", type=int, default=None,
                        help="Workers DataLoader. Si se omite, se auto-detecta (0 en Windows+HDF5).")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Carpeta raíz para checkpoints y logs (default: investigador/models/). "
                             "Útil para redirigir a D: y ahorrar espacio en SSD.")
    parser.add_argument("--cultivar", type=str, default="malbec",
                        help="Cultivar de vid (default: malbec). Parámetros físicos FAO-56 "
                             "se cargan automáticamente desde config/cultivares.json.")
    args = parser.parse_args()

    # Redirigir salidas si se especifica --output-dir
    global CHECKPOINT_DIR, LOG_DIR
    if args.output_dir:
        out_root = Path(args.output_dir)
        CHECKPOINT_DIR = out_root / "checkpoints"
        LOG_DIR        = out_root / "logs"
        print(f"  Salidas → {out_root}")

    cfg = CONFIG[args.stage if args.stage != "eval" else "finetune"]
    if args.num_workers is not None:
        workers = args.num_workers
        workers_source = "manual"
    else:
        workers = _auto_workers(args.stage)
        workers_source = f"auto ({os.cpu_count()} CPUs, {platform.system()})"
    cfg = {**cfg, "workers": workers}
    print(f"  Workers DataLoader: {workers}  [{workers_source}]")

    # Modelo
    if args.edge:
        model = HydroVisionPINN_Edge()
        print(f"Modelo Edge: {model.count_parameters():,} parámetros")
    else:
        model = HydroVisionPINN(pretrained=(args.stage == "synthetic"))
        print(f"Modelo PINN: {model.count_parameters():,} parámetros")

    # Cargar checkpoint si se especifica
    if args.checkpoint:
        ckpt = torch.load(args.checkpoint, map_location=DEVICE)
        model.load_state_dict(ckpt["model_state"])
        print(f"Checkpoint cargado: {args.checkpoint}  (epoch {ckpt['epoch']})")

    if args.stage == "synthetic":
        # Dataset sintético HDF5 — leer por slices completos de chunk (no por índice individual)
        h5_path = args.dataset or str(_REPO_ALEXIS / "data" / "dataset_sintetico_1M.h5")
        if not os.path.exists(h5_path):
            print(f"ERROR: No se encontró el dataset en {h5_path}")
            print("Ejecutá primero: python ../01_simulador/generate_large_dataset.py")
            return

        with h5py.File(h5_path, "r") as hf:
            total = int(hf["images"].shape[0])

        hdf5_chunk = 2000
        all_starts = list(range(0, total, hdf5_chunk))   # 500 chunks para 1M imgs
        # Val split aleatorio distribuido: chunks seleccionados de todo el dataset,
        # no solo el final (evita sesgo por orden de generación)
        rng = random.Random(42)
        shuffled = list(all_starts)
        rng.shuffle(shuffled)
        n_val_chunks = max(1, int(len(shuffled) * cfg["val_split"]))
        val_starts   = sorted(shuffled[:n_val_chunks])    # ordenados para I/O eficiente
        train_starts = shuffled[n_val_chunks:]

        train_ds = SyntheticHDF5IterDataset(h5_path, train_starts, total, hdf5_chunk,
                                            shuffle=True, augment=True)
        val_ds   = SyntheticHDF5IterDataset(h5_path, val_starts,   total, hdf5_chunk,
                                            shuffle=False, augment=False)

        train_loader = DataLoader(train_ds, batch_size=cfg["batch_size"],
                                  num_workers=0, pin_memory=DEVICE.type == "cuda")
        val_loader   = DataLoader(val_ds,   batch_size=cfg["batch_size"] * 2,
                                  num_workers=0)

    elif args.stage in ("finetune", "eval"):
        data_dir = args.real_data or str(_REPO_ALEXIS / "data" / "scholander")
        train_ds = ScholanderDataset(data_dir, augment=(args.stage == "finetune"))
        val_n = int(len(train_ds) * cfg["val_split"])
        train_n = len(train_ds) - val_n
        train_ds, val_ds = random_split(train_ds, [train_n, val_n])

        train_loader = DataLoader(train_ds, batch_size=cfg["batch_size"],
                                  shuffle=True, num_workers=cfg["workers"])
        val_loader = DataLoader(val_ds, batch_size=cfg["batch_size"],
                                shuffle=False, num_workers=cfg["workers"])

    if args.stage == "eval":
        # Solo evaluar
        from pinn_loss import PINNLoss
        trainer = Trainer(model, cfg, "eval", cultivar=args.cultivar)
        metrics = trainer._validate(val_loader)
        print(f"\nEvaluación (cultivar: {args.cultivar}):")
        for k, v in metrics.items():
            print(f"  {k:12s} = {v:.4f}")
        return

    trainer = Trainer(model, cfg, args.stage, cultivar=args.cultivar)
    trainer.train(train_loader, val_loader)


if __name__ == "__main__":
    main()
