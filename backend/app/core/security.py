"""
安全模块 — JWT 签发/验证 + 密码哈希
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import JWTError, jwt
import bcrypt as _bcrypt

from app.core.config import settings

# JWT 常量
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希"""
    return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    """生成 bcrypt 哈希"""
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def create_access_token(
    subject: Any,
    tenant_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """签发 JWT Access Token

    payload 中注入 tenant_id 用于权限隔离
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "exp": expire,
    }
    if tenant_id is not None:
        to_encode["tenant_id"] = tenant_id
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码并验证 JWT Token

    Raises:
        JWTError: Token 无效或已过期
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
