"""
auth.py — Autenticação JWT para o RecrutaAO
- Registo e login de utilizadores
- Tokens JWT com expiração
- Controlo de acesso por role (admin / recruiter)
"""

import os
import hmac
import hashlib
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ─── Configuração ─────────────────────────────────────────────────────────────

SECRET_KEY  = os.environ.get("JWT_SECRET", "recruitao_secret_dev_2024_change_in_prod")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8   # 8 horas

bearer_scheme = HTTPBearer()

# ─── Password hashing (bcrypt-like com PBKDF2) ────────────────────────────────

def hash_password(password: str) -> str:
    """Gera hash seguro da password com salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return base64.b64encode(salt + key).decode()

def verify_password(plain: str, hashed: str) -> bool:
    """Verifica password contra o hash armazenado."""
    try:
        raw   = base64.b64decode(hashed.encode())
        salt  = raw[:16]
        stored_key = raw[16:]
        test_key   = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 260_000)
        return hmac.compare_digest(stored_key, test_key)
    except Exception:
        return False

# ─── JWT manual (sem dependência externa) ─────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))

def create_access_token(user_id: int, email: str, role: str) -> str:
    header  = _b64url_encode(json.dumps({"alg": ALGORITHM, "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "sub":   str(user_id),
        "email": email,
        "role":  role,
        "iat":   int(time.time()),
        "exp":   int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }).encode())
    sig_input = f"{header}.{payload}".encode()
    sig = _b64url_encode(
        hmac.new(SECRET_KEY.encode(), sig_input, hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{sig}"

def decode_token(token: str) -> dict:
    """Decodifica e valida o JWT. Lança HTTPException se inválido."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("formato inválido")
        header, payload, sig = parts
        # verifica assinatura
        expected = _b64url_encode(
            hmac.new(SECRET_KEY.encode(),
                     f"{header}.{payload}".encode(),
                     hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            raise ValueError("assinatura inválida")
        data = json.loads(_b64url_decode(payload))
        # verifica expiração
        if data.get("exp", 0) < time.time():
            raise ValueError("token expirado")
        return data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {e}",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ─── Dependências FastAPI

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Injeta o utilizador autenticado em qualquer endpoint protegido."""
    return decode_token(credentials.credentials)

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    # Restringe o endpoint a utilizadores com role=admin.
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return user

def require_recruiter(user: dict = Depends(get_current_user)) -> dict:
    # Permite admin e recruiter.
    if user.get("role") not in ("admin", "recruiter"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado"
        )
    return user