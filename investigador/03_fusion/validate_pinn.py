"""
validate_pinn.py — Validación del modelo PINN contra ground-truth Scholander
HydroVision AG | ML Engineer / 03_fusion

Evalúa el checkpoint entrenado sobre el dataset Scholander y genera:
    - Métricas: MAE, RMSE, R² (CWSI_pred vs CWSI_real y vs ψ_stem)
    - Scatter plot: CWSI_pred vs CWSI_real coloreado por zona RDI
    - Scatter plot: CWSI_pred vs ψ_stem (si disponible)
    - Bland-Altman: sesgo y límites de acuerdo
    - Curvas por sesión: evolución de error a lo largo del ciclo
    - Resumen estadístico: metrics.json + metrics_summary.txt

Target TRL 4:
    MAE  < 0.10  (CWSI vs CWSI_real)
    R²   > 0.60  (CWSI vs CWSI_real)
    R²   > 0.75  (CWSI vs ψ_stem Scholander, post-finetune)

Uso:
    # Desde investigador/ o desde investigador/03_fusion/
    python validate_pinn.py \\
        --checkpoint ../models/checkpoints/best_finetune.pt \\
        --data-dir ../data/scholander/ \\
        --output-dir ../models/logs/validation_S4/

    # Solo métricas sin gráficos:
    python validate_pinn.py --checkpoint ... --data-dir ... --no-plots

    # Dataset sintético (sin Scholander real):
    python validate_pinn.py \\
        --checkpoint ../models/checkpoints/best_synthetic.pt \\
        --synthetic ../data/dataset_sintetico_1M.h5 \\
        --n-synthetic 5000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader

# ---------------------------------------------------------------------------
# Paths relativos al módulo
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # 03_fusion/
_ALEXIS = _HERE.parent                           # investigador/
_MODELO = _ALEXIS / "02_modelo"
sys.path.insert(0, str(_MODELO))
sys.path.insert(0, str(_ALEXIS / "01_simulador"))

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ---------------------------------------------------------------------------
# Carga del modelo desde checkpoint
# ---------------------------------------------------------------------------
def load_model(checkpoint_path: str | Path, edge: bool = False) -> torch.nn.Module:
    """
    Carga el modelo PINN desde un checkpoint .pt.

    Args:
        checkpoint_path: ruta al archivo .pt
        edge:            si True, cargar HydroVisionPINN_Edge

    Returns:
        modelo en eval mode en DEVICE
    """
    from pinn_model import HydroVisionPINN, HydroVisionPINN_Edge

    ckpt = torch.load(checkpoint_path, map_location=DEVICE)
    model_cls = HydroVisionPINN_Edge if edge else HydroVisionPINN
    model = model_cls(pretrained=False)
    model.load_state_dict(ckpt["model_state"])
    model.eval().to(DEVICE)

    epoch = ckpt.get("epoch", "?")
    val_mse = ckpt.get("metrics", {}).get("val_mse", "?")
    print(f"Modelo cargado: epoch={epoch}, val_mse={val_mse}")
    return model


# ---------------------------------------------------------------------------
# Métricas escalares
# ---------------------------------------------------------------------------
def compute_metrics(
    preds: np.ndarray,
    targets: np.ndarray,
    label: str = "CWSI",
) -> dict:
    """
    Calcula MAE, RMSE, R², sesgo y límites de acuerdo (Bland-Altman).

    Args:
        preds:   predicciones del modelo (N,)
        targets: valores reales (N,)
        label:   etiqueta para los mensajes

    Returns:
        dict con todas las métricas
    """
    diff = preds - targets
    mae = float(np.abs(diff).mean())
    rmse = float(np.sqrt((diff ** 2).mean()))

    ss_res = float(((targets - preds) ** 2).sum())
    ss_tot = float(((targets - targets.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / (ss_tot + 1e-10)

    # Bland-Altman
    mean_vals = (preds + targets) / 2.0
    bias = float(diff.mean())
    std_diff = float(diff.std())
    loa_upper = bias + 1.96 * std_diff   # Upper Limit of Agreement
    loa_lower = bias - 1.96 * std_diff

    return {
        "label": label,
        "n": int(len(preds)),
        "mae": round(mae, 5),
        "rmse": round(rmse, 5),
        "r2": round(r2, 5),
        "bias": round(bias, 5),
        "std_diff": round(std_diff, 5),
        "loa_upper": round(loa_upper, 5),
        "loa_lower": round(loa_lower, 5),
        "within_target_mae": bool(mae < 0.10),
        "within_target_r2": bool(r2 > 0.60),
    }


# ---------------------------------------------------------------------------
# Evaluación sobre ScholanderDataset
# ---------------------------------------------------------------------------
@torch.no_grad()
def evaluate_scholander(
    model: torch.nn.Module,
    data_dir: str | Path,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[dict]]:
    """
    Corre el modelo sobre el dataset Scholander y recolecta predicciones y labels.

    Args:
        model:    modelo en eval mode
        data_dir: directorio con frames/ y labels.json

    Returns:
        cwsi_preds:  (N,) predicciones del modelo
        cwsi_real:   (N,) ground truth CWSI del dataset
        psi_stems:   (N,) ψ_stem medido [MPa] (NaN si no disponible)
        labels_list: lista de dicts con todos los campos de cada entrada
    """
    from train import ScholanderDataset

    ds = ScholanderDataset(str(data_dir), augment=False)
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)

    all_preds, all_cwsi, all_vpd, all_psi = [], [], [], []
    labels_list = []

    for images, cwsi_gt, vpd_batch, etc_batch in loader:
        images = images.to(DEVICE)
        cwsi_pred, _ = model(images)
        all_preds.append(cwsi_pred.cpu().squeeze(1).numpy())
        all_cwsi.append(cwsi_gt.cpu().reshape(-1).numpy())

    # ψ_stem: cargar desde labels.json (no está en el DataLoader estándar)
    labels_path = Path(data_dir) / "labels.json"
    with open(labels_path) as f:
        labels_raw = json.load(f)

    psi_arr = np.array([
        float(e.get("psi_stem", float("nan"))) for e in labels_raw
    ])

    labels_list = labels_raw
    cwsi_preds = np.concatenate(all_preds)
    cwsi_real_arr = np.concatenate(all_cwsi)

    # Asegurar que el orden de ψ_stem coincide con el del DataLoader
    # (ScholanderDataset lee en orden del JSON, igual que DataLoader con shuffle=False)
    assert len(psi_arr) == len(cwsi_preds), (
        f"Desajuste: {len(psi_arr)} etiquetas vs {len(cwsi_preds)} predicciones"
    )

    return cwsi_preds, cwsi_real_arr, psi_arr, labels_list


# ---------------------------------------------------------------------------
# Evaluación sobre dataset sintético (para validación del pre-entrenamiento)
# ---------------------------------------------------------------------------
@torch.no_grad()
def evaluate_synthetic(
    model: torch.nn.Module,
    h5_path: str | Path,
    n_samples: int = 5000,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evalúa sobre un subconjunto del dataset sintético HDF5.

    Args:
        model:     modelo en eval mode
        h5_path:   path al HDF5
        n_samples: número de muestras a evaluar (default 5000)

    Returns:
        cwsi_preds, cwsi_real — arrays (n_samples,)
    """
    import h5py

    with h5py.File(h5_path, "r") as hf:
        total = int(hf["images"].shape[0])
        idxs = np.random.choice(total, min(n_samples, total), replace=False)
        idxs.sort()

        # Leer en chunks para eficiencia
        images_np = hf["images"][idxs].astype(np.float32)
        cwsi_real_np = hf["cwsi"][idxs].astype(np.float32)

    # Normalizar
    images_np = np.clip((images_np - 5.0) / 50.0, 0.0, 1.0)
    images_np = images_np[:, np.newaxis, :, :]  # (N, 1, 120, 160)

    all_preds = []
    batch_size = 256
    for i in range(0, len(images_np), batch_size):
        batch = torch.from_numpy(images_np[i:i + batch_size]).to(DEVICE)
        preds, _ = model(batch)
        all_preds.append(preds.cpu().squeeze(1).numpy())

    return np.concatenate(all_preds), cwsi_real_np


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def _zone_colors() -> dict:
    """Mapa zona → color para scatter plots."""
    return {
        "A": "#2196F3",   # azul — control pleno (100% ETc)
        "B": "#4CAF50",   # verde — 65% ETc
        "C": "#FF9800",   # naranja — 40% ETc
        "D": "#F44336",   # rojo — 15% ETc
        "E": "#9C27B0",   # violeta — 0% ETc (sin riego)
    }


