"""
routers/auth.py — Login / logout
HydroVision AG
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.deps import (
    decode_session_token, get_db, hash_password,
    make_session_token, verify_password,
)
from app.config import SESSION_MAX_AGE
from app.models import User

router = APIRouter()

_TEMPLATES = Path(__file__).parent.parent / "templates"


def _redirect_for(user: User) -> str:
    return "/backoffice" if user.role == "superadmin" else "/dashboard"


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db=Depends(get_db)):
    token = request.cookies.get("hv_session")
    if token:
        user_id = decode_session_token(token)
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return RedirectResponse(_redirect_for(user), status_code=302)
    html = (_TEMPLATES / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@router.post("/login")
def login_submit(
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        html = (_TEMPLATES / "login.html").read_text(encoding="utf-8")
        html = html.replace("<!--ERROR-->",
            '<p class="text-red-500 text-sm text-center mt-2">Usuario o contraseña incorrectos</p>')
        return HTMLResponse(html, status_code=401)

    token = make_session_token(user.id)
    response = RedirectResponse(_redirect_for(user), status_code=302)
    response.set_cookie(
        key="hv_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("hv_session")
    return response
