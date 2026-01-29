"""
权限系统单元测试
测试权限枚举、角色权限映射和权限检查函数
"""
import pytest
from app.core.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    get_role_permissions,
    get_user_permissions,
    has_permission,
    has_any_permission,
    has_role,
    has_any_role,
    require_permission,
    require_all_permissions,
    require_role
)
from app.core.exceptions import PermissionDeniedException


class MockUser:
    """模拟用户对象"""
    def __init__(self, role="operator", user_id=1):
        self.role = role
        self.id = user_id
        self.username = f"testuser_{user_id}"


@pytest.mark.unit
def test_permission_enum_values():
    """测试权限枚举值"""
    # 账号管理权限
    assert Permission.ACCOUNT_READ == "account:read"
    assert Permission.ACCOUNT_CREATE == "account:create"
    assert Permission.ACCOUNT_UPDATE == "account:update"
    assert Permission.ACCOUNT_DELETE == "account:delete"

    # 内容管理权限
    assert Permission.CONTENT_READ == "content:read"
    assert Permission.CONTENT_CREATE == "content:create"
    assert Permission.CONTENT_PUBLISH == "content:publish"

    # 发布管理权限
    assert Permission.PUBLISHER_READ == "publisher:read"
    assert Permission.PUBLISHER_EXECUTE == "publisher:execute"

    print("✓ 权限枚举值测试通过")


@pytest.mark.unit
def test_role_permissions_admin():
    """测试管理员权限"""
    admin_perms = ROLE_PERMISSIONS.get("admin")

    # 管理员应该拥有所有权限
    assert admin_perms is not None
    assert len(admin_perms) > 30  # 管理员应该有30+个权限

    # 验证关键权限
    assert Permission.USER_DELETE in admin_perms
    assert Permission.CUSTOMER_DELETE in admin_perms
    assert Permission.CONFIG_UPDATE in admin_perms

    print(f"✓ 管理员权限测试通过 (拥有 {len(admin_perms)} 个权限)")


@pytest.mark.unit
def test_role_permissions_operator():
    """测试运营人员权限"""
    operator_perms = ROLE_PERMISSIONS.get("operator")

    # 运营人员应该有基本权限
    assert operator_perms is not None

    # 验证应该有的权限
    assert Permission.ACCOUNT_READ in operator_perms
    assert Permission.ACCOUNT_UPDATE in operator_perms
    assert Permission.CONTENT_CREATE in operator_perms
    assert Permission.CONTENT_PUBLISH in operator_perms

    # 验证不应该有的权限
    assert Permission.USER_DELETE not in operator_perms
    assert Permission.CUSTOMER_CREATE not in operator_perms
    assert Permission.CONFIG_UPDATE not in operator_perms

    print(f"✓ 运营人员权限测试通过 (拥有 {len(operator_perms)} 个权限)")


@pytest.mark.unit
def test_role_permissions_customer():
    """测试客户权限"""
    customer_perms = ROLE_PERMISSIONS.get("customer")

    # 客户只应该有只读权限
    assert customer_perms is not None

    # 验证应该有的权限
    assert Permission.ACCOUNT_READ in customer_perms
    assert Permission.CONTENT_READ in customer_perms
    assert Permission.PUBLISHER_READ in customer_perms

    # 验证不应该有的权限
    assert Permission.ACCOUNT_CREATE not in customer_perms
    assert Permission.CONTENT_CREATE not in customer_perms
    assert Permission.CONTENT_PUBLISH not in customer_perms

    print(f"✓ 客户权限测试通过 (拥有 {len(customer_perms)} 个权限)")


@pytest.mark.unit
def test_get_role_permissions():
    """测试获取角色权限"""
    # 测试存在的角色
    admin_perms = get_role_permissions("admin")
    assert len(admin_perms) > 30

    # 测试不存在的角色
    unknown_perms = get_role_permissions("unknown_role")
    assert len(unknown_perms) == 0

    print("✓ 获取角色权限测试通过")


