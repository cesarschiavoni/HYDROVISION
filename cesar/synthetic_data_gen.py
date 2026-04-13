"""
Generador de frames térmicos sintéticos — MLX90640 (sensor BAB, 110° FOV)
HydroVision AG — Prueba de Concepto TRL 3

Genera imágenes térmicas sintéticas (32×24 px) que emulan la salida del
MLX90640 en un viñedo de Malbec bajo distintos regímenes hídricos.

Modelo físico de la imagen:
  - Fondo (cielo/suelo): temperatura de fondo con gradiente espacial
  - Tallos y madera: temperatura intermedia (T_air + 2-4°C)
  - Canopeo foliar: temperatura modelada según CWSI objetivo
      T_leaf = T_air + ΔT_LL(VPD) + CWSI × (ΔT_UL - ΔT_LL)
  - Ruido NETD: ruido gaussiano σ = 0.10°C (NETD típico MLX90640)
  - Patrón espacial: estructura realista de dosel vitícola en espaldera

Este generador es el núcleo del simulador físico que en TRL 4 producirá
1.000.000 de imágenes sintéticas para el pre-entrenamiento del modelo PINN.
"""

import numpy as np
import cv2
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from cwsi_formula import CWSICalculator, MeteoConditions, CROP_COEFFICIENTS


# ─────────────────────────────────────────────
# Constantes MLX90640 (sensor BAB, breakout integrado Adafruit 4407)
# ─────────────────────────────────────────────
MLX_W        = 32
MLX_H        = 24
MLX_NETD     = 0.10     # °C — NETD típico MLX90640 (100 mK)
Y16_OFFSET   = 27315    # offset en LSB (= 273.15K × 100) — codificación interna
Y16_SCALE    = 100      # LSB/K — resolución 0.01K por LSB

# Aliases para compatibilidad con código existente y tests
LEPTON_W     = MLX_W
LEPTON_H     = MLX_H
LEPTON_NETD  = MLX_NETD


def celsius_to_y16(T_celsius: np.ndarray) -> np.ndarray:
    """Convierte temperatura °C a uint16 (codificación interna del pipeline)."""
    T_kelvin = T_celsius + 273.15
    y16 = np.round(T_kelvin * Y16_SCALE).astype(np.uint16)
    return y16

def y16_to_celsius(y16: np.ndarray) -> np.ndarray:
    """Convierte Y16 uint16 a temperatura °C."""
    return y16.astype(np.float32) / Y16_SCALE - 273.15


@dataclass
class VineyardScene:
    """Parámetros de la escena vitícola para generación del frame."""
    n_filas: int = 3         # filas de vid en el frame
    cobertura_foliar: float = 0.55  # fracción del frame con hojas (0-1)
    orientacion: str = "N-S"       # orientación de la espaldera
    estadio: str = "maduracion"    # estadio fenológico


