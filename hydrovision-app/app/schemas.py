"""
schemas.py — Pydantic models para validación de payloads de entrada
HydroVision AG
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class EnvData(BaseModel):
    t_air: float = Field(..., ge=-10.0, le=60.0)
    rh: float = Field(..., ge=0.0, le=100.0)
    wind_ms: float = Field(..., ge=0.0, le=50.0)
    rain_mm: float = Field(..., ge=0.0, le=200.0)


class ThermalData(BaseModel):
    tc_mean: float = Field(..., ge=-10.0, le=70.0)
    tc_max: float = Field(..., ge=-10.0, le=70.0)
    tc_wet: float = Field(..., ge=-10.0, le=70.0)
    tc_dry: float = Field(..., ge=-10.0, le=70.0)
    cwsi: float = Field(..., ge=0.0, le=1.0)
    valid_pixels: int = Field(..., ge=0)


class DendroData(BaseModel):
    mds_mm: float = Field(..., ge=0.0, le=2000.0)
    mds_norm: float = Field(..., ge=0.0, le=1.0)


class HsiData(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0)
    w_cwsi: float = Field(..., ge=0.0, le=1.0)
    w_mds: float = Field(..., ge=0.0, le=1.0)
    wind_override: bool


class GpsData(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


CalidadCaptura = Literal["ok", "lluvia", "post_lluvia", "fumigacion", "post_fumigacion"]


class SolenoidData(BaseModel):
    canal: int = Field(0, ge=0, le=16)
    active: bool = False
    reason: str = "idle"
    ciclos_activo: int = Field(0, ge=0, le=100)


class NodePayload(BaseModel):
    v: int;  node_id: str;  ts: int;  cycle: int
    env: EnvData;  thermal: ThermalData;  dendro: DendroData
    hsi: HsiData;  gps: GpsData
    bat_pct: int = Field(..., ge=0, le=100)
    pm2_5: int = Field(..., ge=0, le=1000)
    calidad_captura: CalidadCaptura
    hmac: Optional[str] = None
    solenoid: Optional[SolenoidData] = None


class ZoneIn(BaseModel):
    name:             str
    lat:              float
    lon:              float
    sw_lat:           Optional[float] = None
    sw_lon:           Optional[float] = None
    ne_lat:           Optional[float] = None
    ne_lon:           Optional[float] = None
    vertices:         Optional[str]   = None   # JSON "[[lat,lon],...]"
    varietal:         Optional[str]   = None
    crop_yield_kg_ha: Optional[float] = None


class NodeConfigIn(BaseModel):
    name:     Optional[str] = None
    zona_id:  Optional[int] = None


class ConfigIn(BaseModel):
    field_name:     Optional[str] = None
    field_location: Optional[str] = None


class InferenceRequest(BaseModel):
    thermal_image: list[list[float]]   # 120×160 matriz de temperaturas [°C]
    t_air: float = Field(..., ge=-10.0, le=60.0)
    rh: float = Field(..., ge=0.0, le=100.0)


class InferenceResponse(BaseModel):
    cwsi: float
    delta_t: float
    latency_ms: float
    model_type: str
