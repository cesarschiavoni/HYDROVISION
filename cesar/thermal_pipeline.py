"""
Pipeline de procesamiento de imágenes térmicas — HydroVision AG
MLX90640 (32×24 px) → segmentación de canopeo → CWSI por frame

El pipeline implementa la metodología de captura multi-angular:
  - 5–6 posiciones de gimbal × 3 ventanas horarias (9h/12h/16h)
  - Segmentación foliar por percentiles de temperatura (P20-P75)
  - Filtro morfológico de regiones conectadas ≥ 4×4px
  - CWSI final = promedio ponderado por fracción foliar

Calibración perfecta por referencias físicas en bracket (Jones 1999 — Índice Ig):
  Cada bracket monta dos paneles físicos ~20-50 cm debajo de la cámara, orientados
  al cielo. El amplio FOV del MLX90640 (110°×75°) los captura en la periferia
  inferior del frame (filas ~20 de 24) en coordenadas de píxel fijas, dejando el
  centro del frame libre para los ~28 píxeles foliares del canopeo:
  - Referencia húmeda: papel de filtro Whatman N°1 (10×10cm) empapado en agua
    destilada por capilaridad desde reservorio 500mL + mecha de algodón.
    Su temperatura ES el Tc_wet real bajo las condiciones atmosféricas actuales
    (Ta, VPD, radiación, viento) — sin ecuaciones, sin suposiciones.
  - Referencia seca: mismo papel pintado con vaselina + recubrimiento negro mate
    ε=0.98. Su temperatura ES el Tc_dry real.
  El Ig (Jones 1999) se calcula directamente desde los píxeles de los paneles:
    Ig = (Tc_canopy − T_ref_húmeda) / (T_ref_seca − T_ref_húmeda)
  Sin VPD, sin NWSB, sin offsets, sin deriva. Calibración automática en cada
  frame (96 veces/día). Stack de calibración triple:
    Nivel 1 — Ig con referencias físicas (primario, si paneles válidos)
    Nivel 2 — Auto-calibración por lluvia/MDS (episódico, baseline.py)
    Nivel 3 — NWSB Jackson 1981 + offset acumulado (fallback de fábrica)
  Hardware adicional: ~USD 15/nodo (panel + reservorio + micro-bomba GPIO).

Referencia segmentación:
  Araújo-Paredes, C. et al. (2022). Using aerial thermal imagery to evaluate
  water status in Vitis vinifera cv. Loureiro. Sensors, 22(20), 8056.

Referencia Índice Ig / referencias físicas:
  Jones, H.G. (1999). Use of thermography for quantitative studies of spatial
  and temporal variation of stomatal conductance over leaf surfaces.
  Plant, Cell & Environment, 22(9), 1043-1055.
  — Base del Ig: referencias húmeda/seca físicas en campo eliminan necesidad
    de NWSB modelado. Validado en vid por Gutiérrez et al. (2018, PLoS ONE).

Metodología multi-ángulo y canopy_side:
  Pires, A. et al. (2025). Scalable thermal imaging and processing framework
  for water status monitoring in vineyards. Computers and Electronics in
  Agriculture, 239, 110931.
  — Resultado clave: capturas de tarde (16h) producen R²=0.663 vs 0.618 global.
  — Diferentes lados del canopeo (norte/sur) tienen lecturas distintas;
    se registran por separado para modelos lado-específicos.

  Zhou, Z. et al. (2022). Ground-Based Thermal Imaging for Assessing Crop Water
  Status in Grapevines over a Growing Season. Agronomy, 12(2), 322.
  — Cámaras orientadas ortogonalmente al canopeo; correlación CWSI ↔ ψ_leaf.
"""

import numpy as np
import cv2
from dataclasses import dataclass, field
from typing import Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from cwsi_formula import CWSICalculator, MeteoConditions


# ─────────────────────────────────────────────
# Constantes MLX90640 (sensor BAB, breakout integrado Adafruit 4407)
# ─────────────────────────────────────────────
MLX_WIDTH  = 32
MLX_HEIGHT = 24
MLX_NETD   = 0.10   # °C — Noise Equivalent Temperature Difference (típico MLX90640)
MLX_Y16_SCALE = 0.01  # K/LSB — codificación interna del pipeline

