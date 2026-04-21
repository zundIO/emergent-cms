"""Authentication helpers for the embedded CMS.

Credentials are stored in ``cms-data/.cms-env.json`` (auto-created on first
setup).  Passwords are bcrypt-hashed; sessions use JWT cookies signed with a
randomly generated secret.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Request

from . import storage

COOKIE_NAME = "cms_token"
JWT_ALG = "HS256"
SESSION_DAYS = 7


def _jwt_secret() -> str:
    secret = os.environ.get("CMS_SECRET") or storage.get_env("CMS_SECRET")
    if not secret:
        secret = secrets.token_hex(32)
        storage.set_env({"CMS_SECRET": secret})
    return secret


def is_setup_complete() -> bool:
    env_pw = os.environ.get("CMS_ADMIN_PASSWORD") or storage.get_env("CMS_ADMIN_PASSWORD")
    return bool(env_pw)


def save_admin_password(plain: str) -> None:
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")
    storage.set_env({"CMS_ADMIN_PASSWORD": hashed})
    # Make sure the JWT secret exists too
    _jwt_secret()


def verify_password(plain: str) -> bool:
    stored = os.environ.get("CMS_ADMIN_PASSWORD") or storage.get_env("CMS_ADMIN_PASSWORD")
    if not stored:
        return False
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    # Legacy plain-text fallback
    return plain == stored


def create_token() -> str:
    payload = {
        "role": "admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALG)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALG])
    except Exception:
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get(COOKIE_NAME)


def is_authenticated(request: Request) -> bool:
    token = get_token_from_request(request)
    return bool(token and verify_token(token))