def plot_scatter_cwsi(
    preds: np.ndarray,
    targets: np.ndarray,
    metrics: dict,
    output_path: str | Path,
    labels_list: Optional[List[dict]] = None,
    title: str = "CWSI predicho vs CWSI real",
) -> None:
    """
    Scatter plot CWSI_pred vs CWSI_real con línea 1:1 y R² anotado.

    Puntos coloreados por zona RDI si labels_list está disponible.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6))

    if labels_list:
        colors_map = _zone_colors()
        zones = [e.get("zone", "A") for e in labels_list[:len(preds)]]
        unique_zones = sorted(set(zones))
        for zone in unique_zones:
            mask = np.array([z == zone for z in zones])
            etc_pct = {"A": 100, "B": 65, "C": 40, "D": 15, "E": 0}.get(zone, "?")
            ax.scatter(
                targets[mask], preds[mask],
                c=colors_map.get(zone, "#888"),
                label=f"Zona {zone} — {etc_pct}% ETc",
                alpha=0.7, s=40, edgecolors="none",
            )
        ax.legend(loc="upper left", fontsize=9)
    else:
        ax.scatter(targets, preds, c="#2196F3", alpha=0.6, s=30, edgecolors="none")

    # Línea 1:1
    lim = [min(targets.min(), preds.min()) - 0.05, max(targets.max(), preds.max()) + 0.05]
    ax.plot(lim, lim, "k--", linewidth=1.0, label="1:1")
    ax.set_xlim(lim)
    ax.set_ylim(lim)

    # Anotación métricas
    ax.text(
        0.97, 0.05,
        f"R² = {metrics['r2']:.3f}\nRMSE = {metrics['rmse']:.3f}\nMAE = {metrics['mae']:.3f}\nn = {metrics['n']}",
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    ax.set_xlabel("CWSI real (ground truth)", fontsize=12)
    ax.set_ylabel("CWSI predicho (modelo)", fontsize=12)
    ax.set_title(title, fontsize=13)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Scatter CWSI guardado: {output_path}")


def plot_scatter_psi(
    preds: np.ndarray,
    psi_stems: np.ndarray,
    output_path: str | Path,
    labels_list: Optional[List[dict]] = None,
) -> dict:
    """
    Scatter plot CWSI_pred vs ψ_stem con regresión lineal.

    Ignora entradas donde ψ_stem es NaN.
    Retorna métricas de correlación CWSI–ψ_stem.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import stats

    valid = ~np.isnan(psi_stems)
    if valid.sum() < 5:
        print("  Scatter ψ_stem omitido: menos de 5 entradas con ψ_stem disponible")
        return {}

    p = preds[valid]
    psi = psi_stems[valid]
    lbl = [labels_list[i] for i in range(len(labels_list)) if valid[i]] if labels_list else None

    # Regresión lineal ψ_stem = a + b * CWSI
    slope, intercept, r, p_val, se = stats.linregress(p, psi)
    r2_psi = r ** 2

    fig, ax = plt.subplots(figsize=(7, 6))

    if lbl:
        colors_map = _zone_colors()
        zones = [e.get("zone", "A") for e in lbl]
        unique_zones = sorted(set(zones))
        for zone in unique_zones:
            mask = np.array([z == zone for z in zones])
            etc_pct = {"A": 100, "B": 65, "C": 40, "D": 15, "E": 0}.get(zone, "?")
            ax.scatter(p[mask], psi[mask],
                       c=colors_map.get(zone, "#888"),
                       label=f"Zona {zone} — {etc_pct}% ETc",
                       alpha=0.7, s=40, edgecolors="none")
        ax.legend(loc="upper right", fontsize=9)
    else:
        ax.scatter(p, psi, c="#E91E63", alpha=0.6, s=30, edgecolors="none")

    # Línea de regresión
    x_line = np.linspace(p.min(), p.max(), 100)
    ax.plot(x_line, intercept + slope * x_line, "k-", linewidth=1.5,
            label=f"ψ = {intercept:.2f} + {slope:.2f}·CWSI")

    ax.text(
        0.97, 0.97,
        f"R² = {r2_psi:.3f}\nR = {r:.3f}\nn = {valid.sum()}",
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    ax.set_xlabel("CWSI predicho (modelo)", fontsize=12)
    ax.set_ylabel("ψ_stem medido (Scholander) [MPa]", fontsize=12)
    ax.set_title("CWSI predicho vs ψ_stem Scholander", fontsize=13)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Scatter ψ_stem guardado: {output_path}")

    return {
        "r2_cwsi_psi": round(r2_psi, 5),
        "r_cwsi_psi": round(float(r), 5),
        "slope_psi_cwsi": round(float(slope), 4),
        "intercept_psi_cwsi": round(float(intercept), 4),
        "n_psi": int(valid.sum()),
        "within_target_r2_psi": bool(r2_psi > 0.75),
    }


def plot_bland_altman(
    preds: np.ndarray,
    targets: np.ndarray,
    metrics: dict,
    output_path: str | Path,
) -> None:
    """
    Diagrama de Bland-Altman: diferencia vs media, con bandas de acuerdo (±1.96σ).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    diff = preds - targets
    mean_vals = (preds + targets) / 2.0
    bias = metrics["bias"]
    loa_upper = metrics["loa_upper"]
    loa_lower = metrics["loa_lower"]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(mean_vals, diff, alpha=0.5, s=30, c="#607D8B", edgecolors="none")

    ax.axhline(bias, color="#F44336", linewidth=1.5, label=f"Sesgo: {bias:+.3f}")
    ax.axhline(loa_upper, color="#FF9800", linewidth=1.2, linestyle="--",
               label=f"+1.96σ: {loa_upper:+.3f}")
    ax.axhline(loa_lower, color="#FF9800", linewidth=1.2, linestyle="--",
               label=f"−1.96σ: {loa_lower:+.3f}")
    ax.axhline(0, color="k", linewidth=0.7, linestyle=":")

    ax.set_xlabel("Media (CWSI_pred + CWSI_real) / 2", fontsize=11)
    ax.set_ylabel("Diferencia (CWSI_pred − CWSI_real)", fontsize=11)
    ax.set_title("Bland-Altman — CWSI predicho vs real", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Bland-Altman guardado: {output_path}")


def plot_error_by_session(
    preds: np.ndarray,
    targets: np.ndarray,
    labels_list: List[dict],
    output_path: str | Path,
) -> None:
    """
    Box plot del error CWSI por sesión Scholander (S1–S4).
    Muestra si el modelo mejora con cada sesión de fine-tuning.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sessions = sorted(set(e.get("session", 1) for e in labels_list[:len(preds)]))
    if len(sessions) < 2:
        return  # no hay suficientes sesiones para plot útil

    errors_by_session = {}
    for s in sessions:
        mask = np.array([e.get("session", 1) == s for e in labels_list[:len(preds)]])
        errors_by_session[s] = np.abs(preds[mask] - targets[mask])

    fig, ax = plt.subplots(figsize=(7, 5))
    session_names = [f"S{s}" for s in sessions]
    ax.boxplot(
        [errors_by_session[s] for s in sessions],
        labels=session_names,
        patch_artist=True,
        boxprops=dict(facecolor="#BBDEFB"),
        medianprops=dict(color="#1976D2", linewidth=2),
    )
    ax.axhline(0.10, color="#F44336", linestyle="--", linewidth=1.2,
               label="Target MAE = 0.10")
    ax.set_xlabel("Sesión Scholander", fontsize=12)
    ax.set_ylabel("|CWSI_pred − CWSI_real|", fontsize=12)
    ax.set_title("Error absoluto CWSI por sesión", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Error por sesión guardado: {output_path}")


# ---------------------------------------------------------------------------
# CLI principal
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Validación del PINN HydroVision AG vs ground-truth Scholander"
    )
    parser.add_argument("--checkpoint", required=True,
        help="Checkpoint PyTorch (.pt) — ej: ../models/checkpoints/best_finetune.pt")
    parser.add_argument("--data-dir", default=None,
        help="Directorio con frames/ + labels.json (dataset Scholander real)")
    parser.add_argument("--synthetic", default=None,
        help="HDF5 del dataset sintético (alternativa a --data-dir)")
    parser.add_argument("--n-synthetic", type=int, default=5000,
        help="Número de muestras sintéticas a evaluar (default 5000)")
    parser.add_argument("--output-dir", default=None,
        help="Directorio para métricas y gráficos (default: ../models/logs/validation/)")
    parser.add_argument("--no-plots", action="store_true",
        help="Solo calcular métricas, sin generar gráficos")
    parser.add_argument("--edge", action="store_true",
        help="Usar modelo HydroVisionPINN_Edge en lugar del PINN completo")
    args = parser.parse_args()

    if args.data_dir is None and args.synthetic is None:
        parser.error("Se requiere --data-dir o --synthetic")

    # Directorio de salida
    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        out_dir = _ALEXIS / "models" / "logs" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nHydroVision AG — Validación PINN")
    print(f"  Checkpoint : {args.checkpoint}")
    print(f"  Dispositivo: {DEVICE}")
    print(f"  Salida     : {out_dir}")
    print()

    # Cargar modelo
    model = load_model(args.checkpoint, edge=args.edge)

    # Evaluar
    if args.data_dir:
        print("Evaluando en dataset Scholander...")
        preds, targets, psi_stems, labels_list = evaluate_scholander(model, args.data_dir)
        mode_tag = "scholander"
    else:
        print(f"Evaluando en dataset sintético ({args.n_synthetic} muestras)...")
        preds, targets = evaluate_synthetic(model, args.synthetic, args.n_synthetic)
        psi_stems = np.full(len(preds), float("nan"))
        labels_list = []
        mode_tag = "synthetic"

    print(f"  n evaluados: {len(preds)}")

    # Métricas CWSI
    metrics_cwsi = compute_metrics(preds, targets, label="CWSI_pred_vs_real")
    print(f"\nMétricas CWSI (pred vs real):")
    for k, v in metrics_cwsi.items():
        if k != "label":
            print(f"  {k:<22} = {v}")

    # Métricas vs ψ_stem (si hay datos)
    metrics_psi = {}
    n_psi_valid = int((~np.isnan(psi_stems)).sum())
    if n_psi_valid >= 5:
        print(f"\nCorrelación CWSI–ψ_stem ({n_psi_valid} pares):")
        valid_mask = ~np.isnan(psi_stems)
        from scipy import stats
        r, p_val = stats.pearsonr(preds[valid_mask], psi_stems[valid_mask])
        print(f"  r = {r:.4f}, p = {p_val:.4e}")
        print(f"  R² = {r**2:.4f}")
        metrics_psi = {"r_cwsi_psi": round(r, 5), "r2_cwsi_psi": round(r**2, 5),
                       "n_psi": n_psi_valid}
    else:
        print(f"\n  ψ_stem disponible en {n_psi_valid} muestras — insuficiente para correlación")

    # Guardar metrics.json
    all_metrics = {
        "checkpoint": str(args.checkpoint),
        "mode": mode_tag,
        "device": str(DEVICE),
        **metrics_cwsi,
        **metrics_psi,
    }
    metrics_path = out_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nMétricas guardadas: {metrics_path}")

    # Resumen TRL
    summary_lines = [
        "=" * 55,
        "HydroVision AG — Resumen de validación PINN",
        "=" * 55,
        f"n evaluados  : {len(preds)}",
        f"",
        f"CWSI pred vs CWSI real:",
        f"  MAE  = {metrics_cwsi['mae']:.4f}  {'✓ OK (<0.10)' if metrics_cwsi['within_target_mae'] else '✗ REVISAR (>0.10)'}",
        f"  RMSE = {metrics_cwsi['rmse']:.4f}",
        f"  R²   = {metrics_cwsi['r2']:.4f}  {'✓ OK (>0.60)' if metrics_cwsi['within_target_r2'] else '✗ REVISAR (<0.60)'}",
        f"  Sesgo = {metrics_cwsi['bias']:+.4f}",
        f"  LoA  = [{metrics_cwsi['loa_lower']:+.3f}, {metrics_cwsi['loa_upper']:+.3f}]",
    ]
    if metrics_psi:
        summary_lines += [
            f"",
            f"CWSI pred vs ψ_stem Scholander:",
            f"  R    = {metrics_psi['r_cwsi_psi']:.4f}",
            f"  R²   = {metrics_psi['r2_cwsi_psi']:.4f}  {'✓ OK (>0.75)' if metrics_psi.get('r2_cwsi_psi', 0) > 0.75 else '✗ REVISAR (<0.75)'}",
        ]
    summary_lines.append("=" * 55)

    summary_txt = "\n".join(summary_lines)
    print("\n" + summary_txt)

    summary_path = out_dir / "metrics_summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary_txt + "\n")
    print(f"Resumen guardado: {summary_path}")

    # Gráficos
    if not args.no_plots:
        try:
            import matplotlib  # noqa: F401 — verificar disponibilidad
            print("\nGenerando gráficos...")

            plot_scatter_cwsi(
                preds, targets, metrics_cwsi,
                out_dir / "scatter_cwsi.png",
                labels_list=labels_list if labels_list else None,
                title=f"CWSI predicho vs real — {mode_tag.capitalize()}",
            )

            plot_bland_altman(
                preds, targets, metrics_cwsi,
                out_dir / "bland_altman.png",
            )

            if n_psi_valid >= 5:
                psi_metrics_plot = plot_scatter_psi(
                    preds, psi_stems,
                    out_dir / "scatter_psi_stem.png",
                    labels_list=labels_list if labels_list else None,
                )
                # Actualizar metrics.json con métricas del scatter ψ_stem
                all_metrics.update(psi_metrics_plot)
                with open(metrics_path, "w") as f:
                    json.dump(all_metrics, f, indent=2)

            if labels_list:
                plot_error_by_session(
                    preds, targets, labels_list,
                    out_dir / "error_by_session.png",
                )

        except ImportError:
            print("  matplotlib no disponible — omitiendo gráficos")
            print("  Instalar con: pip install matplotlib scipy")


if __name__ == "__main__":
    main()