# Aliases para compatibilidad con código existente
LEPTON_WIDTH  = MLX_WIDTH
LEPTON_HEIGHT = MLX_HEIGHT
LEPTON_NETD   = MLX_NETD
LEPTON_Y16_SCALE = MLX_Y16_SCALE


# ─────────────────────────────────────────────
# Referencias físicas de calibración en bracket
# ─────────────────────────────────────────────
@dataclass
class ReferencePanelConfig:
    """
    Posición fija de los paneles de referencia húmeda/seca en el frame.

    Como el bracket tiene geometría fija y el gimbal vuelve a 0°/0° para el
    frame de referencia, los paneles siempre caen en las mismas coordenadas
    de píxel. Se definen una vez en la instalación del nodo.

    Coordenadas: (fila_inicio, fila_fin, col_inicio, col_fin) — slice de numpy.
    Valores por defecto: esquina superior izquierda / derecha del frame,
    fuera del área de canopeo.
    """
    # Panel húmedo: papel de filtro Whatman N°1 empapado — T = Tc_wet real
    wet_rows: Tuple[int, int] = (5, 20)
    wet_cols: Tuple[int, int] = (5, 25)

    # Panel seco: mismo papel + vaselina + coating negro mate ε=0.98 — T = Tc_dry real
    dry_rows: Tuple[int, int] = (5, 20)
    dry_cols: Tuple[int, int] = (135, 155)

    # Tolerancias de validación automática
    max_temp_jump_C: float = 1.0   # salto máximo entre frames consecutivos [°C]
    min_delta_C: float = 1.5       # diferencia mínima seco−húmedo para Ig válido [°C]


class ReferenceCalibrator:
    """
    Calibración Ig automática por referencias físicas húmeda/seca en bracket.

    En cada frame del ángulo 0° (posición de referencia del gimbal), lee los
    píxeles de los paneles y calcula directamente Tc_wet y Tc_dry reales.
    No requiere VPD, modelos NWSB, ni visitas humanas.

    Validación automática por frame:
      - Panel húmedo debe ser más frío que el aire (evaporación activa)
      - Panel seco debe ser más caliente que el aire
      - Diferencia seco−húmedo ≥ min_delta_C (paneles distinguibles)
      - Salto temporal ≤ max_temp_jump_C (panel no se secó abruptamente)

    Si los paneles no pasan validación → retorna calibration_valid=False
    y el pipeline cae al Nivel 2 (auto-calibración por lluvia/MDS).
    """

    def __init__(self, config: Optional[ReferencePanelConfig] = None):
        self.config = config or ReferencePanelConfig()
        self._prev_tc_wet_ref: Optional[float] = None
        self._prev_tc_dry_ref: Optional[float] = None
        self.valid_reads: int = 0
        self.invalid_reads: int = 0

    def read_panels(
        self,
        image_C: np.ndarray,
        ta: float,
    ) -> dict:
        """
        Lee los paneles de referencia del frame térmico y valida.

        Args:
            image_C: frame térmico en °C (H×W float32)
            ta: temperatura del aire [°C] para validación física

        Returns:
            dict con:
              tc_wet_ref    : temperatura del panel húmedo [°C]
              tc_dry_ref    : temperatura del panel seco [°C]
              ig_available  : True si los paneles son válidos para calcular Ig
              reason        : descripción si no son válidos
        """
        cfg = self.config
        r0w, r1w = cfg.wet_rows
        c0w, c1w = cfg.wet_cols
        r0d, r1d = cfg.dry_rows
        c0d, c1d = cfg.dry_cols

        tc_wet_ref = float(image_C[r0w:r1w, c0w:c1w].mean())
        tc_dry_ref = float(image_C[r0d:r1d, c0d:c1d].mean())

        reasons = []

        # 1. Panel húmedo debe estar más frío que el aire (evaporación)
        if tc_wet_ref > ta + 0.5:
            reasons.append(
                f"REF_HÚMEDA_SECA: Twet_ref={tc_wet_ref:.1f}°C > Ta+0.5={ta+0.5:.1f}°C "
                f"— panel sin agua, reservorio vacío"
            )

        # 2. Panel seco debe estar más caliente que el aire
        if tc_dry_ref < ta + 1.0:
            reasons.append(
                f"REF_SECA_FRÍA: Tdry_ref={tc_dry_ref:.1f}°C < Ta+1.0={ta+1.0:.1f}°C "
                f"— posible contaminación húmeda del panel seco"
            )

        # 3. Diferencia mínima entre paneles
        delta = tc_dry_ref - tc_wet_ref
        if delta < cfg.min_delta_C:
            reasons.append(
                f"DELTA_INSUFICIENTE: Tdry−Twet={delta:.2f}°C < {cfg.min_delta_C}°C "
                f"— paneles no distinguibles (posible condensación o panel seco húmedo)"
            )

        # 4. Salto temporal (panel secándose abruptamente)
        if self._prev_tc_wet_ref is not None:
            jump = abs(tc_wet_ref - self._prev_tc_wet_ref)
            if jump > cfg.max_temp_jump_C:
                reasons.append(
                    f"SALTO_TEMPORAL: ΔTwet={jump:.2f}°C > {cfg.max_temp_jump_C}°C "
                    f"— panel húmedo se secó o fue perturbado"
                )

        valid = len(reasons) == 0
        if valid:
            self.valid_reads += 1
            self._prev_tc_wet_ref = tc_wet_ref
            self._prev_tc_dry_ref = tc_dry_ref
        else:
            self.invalid_reads += 1

        return {
            "tc_wet_ref": tc_wet_ref,
            "tc_dry_ref": tc_dry_ref,
            "ig_available": valid,
            "reason": "; ".join(reasons) if reasons else "OK",
            "delta_ref": delta,
        }

    def compute_ig(
        self,
        tc_canopy: float,
        panel_result: dict,
    ) -> Optional[float]:
        """
        Calcula el Índice Jones (Ig) usando las referencias físicas.

        Ig = (Tc_canopy − Tc_wet_ref) / (Tc_dry_ref − Tc_wet_ref)
        Clipeado a [0, 1].

        Returns None si las referencias no son válidas.
        """
        if not panel_result["ig_available"]:
            return None
        tc_wet = panel_result["tc_wet_ref"]
        tc_dry = panel_result["tc_dry_ref"]
        denom = tc_dry - tc_wet
        if abs(denom) < 0.2:
            return None
        return float(np.clip((tc_canopy - tc_wet) / denom, 0.0, 1.0))

    @property
    def reliability(self) -> float:
        """Fracción de lecturas válidas desde el inicio de la sesión."""
        total = self.valid_reads + self.invalid_reads
        return self.valid_reads / total if total > 0 else 0.0


