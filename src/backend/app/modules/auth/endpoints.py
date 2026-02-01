from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.modules.shared.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_refresh_token,
    decode_reset_token,
)
from app.db.sql_db import get_db
from app.modules.shared.schemas.api import ApiResponse
from app.modules.shared.schemas.auth import (
    ForgotPasswordRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyTokenRequest,
)
from app.modules.shared.schemas.user import UserCreate, UserLogin, UserRead
from app.modules.shared.services import user_service
from app.services.audit_service import AuditService

router = APIRouter()


def _token_response(user_id: str) -> TokenPair:
    access_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=ApiResponse[UserRead])
async def register(payload: UserCreate = Body(...), db: Session = Depends(get_db)):
    if user_service.get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在"
        )
    if payload.username and user_service.get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )
    user = user_service.create_user(db, payload)
    return ApiResponse(success=True, data=UserRead.from_orm(user))


@router.post("/login", response_model=ApiResponse[TokenPair])
async def login(request: Request, db: Session = Depends(get_db)) -> Any:
    """
    支持 JSON 与 form-urlencoded（username/password）两种输入。
    JSON: {email|username, password}
    Form: username=...&password=...
    """
    payload: UserLogin
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            body = await request.json()
            payload = UserLogin.model_validate(body)
        else:
            form = await request.form()
            # 直接验证必填字段
            password = form.get("password")
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="密码不能为空",
                )

            email = form.get("email")
            username = form.get("username")
            if not email and not username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱或用户名不能为空",
                )

            payload = UserLogin(
                username=username,
                email=email,
                password=password,
            )
    except ValidationError as e:
        # 将Pydantic ValidationError转换为FastAPI的RequestValidationError
        # 这样validation_exception_handler就能捕获并返回422状态码
        raise RequestValidationError(e.errors()) from None


    if not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码不能为空",
        )

    identifier = payload.email or payload.username or ""
    use_email = bool(payload.email) or ("@" in identifier)

    user = user_service.authenticate_user(
        db, identifier, payload.password, use_email=use_email
    )

    # 审计日志
    if user and user.is_active:
        AuditService.log_event(
            db=db,
            event_type="user_login",
            user_id=user.id,
            result="success",
            details={"username": user.username, "email": user.email},
            request=request
        )
        token_pair = _token_response(str(user.id))
        return ApiResponse(success=True, data=token_pair)
    else:
        # 记录失败的登录尝试
        AuditService.log_event(
            db=db,
            event_type="user_login_failed",
            user_id=None,
            result="failure",
            details={"identifier": identifier},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=ApiResponse[TokenPair])
async def refresh(payload: RefreshRequest = Body(...)) -> Any:
    user_id = decode_refresh_token(payload.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_pair = _token_response(str(user_id))
    return ApiResponse(success=True, data=token_pair)


@router.get("/me", response_model=ApiResponse[UserRead])
async def me(current_user: Any = Depends(get_current_user)) -> Any:
    return ApiResponse(success=True, data=UserRead.from_orm(current_user))


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response:
    # 记录登出审计日志
    AuditService.log_event(
        db=db,
        event_type="user_logout",
        user_id=current_user.id if hasattr(current_user, 'id') else None,
        result="success",
        details={"username": current_user.username if hasattr(current_user, 'username') else None},
        request=request
    )
    # 无状态 JWT，无需服务端存储，直接返回 204
    return Response(status_code=204)


@router.post("/forgot-password", response_model=ApiResponse[Dict[str, Any]])
async def forgot_password(
    payload: ForgotPasswordRequest = Body(...), db: Session = Depends(get_db)
) -> Any:
    user = user_service.get_user_by_email(db, payload.email)
    if not user:
        # 不暴露存在性，仍返回成功
        return ApiResponse(success=True, data={"message": "If the account exists, email sent."})
    token = create_reset_token(str(user.id))
    # 在此可集成邮件发送，这里日志/占位
    return ApiResponse(success=True, data={"reset_token": token})


@router.post("/reset-password", response_model=ApiResponse[Dict[str, Any]])
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    user_id = decode_reset_token(payload.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效或过期的重置令牌"
        )
    user = user_service.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")
    user_service.update_password(db, user, payload.password)

    # 记录密码重置审计日志
    AuditService.log_event(
        db=db,
        event_type="password_reset",
        user_id=user.id,
        result="success",
        details={"username": user.username},
        request=request
    )

    return ApiResponse(success=True, data={"message": "密码已重置"})


@router.post("/verify", response_model=ApiResponse[Dict[str, Any]])
async def verify_reset_token(payload: VerifyTokenRequest = Body(...)) -> Any:
    user_id = decode_reset_token(payload.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效或过期的重置令牌"
        )
    return ApiResponse(success=True, data={"user_id": user_id, "valid": True})
