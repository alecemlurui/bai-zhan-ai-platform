"""
services/auth.py

认证相关：密码哈希、JWT 生成/验证、用户注册/登录。

说明：使用标准库 PBKDF2-HMAC 替代 passlib+bcrypt，避免 bcrypt 版本兼容性
问题，同时减少外部依赖。
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from tortoise.exceptions import DoesNotExist, IntegrityError

from ..config import SETTINGS
from ..models import User


def _encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def get_password_hash(password: str, iterations: int = 260_000) -> str:
    salt = secrets.token_bytes(32)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"$pbkdf2-sha256${iterations}${_encode(salt)}${_encode(hash_bytes)}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password.startswith("$pbkdf2-sha256$"):
        return False
    try:
        _, _, iterations_str, salt_b64, hash_b64 = hashed_password.split("$")
        iterations = int(iterations_str)
        salt = _decode(salt_b64)
        expected_hash = _decode(hash_b64)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, iterations
        )
        return secrets.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=SETTINGS.JWT_EXP_SECONDS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SETTINGS.JWT_SECRET, algorithm=SETTINGS.JWT_ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, SETTINGS.JWT_SECRET, algorithms=[SETTINGS.JWT_ALGORITHM])


async def register_user(username: str, password: str, email: str | None = None) -> User:
    hashed = get_password_hash(password)
    try:
        user = await User.create(
            username=username,
            password_hash=hashed,
            email=email,
        )
    except IntegrityError:
        raise ValueError("Username already registered")
    return user


async def authenticate_user(username: str, password: str) -> User | None:
    try:
        user = await User.get(username=username)
    except DoesNotExist:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
