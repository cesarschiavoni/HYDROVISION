"""
pinn_loss.py — Función de pérdida Physics-Informed para CWSI
HydroVision AG | ML Engineer / 02_modelo

Loss total:
    L = MSE(CWSI_pred, CWSI_real)
      + λ_physics · ‖CWSI_pred − CWSI_physics(ΔT_pred, VPD)‖²
      + λ_monotone · max(0, CWSI(etc_A) − CWSI(etc_B))  [si etc_A > etc_B]

Donde:
    CWSI_physics = clip((ΔT_pred − ΔT_LL) / (ΔT_UL − ΔT_LL), 0, 1)
    ΔT_LL = nwsb_a + nwsb_slope × VPD   (Jackson 1981 two-parameter NWSB)
    ΔT_UL = dt_upper                     (hoja sin transpiración, por cultivar)

    Para Malbec (Colonia Caroya):
        ΔT_LL = 1.5 + (−1.80) × VPD
        A VPD=2.0 kPa → ΔT_LL = 1.5 − 3.6 = −2.1°C ✓  (Bellvert 2016)
        ΔT_UL = 3.5°C  →  hoja en estrés máximo (estomas cerrados)

    NOTA: la versión anterior usaba solo ΔT_LL = −0.45 × VPD (sin intercepto),
    lo que daba −0.90°C a VPD=2.0 kPa — físicamente incorrecto. Corregido con
    la fórmula completa de dos parámetros de Jackson (1981).

El término de física actúa como regularización: el modelo no puede predecir
un CWSI inconsistente con la temperatura diferencial que él mismo estima.
Esto reduce sobreajuste y mejora la generalización a condiciones no vistas.

Referencias:
    Raissi et al. (2019). Physics-informed neural networks.
    Journal of Computational Physics, 378, 686-707.
    Jackson et al. (1981). Canopy temperature as a crop water stress index.
    Water Resources Research, 17(4), 1133-1138.
"""

from __future__ import annotations

import json
import torch
import torch.nn as nn
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Cargar parámetros de cultivares desde config
# ---------------------------------------------------------------------------
def _load_cultivar_params(cultivar: str = "malbec") -> dict:
    """
    Carga parámetros físicos específicos del cultivar desde config/cultivares.json.

    Args:
        cultivar: clave del cultivar (ej: "malbec", "cabernet_sauvignon")

    Returns:
        dict con nwsb_a, nwsb_slope y dt_upper para el cultivar

    Raises:
        ValueError si el cultivar no existe en el config
    """
    config_path = Path(__file__).parent.parent / "config" / "cultivares.json"
    with open(config_path) as f:
        cultivares = json.load(f)

    # Filtrar claves que no son cultivares (e.g. "_nota")
    cultivar_lower = cultivar.lower().replace(" ", "_")
    valid = {k: v for k, v in cultivares.items() if not k.startswith("_")}

    if cultivar_lower not in valid:
        raise ValueError(
            f"Cultivar '{cultivar}' no encontrado. Disponibles: {list(valid.keys())}"
        )

    params = valid[cultivar_lower]
    # Compatibilidad retroactiva: si nwsb_a no existe en config, default 0.0
    if "nwsb_a" not in params:
        params["nwsb_a"] = 0.0
    return params


# Parámetros por defecto (Malbec) — cargados al importar el módulo
_DEFAULT_CULTIVAR_PARAMS = _load_cultivar_params("malbec")
NWSB_A     = _DEFAULT_CULTIVAR_PARAMS["nwsb_a"]      # intercepto ΔT_LL [°C]
NWSB_SLOPE = _DEFAULT_CULTIVAR_PARAMS["nwsb_slope"]  # pendiente [°C/kPa]
DT_UPPER   = _DEFAULT_CULTIVAR_PARAMS["dt_upper"]    # ΔT_UL [°C]
DT_UPPER_STD = 0.5  # variabilidad del ΔT_UL (igual para todos los cultivares)


