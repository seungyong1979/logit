"""
Logit Blog — JWT 인증 유틸리티
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── 비밀번호 ────────────────────────────────────────────────
def hash_password(password: str) -> str:
    import bcrypt as _bcrypt
    pw = password.encode("utf-8")[:72]
    return _bcrypt.hashpw(pw, _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt as _bcrypt
    pw = plain.encode("utf-8")[:72]
    return _bcrypt.checkpw(pw, hashed.encode("utf-8"))


# ── JWT ─────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# ── 현재 관리자 추출 (쿠키 기반) ────────────────────────────
def get_current_admin(request: Request, db: Session = Depends(get_db)) -> Admin:
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    admin = db.query(Admin).filter(Admin.email == payload.get("sub")).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return admin


def get_current_admin_optional(request: Request, db: Session = Depends(get_db)) -> Optional[Admin]:
    """인증 실패 시 None 반환 (페이지 리다이렉트용)"""
    try:
        return get_current_admin(request, db)
    except HTTPException:
        return None


def require_admin(request: Request, db: Session = Depends(get_db)) -> Admin:
    """관리자 필수 — 미인증 시 로그인 페이지로 리다이렉트"""
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/admin/login"}
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/admin/login"}
        )
    admin = db.query(Admin).filter(Admin.email == payload.get("sub")).first()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/admin/login"}
        )
    return admin


# ── 초기 관리자 계정 생성 ────────────────────────────────────
def create_initial_admin(db: Session):
    existing = db.query(Admin).filter(Admin.email == settings.ADMIN_EMAIL).first()
    if not existing:
        admin = Admin(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            name="운영자",
        )
        db.add(admin)
        db.commit()
        print(f"[Logit] 초기 관리자 계정 생성: {settings.ADMIN_EMAIL}")
