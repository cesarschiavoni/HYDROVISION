-- ============================================================
-- HydroVision AG — Schema PostgreSQL para producción
-- Migrado desde models.py (SQLAlchemy/SQLite → PostgreSQL)
-- TRL 4 · Proyecto ANPCyT Startup 2025
-- ============================================================

-- Extensión para UUID si se necesita en el futuro
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────
-- Telemetría — lecturas del nodo vía /ingest
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS telemetry (
    id          SERIAL PRIMARY KEY,
    node_id     VARCHAR(32)   NOT NULL,
    ts          BIGINT        NOT NULL,          -- epoch seconds del nodo
    cwsi        REAL          NOT NULL,
    hsi         REAL          NOT NULL,
    mds_mm      REAL          NOT NULL,          -- MDS en mm (dendrometría)
    t_air       REAL          NOT NULL,          -- °C
    rh          REAL          NOT NULL,          -- %
    wind_ms     REAL          NOT NULL,          -- m/s
    rain_mm     REAL          NOT NULL,          -- mm acumulados
    bat_pct     SMALLINT      NOT NULL,          -- % batería
    calidad     VARCHAR(16)   NOT NULL,          -- ok / fumigacion / lluvia / nocturno
    origen      VARCHAR(8)    NOT NULL DEFAULT 'real',  -- real / sintetico
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    -- Campos ampliados desde payload v1
    rad_wm2     REAL,                            -- irradiancia solar W/m²
    tc_mean     REAL,                            -- temp canopeo media °C
    tc_max      REAL,                            -- temp canopeo máxima °C
    tc_wet      REAL,                            -- temp referencia húmeda °C
    tc_dry      REAL,                            -- temp referencia seca °C
    pm2_5       SMALLINT,                        -- partículas PM2.5 µg/m³
    iso_nodo    SMALLINT,                        -- diagnóstico lente 0-100
    gdd_acum    REAL,                            -- grados-día acumulados
    estadio     VARCHAR(32),                     -- estadio fenológico
    varietal    VARCHAR(32),                     -- cultivo/variedad
    valid_px    SMALLINT,                        -- píxeles foliares válidos
    n_frames    SMALLINT,                        -- frames fusionados
    w_cwsi      REAL,                            -- peso CWSI en HSI
    w_mds       REAL,                            -- peso MDS en HSI
    wind_ovr    BOOLEAN DEFAULT FALSE,           -- override viento
    sol_canal   SMALLINT,                        -- canal solenoide
    sol_active  BOOLEAN DEFAULT FALSE,           -- solenoide activo
    sol_reason  VARCHAR(16),                     -- hsi / manual / off
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_telem_node_created ON telemetry (node_id, created_at);
CREATE INDEX ix_telem_ts           ON telemetry (ts);

-- ─────────────────────────────────────────────────
-- Log de riego — activaciones/detenciones por nodo
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS irrigation_log (
    id            SERIAL PRIMARY KEY,
    node_id       VARCHAR(32),
    zona          SMALLINT,
    duration_min  SMALLINT     DEFAULT 30,
    active        BOOLEAN      NOT NULL,
    ts            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_irrig_node ON irrigation_log (node_id);
CREATE INDEX ix_irrig_ts   ON irrigation_log (ts);

-- ─────────────────────────────────────────────────
-- Configuración de zonas de riego
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS zone_config (
    id                SERIAL PRIMARY KEY,
    name              VARCHAR(64)      NOT NULL,
    lat               DOUBLE PRECISION NOT NULL,     -- centroide
    lon               DOUBLE PRECISION NOT NULL,
    sw_lat            DOUBLE PRECISION,              -- bounding box
    sw_lon            DOUBLE PRECISION,
    ne_lat            DOUBLE PRECISION,
    ne_lon            DOUBLE PRECISION,
    vertices          JSONB,                         -- polígono libre [[lat,lon],...]
    varietal          VARCHAR(32),
    crop_yield_kg_ha  REAL
);

-- ─────────────────────────────────────────────────
-- Metadata de nodos conocidos
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS node_config (
    node_id   VARCHAR(32) PRIMARY KEY,
    name      VARCHAR(64),
    zona_id   INTEGER REFERENCES zone_config(id),
    solenoid  SMALLINT                               -- canal solenoide (NULL = sin riego)
);

-- ─────────────────────────────────────────────────
-- Configuración general clave-valor
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_config (
    key    VARCHAR(64) PRIMARY KEY,
    value  TEXT NOT NULL
);

-- ─────────────────────────────────────────────────
-- Auditoría de eventos
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id       SERIAL PRIMARY KEY,
    ts       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event    VARCHAR(32) NOT NULL,
    node_id  VARCHAR(32),
    detail   TEXT,
    ip       VARCHAR(45)
);

CREATE INDEX ix_audit_ts    ON audit_log (ts);
CREATE INDEX ix_audit_event ON audit_log (event);
CREATE INDEX ix_audit_node  ON audit_log (node_id);

-- ─────────────────────────────────────────────────
-- Cache Sentinel-2 (bandas reales vía GEE/STAC)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS s2_cache (
    id          SERIAL PRIMARY KEY,
    lat         DOUBLE PRECISION NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    fecha       DATE             NOT NULL,
    b4          REAL NOT NULL,
    b8          REAL NOT NULL,
    b8a         REAL NOT NULL,
    b11         REAL NOT NULL,
    b12         REAL NOT NULL,
    scl         SMALLINT,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_s2_cache_point_date ON s2_cache (lat, lon, fecha);

-- ─────────────────────────────────────────────────
-- Sesiones Scholander (validación TRL 4)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scholander_session (
    id            SERIAL PRIMARY KEY,
    fecha         DATE         NOT NULL,
    operador      VARCHAR(64)  NOT NULL,          -- Javier Schiavoni
    supervisor    VARCHAR(64),                     -- Dra. Monteoliva (si presente)
    zona_id       INTEGER REFERENCES zone_config(id),
    node_id       VARCHAR(32),
    ventana       VARCHAR(16)  NOT NULL,          -- 09hs / 12hs / 16hs
    psi_stem_mpa  REAL         NOT NULL,          -- potencial hídrico tallo (MPa)
    hsi_nodo      REAL,                            -- HSI del nodo al momento
    cwsi_nodo     REAL,                            -- CWSI del nodo al momento
    mds_mm_nodo   REAL,                            -- MDS del nodo al momento
    t_air         REAL,
    rh            REAL,
    notas         TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_schol_fecha ON scholander_session (fecha);
CREATE INDEX ix_schol_node  ON scholander_session (node_id);
