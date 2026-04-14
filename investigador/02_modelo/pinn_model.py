"""
pinn_model.py — Arquitectura PINN para estimación de CWSI
HydroVision AG | ML Engineer / 02_modelo

Physics-Informed Neural Network basado en MobileNetV3-Tiny INT8.
Entrada: imagen térmica (1, 120, 160) float32 normalizada [0,1]
Salida:  CWSI estimado [0,1] + ΔT_pred (temperatura diferencial)

La física se incorpora en la función de pérdida (ver pinn_loss.py):
  CWSI_real = (ΔT_pred − ΔT_LL) / (ΔT_UL − ΔT_LL)
  donde ΔT_LL y ΔT_UL son los baselines CWSI (Jackson 1981)

Referencia:
  Howard et al. (2019). Searching for MobileNetV3. ICCV.
  [backbone eficiente para edge, ~1.5M parámetros]
"""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Bloque de atención espacial — focaliza en píxeles de canopia
# ---------------------------------------------------------------------------
class SpatialAttention(nn.Module):
    """
    Módulo de atención espacial ligero.
    Genera un mapa de pesos (H, W) para focalizar en la región de canopia
    y suprimir el fondo de suelo caliente que sesga el CWSI.
    """

    def __init__(self, kernel_size: int = 7):
        super().__init__()
        pad = kernel_size // 2
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=pad, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_pool = x.mean(dim=1, keepdim=True)
        max_pool = x.max(dim=1, keepdim=True).values
        attn = self.conv(torch.cat([avg_pool, max_pool], dim=1))
        return x * self.sigmoid(attn)


# ---------------------------------------------------------------------------
# Bloque residual ligero compatible con INT8
# ---------------------------------------------------------------------------
class LightResBlock(nn.Module):
    """
    Bloque residual depthwise-separable para inferencia eficiente en ESP32-S3.
    Evita operaciones no soportadas por TFLite Micro INT8.
    """

    def __init__(self, channels: int):
        super().__init__()
        self.dw = nn.Conv2d(channels, channels, 3, padding=1, groups=channels, bias=False)
        self.pw = nn.Conv2d(channels, channels, 1, bias=False)
        self.bn = nn.BatchNorm2d(channels)
        self.act = nn.ReLU6()   # ReLU6 mejor que GELU para INT8

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.pw(self.dw(x))) + x)


