"""
权限控制系统
提供基于角色的访问控制（RBAC）和基于权限的访问控制
"""
from enum import Enum
from functools import wraps
from typing import List, Optional, Set, Callable

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials


class Permission(str, Enum):
    """权限枚举类 - 使用 resource:operation 格式"""

    # 账号管理权限
    ACCOUNT_READ = "account:read"
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_UPDATE = "account:update"
    ACCOUNT_DELETE = "account:delete"

    # 内容管理权限
    CONTENT_READ = "content:read"
    CONTENT_CREATE = "content:create"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"

    # 发布管理权限
    PUBLISHER_READ = "publisher:read"
    PUBLISHER_EXECUTE = "publisher:execute"
    PUBLISHER_CONFIG = "publisher:config"

    # 定时任务权限
    SCHEDULER_READ = "scheduler:read"
    SCHEDULER_CREATE = "scheduler:create"
    SCHEDULER_UPDATE = "scheduler:update"
    SCHEDULER_DELETE = "scheduler:delete"
    SCHEDULER_EXECUTE = "scheduler:execute"

    # 发布池权限
    PUBLISH_POOL_READ = "publish-pool:read"
    PUBLISH_POOL_EXECUTE = "publish-pool:execute"

    # 用户管理权限（仅管理员）
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 客户管理权限（仅管理员）
    CUSTOMER_READ = "customer:read"
    CUSTOMER_CREATE = "customer:create"
    CUSTOMER_UPDATE = "customer:update"
    CUSTOMER_DELETE = "customer:delete"

    # 平台管理权限（仅管理员）
    PLATFORM_READ = "platform:read"
    PLATFORM_CREATE = "platform:create"
    PLATFORM_UPDATE = "platform:update"
    PLATFORM_DELETE = "platform:delete"

    # 系统配置权限（仅管理员）
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"

    # 写作风格管理（仅管理员）
    WRITING_STYLE_READ = "writing-style:read"
    WRITING_STYLE_CREATE = "writing-style:create"
    WRITING_STYLE_UPDATE = "writing-style:update"
    WRITING_STYLE_DELETE = "writing-style:delete"

    # 内容主题管理（仅管理员）
    CONTENT_THEME_READ = "content-theme:read"
    CONTENT_THEME_CREATE = "content-theme:create"
    CONTENT_THEME_UPDATE = "content-theme:update"
    CONTENT_THEME_DELETE = "content-theme:delete"

    # 审计日志权限（仅管理员）
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"


# 角色权限映射
ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "admin": {
        # 管理员拥有所有权限
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_CREATE,
        Permission.ACCOUNT_UPDATE,
        Permission.ACCOUNT_DELETE,
        Permission.CONTENT_READ,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.PUBLISHER_READ,
        Permission.PUBLISHER_EXECUTE,
        Permission.PUBLISHER_CONFIG,
        Permission.SCHEDULER_READ,
        Permission.SCHEDULER_CREATE,
        Permission.SCHEDULER_UPDATE,
        Permission.SCHEDULER_DELETE,
        Permission.SCHEDULER_EXECUTE,
        Permission.PUBLISH_POOL_READ,
        Permission.PUBLISH_POOL_EXECUTE,
        Permission.USER_READ,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.CUSTOMER_READ,
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_UPDATE,
        Permission.CUSTOMER_DELETE,
        Permission.PLATFORM_READ,
        Permission.PLATFORM_CREATE,
        Permission.PLATFORM_UPDATE,
        Permission.PLATFORM_DELETE,
        Permission.CONFIG_READ,
        Permission.CONFIG_UPDATE,
        Permission.WRITING_STYLE_READ,
        Permission.WRITING_STYLE_CREATE,
        Permission.WRITING_STYLE_UPDATE,
        Permission.WRITING_STYLE_DELETE,
        Permission.CONTENT_THEME_READ,
        Permission.CONTENT_THEME_CREATE,
        Permission.CONTENT_THEME_UPDATE,
        Permission.CONTENT_THEME_DELETE,
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
    },
    "operator": {
        # 运营人员权限
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_UPDATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.PUBLISHER_READ,
        Permission.PUBLISHER_EXECUTE,
        Permission.SCHEDULER_READ,
        Permission.SCHEDULER_CREATE,
        Permission.SCHEDULER_UPDATE,
        Permission.SCHEDULER_DELETE,
        Permission.SCHEDULER_EXECUTE,
        Permission.PUBLISH_POOL_READ,
        Permission.PUBLISH_POOL_EXECUTE,
    },
    "customer": {
        # 客户只读权限
        Permission.ACCOUNT_READ,
        Permission.CONTENT_READ,
        Permission.PUBLISHER_READ,
        Permission.SCHEDULER_READ,
        Permission.PUBLISH_POOL_READ,
    },
    "editor": {
        # 编辑权限
        Permission.CONTENT_READ,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
    },
    "viewer": {
        # 查看权限
        Permission.CONTENT_READ,
    },
}


