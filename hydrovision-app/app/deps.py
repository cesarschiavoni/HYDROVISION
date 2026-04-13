"""
deps.py — Dependencias compartidas entre routers
HydroVision AG

Contiene:
  - get_db: dependencia FastAPI para sesiones de base de datos
  - Seguridad: HMAC verification + rate limiting para /ingest
  - _audit: registro de eventos en audit_log
"""

import base64
import hashlib
import hmac as _hmac
import json
import secrets
import time
from collections import defaultdict

from fastapi import Cookie, HTTPException
from fastapi.responses import RedirectResponse

from app.config import HMAC_SECRET, SESSION_MAX_AGE
from app.models import AuditLog, SessionLocal, User

# ---------------------------------------------------------------------------
# DB session
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Seguridad: HMAC + Rate limiting
# ---------------------------------------------------------------------------

INGEST_SECRET = HMAC_SECRET

_rate_limit: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60.0
_RATE_LIMIT_MAX = 100


def check_rate_limit(node_id: str) -> bool:
    """Devuelve True si el nodo está dentro del límite de requests/minuto."""
    import time
    now = time.time()
    window = _rate_limit[node_id]
    window[:] = [t for t in window if now - t < _RATE_LIMIT_WINDOW]
    if len(window) >= _RATE_LIMIT_MAX:
        return False
    window.append(now)
    return True


def verify_hmac(payload) -> bool:
    """Verifica la firma HMAC-SHA256 del payload del nodo."""
    if INGEST_SECRET in ("dev-secret-change-in-production", "dev_secret_change_in_prod"):
        return True
    if not payload.hmac:
        return False
    msg = f"{payload.node_id}:{payload.ts}:{payload.cycle}".encode()
    expected = _hmac.new(INGEST_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return _hmac.compare_digest(payload.hmac, expected)


# ---------------------------------------------------------------------------
# Auth — password hashing y session cookie firmada con HMAC-SHA256
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Devuelve 'salt$hash' usando pbkdf2_hmac sha256 (300 000 iteraciones)."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 300_000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verifica password contra el hash almacenado."""
    try:
        salt, key_hex = stored.split("$", 1)
    except ValueError:
        return False
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 300_000)
    return _hmac.compare_digest(key.hex(), key_hex)


def make_session_token(user_id: int) -> str:
    """Crea un token de sesión firmado con HMAC-SHA256 (8 h por defecto)."""
    payload = json.dumps({"uid": user_id, "ts": int(time.time())})
    sig = _hmac.new(HMAC_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}|{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_session_token(token: str) -> int | None:
    """Decodifica y verifica el token. Devuelve user_id o None si inválido/expirado."""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        payload, sig = raw.rsplit("|", 1)
        expected = _hmac.new(HMAC_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(sig, expected):
            return None
        data = json.loads(payload)
        if time.time() - data["ts"] > SESSION_MAX_AGE:
            return None
        return data["uid"]
    except Exception:
        return None


def require_login(hv_session: str | None = Cookie(default=None)):
    """Dependency para páginas protegidas. Redirige a /login si no hay sesión válida."""
    if hv_session and decode_session_token(hv_session) is not None:
        return True
    raise HTTPException(status_code=302, headers={"Location": "/login"})


def get_current_user(
    hv_session: str | None = Cookie(default=None),
    db=None,
):
    """
    Dependency para endpoints API. Devuelve el User autenticado o lanza 401 JSON.
    Usar con doble dependencia: get_current_user necesita get_db inyectado.
    Usar la versión pre-configurada: current_user_dep (ver abajo).
    """
    if not hv_session:
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = decode_session_token(hv_session)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Sesión expirada")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def _make_current_user_dep():
    """Retorna una dependency FastAPI que combina get_db + get_current_user."""
    from fastapi import Depends

    def _dep(hv_session: str | None = Cookie(default=None), db=Depends(get_db)):
        return get_current_user(hv_session=hv_session, db=db)

    return _dep


current_user_dep = _make_current_user_dep()


def _make_user_only_dep():
    """Dependency que solo permite usuarios con role='user'. Superadmin → 403."""
    from fastapi import Depends

    def _dep(hv_session: str | None = Cookie(default=None), db=Depends(get_db)):
        user = get_current_user(hv_session=hv_session, db=db)
        if user.role == "superadmin":
            raise HTTPException(status_code=403, detail="Superadmin debe usar /api/backoffice")
        return user

    return _dep


user_only_dep = _make_user_only_dep()


def require_superadmin(hv_session: str | None = Cookie(default=None)):
    """Dependency para páginas back-office. Redirige a /login si no es superadmin."""
    if not hv_session:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    # Verificar token primero sin DB
    user_id = decode_session_token(hv_session)
    if user_id is None:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user_id   # el router de backoffice verifica el role con get_db


def _make_superadmin_api_dep():
    from fastapi import Depends

    def _dep(hv_session: str | None = Cookie(default=None), db=Depends(get_db)):
        user = get_current_user(hv_session=hv_session, db=db)
        if user.role != "superadmin":
            raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
        return user

    return _dep


superadmin_dep = _make_superadmin_api_dep()


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def audit(db, event: str, node_id: str = None, detail: str = None, ip: str = None, user_id: int = None):
    db.add(AuditLog(event=event, node_id=node_id, detail=detail, ip=ip, user_id=user_id))
    db.commit()
