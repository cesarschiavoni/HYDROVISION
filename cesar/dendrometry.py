"""
Dendrometria — Micro-contracciones del Tronco (MDS)
Prueba de Concepto TRL 3 — HydroVision AG — Colonia Caroya, Córdoba

Cultivo de validacion: Vid Malbec (Vitis vinifera cv. Malbec)
Sitio de referencia:   Colonia Caroya, Sierras Chicas, Cordoba (~700m s.n.m.)

La dendrometria mide la variacion diaria del diametro del tronco con un
extensometro lineal (strain gauge + ADS1231 ADC, resolucion 1 um).
El maximo enogimiento diario (MDS = Maximum Daily Shrinkage) es un
indicador fisiologico directo del estado hidrico interno de la planta,
correlacionado con el potencial hidrico de tallo (psi_stem) medido con
camara Scholander.

Principio biofisico:
  Durante el dia la planta pierde agua por transpiracion -> el floema y
  cambium se retraen -> D_min (minimo diario del diametro).
  Durante la noche la planta recarga desde el suelo -> D_max (maximo).
  MDS = D_max - D_min  [micrometros, um]
  A mayor MDS -> mayor deficit interno -> mayor estres hidrico.

Ventaja sobre CWSI termico:
  - Sennal continua 24/7 (no requiere ventana solar)
  - Correlacion directa con psi_stem (R2 0.80-0.92 vs R2 0.62-0.67 termico)
  - Insensible a condiciones meteorologicas de superficie
  - Detecta recuperacion nocturna: planta que no recupera -> dano acumulado

Limitacion:
  - Medicion puntual (un sensor por fila; no espacial como termico)
  - Requiere calibracion por individuo (variabilidad inter-planta ~15%)
  - Temperatura del tronco afecta la dilatacion termica del extensometro

Referencias principales:
  Fernandez, J.E. & Cuevas, M.V. (2010).
    Irrigation scheduling from stem diameter variations: A review.
    Agricultural and Forest Meteorology, 150(2), 135-151.
    [Revision global MDS-psi_stem; R2 0.80-0.92 en vid]

  Ortuno, M.F. et al. (2010).
    Stem and leaf water potentials, gas exchange, sap flow and trunk diameter
    fluctuations for detecting water stress in lemon trees.
    Trees, 24(4), 641-648.
    [Validacion MDS en citricos; metodologia extensometro]

  Naor, A. (2000).
    Midday stem water potential as a plant water stress indicator in
    grapevines. Acta Horticulturae, 526, 498-506.
    [Umbrales de psi_stem para distintos estadios en vid]

  Perez-Lopez, D. et al. (2008).
    Use of stem diameter variations to assess the hydric status in young
    olive trees. Agricultural Water Management, 95(2), 214-224.
    [Metodologia de correccion termica del extensometro]

  Fernandez, J.E. et al. (2011).
    Combining measurements of stem-water potential and trunk diameter
    variations as indicators of tree water status.
    Irrigation Science, 29(4), 297-305.
    [Fusion de senales; referencia base para combined_stress_index.py]
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, time


# ─────────────────────────────────────────────────────────────────────────────
# CULTIVO DE VALIDACION TRL 3: MALBEC
# Coeficientes MDS -> psi_stem calibrados para vid tinta mediterranea.
# Umbrales MDS del Protocolo de Riego Diferencial — Colonia Caroya.
#
# Modelo: psi_stem = psi_a + psi_b * MDS  [MPa]
# Referencia base: Fernandez & Cuevas (2010), Naor (2000)
# Calibracion sitio: Colonia Caroya (~700m, clima semiarido continental)
# ─────────────────────────────────────────────────────────────────────────────
DENDROMETRY_COEFFICIENTS = {
    "malbec": {
        # ── Regresion lineal MDS -> psi_stem ────────────────────────────────
        # psi_stem = psi_a + psi_b * MDS
        # Intercept: planta sin contraccion -> bien hidratada (-0.15 MPa)
        # Pendiente: cada um de MDS representa degradacion de 0.008 MPa
        "psi_a": -0.15,       # MPa — psi_stem base (MDS=0)
        "psi_b": -0.0080,     # MPa/um — pendiente; Fernandez & Cuevas (2010)
        # ── Umbrales MDS para Protocolo de Riego HydroVision AG ─────────────
        # Basados en Naor (2000) y calibrados para condiciones Colonia Caroya
        "mds_ref_unstressed": 60.0,   # um — referencia sin estres (bien regada)
        "mds_trigger":       150.0,   # um — estres leve: iniciar monitoreo extra
        "mds_severe":        280.0,   # um — estres severo: reducir intervalo riego
        "mds_critical":      400.0,   # um — estres critico: protocolo de rescate
        # ── Correccion termica del extensometro ──────────────────────────────
        # El sensor mecanico se dilata con temperatura del tronco.
        # Correccion: MDS_corr = MDS_raw - alpha * Delta_T_tronco
        # alpha estimado para sensor inox en tronco de vid (Perez-Lopez 2008)
        "thermal_alpha_um_per_C": 2.5,   # um/C — coeficiente expansion termica sensor
        # ── Tasa de recuperacion nocturna ───────────────────────────────────
        # Tronco debe recuperar >= 80% de la contraccion antes del amanecer.
        # Por debajo: estres acumulado (dano potencial en raices o xilema).
        "recovery_min_fraction": 0.80,   # fraccion minima de recuperacion
        "description": "Vid Malbec — Fernandez & Cuevas (2010) + Naor (2000)",
    },
}

# Registro escalable — permite agregar nuevos cultivos sin modificar el motor
_FUTURE_CROPS_DENDRO = {
    "cabernet_sauvignon": {
        # Interpolado desde Fernandez & Cuevas (2010) — variedad similar
        "psi_a": -0.15, "psi_b": -0.0082,
        "mds_ref_unstressed": 55.0, "mds_trigger": 145.0,
        "mds_severe": 270.0, "mds_critical": 390.0,
        "thermal_alpha_um_per_C": 2.5,
        "recovery_min_fraction": 0.80,
        "description": "Vid Cabernet Sauvignon — interpolado Fernandez 2010",
    },
    "olive": {
        # Perez-Lopez et al. (2008) — olivo joven, clima semiarido
        "psi_a": -0.20, "psi_b": -0.0060,
        "mds_ref_unstressed": 80.0, "mds_trigger": 200.0,
        "mds_severe": 380.0, "mds_critical": 550.0,
        "thermal_alpha_um_per_C": 2.8,
        "recovery_min_fraction": 0.75,
        "description": "Olivo — Perez-Lopez et al. (2008) Agr. Water Mgmt.",
    },
}

DENDRO_COEFFICIENTS: dict = {"malbec": DENDROMETRY_COEFFICIENTS["malbec"],
                              **_FUTURE_CROPS_DENDRO}


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES — Estructura de datos del extensometro
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TrunkDiameterReading:
    """
    Lectura individual del extensometro de tronco.

    El sensor ADS1231 (24-bit ADC) resuelve ~1 um por paso.
    La temperatura del tronco es necesaria para correccion termica.
    """
    timestamp: datetime           # Fecha y hora de la lectura
    diameter_um: float            # Diametro del tronco [micrometros, um]
    temperature_c: float          # Temperatura superficial del tronco [degC]
    sensor_id: str = "D01"        # Identificador del extensometro en campo


@dataclass
class DailyDendrometryResult:
    """
    Resultado del analisis dendrometrico diario.

    Calculado a partir de lecturas continuas (tipicamente 15-min interval).
    El MDS es el indicador principal de estres hidrico.
    """
    date: str                          # Fecha analizada (YYYY-MM-DD)
    d_max_um: float                    # Diametro maximo del dia [um]
    d_min_um: float                    # Diametro minimo del dia [um]
    mds_raw_um: float                  # MDS sin correccion termica [um]
    mds_corrected_um: float            # MDS con correccion termica [um]
    delta_T_trunk_c: float             # Variacion termica del tronco en el dia [degC]
    psi_stem_mpa: float                # Potencial hidrico de tallo estimado [MPa]
    recovery_rate: float               # Fraccion de recuperacion nocturna [0-1]
    stress_level: str                  # Clasificacion agronomica del estres
    alert: str                         # Mensaje de alerta para el operario
    rescue_required: bool              # True si requiere riego de emergencia
    sensor_id: str = "D01"            # ID del extensometro
    crop: str = "malbec"              # Cultivo analizado
    n_readings: int = 0               # Numero de lecturas usadas
    coef_source: str = ""             # Referencia bibliografica de coeficientes


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DENDROMETRICO
# ─────────────────────────────────────────────────────────────────────────────

class DendrometryEngine:
    """
    Motor de analisis dendrometrico para vid Malbec — TRL 3.

    Procesa lecturas continuas del extensometro de tronco y calcula:
      - MDS diario (con correccion termica)
      - psi_stem estimado
      - Tasa de recuperacion nocturna
      - Clasificacion agronomica del estres
      - Alerta y flag de rescate para el protocolo de riego

    El motor es parte del nodo HSI (HydroVision Stress Index):
      combined_stress_index.py fusiona MDS (65%) con CWSI termico (35%).
    """

    # Umbral de rescate hidrico — Protocolo HydroVision AG
    # Alineado con cwsi_formula.py: mismo threshold que el modulo termico
    RESCUE_THRESHOLD_MPa = -1.5

    def __init__(self, crop: str = "malbec"):
        if crop not in DENDRO_COEFFICIENTS:
            raise ValueError(
                f"Cultivo '{crop}' no reconocido. "
                f"Opciones: {list(DENDRO_COEFFICIENTS)}"
            )
        self.crop = crop
        self.coef = DENDRO_COEFFICIENTS[crop]

    # ── MDS y correccion termica ───────────────────────────────────────────

    def mds(self, readings: List[TrunkDiameterReading]) -> dict:
        """
        Calcula el MDS (Maximum Daily Shrinkage) desde lecturas del dia.

        MDS = D_max - D_min  [um]
        Incluye correccion termica para eliminar expansion del sensor.

        Parametros
        ----------
        readings : lista de lecturas del dia (minimo 6 horas de cobertura)

        Retorna dict con MDS raw, corregido, D_max, D_min y delta_T.
        """
        if len(readings) < 4:
            raise ValueError(
                f"Se necesitan al menos 4 lecturas para calcular MDS. "
                f"Recibidas: {len(readings)}"
            )

        diameters = np.array([r.diameter_um for r in readings])
        temps = np.array([r.temperature_c for r in readings])

        d_max = float(np.max(diameters))
        d_min = float(np.min(diameters))
        mds_raw = d_max - d_min

        # Correccion termica: elimina expansion del sensor por calor del tronco
        # MDS_corr = MDS_raw - alpha * (T_max_tronco - T_min_tronco)
        delta_T = float(np.max(temps) - np.min(temps))
        alpha = self.coef["thermal_alpha_um_per_C"]
        mds_corrected = max(0.0, mds_raw - alpha * delta_T)

        return {
            "d_max_um": d_max,
            "d_min_um": d_min,
            "mds_raw_um": float(mds_raw),
            "mds_corrected_um": float(mds_corrected),
            "delta_T_trunk_c": delta_T,
            "n_readings": len(readings),
            "crop": self.crop,
        }

    def psi_stem_from_mds(self, mds_um: float) -> float:
        """
        Estima el potencial hidrico de tallo [MPa] desde el MDS corregido.

        Modelo lineal: psi_stem = psi_a + psi_b * MDS
        Referencia: Fernandez & Cuevas (2010) — R2 0.80-0.92

        Parametros
        ----------
        mds_um : MDS corregido [micrometros]

        Retorna psi_stem [MPa] (negativo: mayor negatividad = mayor estres).
        """
        psi = self.coef["psi_a"] + self.coef["psi_b"] * mds_um
        return round(float(psi), 3)

    # ── Tasa de recuperacion nocturna ─────────────────────────────────────

    def recovery_rate(self,
                      readings_night: List[TrunkDiameterReading],
                      d_min_prev_day: float,
                      d_max_prev_day: float) -> float:
        """
        Calcula la fraccion de recuperacion nocturna del tronco.

        recovery = (D_amanecer - D_min_dia) / (D_max_dia - D_min_dia)

        Una planta bien hidratada recupera >= 80% antes del amanecer.
        Recuperacion < 80% indica deficit acumulado o dano en raices.

        Parametros
        ----------
        readings_night   : lecturas nocturnas (tipicamente 22h-06h)
        d_min_prev_day   : D_min del dia anterior [um]
        d_max_prev_day   : D_max del dia anterior [um]

        Retorna fraccion [0-1] (puede superar 1 si la planta sobrerecupera).
        """
        if not readings_night:
            return float("nan")

        mds_day = d_max_prev_day - d_min_prev_day
        if mds_day < 1.0:
            return 1.0  # Sin contraccion -> recuperacion completa por definicion

        d_dawn = float(np.max([r.diameter_um for r in readings_night]))
        recovery = (d_dawn - d_min_prev_day) / mds_day
        return round(float(np.clip(recovery, 0.0, 1.5)), 3)

    # ── Clasificacion agronomica ───────────────────────────────────────────

    def classify(self, mds_um: float) -> tuple:
        """
        Clasifica el nivel de estres y genera alerta para el operario.

        Parametros
        ----------
        mds_um : MDS corregido [um]

        Retorna (stress_level: str, alert: str, rescue_required: bool)
        """
        c = self.coef
        psi = self.psi_stem_from_mds(mds_um)
        rescue = psi <= self.RESCUE_THRESHOLD_MPa

        if mds_um < c["mds_ref_unstressed"]:
            level = "SIN_ESTRES"
            alert = "Estado hidrico optimo. Sin accion requerida."
        elif mds_um < c["mds_trigger"]:
            level = "ESTRES_LEVE"
            alert = "Estres leve detectado. Monitorear evolucion."
        elif mds_um < c["mds_severe"]:
            level = "ESTRES_MODERADO"
            alert = "Estres moderado. Revisar plan de riego."
        elif mds_um < c["mds_critical"]:
            level = "ESTRES_SEVERO"
            alert = "ESTRES SEVERO — Reducir intervalo de riego."
        else:
            level = "ESTRES_CRITICO"
            alert = "ESTRES CRITICO — Riego inmediato recomendado."

        if rescue:
            alert = f"[RESCATE] psi_stem={psi:.2f}MPa < {self.RESCUE_THRESHOLD_MPa}MPa. " \
                    f"RIEGO DE EMERGENCIA — suspender protocolo experimental."

        return level, alert, rescue

    # ── Analisis diario completo ───────────────────────────────────────────

    def analyze_day(self,
                    date: str,
                    readings_day: List[TrunkDiameterReading],
                    readings_night: Optional[List[TrunkDiameterReading]] = None,
                    d_min_prev: Optional[float] = None,
                    d_max_prev: Optional[float] = None) -> DailyDendrometryResult:
        """
        Analisis dendrometrico completo para un dia de monitoreo.

        Parametros
        ----------
        date          : fecha en formato YYYY-MM-DD
        readings_day  : lecturas del dia completo (al menos 8h de cobertura)
        readings_night: lecturas nocturnas para calcular recuperacion (opcional)
        d_min_prev    : D_min del dia anterior [um] (para recovery_rate)
        d_max_prev    : D_max del dia anterior [um] (para recovery_rate)

        Retorna DailyDendrometryResult con todos los indicadores calculados.
        """
        # MDS del dia
        mds_result = self.mds(readings_day)
        mds_corr = mds_result["mds_corrected_um"]

        # psi_stem estimado
        psi = self.psi_stem_from_mds(mds_corr)

        # Recuperacion nocturna
        if readings_night and d_min_prev is not None and d_max_prev is not None:
            rec = self.recovery_rate(readings_night, d_min_prev, d_max_prev)
        else:
            rec = float("nan")

        # Clasificacion y alerta
        level, alert, rescue = self.classify(mds_corr)

        # Alerta adicional por baja recuperacion nocturna
        if not np.isnan(rec) and rec < self.coef["recovery_min_fraction"] and not rescue:
            alert += (f" Recuperacion nocturna baja ({rec:.0%} < "
                      f"{self.coef['recovery_min_fraction']:.0%}): "
                      f"posible deficit acumulado.")

        return DailyDendrometryResult(
            date=date,
            d_max_um=mds_result["d_max_um"],
            d_min_um=mds_result["d_min_um"],
            mds_raw_um=mds_result["mds_raw_um"],
            mds_corrected_um=mds_corr,
            delta_T_trunk_c=mds_result["delta_T_trunk_c"],
            psi_stem_mpa=psi,
            recovery_rate=rec,
            stress_level=level,
            alert=alert,
            rescue_required=rescue,
            sensor_id=readings_day[0].sensor_id,
            crop=self.crop,
            n_readings=mds_result["n_readings"],
            coef_source=self.coef["description"],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Demo — Prueba de Concepto TRL 3
# Cultivo: Malbec — Colonia Caroya, Cordoba
# Escenarios: 4 zonas del viñedo experimental (A=control, B=leve, C=moderado, E=sin riego)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from datetime import datetime

    SEP = "=" * 66

    print(SEP)
    print("  Dendrometria Malbec — HydroVision AG — Prueba de Concepto TRL 3")
    print("  Colonia Caroya, Cordoba (~700m s.n.m.)")
    print("  Fernandez & Cuevas (2010) + Naor (2000)")
    print(SEP)

    engine = DendrometryEngine("malbec")

    # ── Escenarios tipicos de las zonas del viñedo experimental ─────────────
    # Cada escenario simula un dia de enero (mes pico de estres)
    # El extensometro mide cada 15 minutos -> ~96 lecturas/dia
    # Aqui simulamos con perfil simplificado de 8 lecturas horarias

    def make_readings(sensor_id: str,
                      d_dawn: float,      # diametro al amanecer [um]
                      d_max: float,       # diametro maximo (maniana) [um]
                      d_min: float,       # diametro minimo (tarde) [um]
                      T_min_c: float,     # temperatura tronco minima [degC]
                      T_max_c: float,     # temperatura tronco maxima [degC]
                      ) -> List[TrunkDiameterReading]:
        """Genera perfil diario simplificado (6h-22h, 8 lecturas horarias)."""
        hours = [6, 8, 10, 12, 14, 16, 18, 20]
        # Perfil de diametro: crece maniana, cae tarde, sube al anochecer
        diams = [d_dawn, d_max, d_max * 0.998, d_max * 0.995,
                 d_min, d_min * 1.001, d_min * 1.004, d_min * 1.010]
        temps = np.linspace(T_min_c, T_max_c, 8)
        return [
            TrunkDiameterReading(
                timestamp=datetime(2026, 1, 15, h, 0),
                diameter_um=d,
                temperature_c=float(t),
                sensor_id=sensor_id,
            )
            for h, d, t in zip(hours, diams, temps)
        ]

    print(f"\n  Coeficientes: {engine.coef['description']}")
    print(f"  Umbral de rescate: psi_stem < {engine.RESCUE_THRESHOLD_MPa} MPa\n")

    scenarios = [
        # (zona, descripcion, d_dawn, d_max, d_min, T_min, T_max)
        ("A", "Control (riego normal)   ", 25400.0, 25400.0, 25340.0, 20.0, 32.0),
        ("B", "Estres leve (RDI 50%)    ", 25400.0, 25400.0, 25230.0, 20.0, 36.0),
        ("C", "Estres moderado (RDI 25%)", 25400.0, 25400.0, 25100.0, 20.0, 39.0),
        ("E", "Sin riego (enero)        ", 25400.0, 25400.0, 24960.0, 20.0, 42.0),
    ]

    print(f"  {'Zona':<3}  {'Descripcion':<28}  {'MDS':>7}  "
          f"{'MDS_corr':>9}  {'psi_stem':>9}  Nivel")
    print(f"  {'-'*3}  {'-'*28}  {'-'*7}  {'-'*9}  {'-'*9}  {'-'*22}")

    for zona, desc, d_dawn, d_max, d_min, T_min, T_max in scenarios:
        readings = make_readings(f"D0{zona}", d_dawn, d_max, d_min, T_min, T_max)
        result = engine.analyze_day("2026-01-15", readings)
        psi_str = f"{result.psi_stem_mpa:.2f} MPa"
        rescue_flag = " [RESCATE]" if result.rescue_required else ""
        print(f"  {zona:<3}  {desc}  "
              f"{result.mds_raw_um:>7.1f}  "
              f"{result.mds_corrected_um:>9.1f}  "
              f"{psi_str:>9}  "
              f"{result.stress_level}{rescue_flag}")

    # ── Tabla de referencia MDS -> psi_stem ──────────────────────────────────
    print(f"\n{SEP}")
    print("  Referencia MDS -> psi_stem [MPa]")
    print("  Fernandez & Cuevas (2010) — R2 = 0.80-0.92 en vid")
    print(SEP)
    print(f"  {'MDS [um]':>9}  {'psi_stem':>9}  Nivel hidrico")
    print(f"  {'-'*9}  {'-'*9}  {'-'*26}")
    for mds_val in [40, 80, 150, 220, 280, 350, 420]:
        psi = engine.psi_stem_from_mds(mds_val)
        level, _, _ = engine.classify(mds_val)
        print(f"  {mds_val:>9}  {psi:>8.2f}M  {level}")

    # ── Recuperacion nocturna ─────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  Recuperacion nocturna — Diagnostico de estres acumulado")
    print("  Umbral minimo: 80% antes del amanecer (Fernandez 2010)")
    print(SEP)
    # Simular lecturas nocturnas de la zona C (estres moderado)
    night_readings = [
        TrunkDiameterReading(datetime(2026, 1, 16, h, 0), 25100.0 + i * 18.0, 22.0, "D0C")
        for i, h in enumerate([22, 23, 0, 2, 4, 5])
    ]
    rec = engine.recovery_rate(night_readings, d_min_prev_day=25100.0, d_max_prev_day=25400.0)
    print(f"  Zona C — Recuperacion nocturna: {rec:.1%}  "
          f"({'OK' if rec >= engine.coef['recovery_min_fraction'] else 'BAJA — deficit acumulado'})")
    print(f"  D_min dia anterior: 25100.0 um | D_amanecer: {25100.0 + 5*18.0:.1f} um")

    print(f"\n  [OK] Modulo Dendrometria Malbec operativo — TRL 3 Colonia Caroya")
    print(f"  MDS primario con correccion termica (Perez-Lopez 2008)")
    print(f"  psi_stem estimado: R2 0.80-0.92 (Fernandez & Cuevas 2010)")
    print(f"  Fusion con CWSI termico: ver combined_stress_index.py")
