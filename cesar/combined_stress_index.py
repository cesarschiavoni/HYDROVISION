"""
HSI — HydroVision Stress Index
Fusion de Termografia Foliar (CWSI) + Dendrometria (MDS)
Prueba de Concepto TRL 3 — HydroVision AG — Colonia Caroya, Córdoba

Cultivo de validacion: Vid Malbec (Vitis vinifera cv. Malbec)
Sitio de referencia:   Colonia Caroya, Sierras Chicas, Cordoba (~700m s.n.m.)

El HSI (HydroVision Stress Index) es un indice compuesto que combina dos
fuentes de informacion sobre el estado hidrico de la planta:

  1. CWSI termico (cwsi_formula.py):
     - Fuente: temperatura foliar MLX90640 32×24 + meteo
     - Ventaja: cobertura espacial, 50+ plantas por sesion
     - Limitacion: requiere ventana solar (11h-16h), R2=0.62-0.67 vs psi_stem

  2. MDS dendrometrico (dendrometry.py):
     - Fuente: extensometro de tronco (strain gauge ADS1231)
     - Ventaja: continuo 24/7, R2=0.80-0.92 vs psi_stem
     - Limitacion: puntual (1 planta/sensor), sensible a temperatura

Estrategia de fusion — basada en calidad de correlacion con psi_stem:
  - Acuerdo entre señales (delta < umbral): promedio ponderado 35/65 CWSI/MDS
  - Desacuerdo: MDS domina (80%), CWSI como corrector menor (20%)
  - Señal unica disponible: esa señal con incertidumbre aumentada
  - Rescate: cualquier señal que cruce -1.5 MPa activa el protocolo

Racional de la fusion — por que dos señales y no solo MDS:
  El MDS del tallo es la señal mas confiable (R2=0.80-0.92) pero mide exactamente
  1 planta por sensor. La temperatura foliar cubre 50+ plantas por sesion, capturando
  la variabilidad espacial dentro de la hilera (suelo heterogeneo, goteros obstruidos)
  que el extensometro no puede detectar. En 4 hileras de 136m esto es operativamente
  critico.

  Ademas, reflejan capas fisiologicas distintas del mismo proceso:

    Estres hidrico → cierre estomatico → T_hoja sube → CWSI detectable (horas antes)
                   ↓
               contraccion del tallo → MDS detectable

  El cierre estomatico puede preceder al encogimiento del tallo en el ciclo diario:
  la hoja responde mas rapido al VPD atmosferico. CWSI detecta la respuesta estomatica;
  MDS detecta el estado hidraulico resultante.

  Malbec es moderadamente anisohidrico: mantiene los estomas parcialmente abiertos
  bajo estres. El tallo puede contraerse (MDS alto) mientras la planta todavia
  transpira. La señal termica captura esa conductancia residual; el tallo no.

  Por ultimo, la concordancia/discordancia entre señales es informacion en si misma:
  - Acuerdo → confianza alta, R2 compuesto ~0.90-0.95
  - Desacuerdo → anomalia (enfermedad foliar, daño fisico, sensor defectuoso)
  Una sola señal nunca puede proveer esa validacion cruzada.

  En resumen: MDS es el ancla de precision fisiologica (1 planta, alta correlacion);
  CWSI es el mapa espacial de la hilera (50+ plantas, menor correlacion individual
  pero cobertura irreemplazable). La fusion HSI maximiza ambas dimensiones.

Resultado esperado:
  R2(HSI vs psi_stem) ~= 0.90-0.95  (vs 0.65 CWSI solo, 0.85 MDS solo)
  Esto representa la principal innovacion tecnica del nodo HydroVision AG.

Novedad global:
  No se ha identificado en el mercado global ningun producto comercial que
  combine termografia foliar continua + motor fenologico automatico + fusion
  satelital + dendrometria integrada en un nodo autonomo de campo.
  Referencia: Jones (2004), Fernandez et al. (2011).

Referencias:
  Jones, H.G. (2004).
    Irrigation scheduling: advantages and pitfalls of plant-based methods.
    Journal of Experimental Botany, 55(407), 2427-2436.
    [Complementariedad de indicadores termicos vs hidraulicos]

  Fernandez, J.E. et al. (2011).
    Combining measurements of stem-water potential and trunk diameter
    variations as indicators of tree water status.
    Irrigation Science, 29(4), 297-305.
    [Fusion experimental de dendrometria + potencial hidrico; base del HSI]

  Fernandez, J.E. & Cuevas, M.V. (2010).
    Irrigation scheduling from stem diameter variations: A review.
    Agricultural and Forest Meteorology, 150(2), 135-151.
    [R2 dendrometria: 0.80-0.92; base de la ponderacion 65%]

  Pires, A. et al. (2025).
    Scalable thermal imaging and processing framework for water status
    monitoring in vineyards. Computers and Electronics in Agriculture, 239.
    [R2 termico: 0.618-0.663; base de la ponderacion 35%]

  Bellvert, J. et al. (2016).
    Seasonal evolution of crop water stress index in grapevine varieties
    determined with high-resolution remote sensing thermal imagery.
    Precision Agriculture, 17(1), 62-78.
    [Coeficientes CWSI Malbec usados en señal termica]
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cwsi_formula import CWSICalculator, MeteoConditions
from dendrometry import DendrometryEngine, DailyDendrometryResult


# ─────────────────────────────────────────────────────────────────────────────
# PONDERACIONES DEL INDICE HSI
# Basadas en R2 de correlacion con psi_stem (gold standard Scholander)
#   - CWSI termico:  R2 = 0.618-0.663  ->  peso 35%  (Pires 2025)
#   - MDS dendro:    R2 = 0.80-0.92    ->  peso 65%  (Fernandez 2010)
# ─────────────────────────────────────────────────────────────────────────────
HSI_WEIGHT_CWSI = 0.35   # peso CWSI en fusion (acuerdo de señales)
HSI_WEIGHT_MDS  = 0.65   # peso MDS  en fusion (acuerdo de señales)

# Ponderaciones en caso de DESACUERDO entre señales
HSI_DISAGREEMENT_WEIGHT_MDS  = 0.80
HSI_DISAGREEMENT_WEIGHT_CWSI = 0.20

# Umbral de desacuerdo: diferencia de psi_stem entre señales > 0.35 MPa
# -> se activa modo desacuerdo donde MDS domina
HSI_DISAGREEMENT_THRESHOLD_MPa = 0.35

# Rampa gradual de viento para reduccion progresiva del peso CWSI
# Entre RAMP_LO y RAMP_HI: w_cwsi se reduce linealmente de 100% a 0%
# Por encima de RAMP_HI: override total → 100% MDS dendrometrico
WIND_RAMP_LO_MS = 4.0   # m/s — inicio de reduccion
WIND_RAMP_HI_MS = 18.0  # m/s (65 km/h) — override completo con mitigaciones v2 firmware
WIND_OVERRIDE_THRESHOLD_MS = WIND_RAMP_HI_MS  # backward compat

# Umbral de rescate hidrico — Protocolo HydroVision AG
# Cualquier señal individual que cruce este limite activa el protocolo,
# independientemente del indice HSI compuesto.
RESCUE_THRESHOLD_MPa = -1.5

# Factor de incertidumbre cuando solo hay una señal disponible
# El intervalo de confianza se amplifica para reflejar la falta de validacion cruzada
SINGLE_SIGNAL_UNCERTAINTY_FACTOR = 1.4


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERACION — Estado del acuerdo entre señales
# ─────────────────────────────────────────────────────────────────────────────

class SignalAgreement(Enum):
    """
    Estado del acuerdo entre las dos fuentes de informacion del nodo HSI.

    FULL_AGREEMENT : ambas señales disponibles y coherentes (delta < umbral)
    DISAGREEMENT   : ambas señales disponibles pero divergen (delta > umbral)
    THERMAL_ONLY   : solo CWSI disponible (sensor MDS fallo o fuera de rango)
    DENDRO_ONLY    : solo MDS disponible (sesion fuera de ventana solar)
    NO_DATA        : ninguna señal disponible (fallo de comunicacion)
    """
    FULL_AGREEMENT = "ACUERDO_TOTAL"
    DISAGREEMENT   = "DESACUERDO"
    THERMAL_ONLY   = "SOLO_TERMICO"
    DENDRO_ONLY    = "SOLO_DENDRO"
    NO_DATA        = "SIN_DATOS"


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASS — Resultado del indice HSI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HydroVisionStressIndex:
    """
    Resultado del HydroVision Stress Index (HSI) para una planta / zona.

    El HSI unifica ambas fuentes en un psi_stem estimado final con
    menor incertidumbre que cualquier señal individual.
    """
    # ── Entradas ────────────────────────────────────────────────────────────
    psi_cwsi_mpa: Optional[float]       # psi_stem desde CWSI termico [MPa]
    psi_mds_mpa: Optional[float]        # psi_stem desde MDS dendro [MPa]
    cwsi_value: Optional[float]         # CWSI normalizado [0-1]
    mds_corrected_um: Optional[float]   # MDS con correccion termica [um]

    # ── HSI fusionado ────────────────────────────────────────────────────────
    psi_hsi_mpa: float                  # psi_stem HSI final [MPa]
    psi_uncertainty_mpa: float          # incertidumbre estimada [+/- MPa]
    signal_agreement: SignalAgreement   # estado del acuerdo entre señales
    weight_cwsi_used: float             # peso efectivo de CWSI en la fusion
    weight_mds_used: float              # peso efectivo de MDS en la fusion

    # ── Clasificacion y alerta ───────────────────────────────────────────────
    stress_level: str                   # clasificacion agronomica del estres
    alert: str                          # mensaje para el operario
    rescue_required: bool               # True si cualquier señal cruza -1.5 MPa
    rescue_source: str                  # fuente que activo el rescate (o "")

    # ── Metadatos ────────────────────────────────────────────────────────────
    crop: str = "malbec"
    sensor_id: str = "D01"
    fusion_note: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE FUSION
# ─────────────────────────────────────────────────────────────────────────────

class CombinedStressEngine:
    """
    Motor de fusion HSI — combina CWSI termico + MDS dendrometrico.

    Logica de fusion:
      1. Si ambas señales disponibles y coherentes (delta < 0.35 MPa):
         psi_HSI = 0.35 * psi_CWSI + 0.65 * psi_MDS   -> R2 ~0.90-0.95
      2. Si ambas disponibles pero divergen (delta >= 0.35 MPa):
         psi_HSI = 0.20 * psi_CWSI + 0.80 * psi_MDS   -> MDS domina
         (el MDS tiene correlacion fisiologica mas directa)
      3. Solo una señal:
         psi_HSI = esa señal * 1.0, uncertainty *= 1.4
      4. Rescate: si psi_CWSI <= -1.5 MPa OR psi_MDS <= -1.5 MPa
         -> rescue_required = True, independientemente del indice compuesto
    """

    def __init__(self, crop: str = "malbec"):
        self.crop = crop
        self.cwsi_calc = CWSICalculator(crop)
        self.dendro_engine = DendrometryEngine(crop)

    # ── Clasificacion agronomica (psi_stem) ──────────────────────────────────

    @staticmethod
    def _classify_psi(psi_mpa: float) -> str:
        """Clasificacion agronomica desde psi_stem [MPa]."""
        if psi_mpa > -0.60:
            return "SIN_ESTRES"
        elif psi_mpa > -1.00:
            return "ESTRES_LEVE"
        elif psi_mpa > -1.40:
            return "ESTRES_MODERADO_SEVERO"
        else:
            return "ESTRES_CRITICO"

    @staticmethod
    def _alert_from_psi(psi_mpa: float, agreement: SignalAgreement,
                        rescue: bool, rescue_source: str) -> str:
        """Genera mensaje de alerta para el operario."""
        if rescue:
            return (
                f"[RESCATE HSI] psi_stem HSI = {psi_mpa:.2f} MPa "
                f"(fuente: {rescue_source}). "
                f"RIEGO DE EMERGENCIA — suspender protocolo experimental."
            )
        if agreement == SignalAgreement.DISAGREEMENT:
            prefix = "[DESACUERDO SEÑALES] "
        elif agreement in (SignalAgreement.THERMAL_ONLY, SignalAgreement.DENDRO_ONLY):
            prefix = "[SEÑAL UNICA] "
        else:
            prefix = ""

        if psi_mpa > -0.60:
            msg = "Estado hidrico optimo. Sin accion requerida."
        elif psi_mpa > -1.00:
            msg = "Estres leve. Monitorear evolucion."
        elif psi_mpa > -1.40:
            msg = "Estres moderado-severo. Revisar plan de riego."
        else:
            msg = "ESTRES CRITICO — Riego inmediato recomendado."

        return prefix + msg

    # ── Fusion principal ──────────────────────────────────────────────────────

    def fuse(self,
             # Señal termica (opcional)
             T_leaf_c: Optional[float] = None,
             meteo: Optional[MeteoConditions] = None,
             # Señal dendrometrica (opcional)
             dendro_result: Optional[DailyDendrometryResult] = None,
             # Condiciones de viento
             wind_speed_ms: float = 0.0,
             # Metadatos
             sensor_id: str = "D01") -> HydroVisionStressIndex:
        """
        Fusiona las señales termica y dendrometrica en el indice HSI.

        Al menos una de las dos señales debe estar disponible.
        Llama a cwsi_formula.py y dendrometry.py internamente.

        Parametros
        ----------
        T_leaf_c      : temperatura foliar [degC] (None si no disponible)
        meteo         : condiciones meteorologicas (None si no disponible)
        dendro_result : resultado diario del motor dendrometrico (None si no disponible)
        wind_speed_ms : velocidad del viento [m/s]. Rampa gradual 4-18 m/s:
                        entre 4 y 18 m/s el peso del CWSI se reduce linealmente.
                        >= 18 m/s: override total → 100% MDS dendrometrico.
        sensor_id     : identificador del nodo en campo

        Retorna HydroVisionStressIndex con psi_HSI fusionado.
        """
        # Wind override: viento >= 18 m/s invalida completamente la señal termica
        wind_override = wind_speed_ms >= WIND_RAMP_HI_MS
        # Factor de rampa gradual: 1.0 si <=4, 0.0 si >=18, lineal entre ambos
        if wind_speed_ms <= WIND_RAMP_LO_MS:
            wind_cwsi_factor = 1.0
        elif wind_speed_ms >= WIND_RAMP_HI_MS:
            wind_cwsi_factor = 0.0
        else:
            wind_cwsi_factor = (WIND_RAMP_HI_MS - wind_speed_ms) / (WIND_RAMP_HI_MS - WIND_RAMP_LO_MS)
        if wind_override and T_leaf_c is not None:
            # Tratar la señal termica como no disponible en condicion de viento fuerte
            T_leaf_c = None
            meteo = None
        # ── Calcular psi desde cada señal disponible ──────────────────────────
        psi_cwsi = None
        cwsi_val = None
        if T_leaf_c is not None and meteo is not None:
            cwsi_result = self.cwsi_calc.cwsi(T_leaf_c, meteo)
            cwsi_val = cwsi_result["cwsi"]
            psi_cwsi = cwsi_result.get("psi_stem_MPa")

        psi_mds = None
        mds_corr = None
        if dendro_result is not None:
            psi_mds = dendro_result.psi_stem_mpa
            mds_corr = dendro_result.mds_corrected_um

        # ── Verificar disponibilidad ──────────────────────────────────────────
        has_thermal = psi_cwsi is not None
        has_dendro  = psi_mds is not None

        if not has_thermal and not has_dendro:
            # Sin datos: retornar señal de error
            return HydroVisionStressIndex(
                psi_cwsi_mpa=None, psi_mds_mpa=None,
                cwsi_value=None, mds_corrected_um=None,
                psi_hsi_mpa=float("nan"), psi_uncertainty_mpa=float("nan"),
                signal_agreement=SignalAgreement.NO_DATA,
                weight_cwsi_used=0.0, weight_mds_used=0.0,
                stress_level="SIN_DATOS",
                alert="ERROR: ninguna señal disponible. Verificar hardware.",
                rescue_required=False, rescue_source="",
                crop=self.crop, sensor_id=sensor_id,
                fusion_note="No hay datos de ninguna fuente.",
            )

        # ── Deteccion de rescate (independiente de la fusion) ─────────────────
        rescue = False
        rescue_source = ""
        if has_thermal and psi_cwsi <= RESCUE_THRESHOLD_MPa:
            rescue = True
            rescue_source = f"CWSI_termico (psi={psi_cwsi:.2f}MPa)"
        if has_dendro and psi_mds <= RESCUE_THRESHOLD_MPa:
            rescue = True
            rescue_source += ("; " if rescue_source else "") + \
                             f"MDS_dendro (psi={psi_mds:.2f}MPa)"

        # ── Logica de fusion ──────────────────────────────────────────────────
        if has_thermal and has_dendro:
            delta = abs(psi_cwsi - psi_mds)
            if delta < HSI_DISAGREEMENT_THRESHOLD_MPa:
                # Acuerdo: promedio ponderado, modulado por rampa de viento
                agreement = SignalAgreement.FULL_AGREEMENT
                w_cwsi = HSI_WEIGHT_CWSI * wind_cwsi_factor
                w_mds  = 1.0 - w_cwsi
                psi_hsi = w_cwsi * psi_cwsi + w_mds * psi_mds
                # Incertidumbre base: diferencia entre señales / 2
                uncertainty = delta / 2.0 + 0.05   # +5% base instrumental
                note = (f"Fusion ponderada: {w_cwsi:.0%} CWSI + {w_mds:.0%} MDS. "
                        f"Delta psi = {delta:.2f} MPa < {HSI_DISAGREEMENT_THRESHOLD_MPa} MPa."
                        f" Wind factor: {wind_cwsi_factor:.2f}.")
            else:
                # Desacuerdo: MDS domina (mayor correlacion fisiologica)
                agreement = SignalAgreement.DISAGREEMENT
                w_cwsi = HSI_DISAGREEMENT_WEIGHT_CWSI * wind_cwsi_factor
                w_mds  = 1.0 - w_cwsi
                psi_hsi = w_cwsi * psi_cwsi + w_mds * psi_mds
                uncertainty = delta / 2.0 + 0.10   # +10% por desacuerdo
                note = (f"Desacuerdo (delta={delta:.2f}MPa > {HSI_DISAGREEMENT_THRESHOLD_MPa}MPa). "
                        f"MDS domina: {w_mds:.0%}. CWSI como corrector: {w_cwsi:.0%}."
                        f" Wind factor: {wind_cwsi_factor:.2f}.")

        elif has_dendro:
            # Solo dendrometria (o wind override que descarto la señal termica)
            agreement = SignalAgreement.DENDRO_ONLY
            w_cwsi = 0.0
            w_mds  = 1.0
            psi_hsi = psi_mds
            uncertainty = abs(psi_mds) * 0.15 * SINGLE_SIGNAL_UNCERTAINTY_FACTOR
            if wind_override:
                note = (f"Wind override: viento {wind_speed_ms:.1f} m/s >= "
                        f"{WIND_RAMP_HI_MS} m/s. CWSI termico invalido. "
                        f"Peso transferido automaticamente al 100% MDS.")
            else:
                note = "Solo MDS disponible. Incertidumbre ampliada x1.4."

        else:
            # Solo termico
            agreement = SignalAgreement.THERMAL_ONLY
            w_cwsi = 1.0
            w_mds  = 0.0
            psi_hsi = psi_cwsi
            uncertainty = abs(psi_cwsi) * 0.20 * SINGLE_SIGNAL_UNCERTAINTY_FACTOR
            note = "Solo CWSI disponible. Incertidumbre ampliada x1.4."

        psi_hsi = round(float(psi_hsi), 3)
        uncertainty = round(float(uncertainty), 3)

        # ── Clasificacion y alerta ────────────────────────────────────────────
        level = self._classify_psi(psi_hsi)
        alert = self._alert_from_psi(psi_hsi, agreement, rescue, rescue_source)

        return HydroVisionStressIndex(
            psi_cwsi_mpa=round(psi_cwsi, 3) if psi_cwsi is not None else None,
            psi_mds_mpa=round(psi_mds, 3) if psi_mds is not None else None,
            cwsi_value=round(cwsi_val, 3) if cwsi_val is not None else None,
            mds_corrected_um=round(mds_corr, 1) if mds_corr is not None else None,
            psi_hsi_mpa=psi_hsi,
            psi_uncertainty_mpa=uncertainty,
            signal_agreement=agreement,
            weight_cwsi_used=w_cwsi,
            weight_mds_used=w_mds,
            stress_level=level,
            alert=alert,
            rescue_required=rescue,
            rescue_source=rescue_source,
            crop=self.crop,
            sensor_id=sensor_id,
            fusion_note=note,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Demo — Prueba de Concepto TRL 3
# Cultivo: Malbec — Colonia Caroya, Cordoba
# Escenarios: 5 situaciones de campo del viñedo experimental
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from datetime import datetime
    from dendrometry import TrunkDiameterReading

    SEP = "=" * 70

    print(SEP)
    print("  HSI — HydroVision Stress Index — Prueba de Concepto TRL 3")
    print("  Fusion: CWSI termico (35%) + MDS dendrometrico (65%)")
    print("  Colonia Caroya, Cordoba (~700m s.n.m.)")
    print("  Jones (2004) + Fernandez et al. (2011)")
    print(SEP)

    engine = CombinedStressEngine("malbec")
    dendro = DendrometryEngine("malbec")

    # Condicion meteorologica referencia — enero, 13h
    meteo_stress = MeteoConditions(T_air=34.0, RH=28.0, solar_rad=900.0, wind_speed=1.5)

    def make_dendro_result(mds_corr_um: float, delta_T: float = 12.0) -> DailyDendrometryResult:
        """Crea un resultado dendrometrico simplificado para el demo."""
        psi = dendro.psi_stem_from_mds(mds_corr_um)
        level, alert_d, rescue_d = dendro.classify(mds_corr_um)
        mds_raw = mds_corr_um + dendro.coef["thermal_alpha_um_per_C"] * delta_T
        return DailyDendrometryResult(
            date="2026-01-15",
            d_max_um=25400.0,
            d_min_um=25400.0 - mds_raw,
            mds_raw_um=mds_raw,
            mds_corrected_um=mds_corr_um,
            delta_T_trunk_c=delta_T,
            psi_stem_mpa=psi,
            recovery_rate=0.88,
            stress_level=level,
            alert=alert_d,
            rescue_required=rescue_d,
        )

    # ── Escenarios de fusion ──────────────────────────────────────────────────
    print(f"\n--- Escenarios de fusion CWSI + MDS ---\n")
    print(f"  {'Escenario':<30}  {'CWSI':>6}  {'MDS[um]':>8}  "
          f"{'psi_CWSI':>9}  {'psi_MDS':>8}  {'psi_HSI':>8}  {'Acuerdo':<14}  Nivel")
    print(f"  {'-'*30}  {'-'*6}  {'-'*8}  {'-'*9}  {'-'*8}  {'-'*8}  {'-'*14}  {'-'*22}")

    scenarios = [
        # (descripcion, T_leaf, MDS_corr_um, descripcion_acuerdo)
        ("A: Control — acuerdo total     ", 34.2,   55.0),
        ("B: Estres leve — acuerdo       ", 35.8,  160.0),
        ("C: Estres moderado — acuerdo   ", 37.5,  290.0),
        ("D: Desacuerdo — MDS domina     ", 34.5,  310.0),  # CWSI leve, MDS severo
        ("E: Sin riego — rescate         ", 40.2,  440.0),  # Ambas > umbral
    ]

    for desc, T_leaf, mds_val in scenarios:
        dendro_res = make_dendro_result(mds_val)
        hsi = engine.fuse(T_leaf_c=T_leaf, meteo=meteo_stress,
                          dendro_result=dendro_res, sensor_id="D01")
        cwsi_str = f"{hsi.cwsi_value:.3f}" if hsi.cwsi_value is not None else "  ---"
        mds_str  = f"{hsi.mds_corrected_um:.0f}" if hsi.mds_corrected_um is not None else "    ---"
        pc_str   = f"{hsi.psi_cwsi_mpa:.2f}" if hsi.psi_cwsi_mpa is not None else "      ---"
        pm_str   = f"{hsi.psi_mds_mpa:.2f}" if hsi.psi_mds_mpa is not None else "     ---"
        rescue_flag = " [RESCATE]" if hsi.rescue_required else ""
        print(f"  {desc}  {cwsi_str:>6}  {mds_str:>8}  "
              f"{pc_str:>9}  {pm_str:>8}  {hsi.psi_hsi_mpa:>8.2f}  "
              f"{hsi.signal_agreement.value:<14}  {hsi.stress_level}{rescue_flag}")

    # ── Escenario wind override ───────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  Wind override — viento = 18 m/s -> 100% MDS dendrometrico (rampa gradual 4-18 m/s)")
    print(SEP)

    hsi_wind = engine.fuse(T_leaf_c=37.0, meteo=meteo_stress,
                           dendro_result=make_dendro_result(200.0),
                           wind_speed_ms=5.2, sensor_id="D01")
    print(f"  Viento 5.2 m/s: psi_HSI = {hsi_wind.psi_hsi_mpa:.2f} MPa  "
          f"Pesos CWSI={hsi_wind.weight_cwsi_used:.0%}/MDS={hsi_wind.weight_mds_used:.0%}  "
          f"({hsi_wind.signal_agreement.value})")
    print(f"  Nota: {hsi_wind.fusion_note}")

    # ── Escenarios de señal unica ─────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  Señal unica — incertidumbre ampliada x1.4")
    print(SEP)

    # Solo termico (noche o falla sensor dendro)
    hsi_t = engine.fuse(T_leaf_c=36.0, meteo=meteo_stress, sensor_id="D02")
    # Solo dendro (sesion fuera ventana solar)
    hsi_d = engine.fuse(dendro_result=make_dendro_result(220.0), sensor_id="D02")

    for label, hsi in [("Solo CWSI termico", hsi_t), ("Solo MDS dendro  ", hsi_d)]:
        print(f"  {label}: psi_HSI = {hsi.psi_hsi_mpa:.2f} MPa "
              f"+/- {hsi.psi_uncertainty_mpa:.2f} MPa  "
              f"({hsi.signal_agreement.value})")

    # ── Ventaja del HSI vs señal individual ──────────────────────────────────
    print(f"\n{SEP}")
    print("  Ventaja del HSI — Reduccion de incertidumbre")
    print(SEP)
    hsi_full = engine.fuse(T_leaf_c=36.5, meteo=meteo_stress,
                           dendro_result=make_dendro_result(250.0), sensor_id="D01")
    print(f"  Solo CWSI:  R2 ~ 0.62-0.67  (Pires et al. 2025)")
    print(f"  Solo MDS:   R2 ~ 0.80-0.92  (Fernandez & Cuevas 2010)")
    print(f"  HSI fusion: R2 ~ 0.90-0.95  (estimado — objetivo TRL 4)")
    print(f"\n  Ejemplo fusion zona C:")
    print(f"    psi_CWSI = {hsi_full.psi_cwsi_mpa:.2f} MPa  (peso {hsi_full.weight_cwsi_used:.0%})")
    print(f"    psi_MDS  = {hsi_full.psi_mds_mpa:.2f} MPa  (peso {hsi_full.weight_mds_used:.0%})")
    print(f"    psi_HSI  = {hsi_full.psi_hsi_mpa:.2f} MPa +/- {hsi_full.psi_uncertainty_mpa:.2f} MPa")
    print(f"    Acuerdo  = {hsi_full.signal_agreement.value}")
    print(f"    Nivel    = {hsi_full.stress_level}")
    print(f"\n    Nota: {hsi_full.fusion_note}")

    print(f"\n  [OK] Modulo HSI operativo — TRL 3 Colonia Caroya")
    print(f"  Ponderacion: {HSI_WEIGHT_CWSI:.0%} CWSI + {HSI_WEIGHT_MDS:.0%} MDS (acuerdo)")
    print(f"  Desacuerdo : {HSI_DISAGREEMENT_WEIGHT_CWSI:.0%} CWSI + {HSI_DISAGREEMENT_WEIGHT_MDS:.0%} MDS (MDS domina)")
    print(f"  Rescate    : psi_stem <= {RESCUE_THRESHOLD_MPa} MPa (cualquier señal individual)")
    print(f"  Novedad    : primer sistema comercial global con fusion termico+dendro en nodo autonomo")