@dataclass
class ThermalFrame:
    """
    Frame térmico Y16 del FLIR Lepton 3.5.

    canopy_side: lado del canopeo capturado ("N", "S", "E", "O", "top" o "").
      Pires et al. (2025) y Zhou et al. (2022) demuestran que ambos lados
      del canopeo tienen respuestas térmicas distintas (exposición solar,
      temperatura de borde). Se registra para permitir modelos lado-específicos.
      En Colonia Caroya (hemisferio sur): cara norte recibe más radiación
      → habitualmente más caliente y mejor candidata para CWSI de estrés.
    """
    raw_y16: np.ndarray        # Array uint16 160×120
    meteo: MeteoConditions
    timestamp: str = ""
    angle_deg: float = 0.0     # ángulo del gimbal
    frame_id: str = ""
    canopy_side: str = ""      # "N" | "S" | "E" | "O" | "top" | "" (Pires 2025 / Zhou 2022)

    @property
    def temperature_C(self) -> np.ndarray:
        """Convierte Y16 a temperatura en °C (offset calibrado al aire ambiente)."""
        # Y16: T_K = raw / 100.0 — offset FLIR estándar ~27315 LSB = 273.15K
        T_K = self.raw_y16.astype(np.float32) / 100.0
        return T_K - 273.15

    @property
    def shape(self):
        return self.raw_y16.shape