def physics_cwsi(
    delta_t_pred: torch.Tensor,
    vpd: torch.Tensor,
    dt_upper: float = DT_UPPER,
    nwsb_a: float = NWSB_A,
    nwsb_slope: float = NWSB_SLOPE,
) -> torch.Tensor:
    """
    Calcula el CWSI esperado por la física dada la ΔT predicha.

    CWSI_physics = clip((ΔT_pred − ΔT_LL) / (ΔT_UL − ΔT_LL), 0, 1)

    ΔT_LL = nwsb_a + nwsb_slope × VPD   (Jackson 1981, fórmula completa)

    Para Malbec: nwsb_a=1.5, nwsb_slope=-1.80
        → ΔT_LL(VPD=2.0) = 1.5 − 3.6 = −2.1°C ✓

    Args:
        delta_t_pred: (B, 1) — temperatura diferencial predicha [°C]
        vpd:          (B, 1) — déficit de presión de vapor [kPa]
        dt_upper:     ΔT del límite superior [°C]
        nwsb_a:       intercepto NWSB [°C]
        nwsb_slope:   pendiente NWSB [°C/kPa] (negativo para vid)

    Returns:
        cwsi_physics: (B, 1) — CWSI calculado por física ∈ [0, 1]
    """
    dt_ll = nwsb_a + nwsb_slope * vpd  # límite inferior (planta bien regada)
    dt_ul = torch.full_like(vpd, dt_upper)
    denom = torch.clamp(dt_ul - dt_ll, min=0.5)
    cwsi_phys = (delta_t_pred - dt_ll) / denom
    return torch.clamp(cwsi_phys, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Loss PINN
# ---------------------------------------------------------------------------
@dataclass
class PINNLossWeights:
    """Pesos de cada término del loss. Ajustables en config."""
    mse: float = 1.0         # MSE principal CWSI_pred vs CWSI_real
    physics: float = 0.5     # consistencia física ΔT ↔ CWSI
    monotone: float = 0.1    # ordenamiento monotónico por régimen hídrico


class PINNLoss(nn.Module):
    """
    Loss compuesta para el PINN de HydroVision AG.

        L_total = w_mse   · MSE(CWSI_pred, CWSI_real)
                + w_phys  · MSE(CWSI_pred, CWSI_physics(ΔT_pred, VPD))
                + w_mono  · penalización_monotónica

    Los parámetros físicos (NWSB_SLOPE, DT_UPPER) se cargan automáticamente
    según el cultivar desde config/cultivares.json (FAO-56).

    Uso típico:
        criterion = PINNLoss(weights=PINNLossWeights(physics=0.5), cultivar="malbec")
        loss, components = criterion(cwsi_pred, delta_t_pred, cwsi_real, vpd)
    """

    def __init__(
        self,
        weights: Optional[PINNLossWeights] = None,
        cultivar: str = "malbec",
        dt_upper: Optional[float] = None,
    ):
        super().__init__()
        self.w = weights or PINNLossWeights()
        self.cultivar = cultivar

        # Cargar parámetros físicos específicos del cultivar
        cultivar_params = _load_cultivar_params(cultivar)
        self.nwsb_a     = cultivar_params["nwsb_a"]      # intercepto ΔT_LL
        self.nwsb_slope = cultivar_params["nwsb_slope"]  # pendiente VPD
        # dt_upper puede ser override manual, por defecto viene del config
        self.dt_upper = dt_upper if dt_upper is not None else cultivar_params["dt_upper"]

        self.mse = nn.MSELoss()

    def _physics_cwsi(
        self,
        delta_t_pred: torch.Tensor,
        vpd: torch.Tensor,
    ) -> torch.Tensor:
        """
        Calcula CWSI físico usando parámetros del cultivar.

        ΔT_LL = nwsb_a + nwsb_slope × VPD  (Jackson 1981, dos parámetros)
        """
        dt_ll = self.nwsb_a + self.nwsb_slope * vpd
        dt_ul = torch.full_like(vpd, self.dt_upper)
        denom = torch.clamp(dt_ul - dt_ll, min=0.5)
        cwsi_phys = (delta_t_pred - dt_ll) / denom
        return torch.clamp(cwsi_phys, 0.0, 1.0)

    def forward(
        self,
        cwsi_pred: torch.Tensor,     # (B, 1) — salida head CWSI
        delta_t_pred: torch.Tensor,  # (B, 1) — salida head ΔT
        cwsi_real: torch.Tensor,     # (B, 1) — label ground truth
        vpd: torch.Tensor,           # (B, 1) — VPD del frame [kPa]
        etc_fraction: Optional[torch.Tensor] = None,  # (B,) — para monotónica
    ):
        """
        Calcula el loss PINN completo.

        Returns:
            loss_total: escalar — loss para backprop
            components: dict con cada término (para logging W&B)
        """
        # --- Término 1: MSE supervisado ---
        loss_mse = self.mse(cwsi_pred, cwsi_real)

        # --- Término 2: Consistencia física ---
        cwsi_phys = self._physics_cwsi(delta_t_pred, vpd)
        loss_physics = self.mse(cwsi_pred, cwsi_phys)

        # --- Término 3: Monotónica (opcional) ---
        loss_mono = torch.tensor(0.0, device=cwsi_pred.device)
        if etc_fraction is not None and len(etc_fraction) >= 2:
            # Penalizar si CWSI no decrece cuando ETc aumenta
            # Para pares dentro del batch: si etc_i > etc_j → cwsi_i < cwsi_j
            cwsi_flat = cwsi_pred.squeeze(1)
            etc_flat = etc_fraction
            # Tomar todos los pares (i, j) donde etc_i > etc_j
            etc_i = etc_flat.unsqueeze(1)   # (B, 1)
            etc_j = etc_flat.unsqueeze(0)   # (1, B)
            cwsi_i = cwsi_flat.unsqueeze(1)
            cwsi_j = cwsi_flat.unsqueeze(0)
            # Penalizar cuando etc_i > etc_j pero cwsi_i >= cwsi_j (violación monotónica)
            violation_mask = (etc_i - etc_j) > 0.15   # diferencia significativa de ETc
            violations = torch.relu(cwsi_i - cwsi_j + 0.02)  # pequeño margen
            loss_mono = (violations * violation_mask.float()).mean()

        # --- Loss total ---
        loss_total = (
            self.w.mse * loss_mse
            + self.w.physics * loss_physics
            + self.w.monotone * loss_mono
        )

        components = {
            "loss_total": loss_total.item(),
            "loss_mse": loss_mse.item(),
            "loss_physics": loss_physics.item(),
            "loss_monotone": loss_mono.item(),
        }

        return loss_total, components


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    torch = __import__("torch")

    B = 16
    cwsi_pred = torch.sigmoid(torch.randn(B, 1))
    delta_t_pred = torch.randn(B, 1) * 3
    cwsi_real = torch.rand(B, 1)
    vpd = torch.rand(B, 1) * 2.5 + 0.5
    etc = torch.tensor([1.0, 0.65, 0.4, 0.15, 0.0] * (B // 5 + 1))[:B]

    criterion = PINNLoss(PINNLossWeights(mse=1.0, physics=0.5, monotone=0.1))
    loss, comps = criterion(cwsi_pred, delta_t_pred, cwsi_real, vpd, etc)

    print("PINNLoss demo:")
    for k, v in comps.items():
        print(f"  {k:20s} = {v:.6f}")

    print(f"\nFísica Malbec: ΔT_LL = {NWSB_A} + {NWSB_SLOPE}×VPD  |  ΔT_UL = {DT_UPPER}°C")
    vpd_demo = torch.tensor([[2.0]])
    dt_demo = torch.tensor([[1.5]])
    cw = physics_cwsi(dt_demo, vpd_demo)
    dt_ll_demo = NWSB_A + NWSB_SLOPE * 2.0
    print(f"  VPD=2.0 kPa → ΔT_LL = {dt_ll_demo:.2f}°C")
    print(f"  VPD=2.0 kPa, ΔT_pred=1.5°C → CWSI_physics = {cw.item():.3f}")
    # Verificar: CWSI = (1.5 - (-2.1)) / (3.5 - (-2.1)) = 3.6 / 5.6 ≈ 0.643
    print(f"  Verificación manual: (1.5 - ({dt_ll_demo:.2f})) / ({DT_UPPER} - ({dt_ll_demo:.2f})) = {(1.5 - dt_ll_demo) / (DT_UPPER - dt_ll_demo):.3f}")
