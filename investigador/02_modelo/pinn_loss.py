"""
pinn_loss.py — Función de pérdida Physics-Informed para CWSI
HydroVision AG | ML Engineer / 02_modelo

Loss total:
    L = MSE(CWSI_pred, CWSI_real)
      + λ_physics · ‖CWSI_pred − CWSI_physics(ΔT_pred, VPD)‖²
      + λ_monotone · max(0, CWSI(etc_A) − CWSI(etc_B))  [si etc_A > etc_B]
      + λ_ra_wind · ‖CWSI_pred − CWSI_wind_physics(ΔT_pred, VPD, wind, Rn)‖²  [C6]

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

    [C6] Restricción ra(wind):
    Cuando se dispone de wind_ms y Rn, se aplica la formulación teórica
    completa con resistencia aerodinámica dinámica (Jackson 1981, FAO-56):
        ra = 208 / u                     [s/m]  (FAO-56 Eq. 4)
        ΔT_LL = (ra·Rn/(ρ·Cp)) × (γ/(Δ+γ)) − VPD/(Δ+γ)
        ΔT_UL = ra·Rn/(ρ·Cp)
    Esto permite al PINN aprender que con más viento, los baselines se
    comprimen (ra↓ → ΔT_LL, ΔT_UL ↓) y el CWSI se redistribuye.

El término de física actúa como regularización: el modelo no puede predecir
un CWSI inconsistente con la temperatura diferencial que él mismo estima.
Esto reduce sobreajuste y mejora la generalización a condiciones no vistas.

Referencias:
    Raissi et al. (2019). Physics-informed neural networks.
    Journal of Computational Physics, 378, 686-707.
    Jackson et al. (1981). Canopy temperature as a crop water stress index.
    Water Resources Research, 17(4), 1133-1138.
    Allen et al. (1998). Crop evapotranspiration — FAO Irrigation and
    Drainage Paper 56. Eq. 4: ra = 208/u.
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


# ---------------------------------------------------------------------------
# Constantes físicas para balance energético (FAO-56 / Jackson 1981)
# ---------------------------------------------------------------------------
RHO_CP = 1200.0    # ρ·Cp del aire [J/(m³·K)] — densidad×calor específico
GAMMA  = 0.066     # constante psicrométrica [kPa/°C] (a ~1000 hPa)
RA_MIN = 20.0      # ra mínimo para evitar singularidad a viento alto [s/m]


def _aerodynamic_resistance(wind_ms: torch.Tensor) -> torch.Tensor:
    """
    Resistencia aerodinámica ra = 208 / u  [s/m]  (FAO-56 Eq. 4).

    Clamp inferior a RA_MIN (20 s/m ≈ 10.4 m/s) para estabilidad numérica.
    Clamp superior a 416 s/m (u=0.5 m/s, calma total).
    """
    wind_clamped = torch.clamp(wind_ms, min=0.5, max=10.4)
    return 208.0 / wind_clamped


def _saturation_slope(t_air: torch.Tensor) -> torch.Tensor:
    """
    Pendiente de la curva de presión de saturación Δ [kPa/°C].
    Tetens (1930) / FAO-56 Eq. 13:
        Δ = 4098 × 0.6108 × exp(17.27·T / (T+237.3)) / (T+237.3)²
    """
    return (4098.0 * 0.6108 * torch.exp(17.27 * t_air / (t_air + 237.3))
            / (t_air + 237.3) ** 2)


def physics_cwsi_wind(
    delta_t_pred: torch.Tensor,
    vpd: torch.Tensor,
    wind_ms: torch.Tensor,
    rad_wm2: torch.Tensor,
    t_air: torch.Tensor,
) -> torch.Tensor:
    """
    CWSI teórico con baselines dependientes del viento (Jackson 1981 + FAO-56).  [C6]

    ΔT_LL = (ra·Rn/(ρ·Cp)) × (γ/(Δ+γ)) − VPD/(Δ+γ)   [planta bien regada]
    ΔT_UL = ra·Rn/(ρ·Cp)                                [estomas cerrados]
    CWSI = clip((ΔT_pred − ΔT_LL) / (ΔT_UL − ΔT_LL), 0, 1)

    Cuando el viento aumenta, ra disminuye → ambos baselines se comprimen →
    el rango disponible (ΔT_UL − ΔT_LL) se reduce. Esto enseña al PINN que
    las predicciones a viento alto deben tener menor separación ΔT.

    Args:
        delta_t_pred: (B, 1) — ΔT predicha por el modelo [°C]
        vpd:          (B, 1) — déficit de presión de vapor [kPa]
        wind_ms:      (B, 1) — velocidad del viento [m/s]
        rad_wm2:      (B, 1) — radiación neta [W/m²]
        t_air:        (B, 1) — temperatura del aire [°C]

    Returns:
        cwsi_wind: (B, 1) — CWSI calculado con baselines dinámicos ∈ [0, 1]
    """
    ra = _aerodynamic_resistance(wind_ms)
    delta = _saturation_slope(t_air)

    # Balance energético: Rn en W/m² = J/(m²·s)
    ra_rn_rhocp = ra * rad_wm2 / RHO_CP  # [°C]

    delta_gamma = delta + GAMMA
    dt_ll = ra_rn_rhocp * (GAMMA / delta_gamma) - vpd / delta_gamma
    dt_ul = ra_rn_rhocp

    denom = torch.clamp(dt_ul - dt_ll, min=0.5)
    cwsi_wind = (delta_t_pred - dt_ll) / denom
    return torch.clamp(cwsi_wind, 0.0, 1.0)


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
    physics: float = 0.5     # consistencia física ΔT ↔ CWSI (NWSB empírico)
    monotone: float = 0.1    # ordenamiento monotónico por régimen hídrico
    ra_wind: float = 0.0     # [C6] consistencia ra(wind) — 0.0 por defecto,
                              # activar en finetune con datos de viento (~0.2)


class PINNLoss(nn.Module):
    """
    Loss compuesta para el PINN de HydroVision AG.

        L_total = w_mse     · MSE(CWSI_pred, CWSI_real)
                + w_phys    · MSE(CWSI_pred, CWSI_physics(ΔT_pred, VPD))
                + w_mono    · penalización_monotónica
                + w_ra_wind · MSE(CWSI_pred, CWSI_wind(ΔT_pred, VPD, wind, Rn, Ta))  [C6]

    Los parámetros físicos (NWSB_SLOPE, DT_UPPER) se cargan automáticamente
    según el cultivar desde config/cultivares.json (FAO-56).

    El término [C6] ra_wind enseña al modelo que la resistencia aerodinámica
    disminuye con el viento (ra = 208/u), comprimiendo los baselines ΔT_LL
    y ΔT_UL. Activar solo en finetune cuando wind_ms y rad_wm2 están disponibles.

    Uso típico:
        criterion = PINNLoss(weights=PINNLossWeights(physics=0.5, ra_wind=0.2),
                             cultivar="malbec")
        loss, components = criterion(cwsi_pred, delta_t_pred, cwsi_real, vpd,
                                     wind_ms=wind, rad_wm2=rad, t_air=ta)
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
        wind_ms: Optional[torch.Tensor] = None,   # (B, 1) — viento [m/s] [C6]
        rad_wm2: Optional[torch.Tensor] = None,   # (B, 1) — radiación [W/m²] [C6]
        t_air: Optional[torch.Tensor] = None,     # (B, 1) — temp. aire [°C] [C6]
    ):
        """
        Calcula el loss PINN completo.

        Args:
            wind_ms, rad_wm2, t_air: [C6] Si se proveen los tres, se activa
                el término de consistencia con ra(wind). Típicamente disponibles
                solo en finetune con datos reales de campo.

        Returns:
            loss_total: escalar — loss para backprop
            components: dict con cada término (para logging W&B)
        """
        # --- Término 1: MSE supervisado ---
        loss_mse = self.mse(cwsi_pred, cwsi_real)

        # --- Término 2: Consistencia física (NWSB empírico) ---
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

        # --- Término 4: [C6] Consistencia ra(wind) — baselines dinámicos ---
        loss_ra_wind = torch.tensor(0.0, device=cwsi_pred.device)
        if (self.w.ra_wind > 0.0
                and wind_ms is not None
                and rad_wm2 is not None
                and t_air is not None):
            cwsi_wind = physics_cwsi_wind(
                delta_t_pred, vpd, wind_ms, rad_wm2, t_air
            )
            loss_ra_wind = self.mse(cwsi_pred, cwsi_wind)

        # --- Loss total ---
        loss_total = (
            self.w.mse * loss_mse
            + self.w.physics * loss_physics
            + self.w.monotone * loss_mono
            + self.w.ra_wind * loss_ra_wind
        )

        components = {
            "loss_total": loss_total.item(),
            "loss_mse": loss_mse.item(),
            "loss_physics": loss_physics.item(),
            "loss_monotone": loss_mono.item(),
            "loss_ra_wind": loss_ra_wind.item(),
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

    # --- Demo sin ra_wind (backward compatible) ---
    criterion = PINNLoss(PINNLossWeights(mse=1.0, physics=0.5, monotone=0.1))
    loss, comps = criterion(cwsi_pred, delta_t_pred, cwsi_real, vpd, etc)

    print("PINNLoss demo (sin ra_wind):")
    for k, v in comps.items():
        print(f"  {k:20s} = {v:.6f}")

    # --- Demo con ra_wind [C6] ---
    wind = torch.rand(B, 1) * 8.0 + 0.5    # 0.5-8.5 m/s
    rad  = torch.rand(B, 1) * 800 + 100     # 100-900 W/m²
    ta   = torch.rand(B, 1) * 15 + 20       # 20-35 °C

    criterion_c6 = PINNLoss(
        PINNLossWeights(mse=1.0, physics=0.5, monotone=0.1, ra_wind=0.2)
    )
    loss_c6, comps_c6 = criterion_c6(
        cwsi_pred, delta_t_pred, cwsi_real, vpd, etc,
        wind_ms=wind, rad_wm2=rad, t_air=ta,
    )

    print("\nPINNLoss demo (con ra_wind [C6]):")
    for k, v in comps_c6.items():
        print(f"  {k:20s} = {v:.6f}")

    # --- Verificación física empírica ---
    print(f"\nFísica Malbec: ΔT_LL = {NWSB_A} + {NWSB_SLOPE}×VPD  |  ΔT_UL = {DT_UPPER}°C")
    vpd_demo = torch.tensor([[2.0]])
    dt_demo = torch.tensor([[1.5]])
    cw = physics_cwsi(dt_demo, vpd_demo)
    dt_ll_demo = NWSB_A + NWSB_SLOPE * 2.0
    print(f"  VPD=2.0 kPa → ΔT_LL = {dt_ll_demo:.2f}°C")
    print(f"  VPD=2.0 kPa, ΔT_pred=1.5°C → CWSI_physics = {cw.item():.3f}")
    # Verificar: CWSI = (1.5 - (-2.1)) / (3.5 - (-2.1)) = 3.6 / 5.6 ≈ 0.643
    print(f"  Verificación manual: (1.5 - ({dt_ll_demo:.2f})) / ({DT_UPPER} - ({dt_ll_demo:.2f})) = {(1.5 - dt_ll_demo) / (DT_UPPER - dt_ll_demo):.3f}")

    # --- Verificación ra(wind) [C6] ---
    print(f"\n[C6] ra(wind) — efecto del viento en baselines:")
    for u in [1.0, 3.0, 6.0, 10.0]:
        w = torch.tensor([[u]])
        r = torch.tensor([[700.0]])
        t = torch.tensor([[30.0]])
        v = torch.tensor([[2.0]])
        ra_val = _aerodynamic_resistance(w).item()
        cw_wind = physics_cwsi_wind(dt_demo, v, w, r, t).item()
        print(f"  u={u:4.1f} m/s → ra={ra_val:5.1f} s/m → CWSI_wind={cw_wind:.3f}")