class CanopySegmenter:
    """
    Segmentador de canopeo por percentiles de temperatura.

    Principio: las hojas en plena transpiración son los píxeles más fríos
    del frame (P20-P75). El suelo, tallos y cielo quedan fuera de ese rango.
    Filtro morfológico elimina artefactos de borde (regiones < 4×4px).

    Basado en:
      Bellvert et al. (2014), Santesteban et al. (2017).
    """

    def __init__(self, p_low: int = 20, p_high: int = 75, min_region_px: int = 16):
        self.p_low = p_low
        self.p_high = p_high
        self.min_region_px = min_region_px  # 4×4 = 16 px²

    def segment(self, frame: ThermalFrame) -> dict:
        """
        Segmenta píxeles foliares en el frame térmico.

        Retorna
        -------
        dict con:
          mask        : array bool 120×160 — True = píxel foliar
          T_canopy    : array float de temperaturas foliares segmentadas
          T_mean      : temperatura media del canopeo [°C]
          T_std       : desviación estándar [°C]
          foliar_frac : fracción foliar del frame (0-1)
          n_pixels    : cantidad de píxeles foliares
        """
        T = frame.temperature_C
        p_lo = float(np.percentile(T, self.p_low))
        p_hi = float(np.percentile(T, self.p_high))

        # Máscara inicial por percentil
        mask_raw = (T >= p_lo) & (T <= p_hi)

        # Filtro morfológico: eliminar regiones < min_region_px
        mask_uint8 = mask_raw.astype(np.uint8) * 255
        kernel = np.ones((4, 4), np.uint8)
        mask_clean = cv2.morphologyEx(mask_uint8, cv2.MORPH_OPEN, kernel)
        mask = mask_clean > 0

        T_canopy = T[mask]
        n_pixels = int(np.sum(mask))

        return {
            "mask": mask,
            "T_canopy": T_canopy,
            "T_mean": float(np.mean(T_canopy)) if n_pixels > 0 else np.nan,
            "T_std":  float(np.std(T_canopy))  if n_pixels > 0 else np.nan,
            "foliar_frac": n_pixels / (LEPTON_WIDTH * LEPTON_HEIGHT),
            "n_pixels": n_pixels,
            "p_low_C": p_lo,
            "p_high_C": p_hi,
        }


