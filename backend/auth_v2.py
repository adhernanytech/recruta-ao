"""
auth.py — RecrutaAO v3 — JWT com company_id para isolamento multi-tenant
"""

import os, hmac, hashlib, base64, json, time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("JWT_SECRET", "recruitao_secret_dev_2024_change_in_prod")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return base64.b64encode(salt + key).decode()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        raw  = base64.b64decode(hashed.encode())
        salt = raw[:16]
        stored = raw[16:]
        test   = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 260_000)
        return hmac.compare_digest(stored, test)
    except:
        return False

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))

def create_access_token(user_id: int, email: str, role: str, company_id: int) -> str:
    """JWT agora inclui company_id — chave do isolamento multi-tenant."""
    header  = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "sub":        str(user_id),
        "email":      email,
        "role":       role,
        "company_id": company_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }).encode())
    sig = _b64url_encode(
        hmac.new(SECRET_KEY.encode(),
                 f"{header}.{payload}".encode(),
                 hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{sig}"

def decode_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3: raise ValueError("formato inválido")
        header, payload, sig = parts
        expected = _b64url_encode(
            hmac.new(SECRET_KEY.encode(),
                     f"{header}.{payload}".encode(),
                     hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected): raise ValueError("assinatura inválida")
        data = json.loads(_b64url_decode(payload))
        if data.get("exp", 0) < time.time(): raise ValueError("token expirado")
        return data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Token inválido: {e}",
                            headers={"WWW-Authenticate": "Bearer"})

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    return decode_token(credentials.credentials)

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a administradores")
    return user

def require_recruiter(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in ("admin", "recruiter"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso não autorizado")
    return user
