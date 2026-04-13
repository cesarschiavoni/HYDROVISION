"""
unet_segmentation.py — Segmentación semántica de canopia con U-Net++ ResNet34
HydroVision AG | ML Engineer / 02_modelo

Separa píxeles de hoja (canopia) de fondo (suelo, madera, sky) en la imagen
térmica para calcular el CWSI solo sobre temperatura foliar real.

Sin segmentación, el suelo caliente (Ta+8°C) contamina la media de temperatura
y eleva artificialmente el CWSI estimado.

Métricas objetivo:
    F1 (IoU) canopia > 0.95
    RMSE temperatura foliar < 0.15°C

Arquitectura: U-Net++ con backbone ResNet34 (segmentation-models-pytorch)
Entrada: (B, 1, 120, 160) float32 normalizada
Salida:  (B, 1, 120, 160) float32 — máscara probabilística de canopia [0,1]
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Loss de segmentación: Dice + BCE
# ---------------------------------------------------------------------------
class DiceBCELoss(nn.Module):
    """
    Combinación de Dice Loss + Binary Cross-Entropy.
    Robusto ante desbalance de clases (canopia vs fondo).

    L = BCE(pred, target) + (1 − Dice(pred, target))
    """

    def __init__(self, smooth: float = 1.0, bce_weight: float = 0.5):
        super().__init__()
        self.smooth = smooth
        self.bce_weight = bce_weight
        self.bce = nn.BCEWithLogitsLoss()

    def forward(
        self, logits: torch.Tensor, targets: torch.Tensor
    ) -> Tuple[torch.Tensor, dict]:
        # BCE sobre logits
        loss_bce = self.bce(logits, targets)

        # Dice sobre probabilidades
        probs = torch.sigmoid(logits)
        intersection = (probs * targets).sum(dim=(2, 3))
        dice = (2.0 * intersection + self.smooth) / (
            probs.sum(dim=(2, 3)) + targets.sum(dim=(2, 3)) + self.smooth
        )
        loss_dice = 1.0 - dice.mean()

        loss = self.bce_weight * loss_bce + (1.0 - self.bce_weight) * loss_dice

        return loss, {
            "loss_seg": loss.item(),
            "loss_bce": loss_bce.item(),
            "loss_dice": loss_dice.item(),
            "dice_score": dice.mean().item(),
        }


# ---------------------------------------------------------------------------
# Modelo de segmentación
# ---------------------------------------------------------------------------
class CanopySegmenter(nn.Module):
    """
    Segmentador semántico de canopia usando U-Net++ con backbone ResNet34.

    Si segmentation-models-pytorch no está disponible, usa una U-Net propia
    más simple pero igualmente funcional para el tamaño de imagen 120×160.
    """

    def __init__(self, pretrained: bool = True):
        super().__init__()
        try:
            import segmentation_models_pytorch as smp
            self.model = smp.UnetPlusPlus(
                encoder_name="resnet34",
                encoder_weights="imagenet" if pretrained else None,
                in_channels=1,          # imagen térmica monocanal
                classes=1,              # máscara binaria: canopia / fondo
                activation=None,        # logits — aplicamos sigmoid en postproceso
            )
            self._using_smp = True
        except ImportError:
            self.model = self._build_unet_simple()
            self._using_smp = False

    def _build_unet_simple(self) -> nn.Module:
        """U-Net simple como fallback."""
        return _SimpleUNet(in_channels=1, out_channels=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, 1, 120, 160) — imagen térmica normalizada [0,1]

        Returns:
            logits: (B, 1, 120, 160) — mapa de probabilidad (antes de sigmoid)
        """
        return self.model(x)

    @torch.no_grad()
    def predict_mask(
        self, x: torch.Tensor, threshold: float = 0.5
    ) -> torch.Tensor:
        """Retorna máscara binaria (0=fondo, 1=canopia)."""
        self.eval()
        logits = self.forward(x)
        return (torch.sigmoid(logits) > threshold).float()

    @torch.no_grad()
    def apply_to_cwsi(
        self,
        thermal_image: torch.Tensor,
        tc_wet: float,
        tc_dry: float,
        threshold: float = 0.5,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Aplica la máscara de canopia al cálculo de CWSI.

        Args:
            thermal_image: (B, 1, 120, 160) normalizada [0,1]
            tc_wet: temperatura Wet Ref [°C]
            tc_dry: temperatura Dry Ref [°C]

        Returns:
            cwsi_masked: (B,) — CWSI calculado solo sobre píxeles de canopia
            mask:        (B, 1, 120, 160) — máscara binaria usada
        """
        mask = self.predict_mask(thermal_image, threshold)

        # Desnormalizar: [0,1] → [5°C, 55°C]
        tc_image = thermal_image * 50.0 + 5.0   # (B, 1, 120, 160)

        # Temperatura media solo en píxeles de canopia
        canopy_sum = (tc_image * mask).sum(dim=(2, 3))
        canopy_count = mask.sum(dim=(2, 3)).clamp(min=1.0)
        tc_mean = (canopy_sum / canopy_count).squeeze(1)   # (B,)

        # CWSI con temperatura de canopia filtrada
        denom = tc_dry - tc_wet
        if abs(denom) < 0.1:
            return torch.zeros(thermal_image.shape[0]), mask
        cwsi = torch.clamp((tc_mean - tc_wet) / denom, 0.0, 1.0)

        return cwsi, mask

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ---------------------------------------------------------------------------
# U-Net simple (fallback sin segmentation-models-pytorch)
# ---------------------------------------------------------------------------
class _DoubleConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
        )

    def forward(self, x): return self.net(x)


class _SimpleUNet(nn.Module):
    def __init__(self, in_channels: int = 1, out_channels: int = 1):
        super().__init__()
        f = [16, 32, 64, 128]
        self.enc1 = _DoubleConv(in_channels, f[0])
        self.enc2 = _DoubleConv(f[0], f[1])
        self.enc3 = _DoubleConv(f[1], f[2])
        self.enc4 = _DoubleConv(f[2], f[3])
        self.pool = nn.MaxPool2d(2)

        self.up3 = nn.ConvTranspose2d(f[3], f[2], 2, stride=2)
        self.dec3 = _DoubleConv(f[3], f[2])
        self.up2 = nn.ConvTranspose2d(f[2], f[1], 2, stride=2)
        self.dec2 = _DoubleConv(f[2], f[1])
        self.up1 = nn.ConvTranspose2d(f[1], f[0], 2, stride=2)
        self.dec1 = _DoubleConv(f[1], f[0])

        self.out = nn.Conv2d(f[0], out_channels, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        d3 = self.dec3(torch.cat([self.up3(e4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

        return self.out(d1)


# ---------------------------------------------------------------------------
# Generador de máscaras sintéticas para entrenamiento inicial
# ---------------------------------------------------------------------------
def generate_synthetic_masks(
    n: int = 1000,
    canopy_fraction: float = 0.65,
    seed: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Genera pares (imagen_térmica, máscara_canopia) sintéticos para
    pre-entrenar el segmentador antes de tener datos reales anotados.

    Usa el mismo generador de ruido que ThermalSimulator._make_canopy_mask().
    """
    rng = np.random.default_rng(seed)
    H, W = 120, 160
    images = np.empty((n, 1, H, W), dtype=np.float32)
    masks = np.empty((n, 1, H, W), dtype=np.float32)

    for i in range(n):
        # Máscara de canopia con la misma lógica que el simulador
        x = np.linspace(0, 4 * np.pi, W)
        y = np.linspace(0, 4 * np.pi, H)
        xx, yy = np.meshgrid(x, y)
        noise = sum(
            np.sin(xx * f + rng.uniform(0, 2 * np.pi))
            * np.cos(yy * f + rng.uniform(0, 2 * np.pi))
            for f in [1, 2, 3, 5]
        )
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        mask = (noise > (1.0 - canopy_fraction)).astype(np.float32)

        # Imagen térmica sintética correspondiente
        ta = rng.uniform(22, 38)
        tc = ta + rng.uniform(-1, 6)       # canopia
        ts = ta + rng.uniform(3, 12)       # suelo
        image = np.where(mask, tc, ts)
        image += rng.normal(0, 0.05, image.shape)  # ruido NETD
        image = np.clip((image - 5.0) / 50.0, 0.0, 1.0)  # normalizar

        images[i, 0] = image.astype(np.float32)
        masks[i, 0] = mask

    return images, masks


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"CanopySegmenter — HydroVision AG  [device={DEVICE}]")
    seg = CanopySegmenter(pretrained=False).to(DEVICE)
    print(f"  Parámetros: {seg.count_parameters():,}")
    print(f"  Backend   : {'smp U-Net++' if seg._using_smp else 'SimpleUNet (fallback)'}")

    x = torch.randn(2, 1, 120, 160, device=DEVICE)
    logits = seg(x)
    print(f"  Input : {tuple(x.shape)}")
    print(f"  Output: {tuple(logits.shape)}")

    mask = seg.predict_mask(x)
    frac = mask.mean().item()
    print(f"  Fracción canopia predicha (sin entrenar): {frac:.3f}")

    # Test loss
    criterion = DiceBCELoss()
    targets = torch.randint(0, 2, logits.shape).float()
    loss, comps = criterion(logits, targets)
    print(f"\nDiceBCELoss demo:")
    for k, v in comps.items():
        print(f"  {k:15s} = {v:.4f}")

    # Máscaras sintéticas
    print("\nGenerando máscaras sintéticas para pre-entrenamiento...")
    imgs, msks = generate_synthetic_masks(n=100)
    print(f"  Imágenes: {imgs.shape}  Máscaras: {msks.shape}")
    print(f"  Fracción canopia promedio: {msks.mean():.3f}")
