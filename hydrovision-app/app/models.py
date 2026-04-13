"""
models.py — SQLAlchemy models
HydroVision AG

Tablas:
  telemetry      : lecturas de nodos (payload /ingest)
  irrigation_log : historial de activaciones/detenciones por zona
  zone_config    : configuración de zonas
  node_config    : metadata de nodos (nombre, zona asignada)
  app_config     : configuración general clave-valor (campo, umbrales)
  audit_log      : registro de eventos de administración
"""

import datetime
import json
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, Index
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Telemetry(Base):
    __tablename__ = "telemetry"
    __table_args__ = (
        Index("ix_telem_node_created", "node_id", "created_at"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    node_id    = Column(String,  nullable=False)
    ts         = Column(Integer, nullable=False)
    cwsi       = Column(Float,   nullable=False)
    hsi        = Column(Float,   nullable=False)
    mds_mm     = Column(Float,   nullable=False)
    t_air      = Column(Float,   nullable=False)
    rh         = Column(Float,   nullable=False)
    wind_ms    = Column(Float,   nullable=False)
    rain_mm    = Column(Float,   nullable=False)
    bat_pct    = Column(Integer, nullable=False)
    calidad    = Column(String,  nullable=False)
    origen     = Column(String,  nullable=False, default="real")
    lat        = Column(Float,   nullable=True)
    lon        = Column(Float,   nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IrrigationLog(Base):
    __tablename__ = "irrigation_log"

    id           = Column(Integer,  primary_key=True, index=True)
    zona         = Column(Integer,  nullable=True, index=True)       # legacy / derivado
    node_id      = Column(String,   nullable=True, index=True)       # nodo que controla el solenoide
    duration_min = Column(Integer,  default=30)
    active       = Column(Boolean,  nullable=False)
    ts           = Column(DateTime, default=datetime.datetime.utcnow)


class ZoneConfig(Base):
    """
    Configuración de cada zona de riego. Editable desde /admin.

    Las zonas definen la geometría del campo. El riego se controla a nivel
    de NODO: cada nodo puede tener un solenoide asignado (NodeConfig.solenoid).
    La activación física la ejecuta el controlador de riego (ESP32 + LoRa RX
    + relés) al recibir la orden MQTT vía Gateway LoRa.
    """
    __tablename__ = "zone_config"

    id               = Column(Integer, primary_key=True)
    name             = Column(String,  nullable=False)
    lat              = Column(Float,   nullable=False)      # centroide — usado para IDW
    lon              = Column(Float,   nullable=False)
    sw_lat           = Column(Float,   nullable=True)       # bounding box SW (calculado desde el mapa)
    sw_lon           = Column(Float,   nullable=True)
    ne_lat           = Column(Float,   nullable=True)       # bounding box NE
    ne_lon           = Column(Float,   nullable=True)
    vertices         = Column(Text,    nullable=True)       # JSON [[lat,lon],...] — polígono libre (si None → rectángulo)
    varietal         = Column(String,  nullable=True)       # variedad/cultivo de la zona
    crop_yield_kg_ha = Column(Float,   nullable=True)       # rendimiento potencial [kg/ha]
    owner_id         = Column(Integer, nullable=True)       # FK users.id


class NodeConfig(Base):
    """
    Metadata de nodos conocidos. Se crea automáticamente al recibir
    el primer /ingest de un node_id nuevo. Editable desde /admin.
    """
    __tablename__ = "node_config"

    node_id  = Column(String,  primary_key=True)
    name     = Column(String,  nullable=True)        # nombre legible opcional
    zona_id  = Column(Integer, nullable=True)        # asignación explícita de zona
    solenoid = Column(Integer, nullable=True)        # canal solenoide (si tiene — habilita riego)
    owner_id = Column(Integer, nullable=True)        # FK users.id — None = nodo sin reclamar


class AppConfig(Base):
    """Configuración general clave-valor. Editable desde /admin."""
    __tablename__ = "app_config"

    key   = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class AuditLog(Base):
    """
    Registro de auditoría para eventos de seguridad y operaciones críticas.

    Eventos registrados:
      - ingest_ok / ingest_reject  : telemetría aceptada/rechazada
      - hmac_fail                  : firma HMAC inválida
      - rate_limit                 : rate limit excedido
      - irrigate_on / irrigate_off : activación/detención de riego
      - irrigate_inhibit           : riego inhibido por reposo fenológico
      - config_change              : cambio de configuración admin
      - zone_create / zone_update / zone_delete : CRUD de zonas
      - node_update                : cambio de metadata de nodo
      - ota_check / ota_applied    : eventos OTA (futuro — firmware reports)
    """
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_ts", "ts"),
        Index("ix_audit_event", "event"),
        Index("ix_audit_node", "node_id"),
    )

    id       = Column(Integer,  primary_key=True, index=True)
    ts       = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    event    = Column(String,   nullable=False)    # tipo de evento
    user_id  = Column(Integer,  nullable=True)     # usuario que realizó la acción (si aplica)
    node_id  = Column(String,   nullable=True)     # nodo involucrado (si aplica)
    detail   = Column(Text,     nullable=True)     # info adicional (JSON o texto libre)
    ip       = Column(String,   nullable=True)     # IP origen del request


class User(Base):
    """Usuarios del sistema (productor o superadmin)."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String,  unique=True, nullable=False)
    password_hash   = Column(String,  nullable=False)
    role            = Column(String,  nullable=False, default="user")  # "user" | "superadmin"

    # Datos de contacto
    full_name       = Column(String,  nullable=True)       # "Juan Pérez"
    email           = Column(String,  nullable=True)       # para emails lifecycle + reportes
    phone           = Column(String,  nullable=True)       # WhatsApp / celular

    # Campo / empresa
    company         = Column(String,  nullable=True)       # "Bodega Los Andes S.A."
    total_ha        = Column(Float,   nullable=True)       # hectáreas totales del campo (potencial upsell)

    # Agrónomo asociado
    agronomist_name  = Column(String, nullable=True)       # nombre del asesor
    agronomist_email = Column(String, nullable=True)       # recibe copia de informes

    # Preferencias de comunicación
    email_lifecycle  = Column(Boolean, nullable=False, default=True)   # recibe emails lifecycle
    email_reports    = Column(Boolean, nullable=False, default=True)   # recibe informes anuales

    # Preferencias de alertas (estrés, helada, riego, etc.) — desactivables por el productor
    alert_email      = Column(Boolean, nullable=False, default=True)   # alertas por email
    alert_whatsapp   = Column(Boolean, nullable=False, default=True)   # alertas por WhatsApp

    created_at      = Column(DateTime, default=datetime.datetime.utcnow)


TIER_NAMES = {1: "Monitoreo", 2: "Automatización", 3: "Precisión"}
TIER_PRICE_RANGE = {
    1: (80, 110),
    2: (130, 170),
    3: (220, 290),
}
TIER_PRICE_BASE = {   # precio/ha/año por defecto (punto medio del rango)
    1: 95,
    2: 150,
    3: 255,
}
ADD_ONS_CATALOG = ["dron_multiespectral", "consultoria_agronomica", "calibracion_varietal", "daas_export", "sla_garantizado"]


class ServicePlan(Base):
    """Plan de servicio contratado por un usuario/campo. Contrato anual."""
    __tablename__ = "service_plans"

    id              = Column(Integer,  primary_key=True, index=True)
    user_id         = Column(Integer,  nullable=False)   # FK users.id
    tier            = Column(Integer,  nullable=False)   # 1 | 2 | 3
    nodos_max       = Column(Integer,  nullable=False)
    ha_contratadas  = Column(Float,    nullable=False)
    precio_ha_usd   = Column(Float,    nullable=False)
    add_ons         = Column(Text,     nullable=True)    # JSON ["dron_multiespectral",...]
    activo          = Column(Boolean,  nullable=False, default=True)
    starts_at       = Column(DateTime, nullable=True)    # inicio del contrato anual
    vence_at        = Column(DateTime, nullable=True)    # fin del contrato (starts_at + 1 año)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def is_expired(self):
        if not self.vence_at:
            return False
        return datetime.datetime.utcnow() > self.vence_at

    @property
    def days_remaining(self):
        if not self.vence_at:
            return None
        delta = self.vence_at - datetime.datetime.utcnow()
        return max(0, delta.days)

    @property
    def total_anual_usd(self):
        return self.ha_contratadas * self.precio_ha_usd


class S2Cache(Base):
    """Cache de bandas Sentinel-2 reales obtenidas vía GEE."""
    __tablename__ = "s2_cache"
    __table_args__ = (
        Index("ix_s2_cache_point_date", "lat", "lon", "fecha"),
    )

    id         = Column(Integer, primary_key=True)
    lat        = Column(Float,    nullable=False)
    lon        = Column(Float,    nullable=False)
    fecha      = Column(String,   nullable=False)   # YYYY-MM-DD de la imagen S2
    B4         = Column(Float,    nullable=False)
    B8         = Column(Float,    nullable=False)
    B8A        = Column(Float,    nullable=False)
    B11        = Column(Float,    nullable=False)
    B12        = Column(Float,    nullable=False)
    scl        = Column(Integer,  nullable=True)     # SCL value en el pixel
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)


# Valores por defecto de AppConfig (se insertan solo si la tabla está vacía)
APP_CONFIG_DEFAULTS = {
    "field_name":        "Campo demo",
    "field_location":    "Colonia Caroya, Córdoba",
    # field_varietal  — derivado de las zonas (no editable)
    # field_area_ha   — calculado desde geometría de zonas (no editable)
    # cwsi_medio/alto — constantes FAO-56 (Jackson et al. 1981): 0.30 / 0.60
    # crop_ky         — determinado por variedad y fenología por zona (FAO-56)
}

# Zonas por defecto (se insertan solo si zone_config está vacía)
# Dimensiones por defecto de cada zona: ~26 m N-S × 32 m E-W
_HL = 0.000117   # half-lat  ≈ 13 m
_HO = 0.000168   # half-lon  ≈ 16 m

def _bounds(lat, lon):
    return {"sw_lat": lat - _HL, "sw_lon": lon - _HO,
            "ne_lat": lat + _HL, "ne_lon": lon + _HO}

ZONE_DEFAULTS = [
    # ── Bloques principales — ensayo RDI Colonia Caroya (~700 m snm) ─────────
    # Protocolo Scholander doc-09: 5 regímenes hídricos sobre Malbec en espaldera
    {"id": 1, "name": "Bloque Norte",
     "lat": -31.2010, "lon": -64.0927, **_bounds(-31.2010, -64.0927),
     "varietal": "vid - malbec", "crop_yield_kg_ha": 8500},   # 100% ETc — control

    {"id": 2, "name": "Centro-Norte",
     "lat": -31.2013, "lon": -64.0927, **_bounds(-31.2013, -64.0927),
     "varietal": "vid - malbec", "crop_yield_kg_ha": 8000},   # 65% ETc

    {"id": 3, "name": "Centro-Sur",
     "lat": -31.2016, "lon": -64.0927, **_bounds(-31.2016, -64.0927),
     "varietal": "vid - malbec", "crop_yield_kg_ha": 7200},   # 40% ETc — RDI moderado

    {"id": 4, "name": "Bloque Sur",
     "lat": -31.2019, "lon": -64.0927, **_bounds(-31.2019, -64.0927),
     "varietal": "vid - cabernet", "crop_yield_kg_ha": 7000}, # ciclo largo +2-3 semanas

    {"id": 5, "name": "Bloque Este",
     "lat": -31.2015, "lon": -64.0931, **_bounds(-31.2015, -64.0931),
     "varietal": "vid - bonarda", "crop_yield_kg_ha": 9000},  # alta producción — uva de volumen

    # ── Lote Oeste — polígono irregular ~11 ha, Syrah ─────────────────────────
    {"id": 6, "name": "Lote Oeste (grande)",
     "lat": -31.2035, "lon": -64.0950,
     "sw_lat": -31.2053, "sw_lon": -64.0971,
     "ne_lat": -31.2017, "ne_lon": -64.0929,
     "vertices": json.dumps([
         [-31.2053, -64.0967], [-31.2046, -64.0971],
         [-31.2030, -64.0969], [-31.2017, -64.0956],
         [-31.2021, -64.0939], [-31.2031, -64.0929],
         [-31.2044, -64.0935], [-31.2051, -64.0948],
     ]),
     "varietal": "vid - syrah", "crop_yield_kg_ha": 7500},

    # ── Parcelas Casa — monitoreo peridoméstico (olivo + cerezo) ─────────────
    {"id": 7,  "name": "Casa 1",
     "lat": -31.2008, "lon": -64.0935, **_bounds(-31.2008, -64.0935),
     "varietal": "olivo", "crop_yield_kg_ha": 4000},           # rendimiento aceite ~20% fruto

    {"id": 8,  "name": "Casa 2",
     "lat": -31.2010, "lon": -64.0935, **_bounds(-31.2010, -64.0935),
     "varietal": "olivo", "crop_yield_kg_ha": 4200},

    {"id": 9,  "name": "Casa 3",
     "lat": -31.2012, "lon": -64.0935, **_bounds(-31.2012, -64.0935),
     "varietal": "cerezo", "crop_yield_kg_ha": 12000},         # alta densidad — fruto fresco

    {"id": 10, "name": "Casa 4",
     "lat": -31.2014, "lon": -64.0935, **_bounds(-31.2014, -64.0935),
     "varietal": "cerezo", "crop_yield_kg_ha": 11500},

    {"id": 11, "name": "Casa 5",
     "lat": -31.2016, "lon": -64.0935, **_bounds(-31.2016, -64.0935),
     "varietal": "vid - malbec", "crop_yield_kg_ha": 6500},    # parcela pequeña, riego manual

    # ── Lote Sur — polígono grande ~25 ha, Syrah, 3 nodos de 8 necesarios ────
    {"id": 12, "name": "Lote Sur (20 ha)",
     "lat": -31.2080, "lon": -64.0945,
     "sw_lat": -31.2105, "sw_lon": -64.0975,
     "ne_lat": -31.2055, "ne_lon": -64.0915,
     "vertices": json.dumps([
         [-31.2105, -64.0970], [-31.2098, -64.0975],
         [-31.2070, -64.0972], [-31.2055, -64.0958],
         [-31.2057, -64.0930], [-31.2065, -64.0915],
         [-31.2085, -64.0918], [-31.2100, -64.0935],
         [-31.2105, -64.0955],
     ]),
     "varietal": "vid - syrah", "crop_yield_kg_ha": 7800},
]