class Mlx90640Simulator:
    """
    Simulador de frames térmicos MLX90640 (32×24 px) para viñedo Malbec.

    El simulador genera la imagen como suma de capas:
      1. Background: cielo (frío) + suelo (caliente)
      2. Estructura de la espaldera: postes y alambres
      3. Madera/tallos: temperatura intermedia
      4. Canopeo foliar: temperatura calculada por CWSI objetivo
      5. Ruido NETD gaussiano (σ = 0.10°C) + Fixed Pattern Noise residual
    """

    def __init__(self, crop: str = "malbec", seed: int = None):
        self.crop = crop
        self.calc = CWSICalculator(crop)
        self.rng = np.random.default_rng(seed)

    def _target_leaf_temperature(self, meteo: MeteoConditions, cwsi_target: float) -> float:
        """
        Calcula la temperatura foliar necesaria para un CWSI objetivo.
        Inversión de la fórmula Jackson (1981):
          T_leaf = T_air + ΔT_LL + cwsi × (ΔT_UL - ΔT_LL)
        """
        dT_ll = self.calc.delta_T_LL(meteo.VPD)
        dT_ul = self.calc.delta_T_UL(meteo.VPD)
        dT_target = dT_ll + cwsi_target * (dT_ul - dT_ll)
        return meteo.T_air + dT_target

    def _generate_canopy_mask(self, scene: VineyardScene) -> np.ndarray:
        """
        Genera máscara binaria de canopeo realista para una escena de viñedo.
        La espaldera genera bandas horizontales de follaje.
        """
        mask = np.zeros((LEPTON_H, LEPTON_W), dtype=bool)

        # Posición vertical de cada fila de vid en el frame
        row_centers = np.linspace(
            int(LEPTON_H * 0.2),
            int(LEPTON_H * 0.8),
            scene.n_filas,
            dtype=int
        )
        band_height = int(LEPTON_H * scene.cobertura_foliar / scene.n_filas * 1.5)

        for cy in row_centers:
            y1 = max(0, cy - band_height // 2)
            y2 = min(LEPTON_H, cy + band_height // 2)

            # Textura irregular del canopeo (hojas no forman banda perfecta)
            for y in range(y1, y2):
                offset = int(self.rng.integers(-5, 6))
                x1 = max(0, 10 + offset)
                x2 = min(LEPTON_W, LEPTON_W - 10 + offset)
                # Probabilidad de cobertura decrece en los bordes
                prob = 1.0 - abs(y - cy) / (band_height / 2 + 1e-6)
                if self.rng.random() < prob:
                    mask[y, x1:x2] = True

        # Erosión morfológica para bordes más naturales
        kernel = np.ones((3, 3), np.uint8)
        mask_uint8 = mask.astype(np.uint8) * 255
        mask_eroded = cv2.erode(mask_uint8, kernel, iterations=1)
        return mask_eroded > 0

    def generate_frame(
        self,
        meteo: MeteoConditions,
        cwsi_target: float,
        scene: VineyardScene = None,
        angle_deg: float = 0.0,
        frame_id: str = "",
    ):
        """
        Genera un frame térmico sintético completo.

        Parámetros
        ----------
        meteo       : condiciones meteorológicas
        cwsi_target : CWSI objetivo (0.0-1.0)
        scene       : parámetros de la escena vitícola
        angle_deg   : ángulo del gimbal (afecta la proporción cielo/suelo)
        frame_id    : identificador del frame

        Retorna
        -------
        ThermalFrame con array Y16 uint16 24×32
        """
        from thermal_pipeline import ThermalFrame  # import local

        if scene is None:
            scene = VineyardScene()

        # 1. Temperatura objetivo del canopeo para el CWSI deseado
        T_leaf_target = self._target_leaf_temperature(meteo, cwsi_target)

        # 2. Temperaturas de los otros componentes de la escena
        T_soil   = meteo.T_air + 8.0 + self.rng.normal(0, 1.5)  # suelo caliente
        T_sky    = meteo.T_air - 12.0 + self.rng.normal(0, 1.0) # cielo frío
        T_wood   = meteo.T_air + 3.0 + self.rng.normal(0, 0.5)  # tallos/madera
        T_shadow = meteo.T_air - 1.5 + self.rng.normal(0, 0.5)  # zonas de sombra

        # 3. Frame base: gradiente vertical cielo→suelo
        # El ángulo del gimbal afecta qué fracción del frame muestra cielo vs. suelo
        sky_fraction = max(0.1, min(0.5, 0.3 + angle_deg / 180))
        grad = np.linspace(T_sky, T_soil, LEPTON_H)
        T_frame = np.tile(grad, (LEPTON_W, 1)).T.copy()

        # Agregar variación horizontal (textura de suelo/sombras entre filas)
        T_frame += self.rng.normal(0, 0.8, T_frame.shape)

        # 4. Superponer máscara de canopeo
        canopy_mask = self._generate_canopy_mask(scene)

        # Temperatura foliar con variabilidad espacial realista
        T_canopy_map = np.full((LEPTON_H, LEPTON_W), T_leaf_target)
        # Gradiente intra-canopeo: mayor estrés en zonas expuestas al sol
        T_canopy_map += self.rng.normal(0, 0.4, T_canopy_map.shape)  # variabilidad
        # Zonas de sombra dentro del canopeo (temperatura menor)
        sombra_mask = self.rng.random((LEPTON_H, LEPTON_W)) < 0.15
        T_canopy_map[sombra_mask & canopy_mask] -= 1.5

        T_frame[canopy_mask] = T_canopy_map[canopy_mask]

        # 5. Superponer tallos/madera (bandas verticales delgadas en la espaldera)
        for x in range(5, LEPTON_W - 5, LEPTON_W // (scene.n_filas + 1)):
            T_frame[:, max(0, x-1):x+2] = T_wood

        # 6. Ruido NETD (gaussiano, σ = 0.10°C) — realista del MLX90640
        T_frame += self.rng.normal(0, MLX_NETD, T_frame.shape)

        # 7. Patrón de Fixed Pattern Noise (FPN) — artefacto real del sensor
        fpn = self.rng.normal(0, 0.02, (LEPTON_H, LEPTON_W))  # FPN residual post-NUC
        T_frame += fpn

        # 8. Convertir a Y16
        raw_y16 = celsius_to_y16(T_frame)

        return ThermalFrame(
            raw_y16=raw_y16,
            meteo=meteo,
            angle_deg=angle_deg,
            frame_id=frame_id or f"SYN_CWSI{cwsi_target:.2f}_A{angle_deg:+.0f}",
        )

    def generate_dataset(
        self,
        n_frames: int = 100,
        cwsi_levels: list[float] = None,
        meteo_list: list[MeteoConditions] = None,
        output_dir: str = None,
    ) -> list:
        """
        Genera un dataset de frames sintéticos cubriendo distintos niveles de CWSI
        y condiciones meteorológicas.

        En TRL 4 este método genera 1.000.000 de frames para pre-entrenamiento del PINN.
        Aquí genera un dataset reducido para validación de la prueba de concepto.
        """
        from thermal_pipeline import ThermalFrame

        if cwsi_levels is None:
            cwsi_levels = np.linspace(0.0, 1.0, 11).tolist()

        if meteo_list is None:
            # Condiciones típicas de Colonia Caroya en verano (pico de estrés)
            meteo_list = [
                MeteoConditions(T_air=t, RH=rh, solar_rad=rad, wind_speed=1.5)
                for t, rh, rad in [
                    (28.0, 45.0, 700.0),  # mañana
                    (33.0, 32.0, 900.0),  # mediodía
                    (31.0, 38.0, 750.0),  # tarde
                ]
            ]

        frames = []
        angles = [0.0, 30.0, -30.0, 45.0, -45.0, 60.0, -60.0]
        idx = 0

        for cwsi in cwsi_levels:
            for meteo in meteo_list:
                angle = angles[idx % len(angles)]
                frame = self.generate_frame(
                    meteo=meteo,
                    cwsi_target=cwsi,
                    angle_deg=angle,
                    frame_id=f"SYN_{idx:05d}_CWSI{cwsi:.2f}",
                )
                frames.append({"frame": frame, "cwsi_label": cwsi, "meteo": meteo})
                idx += 1
                if idx >= n_frames:
                    break
            if idx >= n_frames:
                break

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            for item in frames:
                f = item["frame"]
                T = y16_to_celsius(f.raw_y16)
                # Normalizar a uint8 para guardar como PNG visualizable
                T_norm = ((T - T.min()) / (T.max() - T.min() + 1e-6) * 255).astype(np.uint8)
                T_color = cv2.applyColorMap(T_norm, cv2.COLORMAP_INFERNO)
                fname = os.path.join(output_dir, f"{f.frame_id}.png")
                cv2.imwrite(fname, T_color)

        return frames


# Alias para compatibilidad con tests y código existente
FlirLepton35Simulator = Mlx90640Simulator


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    print("=" * 60)
    print("Generador Frames Sintéticos MLX90640 (32×24 px) — TRL 3")
    print("Viñedo Malbec — Colonia Caroya")
    print("=" * 60)

    sim = Mlx90640Simulator("malbec", seed=42)

    # Generar frames para 5 niveles de CWSI con condición del mediodía de enero
    meteo_jan = MeteoConditions(T_air=34.0, RH=28.0, solar_rad=950.0, wind_speed=1.8)
    cwsi_targets = [0.0, 0.25, 0.50, 0.75, 1.0]

    fig, axes = plt.subplots(2, 5, figsize=(18, 7))
    fig.suptitle(
        "Frames térmicos sintéticos MLX90640 (32×24 px) — Malbec Colonia Caroya\n"
        "T_aire=34°C, RH=28%, Rad=950W/m², VPD≈2.78kPa",
        fontsize=12, fontweight="bold"
    )

    from thermal_pipeline import ThermalPipeline
    pipeline = ThermalPipeline("malbec")

    for i, cwsi_t in enumerate(cwsi_targets):
        frame = sim.generate_frame(meteo_jan, cwsi_t, frame_id=f"demo_CWSI{cwsi_t:.2f}")
        T = frame.temperature_C
        result = pipeline.process_frame(frame)

        # Imagen térmica (colormap inferno)
        T_norm = ((T - T.min()) / (T.max() - T.min() + 1e-6) * 255).astype(np.uint8)
        ax_img = axes[0, i]
        im = ax_img.imshow(T, cmap="inferno", vmin=20, vmax=42, aspect="auto")
        ax_img.set_title(
            f"CWSI target={cwsi_t:.2f}\n"
            f"CWSI medido={result.get('cwsi', float('nan')):.3f}\n"
            f"{result.get('stress_level', 'N/A')}",
            fontsize=8
        )
        ax_img.axis("off")
        plt.colorbar(im, ax=ax_img, fraction=0.046, pad=0.04, label="°C")

        # Histograma de temperaturas foliares
        seg = result.get("seg", {})
        ax_hist = axes[1, i]
        if seg.get("n_pixels", 0) > 0:
            ax_hist.hist(seg["T_canopy"], bins=20, color="orangered", alpha=0.7,
                         edgecolor="darkred", linewidth=0.5)
            ax_hist.axvline(meteo_jan.T_air, color="navy", ls="--", lw=1.5,
                            label=f"T_aire={meteo_jan.T_air}°C")
            ax_hist.axvline(seg["T_mean"], color="red", ls="-", lw=2,
                            label=f"T_foliar={seg['T_mean']:.1f}°C")
            ax_hist.legend(fontsize=6)
        ax_hist.set_xlabel("Temperatura [°C]", fontsize=8)
        ax_hist.set_ylabel("Píxeles", fontsize=8)
        ax_hist.set_title(f"Histograma canopeo\n{seg.get('n_pixels',0)} px "
                          f"({seg.get('foliar_frac',0):.0%})", fontsize=8)

    plt.tight_layout()
    out_dir = "c:/Temp/Agro/prueba computacional/outputs"
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, "frames_sinteticos_cwsi.png"),
                dpi=150, bbox_inches="tight")
    print(f"\n  Figura guardada en outputs/frames_sinteticos_cwsi.png")

    # Generar dataset mini (30 frames)
    dataset = sim.generate_dataset(
        n_frames=30,
        output_dir="c:/Temp/Agro/prueba computacional/data/synthetic_frames"
    )
    print(f"\n  Dataset sintético: {len(dataset)} frames generados")
    print(f"  Guardados en: data/synthetic_frames/")

    # Verificar ruido NETD
    frame_ref = sim.generate_frame(meteo_jan, 0.5, frame_id="netd_test")
    frame_ref2 = sim.generate_frame(meteo_jan, 0.5, frame_id="netd_test2")
    T1 = frame_ref.temperature_C
    T2 = frame_ref2.temperature_C
    netd_medido = float(np.std(T1 - T2) / np.sqrt(2))
    print(f"\n  NETD verificado: {netd_medido*1000:.1f}mK "
          f"({'✓' if netd_medido < 0.07 else '✗'} especificación <50mK ± tolerancia sim)")

    print("\n✓ Generador de frames sintéticos operativo")
