"""
config.py — Configuración desde variables de entorno
HydroVision AG

Variables de entorno reconocidas (ver .env.example):
  DATABASE_URL   : cadena de conexión SQLAlchemy (default: SQLite local)
  MQTT_BROKER    : host del broker MQTT
  MQTT_PORT      : puerto MQTT (default: 1883)
  HMAC_SECRET    : clave secreta para verificar firma de payloads de nodos
  SIMULATION_MODE: "true" para habilitar endpoints /api/simulate/* (default: false)
"""

import os

# Base de datos
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./hydrovision.db",   # fallback local solo para desarrollo
)

# MQTT
MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))

# Seguridad
HMAC_SECRET: str = os.getenv("HMAC_SECRET", "dev_secret_change_in_prod")

# Auth
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "hydrovision")
SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", str(30 * 60)))  # 30 minutos

# Feature flags
SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "false").lower() == "true"

# Email (SMTP)
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")
EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@hydrovision.ag")

# Metadata de la app
APP_TITLE: str = "HydroVision AG"
APP_VERSION: str = "1.0.0"
