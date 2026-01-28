from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.sql_db import get_db
from app.modules.shared.services import user_service

_allow_bypass = bool(getattr(settings, "DEBUG", False)) and bool(
    getattr(settings, "DEV_AUTH_BYPASS", False)
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_STR}/v1/auth/login",
    auto_error=not _allow_bypass,
)


async def get_current_subject(
    token: Optional[str] = Depends(oauth2_scheme),
) -> str:
    """
    验证当前用户
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if _allow_bypass and not token:
        return str(getattr(settings, "DEV_AUTH_BYPASS_SUBJECT", "dev-user"))

    try:
        user_id = decode_access_token(token)
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception

    return str(user_id)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    返回当前登录用户对象
    """
    user_id = await get_current_subject(token)
    user = user_service.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