def get_role_permissions(role: str) -> Set[Permission]:
    """
    获取角色的权限集合

    Args:
        role: 角色名称

    Returns:
        权限集合
    """
    return ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(user) -> Set[Permission]:
    """
    获取用户的权限集合（基于角色）

    Args:
        user: 用户对象

    Returns:
        权限集合
    """
    return get_role_permissions(user.role)


def has_permission(user, required_permission: Permission) -> bool:
    """
    检查用户是否拥有指定权限

    Args:
        user: 用户对象
        required_permission: 需要的权限

    Returns:
        是否拥有权限
    """
    if user.role == "admin":
        return True

    user_permissions = get_user_permissions(user)
    return required_permission in user_permissions


def has_any_permission(user, required_permissions: List[Permission]) -> bool:
    """
    检查用户是否拥有任意一个指定权限

    Args:
        user: 用户对象
        required_permissions: 需要的权限列表

    Returns:
        是否拥有任意权限
    """
    if user.role == "admin":
        return True

    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in required_permissions)


def has_role(user, required_role: str) -> bool:
    """
    检查用户是否拥有指定角色

    Args:
        user: 用户对象
        required_role: 需要的角色

    Returns:
        是否拥有角色
    """
    return user.role == required_role


def has_any_role(user, required_roles: List[str]) -> bool:
    """
    检查用户是否拥有任意一个指定角色

    Args:
        user: 用户对象
        required_roles: 需要的角色列表

    Returns:
        是否拥有任意角色
    """
    return user.role in required_roles


def require_permission(*permissions: Permission):
    """
    权限装饰器 - 要求用户拥有指定权限（满足任意一个即可）

    用法:
        @require_permission(Permission.ACCOUNT_CREATE, Permission.ACCOUNT_UPDATE)
        async def create_account(...):
            ...

    Args:
        *permissions: 需要的权限列表（满足任意一个即可）
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 中获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户"
                )

            if not has_any_permission(current_user, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下权限之一: {[p.value for p in permissions]}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(*permissions: Permission):
    """
    权限装饰器 - 要求用户拥有所有指定权限

    用法:
        @require_all_permissions(Permission.ACCOUNT_CREATE, Permission.ACCOUNT_UPDATE)
        async def create_and_update_account(...):
            ...

    Args:
        *permissions: 需要的权限列表（必须全部满足）
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 中获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户"
                )

            user_permissions = get_user_permissions(current_user)
            missing_permissions = [p for p in permissions if p not in user_permissions]

            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，缺少以下权限: {[p.value for p in missing_permissions]}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: str):
    """
    角色装饰器 - 要求用户拥有指定角色（满足任意一个即可）

    用法:
        @require_role("admin", "operator")
        async def admin_or_operator_endpoint(...):
            ...

    Args:
        *roles: 需要的角色列表（满足任意一个即可）
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 中获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户"
                )

            if not has_any_role(current_user, list(roles)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下角色之一: {roles}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
