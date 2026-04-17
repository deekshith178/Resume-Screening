from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


# ---------------------------------------------------------------------------
# Shared settings
# ---------------------------------------------------------------------------


SECRET_KEY = os.environ.get("APP_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60



security_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Candidate token (HMAC) helpers
# ---------------------------------------------------------------------------


def generate_candidate_token() -> str:
    """Generate a secure opaque token for candidate login links."""
    raw = os.urandom(32)
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def hash_token(token: str) -> str:
    """Hash a token using HMAC-SHA256 with the app secret."""
    mac = hmac.new(SECRET_KEY.encode("utf-8"), token.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    """Constant-time comparison of token hash."""
    expected = hash_token(token)
    return hmac.compare_digest(expected, token_hash)


# ---------------------------------------------------------------------------
# Recruiter JWT helpers
# ---------------------------------------------------------------------------


def create_recruiter_access_token(
    subject: str,
    role: str = "recruiter",
    recruiter_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: Dict[str, Any] = {"sub": subject, "role": role, "exp": expire}
    if recruiter_id is not None:
        to_encode["recruiter_id"] = recruiter_id
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_current_recruiter(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> Dict[str, Any]:
    """FastAPI dependency to enforce recruiter auth on protected endpoints."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    payload = decode_token(credentials.credentials)
    # Allow both 'recruiter' and 'admin' roles
    if payload.get("role") not in ["recruiter", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return payload




import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt.checkpw requires bytes
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    # bcrypt.hashpw returns bytes, decode to string for storage
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')




def verify_recruiter_credentials(username: str, password: str) -> bool:
    """Verify recruiter credentials against the database."""
    import logging
    from .database import get_session
    from .models import Recruiter
    from sqlalchemy import select

    logger = logging.getLogger("uvicorn")
    logger.info(f"[VERIFY_CREDS] Checking credentials for: {username}")
    
    # ⚠️ DEV BYPASS - allows test@example.com / password123 without bcrypt
    if username == "test@example.com" and password == "password123":
        logger.info("[VERIFY_CREDS] DEV BYPASS: Using hardcoded test credentials")
        return True
    
    with get_session() as db:
        user = db.execute(select(Recruiter).where(Recruiter.email == username)).scalars().first()
        if not user:
            logger.warning(f"[VERIFY_CREDS] User not found: {username}")
            return False
        
        logger.info(f"[VERIFY_CREDS] User found: {user.email}, role: {user.role}")
        
        password_valid = verify_password(password, user.hashed_password)
        logger.info(f"[VERIFY_CREDS] Password valid: {password_valid}")
        
        if not password_valid:
            return False
        return True













