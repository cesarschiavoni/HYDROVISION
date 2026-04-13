"""
Motor de Alertas Agronomicas — HydroVision AG
Reglas basadas en datos del nodo (temperatura, HR, viento, CWSI, GDD, lluvia, PM2.5).
12+ tipos de alerta para cultivos de alto valor.

Cada regla recibe un dict con los datos del ultimo ciclo del nodo y el estado
acumulado (GDD, estadio fenologico, historial reciente). Retorna una lista de
Alert con severidad, mensaje y canal sugerido.

Integracion: Cesar conecta estas reglas al backend MVC (FastAPI) en Mes 7-10.
Las alertas se persisten en PostgreSQL y se exponen via GET /api/alertas/{nodo_id}.

Referencia umbrales:
  - Helada: Snyder & Melo-Abreu (2005), FAO Frost Protection.
  - Botrytis: Ciliberti et al. (2015), EPPO.
  - Mildiu: Gessler et al. (2011), Phytopathology.
  - CWSI umbrales: Jackson et al. (1981), Bellvert et al. (2016).
  - PHI: SENASA Argentina — periodos de carencia por principio activo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import datetime


# ─────────────────────────────────────────────────────────────────
# Tipos
# ─────────────────────────────────────────────────────────────────

class Severidad(Enum):
    INFO = "info"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Canal(Enum):
    """Canal de entrega sugerido (el productor configura en TRL 5)."""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    LOG = "log"  # solo persistir en DB, sin notificacion


@dataclass
class Alerta:
    tipo: str
    severidad: Severidad
    mensaje: str
    canal: Canal = Canal.LOG
    nodo_id: str = ""
    ts: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class EstadoNodo:
    """Estado acumulado del nodo — se mantiene entre ciclos."""
    nodo_id: str = ""
    gdd_acumulado: float = 0.0
    estadio: str = "dormancia"
    ultimo_riego_ts: Optional[datetime.datetime] = None
    horas_frio_acum: float = 0.0
    dias_consecutivos_sin_dato: int = 0
    lluvia_acum_24h: float = 0.0
    # Historial corto para reglas temporales
    t_air_min_24h: Optional[float] = None
    t_air_max_24h: Optional[float] = None
    hr_max_24h: Optional[float] = None


@dataclass
class DatosNodo:
    """Datos del ultimo ciclo de captura del nodo."""
    nodo_id: str
    ts: datetime.datetime
    t_air: float           # temperatura del aire (SHT31) [C]
    hr: float              # humedad relativa [%]
    viento: float          # velocidad viento [m/s]
    cwsi: float            # CWSI calculado [0-1]
    hsi: float             # HSI fusionado CWSI+MDS [0-1]
    rain_mm: float         # lluvia acumulada este ciclo [mm]
    pm25: float            # particulas PM2.5 [ug/m3]
    rad_wm2: float         # radiacion solar [W/m2]
    bat_v: float           # voltaje bateria [V]
    iso_nodo: float        # indice integridad optica [0-1]
    mds_um: float          # micro-contraccion diaria tronco [um]
    t_canopy: float        # temperatura canopy promedio [C]
    gdd_diario: float      # GDD calculado hoy
    estadio: str           # estadio fenologico actual


# ─────────────────────────────────────────────────────────────────
# Umbrales configurables
# ─────────────────────────────────────────────────────────────────

UMBRALES = {
    # Helada
    "helada_critica_c": 0.0,
    "helada_alerta_c": 2.0,

    # Estres calorico
    "calor_alerta_c": 38.0,
    "calor_critico_c": 42.0,

    # CWSI / HSI
    "cwsi_leve": 0.30,
    "cwsi_moderado": 0.55,
    "cwsi_severo": 0.75,

    # Botrytis (Ciliberti et al. 2015)
    "botrytis_hr_min": 90.0,
    "botrytis_t_min": 15.0,
    "botrytis_t_max": 25.0,
    "botrytis_estadios": ["envero", "maduracion"],

    # Mildiu / Downy mildew (Gessler et al. 2011)
    "mildiu_hr_min": 85.0,
    "mildiu_t_min": 18.0,
    "mildiu_t_max": 25.0,
    "mildiu_lluvia_min_mm": 2.0,

    # Ventana de desbrote (GDD)
    "desbrote_gdd_min": 150,
    "desbrote_gdd_max": 200,

    # Bateria baja
    "bat_baja_v": 3.3,
    "bat_critica_v": 3.0,

    # Nodo offline (ciclos sin dato)
    "nodo_offline_ciclos": 4,

    # Fumigacion detectada por PMS5003
    "fumigacion_pm25_ug": 200.0,

    # ISO nodo (integridad optica)
    "iso_limpieza_umbral": 0.80,

    # PHI fungicidas — dias de carencia (SENASA Argentina)
    "phi_dias": {
        "mancozeb": 28,
        "azoxistrobina": 21,
        "cobre": 14,
        "metil_tiofanato": 14,
    },

    # Horas de frio (dormancia)
    "horas_frio_umbral_base": 7.2,  # T < 7.2C cuenta como hora frio
    "horas_frio_objetivo_malbec": 400,
}


# ─────────────────────────────────────────────────────────────────
# Reglas de alerta
# ─────────────────────────────────────────────────────────────────

def regla_helada(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Alerta de helada tardia — critica si hay brotes presentes."""
    alertas = []
    tiene_brotes = estado.estadio not in ("dormancia",)

    if datos.t_air <= UMBRALES["helada_critica_c"] and tiene_brotes:
        alertas.append(Alerta(
            tipo="helada_critica",
            severidad=Severidad.CRITICA,
            mensaje=f"HELADA CRITICA: {datos.t_air:.1f}C con brotes presentes ({estado.estadio}). Riesgo de dano irreversible.",
            canal=Canal.SMS,
            nodo_id=datos.nodo_id,
            metadata={"t_air": datos.t_air, "estadio": estado.estadio},
        ))
    elif datos.t_air <= UMBRALES["helada_alerta_c"] and tiene_brotes:
        alertas.append(Alerta(
            tipo="helada_alerta",
            severidad=Severidad.ALTA,
            mensaje=f"Alerta helada: {datos.t_air:.1f}C — brotes presentes. Monitorear proximas horas.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
            metadata={"t_air": datos.t_air},
        ))
    return alertas