class ThermalPipeline:
    """
    Pipeline completo: frame térmico → CWSI/Ig verificado.

    Pasos:
      1. Validar condiciones de captura (radiación, VPD, viento)
      2. Verificar calidad del frame (NETD, saturación, blur)
      3. Leer paneles de referencia húmeda/seca del bracket (Nivel 1)
      4. Segmentar canopeo por percentiles
      5. Calcular Ig (primario, si referencias válidas) y CWSI (secundario)
      6. Flag de alta variabilidad angular si std > 0.12

    Stack de calibración triple por frame:
      Nivel 1 — Ig con referencias físicas (automático, si paneles válidos)
      Nivel 2 — CWSI con baseline auto-calibrado por lluvia/MDS (baseline.py)
      Nivel 3 — CWSI con NWSB Jackson 1981 de fábrica (fallback)

    El índice primario de salida es Ig cuando está disponible.
    CWSI siempre se calcula como verificación cruzada.
    """

    def __init__(
        self,
        crop: str = "malbec",
        ref_config: Optional[ReferencePanelConfig] = None,
    ):
        self.cwsi_calc = CWSICalculator(crop)
        self.segmenter = CanopySegmenter()
        self.crop = crop
        self.calibrator = ReferenceCalibrator(ref_config)

    def validate_frame(self, frame: ThermalFrame) -> dict:
        """Controles de calidad del frame antes de procesar."""
        T = frame.temperature_C
        issues = []

        # 1. Saturación: píxeles en los extremos del rango del sensor
        sat_lo = float(np.mean(T < -10))   # bajo rango
        sat_hi = float(np.mean(T > 80))    # sobre rango
        if sat_lo > 0.05 or sat_hi > 0.05:
            issues.append(f"Saturación: {sat_lo:.1%} bajo / {sat_hi:.1%} sobre rango")

        # 2. Varianza mínima: frame congelado o sin señal
        if float(np.std(T)) < 0.3:
            issues.append(f"Varianza muy baja ({np.std(T):.3f}°C) — sensor posiblemente bloqueado")

        # 3. Gradiente de borde: detecta si la lente está sucia
        sobel = cv2.Sobel(T.astype(np.float32), cv2.CV_32F, 1, 1, ksize=3)
        if float(np.mean(np.abs(sobel))) < 0.05:
            issues.append("Gradiente de borde mínimo — posible lente sucia o fuera de foco")

        # 4. Condiciones de captura
        if not frame.meteo.is_valid_capture_window:
            issues.append(
                f"Condiciones sub-óptimas: rad={frame.meteo.solar_rad}W/m² "
                f"VPD={frame.meteo.VPD:.2f}kPa wind={frame.meteo.wind_speed}m/s"
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "T_min": float(np.min(T)),
            "T_max": float(np.max(T)),
            "T_std": float(np.std(T)),
        }

    def process_frame(self, frame: ThermalFrame) -> dict:
        """
        Procesa un frame individual y retorna Ig (primario) + CWSI (verificación).

        El índice de salida principal es:
          - 'ig'   : Índice Jones por referencias físicas (si paneles válidos)
          - 'cwsi' : CWSI por NWSB (siempre calculado, como verificación)
          - 'stress_index' : ig si disponible, cwsi si no (el que usa el sistema)
          - 'calibration_level' : 1 (Ig), 2 (CWSI+offset lluvia), 3 (NWSB fábrica)
        """
        qc = self.validate_frame(frame)
        seg = self.segmenter.segment(frame)

        if seg["n_pixels"] < 50:
            return {
                "cwsi": np.nan,
                "ig": np.nan,
                "stress_index": np.nan,
                "calibration_level": None,
                "status": "INSUFICIENTE_COBERTURA_FOLIAR",
                "frame_id": frame.frame_id,
                "qc": qc,
                "seg": seg,
            }

        tc_canopy = seg["T_mean"]
        ta = frame.meteo.T_air

        # --- Nivel 1: Ig con referencias físicas ---
        panel_result = self.calibrator.read_panels(frame.temperature_C, ta)
        ig = self.calibrator.compute_ig(tc_canopy, panel_result)

        # --- Nivel 2/3: CWSI por NWSB (siempre, como verificación) ---
        cwsi_result = self.cwsi_calc.cwsi(tc_canopy, frame.meteo)
        cwsi = cwsi_result["cwsi"]

        # --- Índice primario y nivel de calibración ---
        if ig is not None:
            stress_index = ig
            calibration_level = 1
        else:
            stress_index = cwsi
            calibration_level = 3  # baseline.py puede promover a 2 si tiene offset

        # Consistencia cruzada Ig vs CWSI
        ig_cwsi_delta = abs(ig - cwsi) if ig is not None else None
        ig_cwsi_consistent = ig_cwsi_delta < 0.15 if ig_cwsi_delta is not None else None

        # ψ_stem desde el índice primario
        try:
            psi = self.cwsi_calc.psi_stem(stress_index)
            psi_stem_mpa = psi["psi_stem_MPa"]
            nivel_hidrico = psi["nivel_hidrico"]
        except (NotImplementedError, Exception):
            psi_stem_mpa = None
            nivel_hidrico = None

        return {
            "ig": ig if ig is not None else np.nan,
            "cwsi": cwsi,
            "stress_index": stress_index,
            "calibration_level": calibration_level,
            "panel": panel_result,
            "ig_cwsi_delta": ig_cwsi_delta,
            "ig_cwsi_consistent": ig_cwsi_consistent,
            "psi_stem_MPa": psi_stem_mpa,
            "nivel_hidrico": nivel_hidrico,
            "status": "OK" if qc["valid"] else "ADVERTENCIA",
            "frame_id": frame.frame_id,
            "angle_deg": frame.angle_deg,
            "canopy_side": frame.canopy_side,
            "foliar_frac": seg["foliar_frac"],
            "T_canopy_std": seg["T_std"],
            "T_canopy_mean": tc_canopy,
            "n_pixels": seg["n_pixels"],
            "qc": qc,
            "seg": seg,
        }

    def process_session(self, frames: list[ThermalFrame]) -> dict:
        """
        Procesa una sesión de captura (múltiples ángulos / ventanas horarias).
        CWSI final = promedio ponderado por fracción foliar de cada frame.
        Flag 'alta_variabilidad_angular' si std(CWSI) > 0.12.
        """
        results = [self.process_frame(f) for f in frames]
        valid = [r for r in results if r["status"] in ("OK", "ADVERTENCIA")
                 and not np.isnan(r.get("stress_index", np.nan))]

        if not valid:
            return {"stress_index_final": np.nan, "cwsi_final": np.nan,
                    "status": "SIN_DATOS_VÁLIDOS", "frames": results}

        idx_vals  = np.array([r["stress_index"] for r in valid])
        cwsi_vals = np.array([r["cwsi"] for r in valid])
        weights   = np.array([r["foliar_frac"] for r in valid])
        weights   = weights / weights.sum()

        stress_index_final = float(np.average(idx_vals, weights=weights))
        cwsi_final         = float(np.average(cwsi_vals, weights=weights))
        idx_std            = float(np.std(idx_vals))

        alta_variabilidad = idx_std > 0.12

        # Nivel de calibración predominante en la sesión
        levels = [r["calibration_level"] for r in valid if r["calibration_level"]]
        cal_level = min(levels) if levels else 3  # mejor nivel disponible
        cal_label = {1: "Ig_referencias_físicas", 2: "CWSI_offset_lluvia",
                     3: "CWSI_NWSB_fábrica"}.get(cal_level, "desconocido")

        # Consistencia Ig vs CWSI en la sesión
        ig_vals = [r["ig"] for r in valid if not np.isnan(r.get("ig", np.nan))]
        ig_cwsi_session_delta = (
            abs(float(np.mean(ig_vals)) - cwsi_final) if ig_vals else None
        )

        return {
            "stress_index_final": stress_index_final,
            "cwsi_final": cwsi_final,
            "stress_index_std": idx_std,
            "alta_variabilidad_angular": alta_variabilidad,
            "calibration_level": cal_level,
            "calibration_label": cal_label,
            "ig_cwsi_session_delta": ig_cwsi_session_delta,
            "ref_panel_reliability": self.calibrator.reliability,
            "n_frames_validos": len(valid),
            "n_frames_total": len(frames),
            "stress_level": self.cwsi_calc._classify(stress_index_final),
            "frames": results,
            "status": "ADVERTENCIA_VARIABILIDAD" if alta_variabilidad else "OK",
        }

    def build_cwsi_map(self, frame: ThermalFrame) -> np.ndarray:
        """
        Genera mapa CWSI píxel a píxel (para exportación GeoJSON/visualización).
        Retorna array float32 160×120 con valores CWSI (NaN = no-canopeo).
        """
        seg = self.segmenter.segment(frame)
        cwsi_map = np.full(frame.shape, np.nan, dtype=np.float32)
        if seg["n_pixels"] > 0:
            cwsi_values = self.cwsi_calc.cwsi_batch(
                frame.temperature_C[seg["mask"]], frame.meteo
            )
            cwsi_map[seg["mask"]] = cwsi_values
        return cwsi_map


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from synthetic_data_gen import FlirLepton35Simulator

    print("=" * 60)
    print("Pipeline Térmico — HydroVision AG — TRL 3")
    print("FLIR Lepton 3.5 → Segmentación → CWSI")
    print("=" * 60)

    sim = FlirLepton35Simulator(seed=42)
    pipeline = ThermalPipeline("malbec")

    # Simular sesión de 3 ángulos en ventana 12h (pico de estrés)
    meteo_noon = MeteoConditions(T_air=32.0, RH=33.0, solar_rad=880.0, wind_speed=1.2)

    print("\nSesión 12h — 3 ángulos de gimbal (0°, 30°, -30°)")
    frames = []
    for angle, cwsi_target in zip([0.0, 30.0, -30.0], [0.55, 0.58, 0.52]):
        frame = sim.generate_frame(meteo_noon, cwsi_target=cwsi_target,
                                   angle_deg=angle, frame_id=f"F_{angle:+.0f}")
        frames.append(frame)
        result = pipeline.process_frame(frame)
        print(f"  Ángulo {angle:+.0f}°  →  CWSI={result['cwsi']:.3f}  "
              f"cobertura={result['foliar_frac']:.1%}  {result['stress_level']}")

    session = pipeline.process_session(frames)
    print(f"\n  CWSI FINAL (ponderado): {session['cwsi_final']:.3f}")
    print(f"  Desv. std entre ángulos: {session['cwsi_std']:.3f}")
    print(f"  Alta variabilidad angular: {session['alta_variabilidad_angular']}")
    print(f"  Estado: {session['status']}")
    print(f"  Clasificación: {session['stress_level']}")

    # Mapa CWSI del primer frame
    cwsi_map = pipeline.build_cwsi_map(frames[0])
    valid_px = ~np.isnan(cwsi_map)
    print(f"\n  Mapa CWSI frame 0°: {np.sum(valid_px)} px foliares, "
          f"media={np.nanmean(cwsi_map):.3f}")
    print("\n✓ Pipeline térmico operativo")
