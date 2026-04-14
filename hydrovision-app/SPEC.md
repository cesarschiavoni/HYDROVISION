# HydroVision AG — Especificacion de la Aplicacion Web

**hydrovision-app/** — Backend FastAPI + Frontend Alpine.js/Leaflet/Tailwind
**Version:** TRL 3-4 (demo + validacion experimental)
**Puerto default:** 8096 (uvicorn)

---

## 1. Estructura de Archivos

```
hydrovision-app/
  app/
    __init__.py
    main.py               # App FastAPI, lifespan, process_ingest (NOTA: contiene copia legacy de helpers de core.py — los routers importan desde core.py)
    core.py               # Logica de negocio autoritativa: fusion satelital, ZONES dict, GDD, helpers fenologicos
    config.py             # Configuracion desde variables de entorno
    deps.py               # Dependencias: HMAC, sesion, rate limit, audit
    models.py             # Modelos SQLAlchemy ORM
    schemas.py            # Validadores Pydantic
    mqtt.py               # Cliente MQTT: consumer + publisher
    routers/
      __init__.py
      auth.py             # POST /login, /logout
      pages.py            # GET /dashboard, /admin, /informe, /trazabilidad, /viento, /backoffice
      api.py              # POST /ingest, GET /api/status, /alerts, /history, /zones, POST /api/irrigate
      admin.py            # GET/PUT /api/admin/config, /zones, /nodes
      backoffice.py       # Superadmin: /api/backoffice/users, /plans, /nodes/assign
      simulate.py         # POST /api/simulate/start, /stop — modelo hidrologico
      report.py           # GET /api/report/summary, /csv, /traceability
      inference.py        # POST /api/inference — PINN imagen termica -> CWSI
      emails.py           # Background: annual_report, lifecycle emails
      wind.py             # GET /api/wind-rose — rosa de vientos por zona
    services/
      __init__.py
      email_service.py    # EmailService: render + envio de emails transaccionales
      phenology.py        # Crop group, phase, GDD helpers
    templates/
      login.html          # Login con formulario
      dashboard.html      # Alpine.js: mapa Leaflet + estado de zonas/nodos en vivo
      admin.html          # Leaflet.draw: crear/editar zonas (poligonos)
      backoffice.html     # Superadmin: gestion de usuarios y planes
      informe.html        # Generador de informe anual
      trazabilidad.html   # Viewer de trazabilidad/audit log (Tier 3)
      home.html           # Landing page
      emails/
        base.html         # Template base Jinja2 para emails
        annual_report.html
        lifecycle.html
      favicon.svg
  services/
    mqtt_ingester.py      # Consumer MQTT externo (TRL 5+)
  infra/
    docker-compose.yml    # PostgreSQL + Mosquitto
    mosquitto/
      mosquitto.conf
    schema_postgresql.sql
  requirements.txt
  .env.example
  hydrovision.db          # SQLite (solo desarrollo)
  test_sim.py
  tests/
```

---

## 2. Configuracion (config.py / .env)

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./hydrovision.db` | Conexion DB (SQLite dev, PostgreSQL prod) |
| `MQTT_BROKER` | `localhost` | Broker MQTT (Mosquitto) |
| `MQTT_PORT` | `1883` | Puerto MQTT |
| `HMAC_SECRET` | — | Secreto compartido con nodos para firma de payloads |
| `ADMIN_USERNAME` | `admin` | Usuario admin por defecto |
| `ADMIN_PASSWORD` | `hydrovision` | Password admin por defecto |
| `SESSION_MAX_AGE` | `1800` | Duracion maxima de sesion (30 min) |
| `SIMULATION_MODE` | `false` | Habilita /api/simulate/* |
| `SMTP_*` | — | Configuracion de email (host, port, user, pass) |
| `APP_TITLE` | `HydroVision AG` | Titulo de la app |

---

## 3. Modelos de Datos (models.py)

### Telemetry
Lectura por nodo (~1 cada 15 min en produccion, ~30s en simulacion).

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| node_id | String | ID del nodo (ej. HV-0001) |
| ts | Integer | Timestamp Unix de la lectura |
| cwsi | Float | Crop Water Stress Index (0-1) |
| hsi | Float | Hybrid Stress Index (CWSI + MDS ponderado) |
| mds_mm | Float | Maximum Daily Shrinkage del tronco (mm) |
| t_air | Float | Temperatura del aire (C) |
| rh | Float | Humedad relativa (%) |
| wind_ms | Float | Velocidad del viento (m/s) |
| rain_mm | Float | Lluvia acumulada (mm) |
| bat_pct | Integer | Bateria del nodo (%) |
| calidad | String | ok, lluvia, post_lluvia, fumigacion, post_fumigacion |
| origen | String | Origen del dato (real, simulado, fusion_s2). Default: "real" |
| lat | Float | Latitud GPS del nodo |
| lon | Float | Longitud GPS del nodo |
| created_at | DateTime | Timestamp de insercion |

### NodeConfig
Metadata de cada nodo. Auto-creado en primer /ingest.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| node_id | String PK | ID unico del nodo |
| name | String | Nombre legible (ej. "Nodo Fila 3") |
| zona_id | Integer FK | Zona asignada (NULL si no asignado) |
| solenoid | Integer | Canal de solenoide (0 = sin solenoide, 1-16) |
| owner_id | Integer FK | Usuario propietario (NULL = sin asignar) |

### ZoneConfig
Zona de cultivo con geometria (poligono o rectangulo).

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| name | String | Nombre de la zona (ej. "Lote Oeste") |
| lat | Float | Latitud central |
| lon | Float | Longitud central |
| sw_lat, sw_lon | Float | Esquina suroeste (bounding box) |
| ne_lat, ne_lon | Float | Esquina noreste (bounding box) |
| vertices | Text (JSON) | Poligono [[lat,lon], ...] para zonas irregulares |
| varietal | String | Cultivo (Malbec, Cabernet, Olivo, Cerezo, etc.) |
| crop_yield_kg_ha | Float | Rendimiento esperado (kg/ha) |
| owner_id | Integer FK | Usuario propietario |

### User
Cuentas de usuario.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| username | String UNIQUE | Nombre de usuario |
| password_hash | String | PBKDF2-HMAC SHA256 (salt$hash) |
| role | String | `user` o `superadmin` |
| full_name | String | Nombre completo |
| email | String | Email principal |
| phone | String | Telefono |
| company | String | Empresa/finca |
| agronomist_name | String | Nombre del agronomo asesor |
| agronomist_email | String | Email del agronomo (CC en reportes) |
| email_lifecycle | Boolean | Recibir emails de campana |
| email_reports | Boolean | Recibir reportes anuales |
| alert_email | Boolean | Alertas por email |
| alert_whatsapp | Boolean | Alertas por WhatsApp (futuro) |
| total_ha | Float | Hectareas totales del campo (nullable) |
| created_at | DateTime | Fecha de creacion |

### ServicePlan
Plan de servicio por usuario (facturacion SaaS).

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| user_id | Integer FK | Usuario |
| tier | Integer | 1=Monitoreo, 2=Automatizacion, 3=Precision |
| nodos_max | Integer | Limite de nodos (0 = sin limite) |
| ha_contratadas | Float | Hectareas contratadas (0 = sin limite) |
| precio_ha_usd | Float | Precio por ha/ano (95, 150, 255) |
| add_ons | Text (JSON) | Extras contratados |
| activo | Boolean | Plan vigente |
| starts_at | DateTime | Inicio del plan |
| vence_at | DateTime | Vencimiento del plan |
| created_at | DateTime | Fecha de creacion |

### IrrigationLog
Registro de activaciones/desactivaciones de riego.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| zona | Integer | ID de la zona (legacy/derivado) |
| node_id | String | Nodo que controla el solenoide |
| duration_min | Integer | Duracion del ciclo (min). Default: 30 |
| active | Boolean | true=encendido, false=apagado |
| ts | DateTime | Timestamp del evento |

### AuditLog
Log de auditoria completo.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| ts | DateTime | Timestamp |
| event | String | Tipo (ingest_ok, irrigate_on, irrigate_off, inhibit, login, etc.) |
| user_id | Integer | Usuario que ejecuto la accion |
| node_id | String | Nodo involucrado |
| detail | Text (JSON) | Detalle estructurado del evento |
| ip | String | IP del cliente |

### AppConfig
Configuracion global clave-valor.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| key | String PK | Nombre de la config (field_name, field_location, etc.) |
| value | String | Valor |

### S2Cache
Cache de bandas Sentinel-2 (para integracion futura con GEE).

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Auto-incremental |
| lat, lon | Float | Coordenadas del punto |
| fecha | String | Fecha de la imagen (formato YYYY-MM-DD) |
| B4, B8, B8A, B11, B12 | Float | Bandas espectrales |
| scl | Integer | Scene Classification Layer |
| fetched_at | DateTime | Cuando se descargo |

---

## 4. Autenticacion y Sesiones (deps.py)

### Flujo de login
1. GET `/login` — formulario HTML
2. POST `/login` (username, password) — verifica contra DB
3. Exito: genera token firmado HMAC-SHA256 → cookie `hv_session` (httponly, samesite=lax, max_age=1800s)
4. Redirige a `/dashboard` (user) o `/backoffice` (superadmin)

### Token de sesion
```
payload = {"uid": user_id, "ts": unix_timestamp}
token = base64(json(payload) + "|" + hmac_sha256(payload, HMAC_SECRET))
```
Verificacion: decodifica base64, verifica firma HMAC, valida que ts no supere SESSION_MAX_AGE.

### Password hashing
PBKDF2-HMAC SHA256 con 300.000 iteraciones y salt aleatorio de 16 bytes.

### Dependencias de auth
| Dependencia | Uso | Descripcion |
|-------------|-----|-------------|
| `require_login` | Pages | Verifica cookie, redirige a /login si invalida |
| `get_current_user` | API | Decodifica token, retorna User de DB |
| `current_user_dep` | API | Depends(get_current_user) pre-configurado |
| `user_only_dep` | API | current_user + role != "superadmin" |
| `superadmin_dep` | API | current_user + role == "superadmin" |

### Roles
- **user**: accede a dashboard, admin (sus zonas/nodos), informe, trazabilidad (tier 3)
- **superadmin**: accede a backoffice, gestion de usuarios, planes, asignacion de nodos

---

## 5. Endpoints API

### 5.1 Auth (routers/auth.py)

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/login` | — | Pagina de login |
| POST | `/login` | Form | Autenticar usuario, setear cookie |
| POST | `/logout` | Cookie | Borrar cookie, redirigir a /login |

### 5.2 Paginas HTML (routers/pages.py)

| Metodo | Ruta | Auth | Template | Descripcion |
|--------|------|------|----------|-------------|
| GET | `/` | — | home.html | Landing page |
| GET | `/dashboard` | User | dashboard.html | Dashboard principal con mapa y estado en vivo |
| GET | `/admin` | User | admin.html | Configuracion de campo (zonas con Leaflet.draw) |
| GET | `/informe` | User | informe.html | Generador de informe anual |
| GET | `/trazabilidad` | User | trazabilidad.html | Trazabilidad hidrica (gated Tier 3) |
| GET | `/viento` | User | viento.html | Viento dominante por zona (rosa de vientos) |
| GET | `/backoffice` | Superadmin | backoffice.html | Gestion de usuarios y planes |

### 5.3 Telemetria y Control (routers/api.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| POST | `/ingest` | HMAC | NodePayload (JSON) | `{status, node_id, varietal, sol_sim?}` | Ingesta de telemetria (HTTP fallback de MQTT). Rate limit: 100 req/min/nodo |
| GET | `/api/status` | User | — | `[{node_id, name, cwsi, hsi, mds_mm, t_air, rh, wind_ms, bat_pct, stress, origen, hace_min, lat, lon}]` | Ultima lectura por nodo propio |
| GET | `/api/alerts` | User | — | `[{node_id, cwsi}]` | Nodos con CWSI >= 0.60 (estres severo) |
| GET | `/api/history/{node_id}` | User | — | `[{ts, cwsi, hsi}]` | Historial 48 horas del nodo |
| POST | `/api/irrigate/{node_id}` | User | — | `{status, node_id, active, source}` | Toggle manual de solenoide + publicacion MQTT. Inhibido si zona en dormancia |
| POST | `/api/sol_sim/{node_id}` | User | — | `{status, node_id, sol_sim}` | Toggle modo simulacion de solenoide |
| GET | `/api/zones` | User | — | `{zones: [...], unzoned_nodes: [...]}` | Estado de zonas con CWSI, fenologia, nodos asignados, recomendacion de riego |

### 5.4 Administracion de Campo (routers/admin.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| GET | `/api/admin/config` | User | — | `{field_name, field_location, field_varietal, field_area_ha, cwsi_medio, cwsi_alto}` | Configuracion global |
| PUT | `/api/admin/config` | User | ConfigIn | `{status}` | Actualizar nombre/ubicacion del campo |
| GET | `/api/admin/zones` | User | — | `[{id, name, lat, lon, vertices, varietal, crop_yield_kg_ha, ...}]` | Zonas del usuario |
| POST | `/api/admin/zones` | User | ZoneIn | `{status, zona_id}` | Crear zona (valida overlap + limite ha del plan) |
| PUT | `/api/admin/zones/{id}` | User | ZoneIn | `{status}` | Editar zona |
| DELETE | `/api/admin/zones/{id}` | User | — | `{status}` | Eliminar zona |
| GET | `/api/admin/nodes` | User | — | `[{node_id, name, zona_id, solenoid, bat_pct, last_reading}]` | Nodos del usuario |
| PUT | `/api/admin/nodes/{node_id}` | User | NodeConfigIn | `{status}` | Actualizar nombre/zona del nodo |
| GET | `/api/admin/audit` | User | — | `[{ts, event, node_id, detail}]` | Log de auditoria del usuario |

### 5.5 Backoffice — Superadmin (routers/backoffice.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| GET | `/api/backoffice/catalog` | Superadmin | — | `{tiers: [...]}` | Definiciones de tiers |
| GET | `/api/backoffice/users` | Superadmin | — | `[{id, username, role, full_name, email, company, nodos, zonas, plan}]` | Lista de usuarios con estado de plan |
| POST | `/api/backoffice/users` | Superadmin | UserCreate | `{id, username}` | Crear usuario |
| PUT | `/api/backoffice/users/{id}` | Superadmin | UserUpdate | `{status}` | Editar usuario |
| DELETE | `/api/backoffice/users/{id}` | Superadmin | — | `{status}` | Eliminar usuario (cascade zonas/nodos/plan) |
| POST | `/api/backoffice/plans` | Superadmin | PlanCreate | `{id}` | Crear/renovar plan |
| PUT | `/api/backoffice/plans/{id}` | Superadmin | PlanUpdate | `{status}` | Editar plan |
| GET | `/api/backoffice/nodes` | Superadmin | — | `[{node_id, name, owner_id, zona_id, ...}]` | Lista de nodos |
| PUT | `/api/backoffice/nodes/{node_id}/assign` | Superadmin | `{owner_id}` | `{status}` | Asignar nodo a propietario |
| GET | `/api/backoffice/stats` | Superadmin | — | `{total_users, total_nodes, ...}` | Estadisticas globales |
| GET | `/api/backoffice/audit` | Superadmin | — | `[{ts, event, user_id, ...}]` | Log de auditoria |

### 5.6 Simulacion Hidrologica (routers/simulate.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| POST | `/api/simulate/start` | User | `{duration_sec?, tick_interval_s?}` | `{status, task_id}` | Iniciar simulacion: lecturas sinteticas con modelo de balance hidrico |
| POST | `/api/simulate/stop` | User | — | `{status}` | Detener simulacion |
| GET | `/api/simulate/status` | User | — | `{running}` | Estado de la simulacion |

**Modelo hidrologico:**
- ET_RATE = 0.008/tick (evapotranspiracion base)
- ET_DIURNAL = 0.006/tick (extra al mediodia)
- IRRIG_RATE = 0.035/tick (ganancia con riego activo)
- RAIN_RATE = 0.05/mm
- CWSI = (1 - water_level) + variacion_diurna + ruido

### 5.7 Reportes (routers/report.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| GET | `/api/report/summary` | User | `days=7` (1-90) | `{cwsi_avg, cwsi_max, rain_total, temp_avg, rh_avg, stress_high_count, irrigation_count, ...}` | KPIs del periodo |
| GET | `/api/report/export/csv` | User | `days=7` | CSV stream | Descarga de telemetria + riego en CSV |
| GET | `/api/report/traceability` | User (Tier 3) | `days=30, fmt?` | JSON o CSV | Trazabilidad hidrica (gated por tier >= 3) |
| GET | `/api/report/cwsi-history` | User | `days?, resolution?` | `[{ts, cwsi}]` | Historial CWSI de todos los nodos (no acepta node_id) |
| GET | `/api/report/zone-history` | User | `days?, resolution?` | `[{ts, cwsi_avg}]` | Historial CWSI promedio de todas las zonas (no acepta zone_id) |
| GET | `/api/report/irrigation-history` | User | `zone_id?, days?` | `[{ts, zone, node_id, active}]` | Historial de activaciones de riego |
| GET | `/api/report/zone-performance` | User | `days?` | `{stress_events, irrigation_count, ...}` | Performance de todas las zonas (no acepta zone_id) |
| GET | `/api/report/comparison` | User | — | `{hydrovision: {...}, traditional: {...}, competitors: [...]}` | Comparativa HydroVision vs riego tradicional vs competencia |
| GET | `/api/user/plan` | User | — | `{tier}` | Tier del plan activo del usuario |

### 5.8 Inferencia IA (routers/inference.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| POST | `/api/inference` | — | InferenceRequest | `{cwsi, delta_t, latency_ms, model_type}` | Imagen termica 120x160 (C) -> CWSI via PINN (TFLite INT8 o PyTorch FP32) |
| GET | `/api/validacion/reporte` | User | — | `{metrics, summary}` | Reporte de validacion del modelo |
| GET | `/api/nodos/{node_id}/latest` | User | — | `{node_id, ts, cwsi, ...}` | Ultima lectura del nodo |

### 5.9 Emails (routers/emails.py)

| Metodo | Ruta | Auth | Body | Descripcion |
|--------|------|------|------|-------------|
| POST | `/api/emails/preview/{email_type}` | Superadmin | SendRequest | Previsualizar email sin enviarlo |
| POST | `/api/emails/send/{email_type}` | Superadmin | SendRequest | Enviar email (annual_report o lifecycle) |
| GET | `/api/emails/schedule` | Superadmin | — | Calendario de proximos envios |

### 5.10 Viento dominante (routers/wind.py)

| Metodo | Ruta | Auth | Params | Retorna | Descripcion |
|--------|------|------|--------|---------|-------------|
| GET | `/api/wind-rose` | User | `zone_id` o `lat+lon`, `varietal?`, `years?` (1-5, default 3) | `{dominant, dominant_pct, sectors[], calm_pct, avg_speed_ms, leaf_months[]}` | Rosa de vientos historica (Open-Meteo ERA5), filtrada por meses con hojas del varietal |

Servicio: `app/services/wind_analysis.py` — consulta Open-Meteo Archive API (gratis, sin key).
Filtra horas diurnas (6-20 hs), calma < 0.5 m/s. 16 sectores de brujula.
Meses con hojas determinados por `app/services/phenology.py` (vid: Sep-May, olivo: todo el ano, cerezo: Ago-Abr).

---

## 6. Logica de Negocio Principal

### 6.1 Ingesta de Telemetria (process_ingest)

```
1. Verificar HMAC-SHA256 (en dev mode se omite)
2. Rate limit: 100 req/min/nodo
3. Check calidad captura (ok | lluvia | post_lluvia | fumigacion | post_fumigacion)
4. Extraer campos: env, thermal, dendro, gps, solenoid
5. Auto-crear NodeConfig si el nodo es nuevo (_ensure_node_config)
6. Insertar fila en Telemetry
7. Manejar estado de solenoide:
   a. Si zona en dormancia (Ky <= 0.15) + solenoide activo -> inhibir, forzar apagado
   b. Si cambio de estado -> insertar IrrigationLog
8. Insertar AuditLog (ingest_ok | inhibit | irrigate_on/off)
9. Retornar downlink: {status, varietal, sol_sim?, command?}
```

### 6.2 Resolucion de CWSI por Zona (GET /api/zones)

Prioridad para determinar el CWSI de una zona:
1. **Nodo asignado explicitamente** -> usar CWSI del nodo
2. **Nodo dentro del bounding box** (GPS) -> usar CWSI del nodo
3. **Simulacion activa** -> water_level -> CWSI sintetico con ciclo diurno
4. **Fusion satelital S2** -> predecir_cwsi(zona_lat, zona_lon, vpd) via modelo NDWI-CWSI
5. **Sin datos** -> "sin datos"

### 6.3 Motor Fenologico (GDD)

Calcula Grados Dia Acumulados: `GDD = SUM(max(0, T_media_dia - T_base))`

**Cultivos soportados:**

| Cultivo | T_base (C) | Etapas principales |
|---------|------------|-------------------|
| Vid — Malbec, Bonarda, Syrah | 10 | Brotacion (0-150 GDD), Desarrollo veg (150-450), Floracion/Cuaje (450-750), Envero (750-1300), Vendimia (1300-1600), Reposo (>1600) |
| Vid — Cabernet | 10 | Brotacion (0-180 GDD), Desarrollo veg (180-500), Floracion/Cuaje (500-800), Envero (800-1450), Vendimia (1450-1750), Reposo (>1750) |
| Olivo | 12.5 | Brotacion, Floracion/Cuaje, Endurecimiento, Maduracion/Cosecha, Reposo |
| Cerezo | 4.5 | Brotacion, Floracion (Ky=1.10 critico), Desarrollo, Madurez, Reposo |
| Pistacho | 10 | Similar a vid |
| Arandano | 7 | Brotacion, Floracion, Desarrollo, Madurez, Reposo |
| Nogal | 10 | Brotacion, Floracion, Desarrollo, Madurez, Reposo |
| Citricos (naranja, limon, pomelo) | 13 | Brotacion, Floracion, Desarrollo, Madurez, Reposo (3 entries separadas en codigo) |

**Coeficiente Ky (FAO-56):** indica sensibilidad al estres hidrico por etapa fenologica.
- Ky <= 0.15: dormancia -> se inhibe el riego automatico
- Ky >= 0.85: etapa critica (floracion/cuaje) -> umbrales de alerta mas conservadores

**Metodo de calculo:**
1. Primario: GDD si hay >= 14 dias de datos de temperatura
2. Fallback: tabla mensual (meses del ano -> Ky)

### 6.4 Sistema de Alertas

**Umbrales CWSI:**
- `CWSI_MEDIO = 0.30` — estres moderado (amarillo)
- `CWSI_ALTO = 0.60` — estres severo (rojo), recomienda riego
- `CWSI_IRRIGATE = 0.60` — umbral para activacion de riego

**Tipos de alerta:**
- CWSI-based: nodos con CWSI >= 0.60
- Fenologia-based: suprime recomendaciones en dormancia
- Helada: t_air < 0 C
- Stress events: conteo de CWSI >= 0.60 en periodo

**Preferencias del usuario** (modelo User):
- alert_email, alert_whatsapp, email_lifecycle, email_reports

### 6.5 Control de Riego

**Modos de operacion:**
1. **Autonomo (TRL 5+):** el nodo decide localmente si HSI >= umbral -> activa solenoide via GPIO
2. **Override manual (dashboard):** POST /api/irrigate/{node_id} -> toggle + publicacion MQTT
3. **Simulacion:** POST /api/sol_sim/{node_id} -> logica activa pero GPIO apagado

**Inhibicion automatica:**
- Si la zona esta en dormancia (Ky <= 0.15) y el solenoide esta activo -> forzar apagado + audit "irrigate_inhibit"
- Motivo: riego en dormancia es contraproducente

**Estado en memoria:**
- `_NODE_IRRIGATION: dict[node_id -> bool]` — restaurado desde IrrigationLog al startup
- `_NODE_SOL_SIM: dict[node_id -> bool]` — flag de simulacion

### 6.6 Dict ZONES en Memoria (core.py)

```python
ZONES: dict[int, dict] = {}
# {id: {name, lat, lon, vertices, varietal, sw_lat, sw_lon, ne_lat, ne_lon}}
```

- Cargado al startup via `_reload_zones(db)`
- Mutado in-place con `.clear()` + `.update()` para que todos los modulos vean los cambios
- Usado por /api/zones, /api/irrigate, process_ingest (fenologia)

### 6.7 Fusion Satelital (_SatelliteFusionService)

Estima CWSI en zonas sin nodos directos usando correlacion NDWI-CWSI:

1. **Calibracion:** recolecta pares (cwsi_nodo, vpd) de telemetria real, genera observaciones S2 sinteticas consistentes
2. **Prediccion:** zona sin nodo -> features S2 (NDWI, NDRE, VPD) -> modelo predice CWSI
3. **TRL 4 (demo):** bandas S2 sinteticas (consistentes con fenologia GDD)
4. **TRL 5+ (prod):** bandas S2 reales desde GEE / STAC

### 6.8 Auto-asignacion de Nodos a Zonas

`_autoasignar_zonas_nodos(db)` — ejecutada al startup:
- Para cada NodeConfig con zona_id=None y coordenadas GPS validas
- Busca ZoneConfig cuyo bounding box contenga el punto GPS
- Asigna zona_id automaticamente

---

## 7. MQTT (mqtt.py)

**Broker:** Mosquitto (localhost:1883)

**Topics:**
| Topic | QoS | Direccion | Contenido |
|-------|-----|-----------|-----------|
| `hydrovision/{node_id}/telemetry` | 1 | Nodo -> App | JSON NodePayload |
| `hydrovision/{node_id}/command` | 1 | App -> Nodo | `{irrigate: bool, ...}` |
| `hydrovision/{node_id}/downlink` | 0 | App -> Nodo | `{status, varietal, sol_sim?, command?}` |

**Consumer:** callback `_on_message` parsea payload y llama a `process_ingest()` en thread.
**Publisher:** `publish_command()` llamado por POST /api/irrigate para comandos manuales.
**Fallback:** si MQTT no esta disponible, /ingest (HTTP) funciona como alternativa.

---

## 8. Startup de la App (lifespan)

```python
async def lifespan(app):
    Base.metadata.create_all(bind=engine)    # Crear tablas
    db = SessionLocal()

    admin = _seed_admin_user(db)             # admin/hydrovision si DB vacia
    _seed_defaults(db, owner_id=admin.id)    # 12 zonas demo + config global
    _core_reload_zones(db)                   # Cargar ZONES dict en memoria
    _restore_node_irrigation(db)             # Restaurar estado de solenoides
    _autoasignar_zonas_nodos(db)             # Auto-asignar nodos a zonas por GPS

    db.close()
    start_mqtt()                             # Iniciar consumer MQTT en thread
    yield
    stop_mqtt()                              # Apagar MQTT al cerrar
```

**Routers registrados (en orden):**
auth, backoffice, pages, api, simulate, admin, report, inference, emails

---

## 9. Frontend — Stack y Paginas

### Stack
| Libreria | Version | CDN | Uso |
|----------|---------|-----|-----|
| Tailwind CSS | 3.x | CDN | Estilos utilitarios |
| Alpine.js | 3.x | defer | Reactividad frontend |
| Chart.js | 3.9.1 | pinned | Graficos (historial CWSI, barras de consumo) |
| Leaflet | 1.9.4 | CDN | Mapas interactivos |
| Leaflet.draw | 1.0.4 | CDN | Dibujo de poligonos (admin) |
| Google Fonts | — | CDN | Inter, IBM Plex Sans/Mono |

### Esquema de colores
- Header: Green 800 (#1B6B4A)
- Gradiente: Green 50-900
- CWSI: verde (< 0.30), amarillo (0.30-0.60), rojo (>= 0.60)

### 9.1 dashboard.html

**Componente Alpine:** `dashboard()`

**Estado:** fieldSubtitle, zones, nodes, refreshing, selectedZone, map, interval (auto-refresh)

**Funcionalidad:**
- Mapa Leaflet con poligonos de zonas (color por nivel de estres) y marcadores de nodos
- Cards de zona: CWSI, nivel de estres, estado de riego, fenologia, nodos asignados
- Cards de nodos: CWSI, HSI, bateria, ultima lectura
- Seccion de nodos sin zona con control de solenoide
- Toggle de riego manual por nodo
- Auto-refresh periodico

### 9.2 admin.html

**Componente Alpine:** `adminPanel()`

**Funcionalidad:**
- Layout 2 columnas: sidebar (lista zonas + formulario) + mapa Leaflet
- Crear/editar/eliminar zonas con Leaflet.draw (poligonos)
- Formulario: nombre, coordenadas, vertices JSON, varietal, rendimiento
- Validacion de overlap y limite de hectareas vs plan

### 9.3 backoffice.html

**Componente Alpine:** `backoffice()`

**Funcionalidad:**
- Tabla de usuarios con estado de plan (tier, vencimiento, dias restantes)
- CRUD de usuarios (crear, editar password/perfil, eliminar con cascade)
- CRUD de planes (crear, renovar, editar tier/vigencia)
- Asignacion de nodos a propietarios

### 9.4 informe.html

**Componente Alpine:** `reportGenerator()`

**Funcionalidad:**
- Selector de periodo (7/30/90 dias)
- Cards KPI: CWSI promedio/maximo, lluvia total, eventos de estres, agua ahorrada
- Descarga CSV de telemetria
- Boton de trazabilidad hidrica (visible solo para Tier >= 3)

### 9.5 trazabilidad.html (Tier 3)

**Componente Alpine:** `traceability()`

**Funcionalidad:**
- Gate de acceso: si tier < 3 muestra pantalla de upgrade
- 4 cards KPI: agua total (m3), riegos totales, eficiencia, cumplimiento
- Tabla paginada de eventos con busqueda
- Consumo por zona con barras visuales
- Seccion colapsable de metodologia
- Sello de auditoria con timestamp
- Exportar CSV

---

## 10. Schemas Pydantic (schemas.py)

### Payload de ingesta (NodePayload)
```python
class NodePayload(BaseModel):
    v: int                        # Version del payload
    node_id: str                  # ID del nodo
    ts: int                       # Timestamp Unix (epoch seconds)
    cycle: int                    # Numero de ciclo
    env: EnvData                  # {t_air, rh, wind_ms, rain_mm}
    thermal: ThermalData          # {tc_mean, tc_max, tc_wet, tc_dry, cwsi, valid_pixels}
    dendro: DendroData            # {mds_mm, mds_norm}
    hsi: HsiData                  # {value, w_cwsi, w_mds, wind_override}
    gps: GpsData                  # {lat, lon}
    bat_pct: int                  # Bateria %
    pm2_5: int                    # Particulas PM2.5 (0-1000, requerido)
    calidad_captura: str          # ok | lluvia | ...
    hmac: Optional[str] = None    # SHA256 firma (opcional en dev)
    solenoid: Optional[SolenoidData]  # {canal, active, reason, ciclos_activo}
```

### Zona (ZoneIn)
```python
class ZoneIn(BaseModel):
    name: str
    lat: float
    lon: float
    sw_lat: Optional[float]
    sw_lon: Optional[float]
    ne_lat: Optional[float]
    ne_lon: Optional[float]
    vertices: Optional[str]       # JSON [[lat,lon], ...]
    varietal: Optional[str]
    crop_yield_kg_ha: Optional[float]
```

### Inferencia (InferenceRequest)
```python
class InferenceRequest(BaseModel):
    thermal_image: list[list[float]]  # Matriz 32x24 de temperaturas (C)
    t_air: float
    rh: float
```

---

## 11. Filtrado Multi-tenant

Todos los endpoints de datos filtran por `owner_id == current_user.id`:
- `/api/status` — solo nodos propios
- `/api/alerts` — solo nodos propios
- `/api/history/{node_id}` — verifica propiedad
- `/api/zones` — zonas propias + zonas con nodos propios asignados
- `/api/admin/zones` — solo zonas propias
- `/api/admin/nodes` — solo nodos propios

Nodos con `owner_id = NULL` no aparecen en ningun endpoint de usuario.
El superadmin ve y gestiona todos los recursos desde el backoffice.

---

## 12. Infraestructura (infra/)

### docker-compose.yml
- **postgres**: PostgreSQL 15, puerto 5432
- **mosquitto**: MQTT broker, puerto 1883, sin auth (TRL 4)
- **app**: FastAPI uvicorn, build desde Dockerfile

### Desarrollo local
```bash
cd hydrovision-app
pip install -r requirements.txt
# Configurar .env (copiar de .env.example)
uvicorn app.main:app --host 0.0.0.0 --port 8096 --reload
```

DB default: SQLite (`hydrovision.db` en raiz del proyecto).
MQTT default: localhost:1883 (levantar Mosquitto o docker-compose).

---

## 13. Testing

- `test_sim.py` — ciclo de vida de simulacion
- `tests/test_mqtt_ingester.py` — consumer MQTT
- Stack: pytest + httpx (async client para FastAPI)