def regla_estres_calorico(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Estres calorico — temperatura foliar y del aire extremas."""
    alertas = []
    if datos.t_air >= UMBRALES["calor_critico_c"]:
        alertas.append(Alerta(
            tipo="calor_critico",
            severidad=Severidad.CRITICA,
            mensaje=f"ESTRES CALORICO CRITICO: T_air={datos.t_air:.1f}C. Riesgo de quemadura foliar y aborto floral.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        ))
    elif datos.t_air >= UMBRALES["calor_alerta_c"]:
        alertas.append(Alerta(
            tipo="calor_alerta",
            severidad=Severidad.ALTA,
            mensaje=f"Estres calorico: T_air={datos.t_air:.1f}C. CWSI={datos.cwsi:.2f}. Considerar riego de refrescamiento.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        ))
    return alertas


def regla_cwsi(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Alerta por umbral de estres hidrico (CWSI/HSI)."""
    alertas = []
    valor = datos.hsi  # usar HSI fusionado como metrica principal

    if valor >= UMBRALES["cwsi_severo"]:
        alertas.append(Alerta(
            tipo="estres_hidrico_severo",
            severidad=Severidad.CRITICA,
            mensaje=f"ESTRES HIDRICO SEVERO: HSI={valor:.2f} (CWSI={datos.cwsi:.2f}, MDS={datos.mds_um:.0f}um). Riego urgente.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
            metadata={"hsi": valor, "cwsi": datos.cwsi, "mds_um": datos.mds_um},
        ))
    elif valor >= UMBRALES["cwsi_moderado"]:
        alertas.append(Alerta(
            tipo="estres_hidrico_moderado",
            severidad=Severidad.ALTA,
            mensaje=f"Estres hidrico moderado: HSI={valor:.2f}. Evaluar programacion de riego.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        ))
    elif valor >= UMBRALES["cwsi_leve"]:
        alertas.append(Alerta(
            tipo="estres_hidrico_leve",
            severidad=Severidad.MEDIA,
            mensaje=f"Estres hidrico leve: HSI={valor:.2f}. Sin accion inmediata requerida.",
            canal=Canal.LOG,
            nodo_id=datos.nodo_id,
        ))
    return alertas


def regla_botrytis(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Riesgo de Botrytis cinerea — HR >90%, T 15-25C, estadio envero+."""
    if estado.estadio not in UMBRALES["botrytis_estadios"]:
        return []
    if (datos.hr >= UMBRALES["botrytis_hr_min"]
            and UMBRALES["botrytis_t_min"] <= datos.t_air <= UMBRALES["botrytis_t_max"]):
        return [Alerta(
            tipo="riesgo_botrytis",
            severidad=Severidad.ALTA,
            mensaje=f"Riesgo BOTRYTIS: HR={datos.hr:.0f}%, T={datos.t_air:.1f}C en {estado.estadio}. Inspeccionar racimos.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
            metadata={"hr": datos.hr, "t_air": datos.t_air, "estadio": estado.estadio},
        )]
    return []


def regla_mildiu(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Riesgo de mildiu (downy mildew) — HR >85%, T 18-25C, lluvia reciente."""
    if (datos.hr >= UMBRALES["mildiu_hr_min"]
            and UMBRALES["mildiu_t_min"] <= datos.t_air <= UMBRALES["mildiu_t_max"]
            and estado.lluvia_acum_24h >= UMBRALES["mildiu_lluvia_min_mm"]):
        return [Alerta(
            tipo="riesgo_mildiu",
            severidad=Severidad.ALTA,
            mensaje=f"Riesgo MILDIU: HR={datos.hr:.0f}%, T={datos.t_air:.1f}C, lluvia 24h={estado.lluvia_acum_24h:.1f}mm. Aplicar fungicida si no hay PHI activo.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        )]
    return []


def regla_ventana_desbrote(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Ventana optima de desbrote por GDD."""
    gdd = estado.gdd_acumulado
    if UMBRALES["desbrote_gdd_min"] <= gdd <= UMBRALES["desbrote_gdd_max"]:
        return [Alerta(
            tipo="ventana_desbrote",
            severidad=Severidad.MEDIA,
            mensaje=f"Ventana de DESBROTE: GDD={gdd:.0f} (optimo {UMBRALES['desbrote_gdd_min']}-{UMBRALES['desbrote_gdd_max']}). Programar operacion.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        )]
    return []


def regla_prediccion_fenologia(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Notificacion de cambio de estadio fenologico detectado."""
    if datos.estadio != estado.estadio and datos.estadio != "dormancia":
        return [Alerta(
            tipo="cambio_estadio",
            severidad=Severidad.INFO,
            mensaje=f"Estadio fenologico: {estado.estadio} -> {datos.estadio} (GDD={estado.gdd_acumulado:.0f}).",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
            metadata={"anterior": estado.estadio, "nuevo": datos.estadio, "gdd": estado.gdd_acumulado},
        )]
    return []


def regla_bateria_baja(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Bateria del nodo baja o critica."""
    alertas = []
    if datos.bat_v <= UMBRALES["bat_critica_v"]:
        alertas.append(Alerta(
            tipo="bateria_critica",
            severidad=Severidad.CRITICA,
            mensaje=f"BATERIA CRITICA: {datos.bat_v:.2f}V — nodo puede apagarse. Verificar panel solar.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        ))
    elif datos.bat_v <= UMBRALES["bat_baja_v"]:
        alertas.append(Alerta(
            tipo="bateria_baja",
            severidad=Severidad.ALTA,
            mensaje=f"Bateria baja: {datos.bat_v:.2f}V. Revisar orientacion del panel solar.",
            canal=Canal.EMAIL,
            nodo_id=datos.nodo_id,
        ))
    return alertas


def regla_nodo_offline(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Nodo sin datos por mas de N ciclos consecutivos."""
    if estado.dias_consecutivos_sin_dato >= UMBRALES["nodo_offline_ciclos"]:
        return [Alerta(
            tipo="nodo_offline",
            severidad=Severidad.ALTA,
            mensaje=f"Nodo {datos.nodo_id} sin datos hace {estado.dias_consecutivos_sin_dato} ciclos. Verificar conectividad LoRa y alimentacion.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        )]
    return []


def regla_fumigacion(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Deteccion de fumigacion por PM2.5 elevado (PMS5003)."""
    if datos.pm25 >= UMBRALES["fumigacion_pm25_ug"]:
        return [Alerta(
            tipo="fumigacion_detectada",
            severidad=Severidad.MEDIA,
            mensaje=f"Fumigacion detectada: PM2.5={datos.pm25:.0f} ug/m3. Capturas termicas invalidadas automaticamente por 4h.",
            canal=Canal.LOG,
            nodo_id=datos.nodo_id,
            metadata={"pm25": datos.pm25},
        )]
    return []


def regla_iso_nodo(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """ISO_nodo bajo — lente de la camara termica necesita limpieza."""
    if datos.iso_nodo < UMBRALES["iso_limpieza_umbral"]:
        return [Alerta(
            tipo="iso_limpieza",
            severidad=Severidad.MEDIA,
            mensaje=f"ISO_nodo={datos.iso_nodo:.0%} — lente termica degradada. Limpiar con pano suave.",
            canal=Canal.PUSH,
            nodo_id=datos.nodo_id,
        )]
    return []


def regla_horas_frio(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """Acumulacion de horas de frio en dormancia — relevante para brotacion."""
    if estado.estadio != "dormancia":
        return []
    objetivo = UMBRALES["horas_frio_objetivo_malbec"]
    acum = estado.horas_frio_acum

    if acum >= objetivo and acum < objetivo + 10:  # notificar una sola vez (~)
        return [Alerta(
            tipo="horas_frio_completas",
            severidad=Severidad.INFO,
            mensaje=f"Horas de frio acumuladas: {acum:.0f}h (objetivo Malbec: {objetivo}h). Brotacion esperable en las proximas semanas.",
            canal=Canal.EMAIL,
            nodo_id=datos.nodo_id,
        )]
    return []


# ─────────────────────────────────────────────────────────────────
# Motor principal
# ─────────────────────────────────────────────────────────────────

REGLAS = [
    regla_helada,
    regla_estres_calorico,
    regla_cwsi,
    regla_botrytis,
    regla_mildiu,
    regla_ventana_desbrote,
    regla_prediccion_fenologia,
    regla_bateria_baja,
    regla_nodo_offline,
    regla_fumigacion,
    regla_iso_nodo,
    regla_horas_frio,
]


def evaluar_alertas(datos: DatosNodo, estado: EstadoNodo) -> list[Alerta]:
    """
    Evalua todas las reglas de alerta contra los datos del nodo.

    Args:
        datos: datos del ultimo ciclo de captura del nodo
        estado: estado acumulado del nodo (GDD, estadio, historial)

    Returns:
        Lista de alertas disparadas (puede ser vacia).

    Uso en backend MVC:
        alertas = evaluar_alertas(datos_nodo, estado_nodo)
        for a in alertas:
            db.add(AlertaDB(nodo_id=a.nodo_id, tipo=a.tipo, ...))
        db.commit()
    """
    alertas = []
    for regla in REGLAS:
        alertas.extend(regla(datos, estado))
    return alertas


# ─────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────

def filtrar_por_severidad(alertas: list[Alerta], minima: Severidad) -> list[Alerta]:
    """Filtra alertas por severidad minima."""
    orden = {Severidad.INFO: 0, Severidad.MEDIA: 1, Severidad.ALTA: 2, Severidad.CRITICA: 3}
    umbral = orden[minima]
    return [a for a in alertas if orden[a.severidad] >= umbral]


def resumen_alertas(alertas: list[Alerta]) -> dict:
    """Resumen de alertas por tipo y severidad."""
    resumen: dict = {"total": len(alertas), "por_severidad": {}, "por_tipo": {}}
    for a in alertas:
        resumen["por_severidad"][a.severidad.value] = resumen["por_severidad"].get(a.severidad.value, 0) + 1
        resumen["por_tipo"][a.tipo] = resumen["por_tipo"].get(a.tipo, 0) + 1
    return resumen


# ─────────────────────────────────────────────────────────────────
# Demo / test rapido
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Simular un ciclo con condiciones de riesgo
    datos_test = DatosNodo(
        nodo_id="nodo_01",
        ts=datetime.datetime(2026, 1, 15, 13, 0),
        t_air=1.5,       # helada!
        hr=92.0,
        viento=1.2,
        cwsi=0.60,
        hsi=0.58,
        rain_mm=0.0,
        pm25=15.0,
        rad_wm2=450.0,
        bat_v=3.2,
        iso_nodo=0.75,
        mds_um=120.0,
        t_canopy=0.8,
        gdd_diario=0.0,
        estadio="brotacion",
    )

    estado_test = EstadoNodo(
        nodo_id="nodo_01",
        gdd_acumulado=95.0,
        estadio="dormancia",   # cambio de estadio!
        lluvia_acum_24h=0.0,
        horas_frio_acum=380.0,
    )

    alertas = evaluar_alertas(datos_test, estado_test)
    print(f"\n{'='*60}")
    print(f"  Motor de Alertas Agronomicas — HydroVision AG")
    print(f"  Nodo: {datos_test.nodo_id} | {datos_test.ts}")
    print(f"{'='*60}")

    for a in alertas:
        print(f"  [{a.severidad.value:>8}] {a.tipo}: {a.mensaje}")

    print(f"\n  Resumen: {resumen_alertas(alertas)}")
    print(f"  Total alertas: {len(alertas)}")