@pytest.mark.unit
def test_get_user_permissions():
    """测试获取用户权限"""
    admin_user = MockUser(role="admin")
    operator_user = MockUser(role="operator")
    customer_user = MockUser(role="customer")

    # 管理员用户权限最多
    admin_perms = get_user_permissions(admin_user)
    assert len(admin_perms) > 30

    # 运营用户权限中等
    operator_perms = get_user_permissions(operator_user)
    assert len(operator_perms) < len(admin_perms)
    assert len(operator_perms) > 0

    # 客户用户权限最少
    customer_perms = get_user_permissions(customer_user)
    assert len(customer_perms) < len(operator_perms)
    assert len(customer_perms) > 0

    print("✓ 获取用户权限测试通过")


@pytest.mark.unit
def test_has_permission_admin():
    """测试管理员权限检查"""
    admin_user = MockUser(role="admin")

    # 管理员应该拥有所有权限
    assert has_permission(admin_user, Permission.USER_DELETE) is True
    assert has_permission(admin_user, Permission.CONTENT_CREATE) is True
    assert has_permission(admin_user, Permission.ACCOUNT_READ) is True

    print("✓ 管理员权限检查测试通过")


@pytest.mark.unit
def test_has_permission_operator():
    """测试运营人员权限检查"""
    operator_user = MockUser(role="operator")

    # 运营人员应该有的权限
    assert has_permission(operator_user, Permission.CONTENT_CREATE) is True
    assert has_permission(operator_user, Permission.ACCOUNT_READ) is True
    assert has_permission(operator_user, Permission.CONTENT_PUBLISH) is True

    # 运营人员不应该有的权限
    assert has_permission(operator_user, Permission.USER_DELETE) is False
    assert has_permission(operator_user, Permission.CONFIG_UPDATE) is False

    print("✓ 运营人员权限检查测试通过")


@pytest.mark.unit
def test_has_permission_customer():
    """测试客户权限检查"""
    customer_user = MockUser(role="customer")

    # 客户应该有的权限
    assert has_permission(customer_user, Permission.CONTENT_READ) is True
    assert has_permission(customer_user, Permission.ACCOUNT_READ) is True

    # 客户不应该有的权限
    assert has_permission(customer_user, Permission.CONTENT_CREATE) is False
    assert has_permission(customer_user, Permission.CONTENT_PUBLISH) is False

    print("✓ 客户权限检查测试通过")


@pytest.mark.unit
def test_has_any_permission():
    """测试拥有任意权限检查"""
    operator_user = MockUser(role="operator")

    # 测试拥有其中一个权限
    assert has_any_permission(
        operator_user,
        [Permission.CONTENT_CREATE, Permission.USER_DELETE]
    ) is True  # 运营人员有 CONTENT_CREATE

    # 测试拥有所有权限
    assert has_any_permission(
        operator_user,
        [Permission.CONTENT_CREATE, Permission.ACCOUNT_READ]
    ) is True

    # 测试没有任何权限
    assert has_any_permission(
        operator_user,
        [Permission.USER_DELETE, Permission.CONFIG_UPDATE]
    ) is False

    print("✓ 任意权限检查测试通过")


@pytest.mark.unit
def test_has_role():
    """测试角色检查"""
    admin_user = MockUser(role="admin")
    operator_user = MockUser(role="operator")

    # 正确的角色
    assert has_role(admin_user, "admin") is True
    assert has_role(operator_user, "operator") is True

    # 错误的角色
    assert has_role(admin_user, "operator") is False
    assert has_role(operator_user, "admin") is False

    print("✓ 角色检查测试通过")


