"""
审计装饰器
用于自动记录操作到审计日志
"""
from functools import wraps
from typing import Optional, Dict, Any, Callable
from fastapi import Request

from app.services.audit_service import AuditService


def audit_log(
    event_type: str,
    result_on_success: str = "success",
    result_on_failure: str = "failure",
    include_request: bool = True
):
    """
    审计日志装饰器

    用法:
        @audit_log("user_login")
        async def login(...):
            ...

        @audit_log("content_delete", include_request=False)
        async def delete_content(...):
            ...

    :param event_type: 事件类型
    :param result_on_success: 成功时的结果（默认 "success"）
    :param result_on_failure: 失败时的结果（默认 "failure"）
    :param include_request: 是否包含请求对象（用于提取 IP 和 User-Agent）
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 尝试从 kwargs 中提取常用参数
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request = kwargs.get("request") if include_request else None

            # 尝试获取用户ID
            user_id = None
            if current_user:
                user_id = current_user.id if hasattr(current_user, 'id') else current_user

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 记录成功的审计日志
                if db:
                    try:
                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_success,
                            details={"function": func.__name__},
                            request=request
                        )
                    except Exception as e:
                        # 记录审计日志失败不应影响主业务流程
                        print(f"Failed to log audit event: {str(e)}")

                return result

            except Exception as e:
                # 记录失败的审计日志
                if db:
                    try:
                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_failure,
                            details={
                                "function": func.__name__,
                                "error": str(e),
                                "error_type": type(e).__name__
                            },
                            request=request
                        )
                    except Exception as audit_error:
                        print(f"Failed to log audit event: {str(audit_error)}")

                # 重新抛出异常
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数版本
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request = kwargs.get("request") if include_request else None

            user_id = None
            if current_user:
                user_id = current_user.id if hasattr(current_user, 'id') else current_user

            try:
                result = func(*args, **kwargs)

                if db:
                    try:
                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_success,
                            details={"function": func.__name__},
                            request=request
                        )
                    except Exception as e:
                        print(f"Failed to log audit event: {str(e)}")

                return result

            except Exception as e:
                if db:
                    try:
                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_failure,
                            details={
                                "function": func.__name__,
                                "error": str(e),
                                "error_type": type(e).__name__
                            },
                            request=request
                        )
                    except Exception as audit_error:
                        print(f"Failed to log audit event: {str(audit_error)}")

                raise

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def audit_log_with_details(
    event_type: str,
    get_details: Callable[..., Dict[str, Any]],
    result_on_success: str = "success",
    result_on_failure: str = "failure",
    include_request: bool = True
):
    """
    带自定义详细信息的审计日志装饰器

    用法:
        @audit_log_with_details(
            "content_update",
            lambda **kwargs: {"content_id": kwargs.get("content_id")}
        )
        async def update_content(content_id: int, ...):
            ...

    :param event_type: 事件类型
    :param get_details: 函数，接收 kwargs 返回详细信息字典
    :param result_on_success: 成功时的结果
    :param result_on_failure: 失败时的结果
    :param include_request: 是否包含请求对象
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request = kwargs.get("request") if include_request else None

            user_id = None
            if current_user:
                user_id = current_user.id if hasattr(current_user, 'id') else current_user

            try:
                result = await func(*args, **kwargs)

                if db:
                    try:
                        details = get_details(**kwargs) if get_details else {}
                        details["function"] = func.__name__

                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_success,
                            details=details,
                            request=request
                        )
                    except Exception as e:
                        print(f"Failed to log audit event: {str(e)}")

                return result

            except Exception as e:
                if db:
                    try:
                        details = get_details(**kwargs) if get_details else {}
                        details.update({
                            "function": func.__name__,
                            "error": str(e),
                            "error_type": type(e).__name__
                        })

                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_failure,
                            details=details,
                            request=request
                        )
                    except Exception as audit_error:
                        print(f"Failed to log audit event: {str(audit_error)}")

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request = kwargs.get("request") if include_request else None

            user_id = None
            if current_user:
                user_id = current_user.id if hasattr(current_user, 'id') else current_user

            try:
                result = func(*args, **kwargs)

                if db:
                    try:
                        details = get_details(**kwargs) if get_details else {}
                        details["function"] = func.__name__

                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_success,
                            details=details,
                            request=request
                        )
                    except Exception as e:
                        print(f"Failed to log audit event: {str(e)}")

                return result

            except Exception as e:
                if db:
                    try:
                        details = get_details(**kwargs) if get_details else {}
                        details.update({
                            "function": func.__name__,
                            "error": str(e),
                            "error_type": type(e).__name__
                        })

                        AuditService.log_event(
                            db=db,
                            event_type=event_type,
                            user_id=user_id,
                            result=result_on_failure,
                            details=details,
                            request=request
                        )
                    except Exception as audit_error:
                        print(f"Failed to log audit event: {str(audit_error)}")

                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