# ---------------------------------------------------------------------------
# PINN principal
# ---------------------------------------------------------------------------
class HydroVisionPINN(nn.Module):
    """
    Physics-Informed Neural Network para estimación de CWSI.

    Arquitectura:
        Encoder  : MobileNetV3-Tiny (backbone pre-entrenado ImageNet)
                   Adaptado para entrada 1 canal (térmico) vs 3 (RGB)
        Neck     : SpatialAttention + pooling adaptativo
        Head CWSI: MLP → sigmoid → CWSI ∈ [0,1]
        Head ΔT  : MLP → temperatura diferencial Tc−Ta [°C]
                   Usado por la física del PINN en el loss

    Parámetros: ~1.05M (objetivo: <2M para INT8 en ESP32-S3)
    """

    def __init__(
        self,
        pretrained: bool = True,
        dropout: float = 0.2,
    ):
        super().__init__()

        # --- Encoder: MobileNetV3-Tiny ---
        try:
            import timm
            backbone = timm.create_model(
                "mobilenetv3_small_100",   # 100% ancho vs 050: ~2x capacidad, misma familia edge
                pretrained=pretrained,
                features_only=True,
            )
            # Adaptar primer conv de 3→1 canal (imagen térmica monocanal)
            old_conv = backbone.conv_stem
            new_conv = nn.Conv2d(
                1, old_conv.out_channels,
                kernel_size=old_conv.kernel_size,
                stride=old_conv.stride,
                padding=old_conv.padding,
                bias=False,
            )
            # Inicializar con promedio de los 3 canales RGB
            with torch.no_grad():
                new_conv.weight.copy_(old_conv.weight.mean(dim=1, keepdim=True))
            backbone.conv_stem = new_conv
            self.encoder = backbone
            # Detectar canales del último stage dinámicamente (evita hardcodear por variante)
            enc_channels = backbone.feature_info.channels()[-1]

        except ImportError:
            # Fallback sin timm: encoder convolucional propio
            self.encoder = self._build_fallback_encoder()
            enc_channels = 128

        # --- Neck ---
        self.neck = nn.Sequential(
            nn.Conv2d(enc_channels, 256, 1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU6(),
            LightResBlock(256),
            LightResBlock(256),
            SpatialAttention(kernel_size=5),
            nn.AdaptiveAvgPool2d(1),   # → (B, 256, 1, 1)
        )

        # --- Head CWSI ---
        self.head_cwsi = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU6(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU6(),
            nn.Dropout(dropout / 2),
            nn.Linear(64, 1),
            nn.Sigmoid(),   # CWSI ∈ [0, 1]
        )

        # --- Head ΔT (para término físico del loss) ---
        self.head_delta_t = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 64),
            nn.ReLU6(),
            nn.Linear(64, 1),
            # Sin activación: ΔT puede ser negativo (planta más fría que el aire)
        )

        self._init_heads()

    def _build_fallback_encoder(self) -> nn.Module:
        """Encoder convolucional simple cuando timm no está disponible."""
        return nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(16), nn.ReLU6(),
            nn.Conv2d(16, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32), nn.ReLU6(),
            LightResBlock(32),
            nn.Conv2d(32, 64, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64), nn.ReLU6(),
            LightResBlock(64),
            nn.Conv2d(64, 128, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128), nn.ReLU6(),
        )

    def _init_heads(self):
        """Inicialización conservadora de las capas lineales."""
        for m in [self.head_cwsi, self.head_delta_t]:
            for layer in m:
                if isinstance(layer, nn.Linear):
                    nn.init.kaiming_normal_(layer.weight, mode="fan_out")
                    if layer.bias is not None:
                        nn.init.zeros_(layer.bias)

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (B, 1, 120, 160) float32 — imagen térmica normalizada [0,1]

        Returns:
            cwsi_pred:    (B, 1) — CWSI estimado ∈ [0, 1]
            delta_t_pred: (B, 1) — ΔT = Tc − Ta estimado [°C]
        """
        # Encoder: extraer features
        feat = self.encoder(x)
        if isinstance(feat, (list, tuple)):
            feat = feat[-1]   # timm features_only=True devuelve lista por escala

        # Neck
        neck_out = self.neck(feat)

        # Heads
        cwsi_pred = self.head_cwsi(neck_out)
        delta_t_pred = self.head_delta_t(neck_out)

        return cwsi_pred, delta_t_pred

    def predict_cwsi(self, x: torch.Tensor) -> torch.Tensor:
        """Inferencia simplificada — solo retorna CWSI."""
        cwsi, _ = self.forward(x)
        return cwsi

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ---------------------------------------------------------------------------
# Versión edge para ESP32-S3 (post-cuantización INT8)
# ---------------------------------------------------------------------------
class HydroVisionPINN_Edge(nn.Module):
    """
    Versión ultraligera para deployment en ESP32-S3.
    Sin timm, sin SpatialAttention, < 500K parámetros.
    Latencia objetivo: < 200ms en ESP32-S3.
    """

    def __init__(self, dropout: float = 0.1):
        super().__init__()
        self.features = nn.Sequential(
            # Bloque 1
            nn.Conv2d(1, 8, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(8), nn.ReLU6(),
            # Bloque 2 depthwise
            nn.Conv2d(8, 8, 3, stride=2, padding=1, groups=8, bias=False),
            nn.Conv2d(8, 16, 1, bias=False),
            nn.BatchNorm2d(16), nn.ReLU6(),
            # Bloque 3 depthwise
            nn.Conv2d(16, 16, 3, stride=2, padding=1, groups=16, bias=False),
            nn.Conv2d(16, 32, 1, bias=False),
            nn.BatchNorm2d(32), nn.ReLU6(),
            # Bloque 4
            nn.Conv2d(32, 32, 3, stride=2, padding=1, groups=32, bias=False),
            nn.Conv2d(32, 64, 1, bias=False),
            nn.BatchNorm2d(64), nn.ReLU6(),
            # Pool
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(64, 16),
            nn.ReLU6(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("HydroVision AG — PINN Model")
    print("=" * 50)

    # Modelo completo
    try:
        model = HydroVisionPINN(pretrained=False)
        x = torch.randn(4, 1, 120, 160)
        cwsi, dt = model(x)
        print(f"PINN completo:")
        print(f"  Parámetros : {model.count_parameters():,}")
        print(f"  Input      : {tuple(x.shape)}")
        print(f"  CWSI output: {tuple(cwsi.shape)}  rango [{cwsi.min():.3f}, {cwsi.max():.3f}]")
        print(f"  ΔT output  : {tuple(dt.shape)}")
    except Exception as e:
        print(f"  (timm no disponible, usando fallback): {e}")
        model = HydroVisionPINN(pretrained=False)

    # Modelo edge
    edge = HydroVisionPINN_Edge()
    x_e = torch.randn(1, 1, 120, 160)
    out_e = edge(x_e)
    print(f"\nPINN Edge (ESP32-S3):")
    print(f"  Parámetros : {edge.count_parameters():,}")
    print(f"  Output     : {tuple(out_e.shape)}")