@pytest.mark.unit
def test_has_any_role():
    """测试拥有任意角色检查"""
    operator_user = MockUser(role="operator")
    customer_user = MockUser(role="customer")

    # 测试匹配
    assert has_any_role(operator_user, ["admin", "operator"]) is True
    assert has_any_role(customer_user, ["operator", "customer"]) is True

    # 测试不匹配
    assert has_any_role(customer_user, ["admin", "operator"]) is False

    print("✓ 任意角色检查测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_permission_success():
    """测试权限装饰器 - 成功场景"""
    operator_user = MockUser(role="operator")

    @require_permission(Permission.CONTENT_CREATE, Permission.USER_DELETE)
    async def test_function(current_user):
        return "success"

    # 运营人员有 CONTENT_CREATE 权限，应该通过
    result = await test_function(current_user=operator_user)
    assert result == "success"

    print("✓ 权限装饰器成功测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_permission_denied():
    """测试权限装饰器 - 拒绝场景"""
    customer_user = MockUser(role="customer")

    @require_permission(Permission.CONTENT_CREATE)
    async def test_function(current_user):
        return "success"

    # 客户没有 CONTENT_CREATE 权限，应该被拒绝
    from fastapi import HTTPException

    try:
        await test_function(current_user=customer_user)
        assert False, "应该抛出 HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
        assert "权限不足" in e.detail

    print("✓ 权限装饰器拒绝测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_permission_no_user():
    """测试权限装饰器 - 无用户"""
    @require_permission(Permission.CONTENT_CREATE)
    async def test_function(current_user):
        return "success"

    # 没有用户信息，应该被拒绝
    from fastapi import HTTPException

    try:
        await test_function()
        assert False, "应该抛出 HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        assert "未认证" in e.detail

    print("✓ 权限装饰器无用户测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_all_permissions_success():
    """测试拥有所有权限装饰器 - 成功场景"""
    operator_user = MockUser(role="operator")

    @require_all_permissions(Permission.CONTENT_CREATE, Permission.ACCOUNT_READ)
    async def test_function(current_user):
        return "success"

    # 运营人员同时拥有这两个权限，应该通过
    result = await test_function(current_user=operator_user)
    assert result == "success"

    print("✓ 所有权限装饰器成功测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_all_permissions_denied():
    """测试拥有所有权限装饰器 - 拒绝场景"""
    operator_user = MockUser(role="operator")

    @require_all_permissions(Permission.CONTENT_CREATE, Permission.USER_DELETE)
    async def test_function(current_user):
        return "success"

    # 运营人员没有 USER_DELETE 权限，应该被拒绝
    from fastapi import HTTPException

    try:
        await test_function(current_user=operator_user)
        assert False, "应该抛出 HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
        assert "权限不足" in e.detail
        assert "缺少" in e.detail

    print("✓ 所有权限装饰器拒绝测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_role_success():
    """测试角色装饰器 - 成功场景"""
    operator_user = MockUser(role="operator")

    @require_role("admin", "operator")
    async def test_function(current_user):
        return "success"

    # 运营人员在允许的角色列表中，应该通过
    result = await test_function(current_user=operator_user)
    assert result == "success"

    print("✓ 角色装饰器成功测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_role_denied():
    """测试角色装饰器 - 拒绝场景"""
    customer_user = MockUser(role="customer")

    @require_role("admin", "operator")
    async def test_function(current_user):
        return "success"

    # 客户不在允许的角色列表中，应该被拒绝
    from fastapi import HTTPException

    try:
        await test_function(current_user=customer_user)
        assert False, "应该抛出 HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
        assert "权限不足" in e.detail
        assert "角色" in e.detail

    print("✓ 角色装饰器拒绝测试通过")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_role_no_user():
    """测试角色装饰器 - 无用户"""
    @require_role("operator")
    async def test_function(current_user):
        return "success"

    # 没有用户信息，应该被拒绝
    from fastapi import HTTPException

    try:
        await test_function()
        assert False, "应该抛出 HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        assert "未认证" in e.detail

    print("✓ 角色装饰器无用户测试通过")


@pytest.mark.unit
def test_permission_isolation():
    """测试权限隔离"""
    # 不同角色的权限应该互不干扰
    admin_perms = get_role_permissions("admin")
    operator_perms = get_role_permissions("operator")
    customer_perms = get_role_permissions("customer")

    # 验证权限层级
    assert len(admin_perms) > len(operator_perms) > len(customer_perms)

    # 验证权限包含关系
    assert customer_perms.issubset(operator_perms)
    assert operator_perms.issubset(admin_perms)

    print("✓ 权限隔离测试通过")


@pytest.mark.unit
def test_unknown_role():
    """测试未知角色"""
    unknown_user = MockUser(role="unknown")

    # 未知角色应该没有任何权限
    perms = get_user_permissions(unknown_user)
    assert len(perms) == 0

    # 未知角色检查
    assert has_permission(unknown_user, Permission.ACCOUNT_READ) is False
    assert has_role(unknown_user, "operator") is False

    print("✓ 未知角色测试通过")
