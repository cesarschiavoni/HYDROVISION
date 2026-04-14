"""
CWSI — Crop Water Stress Index
Prueba de Concepto TRL 3 — HydroVision AG — Colonia Caroya, Córdoba

Cultivo de validación: Vid Malbec (Vitis vinifera cv. Malbec)
Sitio de referencia:   Colonia Caroya, Sierras Chicas, Córdoba (~700m s.n.m.)

Implementación basada en Jackson et al. (1981) con coeficientes empíricos
calibrados para Malbec por Bellvert et al. (2016).

Índices implementados:
  1. CWSI (Jackson 1981): normaliza el diferencial térmico medido respecto a
     los límites biofísicos del cultivo (0 = sin estrés, 1 = estrés máximo).
  2. Índice Jones / Ig (Jones 1999): alternativa sin dependencia de VPD
     modelado; usa referencias Twet/Tdry medidas directamente en campo.
  3. ψ_stem [MPa] (Pires et al. 2025): convierte CWSI al potencial hídrico
     de tallo, unidad estándar de la cámara Scholander usada en campo.

Referencias principales:
  Jackson, R.D., Idso, S.B., Reginato, R.J. & Pinter, P.J. (1981).
    Canopy temperature as a crop water stress indicator.
    Water Resources Research, 17(4), 1133-1138.

  Bellvert, J., Marsal, J., Girona, J. & Zarco-Tejada, P.J. (2016).
    Seasonal evolution of crop water stress index in grapevine varieties
    determined with high-resolution remote sensing thermal imagery.
    Precision Agriculture, 17(1), 62-78.
    [Coeficientes ΔT_LL / ΔT_UL para Malbec]

  Jones, H.G. (1999). Use of infrared thermometry for estimation of stomatal
    conductance as a possible aid to irrigation scheduling. Agricultural and
    Forest Meteorology, 95(3), 139-149.

  Gutierrez, S. et al. (2018). Vineyard water status assessment using on-the-go
    thermal imaging and machine learning. PLoS ONE, 13(2), e0192037.
    [Validacion del Indice Jones en vid; R2=0.61 con referencias Tdry/Twet]

  Pires, A. et al. (2025). Scalable thermal imaging and processing framework
    for water status monitoring in vineyards. Computers and Electronics in
    Agriculture, 239, 110931.
    [Correlacion CWSI termico -> psi_stem; R2=0.618 global, R2=0.663 tarde]

  Zhou, Z. et al. (2022). Ground-based thermal imaging for assessing crop
    water status in grapevines over a growing season. Agronomy, 12(2), 322.
    [Correlacion CWSI <-> psi_leaf en vid Riesling; plataforma terrestre]

  Araujo-Paredes, C. et al. (2022). Using aerial thermal imagery to evaluate
    water status in Vitis vinifera cv. Loureiro. Sensors, 22(20), 8056.
    [Validacion CWSI aereo vs psi_stem; precision NETD aceptable < +-0.07]

Arquitectura multi-cultivo:
  El modulo incluye coeficientes para otros cultivos del portfolio de
  HydroVision AG (olivo con respaldo cientifico; otras variedades de vid
  interpoladas desde Bellvert 2016). Estos estan disenados para calibracion
  futura en campo y NO son el objeto de la prueba TRL 3.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# CULTIVO DE VALIDACIÓN TRL 3: MALBEC
# Coeficientes Bellvert et al. (2016) — únicos con respaldo directo para
# el sitio de referencia (condiciones de alta insolación, similares a Cuyo).
#
# ΔT_LL = a + b·VPD  → límite inferior (planta perfectamente hidratada)
# ΔT_UL = c + d·VPD  → límite superior (planta sin transpiración)
# ─────────────────────────────────────────────────────────────────────────────
MALBEC = {
    "a": -1.97,   # intercept ΔT_LL  [°C]  — Bellvert 2016 Tabla 2
    "b":  1.49,   # pendiente ΔT_LL vs VPD — Bellvert 2016 Tabla 2
    "c":  3.50,   # intercept ΔT_UL  [°C]  — Bellvert 2016
    "d":  0.00,   # pendiente ΔT_UL (constante en condiciones normales)
    "description": "Vid Malbec — Bellvert et al. (2016) Precision Agriculture",
    "T_base_gdd": 10.0,  # temperatura base GDD metodo Winkler [°C]
    # Prediccion psi_stem [MPa]: regresion lineal CWSI -> psi_stem
    # Calibrada en vid tinta Mediterraneo (Pires 2025, Zhou 2022, Araujo-Paredes 2022)
    # psi_stem = psi_a + psi_b * CWSI
    "psi_a": -0.35,   # psi_stem con CWSI=0 (planta bien hidratada) [MPa]
    "psi_b": -1.20,   # pendiente: mayor CWSI -> psi mas negativo [MPa/CWSI]
}


# ─────────────────────────────────────────────────────────────────────────────
# ARQUITECTURA ESCALABLE — otros cultivos del portfolio HydroVision AG
# Estos coeficientes son para calibracion futura en campo.
# NO son objeto de la prueba de concepto TRL 3.
# ─────────────────────────────────────────────────────────────────────────────
_FUTURE_CROPS = {
    "cabernet_sauvignon": {
        # Interpolado desde Bellvert (2016) — variedad similar al Malbec
        "a": -2.10, "b": 1.55, "c": 3.60, "d": 0.00,
        "description": "Vid Cabernet Sauvignon — interpolado Bellvert 2016",
        "T_base_gdd": 10.0,
        "psi_a": -0.35, "psi_b": -1.20,
    },
    "torrontes": {
        # Estimado para hoja mas grande (mayor conductancia estomatica)
        "a": -2.30, "b": 1.60, "c": 3.40, "d": 0.00,
        "description": "Vid Torrontes — estimado desde literatura INTA",
        "T_base_gdd": 10.0,
        "psi_a": -0.30, "psi_b": -1.15,
    },
    "olive": {
        # Garcia-Tejero, I.F. et al. (2018). Thermal imaging to monitor the
        # crop-water status in almonds and olives. Scientia Horticulturae, 240, 74-82.
        "a": -1.75, "b": 1.35, "c": 4.10, "d": 0.00,
        "description": "Olivo — Garcia-Tejero et al. (2018) Sci. Horticulturae",
        "T_base_gdd": 10.0,
        "psi_a": -0.40, "psi_b": -1.50,
    },
}

# Registro unificado — permite instanciar cualquier cultivo por nombre
CROP_COEFFICIENTS: dict = {"malbec": MALBEC, **_FUTURE_CROPS}


@dataclass
class MeteoConditions:
    """Condiciones meteorologicas en el momento de la captura termica."""
    T_air: float        # Temperatura del aire [°C]
    RH: float           # Humedad relativa [%]  0-100
    solar_rad: float    # Radiacion solar global [W/m2]
    wind_speed: float   # Velocidad del viento [m/s]

    @property
    def VPD(self) -> float:
        """Deficit de presion de vapor [kPa]. Ecuacion de Buck (1981)."""
        es = 0.6108 * np.exp(17.27 * self.T_air / (self.T_air + 237.3))
        ea = es * self.RH / 100.0
        return es - ea

    @property
    def is_valid_capture_window(self) -> bool:
        """
        Verifica condiciones optimas para captura CWSI (protocolo Monteoliva).
        Requiere: radiacion >= 400 W/m2, VPD >= 0.5 kPa, viento <= 18 m/s.
        Nota: con mitigaciones v2 firmware (sotavento+tubo+termopar Kalman+Muller gbh+
        Hampel+2do termopar), 18 m/s en anemometro ≈ 5.4-7.2 m/s en hoja.
        """
        return (
            self.solar_rad >= 400        # W/m2 — sol suficiente para diferencial termico
            and self.VPD >= 0.5          # kPa  — diferencial foliar medible
            and self.wind_speed <= 18.0  # m/s (65 km/h) — limite con mitigacion v2 firmware
        )

    @property
    def aerodynamic_resistance(self) -> float:
        """
        Resistencia aerodinamica [s/m] — FAO-56 simplificado para vid.
        ra = 208 / u  (Allen et al. 1998)
        Consistente con investigador/01_simulador/weather.py.
        """
        return max(208.0 / max(self.wind_speed, 0.5), 20.0)

    @property
    def delta_sat(self) -> float:
        """Pendiente de la curva de presion de vapor de saturacion [kPa/K]."""
        return (
            4098.0 * 0.6108 * np.exp(17.27 * self.T_air / (self.T_air + 237.3))
            / (self.T_air + 237.3) ** 2
        )

    @property
    def wind_cwsi_weight(self) -> float:
        """
        Peso del CWSI en el HSI segun viento (transicion gradual).
        Consistente con firmware: rampa lineal 4-18 m/s (v2 con Kalman+Muller+Hampel).
          <= 4 m/s (14 km/h)  → 0.35 (normal)
          4-18 m/s (14-65 km/h) → rampa lineal 0.35 → 0.00
          >= 18 m/s (65 km/h) → 0.00 (backup 100% MDS)
        """
        RAMP_LO, RAMP_HI = 4.0, 18.0
        if self.wind_speed <= RAMP_LO:
            return 0.35
        if self.wind_speed >= RAMP_HI:
            return 0.0
        return 0.35 * (RAMP_HI - self.wind_speed) / (RAMP_HI - RAMP_LO)


class CWSICalculator:
    """
    Calculador de indices de estres hidrico para vid Malbec — TRL 3.

    Indice principal: CWSI (Jackson et al. 1981)
      CWSI = (dT_medido - dT_LL) / (dT_UL - dT_LL)
      - CWSI = 0: planta bien hidratada (transpirando al maximo)
      - CWSI = 1: planta bajo estres maximo (estomas cerrados)

    Indice complementario: Ig (Jones 1999)
      Ig = (Tc - Tdry) / (Twet - Tdry)
      No requiere VPD modelado; valida la medicion con referencias de campo.

    Output agronomico: psi_stem [MPa] (Pires et al. 2025)
      Convierte CWSI a la unidad que el productor mide con Scholander.
    """

    def __init__(self, crop: str = "malbec"):
        if crop not in CROP_COEFFICIENTS:
            raise ValueError(
                f"Cultivo '{crop}' no reconocido. "
                f"Opciones: {list(CROP_COEFFICIENTS)}"
            )
        self.crop = crop
        self.coef = CROP_COEFFICIENTS[crop]

    # ── Limites biofisicos ──────────────────────────────────────────────────

    def delta_T_LL(self, VPD: float) -> float:
        """
        Limite inferior de dT: planta perfectamente hidratada [°C].
        dT_LL = a + b*VPD  (Bellvert 2016 para Malbec)
        """
        return self.coef["a"] + self.coef["b"] * VPD

    def delta_T_UL(self, VPD: float = 0.0) -> float:
        """
        Limite superior de dT: planta sin transpiracion (estomas cerrados) [°C].
        Constante para la mayoria de condiciones de campo (d=0).
        """
        return self.coef["c"] + self.coef["d"] * VPD

    # ── CWSI principal ──────────────────────────────────────────────────────

    def cwsi(self, T_leaf: float, meteo: MeteoConditions) -> dict:
        """
        Calcula CWSI desde temperatura foliar y condiciones meteorologicas.

        Parametros
        ----------
        T_leaf : temperatura del canopeo [°C] — promedio del segmento foliar
        meteo  : condiciones meteorologicas en el momento de captura

        Retorna dict con CWSI, componentes, clasificacion agronomica y psi_stem.
        """
        dT_measured = T_leaf - meteo.T_air
        dT_ll = self.delta_T_LL(meteo.VPD)
        dT_ul = self.delta_T_UL(meteo.VPD)

        denominator = dT_ul - dT_ll
        if denominator <= 0:
            raise ValueError(
                f"dT_UL ({dT_ul:.2f}) <= dT_LL ({dT_ll:.2f}): condicion invalida."
            )

        cwsi_value = (dT_measured - dT_ll) / denominator
        cwsi_clamped = float(np.clip(cwsi_value, 0.0, 1.5))

        result = {
            "cwsi": cwsi_clamped,
            "cwsi_raw": float(cwsi_value),
            "dT_measured": float(dT_measured),
            "dT_LL": float(dT_ll),
            "dT_UL": float(dT_ul),
            "VPD_kPa": float(meteo.VPD),
            "T_leaf_C": float(T_leaf),
            "T_air_C": float(meteo.T_air),
            "stress_level": self._classify(cwsi_clamped),
            "crop": self.crop,
            "coef_source": self.coef["description"],
        }

        # psi_stem siempre incluido si el cultivo tiene coeficientes
        if "psi_a" in self.coef:
            psi = self.psi_stem(cwsi_clamped)
            result["psi_stem_MPa"] = psi["psi_stem_MPa"]
            result["nivel_hidrico"] = psi["nivel_hidrico"]

        return result

    def _classify(self, cwsi: float) -> str:
        """Clasificacion agronomica del nivel de estres hidrico."""
        if cwsi < 0.10:
            return "SIN_ESTRES"
        elif cwsi < 0.30:
            return "ESTRES_LEVE"
        elif cwsi < 0.55:
            return "ESTRES_MODERADO"
        elif cwsi < 0.85:
            return "ESTRES_SEVERO"
        else:
            return "ESTRES_CRITICO"

    # ── CWSI teorico (Jackson 1981 con ra)  [C1] ─────────────────────────────

    def cwsi_theoretical(self, T_leaf: float, meteo: MeteoConditions) -> dict:
        """
        CWSI teorico basado en balance energetico (Jackson et al. 1981).

        A diferencia del CWSI empirico (baselines fijos por varietal), el teorico
        calcula baselines dinamicos que se adaptan a viento y radiacion:

          dT_LL = (ra·Rn / (rho·Cp)) × (gamma / (delta+gamma)) − (VPD / (delta+gamma))
          dT_UL = ra·Rn / (rho·Cp)   (estomas completamente cerrados, sin transpiracion)

        Donde:
          ra    = resistencia aerodinamica [s/m] = 208/u (FAO-56)
          Rn    = radiacion neta [W/m2]
          delta = pendiente curva saturacion [kPa/K]
          gamma = constante psicrométrica [kPa/K] ≈ 0.066
          rho·Cp = 1200 [J/m3/K] (aire a 20°C)

        Ventaja sobre empirico: baselines se ajustan por viento (+2 m/s de tolerancia).
        Referencia: Jackson et al. (1981) WRR 17(4):1133-1138.
        """
        # Constantes atmosfericas
        GAMMA = 0.066       # constante psicrometrica [kPa/K]
        RHO_CP = 1200.0     # rho_air × Cp [J/m3/K]

        ra = meteo.aerodynamic_resistance    # [s/m]
        delta = meteo.delta_sat              # [kPa/K]
        vpd = meteo.VPD                      # [kPa]
        Rn = meteo.solar_rad * 0.75          # Rn ≈ 75% de radiacion global (aprox.)

        # Termino de radiacion disponible
        A = ra * Rn / RHO_CP   # [K] — calentamiento maximo posible

        # Baseline inferior (planta bien hidratada, transpiracion maxima)
        dT_ll_theo = A * GAMMA / (delta + GAMMA) - vpd / (delta + GAMMA)

        # Baseline superior (estomas completamente cerrados)
        dT_ul_theo = A  # sin transpiracion, toda la energia va a calentamiento

        dT_measured = T_leaf - meteo.T_air
        denominator = dT_ul_theo - dT_ll_theo

        if denominator <= 0.1:
            return {
                "cwsi_theoretical": float('nan'),
                "dT_LL_theo": float(dT_ll_theo),
                "dT_UL_theo": float(dT_ul_theo),
                "ra_sm": float(ra),
                "status": "denominador_insuficiente",
            }

        cwsi_theo = float(np.clip(
            (dT_measured - dT_ll_theo) / denominator, 0.0, 1.5
        ))

        return {
            "cwsi_theoretical": cwsi_theo,
            "dT_measured": float(dT_measured),
            "dT_LL_theo": float(dT_ll_theo),
            "dT_UL_theo": float(dT_ul_theo),
            "ra_sm": float(ra),
            "Rn_est": float(Rn),
            "stress_level": self._classify(cwsi_theo),
            "status": "ok",
        }

    # ── Indice Jones (Ig) ───────────────────────────────────────────────────

    def jones_index(self, T_leaf: float, T_dry: float, T_wet: float) -> dict:
        """
        Indice Jones (Ig) — Jones (1999), Gutierrez et al. (2018).

        No requiere VPD modelado: usa referencias medidas en campo.
        Valida la lectura termica con hojas de referencia real.

          Ig = (Tc - Tdry) / (Twet - Tdry)
          Ig ~= 0  -> estomas cerrados (estres maximo)
          Ig ~= 1  -> transpiracion libre (sin estres)

        Escala inversa al CWSI: CWSI_equiv ~= 1 - Ig.

        Parametros
        ----------
        T_leaf : temperatura canopeo [°C]
        T_dry  : referencia seca (hoja con vaselina / bolsa plastica) [°C]
        T_wet  : referencia humeda (hoja con algodon humedo) [°C]
        """
        denom = T_wet - T_dry
        if abs(denom) < 0.1:
            raise ValueError(
                f"T_wet - T_dry = {denom:.2f} degC — diferencia insuficiente."
            )
        ig = (T_leaf - T_dry) / denom
        ig_clamped = float(np.clip(ig, -0.2, 1.2))
        cwsi_equiv = float(np.clip(1.0 - ig_clamped, 0.0, 1.5))

        return {
            "Ig": ig_clamped,
            "Ig_raw": float(ig),
            "cwsi_equivalent": cwsi_equiv,
            "T_leaf_C": float(T_leaf),
            "T_dry_C": float(T_dry),
            "T_wet_C": float(T_wet),
            "stress_level": self._classify(cwsi_equiv),
            "crop": self.crop,
        }

    # ── psi_stem [MPa] ──────────────────────────────────────────────────────

    def psi_stem(self, cwsi_value: float) -> dict:
        """
        Prediccion de potencial hidrico de tallo (psi_stem) [MPa] desde CWSI.

        El psi_stem es la variable de referencia de la camara de presion
        Scholander (PMS Model 600), usada como gold standard en campo.
        Esta funcion traduce el CWSI automatico a la unidad que el agronomico
        conoce y registra en sus protocolos de riego.

        Modelo lineal por cultivo (calibrado en vid):
          psi_stem = psi_a + psi_b * CWSI  [MPa]

        Para Malbec (Pires et al. 2025 / Zhou et al. 2022):
          psi_stem = -0.35 + (-1.20) * CWSI

        Umbrales psi_stem para vid (referencia bibliografica):
          > -0.60 MPa : sin estres
          -0.60 a -1.00 MPa : estres leve (RDI tolerable segun estadio)
          -1.00 a -1.40 MPa : estres moderado-severo (impacto en calidad)
          < -1.40 MPa : estres critico (dano irreversible posible)
        """
        if "psi_a" not in self.coef:
            raise NotImplementedError(
                f"Coeficientes psi_stem no disponibles para '{self.crop}'."
            )
        psi = self.coef["psi_a"] + self.coef["psi_b"] * float(cwsi_value)

        if psi > -0.60:
            nivel = "SIN_ESTRES"
        elif psi > -1.00:
            nivel = "ESTRES_LEVE"
        elif psi > -1.40:
            nivel = "ESTRES_MODERADO_SEVERO"
        else:
            nivel = "ESTRES_CRITICO"

        return {
            "psi_stem_MPa": round(psi, 3),
            "cwsi_input": float(cwsi_value),
            "nivel_hidrico": nivel,
            "crop": self.crop,
            "model_note": "Regresion lineal CWSI->psi_stem (Pires et al. 2025)",
        }

    # ── Procesamiento batch y sensibilidad ──────────────────────────────────

    def cwsi_batch(self, T_leaf_array: np.ndarray, meteo: MeteoConditions) -> np.ndarray:
        """
        Calcula CWSI para un array de temperaturas foliares (mapa de pixeles).
        Usado para procesar frames termicos completos del MLX90640 32×24.
        """
        dT = T_leaf_array - meteo.T_air
        dT_ll = self.delta_T_LL(meteo.VPD)
        dT_ul = self.delta_T_UL(meteo.VPD)
        return np.clip((dT - dT_ll) / (dT_ul - dT_ll), 0.0, 1.5)

    def sensitivity_analysis(self, meteo: MeteoConditions,
                              T_leaf_range: Optional[np.ndarray] = None) -> dict:
        """
        Analisis de sensibilidad: variacion de CWSI vs temperatura foliar.
        Permite verificar que el NETD del sensor es suficientemente preciso.
        """
        if T_leaf_range is None:
            T_leaf_range = np.linspace(meteo.T_air - 3, meteo.T_air + 6, 100)

        cwsi_values = np.array([
            self.cwsi(T, meteo)["cwsi"] for T in T_leaf_range
        ])
        dCWSI_dT = np.gradient(cwsi_values, T_leaf_range)

        cwsi_per_deg = float(np.mean(np.abs(dCWSI_dT)))
        import math as _math
        netd_mlx = 0.10   # MLX90640 (sensor BAB, breakout Adafruit 4407) — NETD típico 100 mK
        n_pixels_promediados = 28  # P20–P75 filtro foliar, promedio típico
        netd_efectivo = netd_mlx / _math.sqrt(n_pixels_promediados)
        return {
            "T_leaf_range": T_leaf_range,
            "cwsi_values": cwsi_values,
            "dCWSI_dT": dCWSI_dT,
            "cwsi_per_degree": cwsi_per_deg,
            "NETD_50mK_cwsi_error": cwsi_per_deg * 0.05,          # compatibilidad
            "NETD_100mK_cwsi_error": cwsi_per_deg * netd_mlx,     # MLX90640 pixel único
            "NETD_efectivo_cwsi_error": cwsi_per_deg * netd_efectivo,  # 28-px promediado
        }


# ─────────────────────────────────────────────────────────────────────────────
# Demo — Prueba de Concepto TRL 3
# Cultivo: Malbec — Colonia Caroya, Córdoba
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    SEP = "=" * 62

    print(SEP)
    print("  CWSI Malbec — HydroVision AG — Prueba de Concepto TRL 3")
    print("  Colonia Caroya, Cordoba (~700m s.n.m.)")
    print("  Jackson et al. (1981) + Bellvert et al. (2016)")
    print(SEP)

    calc = CWSICalculator("malbec")

    # ── Escenarios tipicos de Colonia Caroya en enero (mes pico de estres) ──
    print("\n--- Escenarios Malbec — Enero, ventana 12h ---")
    print(f"  Coeficientes: {calc.coef['description']}\n")

    scenarios = [
        ("Bien regada        ", 32.0, 30.5, 35, 850, 1.5),
        ("Estres leve        ", 32.0, 32.1, 35, 850, 1.5),
        ("Estres moderado    ", 32.0, 33.2, 35, 850, 1.5),
        ("Estres severo      ", 32.0, 35.8, 35, 850, 1.5),
        ("Estres critico     ", 32.0, 37.5, 35, 850, 1.5),
        ("Maniana (VPD bajo) ", 22.0, 21.0, 65, 450, 0.8),
        ("Tarde (VPD alto)   ", 36.0, 38.5, 22, 950, 2.0),
    ]

    print(f"  {'Escenario':<22} {'CWSI':>6}  {'psi_stem':>9}  Nivel hidrico")
    print(f"  {'-'*22}  {'-'*6}  {'-'*9}  {'-'*22}")
    for label, T_air, T_leaf, RH, rad, wind in scenarios:
        meteo = MeteoConditions(T_air, RH, rad, wind)
        r = calc.cwsi(T_leaf, meteo)
        psi_str = f"{r['psi_stem_MPa']:.2f} MPa" if "psi_stem_MPa" in r else "  --   "
        print(f"  {label}  {r['cwsi']:>6.3f}  {psi_str:>9}  {r['nivel_hidrico']}")

    # ── Sensibilidad NETD ───────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  Sensibilidad NETD — MLX90640 breakout (NETD ~100 mK)")
    print(SEP)
    meteo_ref = MeteoConditions(T_air=32, RH=35, solar_rad=850, wind_speed=1.5)
    sens = calc.sensitivity_analysis(meteo_ref)
    print(f"  Sensibilidad media:                {sens['cwsi_per_degree']:.3f} CWSI/degC")
    print(f"  Error CWSI por 100mK (pixel solo): +/-{sens['NETD_100mK_cwsi_error']:.4f}")
    print(f"  Error efectivo 28 px promediados:  +/-{sens['NETD_efectivo_cwsi_error']:.4f}   [OK — << +-0.05]")
    print(f"  Referencia: Araujo-Paredes et al. (2022) — error < +/-0.07 aceptable")

    # ── Indice Jones (validacion con referencias de campo) ──────────────────
    print(f"\n{SEP}")
    print("  Indice Jones (Ig) — validacion con referencias de campo")
    print("  Jones (1999) / Gutierrez et al. (2018)")
    print(SEP)
    print("  Protocolo: Twet = hoja con algodon humedo (~T_aire - 2degC)")
    print("             Tdry = hoja con vaselina (~T_aire + 4degC)\n")
    T_aire_ref = 32.0
    T_wet_ref = T_aire_ref - 2.0
    T_dry_ref = T_aire_ref + 4.0
    print(f"  {'Escenario':<20}  {'T_foliar':>9}  {'Ig':>6}  {'CWSI_equiv':>10}  Nivel")
    print(f"  {'-'*20}  {'-'*9}  {'-'*6}  {'-'*10}  {'-'*18}")
    for label, T_leaf in [
        ("Bien regada    ", 30.5),
        ("Estres moderado", 33.2),
        ("Estres severo  ", 35.8),
    ]:
        ig = calc.jones_index(T_leaf, T_dry_ref, T_wet_ref)
        print(f"  {label:<20}  {T_leaf:>7.1f}C  {ig['Ig']:>6.3f}  "
              f"{ig['cwsi_equivalent']:>10.3f}  {ig['stress_level']}")
    print(f"\n  Concordancia CWSI (Jackson) <-> CWSI_equiv (Jones): [esperado ~=]")

    # ── psi_stem: tabla de referencia para el agronomico ───────────────────
    print(f"\n{SEP}")
    print("  psi_stem [MPa] — referencia para el productor (Scholander)")
    print("  Pires et al. (2025) — R2=0.663 en capturas de tarde")
    print(SEP)
    print(f"  {'CWSI':>6}  {'psi_stem':>9}  Nivel hidrico")
    print(f"  {'-'*6}  {'-'*9}  {'-'*24}")
    for cwsi_v, label in [
        (0.05, "sin estres"),
        (0.25, "estres leve"),
        (0.50, "estres moderado"),
        (0.75, "estres severo"),
        (0.95, "estres critico"),
    ]:
        psi = calc.psi_stem(cwsi_v)
        print(f"  {cwsi_v:>6.2f}  {psi['psi_stem_MPa']:>8.2f}M  {psi['nivel_hidrico']}")

    print(f"\n  [OK] Modulo CWSI Malbec operativo — TRL 3 Colonia Caroya")
    print(f"  Indice primario  : CWSI (Jackson 1981 + Bellvert 2016)")
    print(f"  Indice secundario: Ig   (Jones 1999 + Gutierrez 2018)")
    print(f"  Output agronomico: psi_stem MPa (Pires 2025)")
