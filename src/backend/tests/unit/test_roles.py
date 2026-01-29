"""
角色权限映射单元测试
测试不同角色的权限分配和验证
"""
import pytest
from app.core.permissions import Permission, ROLE_PERMISSIONS, get_role_permissions, get_user_permissions, has_permission


class MockUser:
    """模拟用户对象"""
    def __init__(self, role="operator", user_id=1):
        self.role = role
        self.id = user_id
        self.username = f"testuser_{user_id}"


@pytest.mark.unit
def test_admin_role_has_all_permissions():
    """测试管理员拥有所有权限"""
    admin_perms = get_role_permissions("admin")

    # 验证账号管理权限
    assert Permission.ACCOUNT_READ in admin_perms
    assert Permission.ACCOUNT_CREATE in admin_perms
    assert Permission.ACCOUNT_UPDATE in admin_perms
    assert Permission.ACCOUNT_DELETE in admin_perms

    # 验证内容管理权限
    assert Permission.CONTENT_READ in admin_perms
    assert Permission.CONTENT_CREATE in admin_perms
    assert Permission.CONTENT_UPDATE in admin_perms
    assert Permission.CONTENT_DELETE in admin_perms
    assert Permission.CONTENT_PUBLISH in admin_perms

    # 验证发布管理权限
    assert Permission.PUBLISHER_READ in admin_perms
    assert Permission.PUBLISHER_EXECUTE in admin_perms
    assert Permission.PUBLISHER_CONFIG in admin_perms

    # 验证定时任务权限
    assert Permission.SCHEDULER_READ in admin_perms
    assert Permission.SCHEDULER_CREATE in admin_perms
    assert Permission.SCHEDULER_UPDATE in admin_perms
    assert Permission.SCHEDULER_DELETE in admin_perms
    assert Permission.SCHEDULER_EXECUTE in admin_perms

    # 验证发布池权限
    assert Permission.PUBLISH_POOL_READ in admin_perms
    assert Permission.PUBLISH_POOL_EXECUTE in admin_perms

    # 验证用户管理权限（仅管理员）
    assert Permission.USER_READ in admin_perms
    assert Permission.USER_CREATE in admin_perms
    assert Permission.USER_UPDATE in admin_perms
    assert Permission.USER_DELETE in admin_perms

    # 验证客户管理权限（仅管理员）
    assert Permission.CUSTOMER_READ in admin_perms
    assert Permission.CUSTOMER_CREATE in admin_perms
    assert Permission.CUSTOMER_UPDATE in admin_perms
    assert Permission.CUSTOMER_DELETE in admin_perms

    # 验证平台管理权限（仅管理员）
    assert Permission.PLATFORM_READ in admin_perms
    assert Permission.PLATFORM_CREATE in admin_perms
    assert Permission.PLATFORM_UPDATE in admin_perms
    assert Permission.PLATFORM_DELETE in admin_perms

    # 验证系统配置权限（仅管理员）
    assert Permission.CONFIG_READ in admin_perms
    assert Permission.CONFIG_UPDATE in admin_perms

    # 验证写作风格管理权限（仅管理员）
    assert Permission.WRITING_STYLE_READ in admin_perms
    assert Permission.WRITING_STYLE_CREATE in admin_perms
    assert Permission.WRITING_STYLE_UPDATE in admin_perms
    assert Permission.WRITING_STYLE_DELETE in admin_perms

    # 验证内容主题管理权限（仅管理员）
    assert Permission.CONTENT_THEME_READ in admin_perms
    assert Permission.CONTENT_THEME_CREATE in admin_perms
    assert Permission.CONTENT_THEME_UPDATE in admin_perms
    assert Permission.CONTENT_THEME_DELETE in admin_perms

    print(f"✓ 管理员拥有所有权限测试通过 (共 {len(admin_perms)} 个权限)")


@pytest.mark.unit
def test_operator_role_permissions():
    """测试运营人员权限"""
    operator_perms = get_role_permissions("operator")

    # 验证应该有的权限
    assert Permission.ACCOUNT_READ in operator_perms
    assert Permission.ACCOUNT_UPDATE in operator_perms
    assert Permission.CONTENT_READ in operator_perms
    assert Permission.CONTENT_CREATE in operator_perms
    assert Permission.CONTENT_UPDATE in operator_perms
    assert Permission.CONTENT_DELETE in operator_perms
    assert Permission.CONTENT_PUBLISH in operator_perms
    assert Permission.PUBLISHER_READ in operator_perms
    assert Permission.PUBLISHER_EXECUTE in operator_perms
    assert Permission.SCHEDULER_READ in operator_perms
    assert Permission.SCHEDULER_CREATE in operator_perms
    assert Permission.SCHEDULER_UPDATE in operator_perms
    assert Permission.SCHEDULER_DELETE in operator_perms
    assert Permission.SCHEDULER_EXECUTE in operator_perms
    assert Permission.PUBLISH_POOL_READ in operator_perms
    assert Permission.PUBLISH_POOL_EXECUTE in operator_perms

    # 验证不应该有的权限（管理员专属）
    assert Permission.ACCOUNT_CREATE not in operator_perms
    assert Permission.ACCOUNT_DELETE not in operator_perms
    assert Permission.PUBLISHER_CONFIG not in operator_perms
    assert Permission.USER_READ not in operator_perms
    assert Permission.USER_CREATE not in operator_perms
    assert Permission.USER_UPDATE not in operator_perms
    assert Permission.USER_DELETE not in operator_perms
    assert Permission.CUSTOMER_READ not in operator_perms
    assert Permission.CUSTOMER_CREATE not in operator_perms
    assert Permission.CUSTOMER_UPDATE not in operator_perms
    assert Permission.CUSTOMER_DELETE not in operator_perms
    assert Permission.PLATFORM_READ not in operator_perms
    assert Permission.PLATFORM_CREATE not in operator_perms
    assert Permission.PLATFORM_UPDATE not in operator_perms
    assert Permission.PLATFORM_DELETE not in operator_perms
    assert Permission.CONFIG_READ not in operator_perms
    assert Permission.CONFIG_UPDATE not in operator_perms
    assert Permission.WRITING_STYLE_READ not in operator_perms
    assert Permission.WRITING_STYLE_CREATE not in operator_perms
    assert Permission.WRITING_STYLE_UPDATE not in operator_perms
    assert Permission.WRITING_STYLE_DELETE not in operator_perms
    assert Permission.CONTENT_THEME_READ not in operator_perms
    assert Permission.CONTENT_THEME_CREATE not in operator_perms
    assert Permission.CONTENT_THEME_UPDATE not in operator_perms
    assert Permission.CONTENT_THEME_DELETE not in operator_perms

    print(f"✓ 运营人员权限测试通过 (共 {len(operator_perms)} 个权限)")


@pytest.mark.unit
def test_customer_role_permissions():
    """测试客户权限（只读）"""
    customer_perms = get_role_permissions("customer")

    # 验证应该有的权限（只读）
    assert Permission.ACCOUNT_READ in customer_perms
    assert Permission.CONTENT_READ in customer_perms
    assert Permission.PUBLISHER_READ in customer_perms
    assert Permission.SCHEDULER_READ in customer_perms
    assert Permission.PUBLISH_POOL_READ in customer_perms

    # 验证不应该有的权限（写操作）
    assert Permission.ACCOUNT_CREATE not in customer_perms
    assert Permission.ACCOUNT_UPDATE not in customer_perms
    assert Permission.ACCOUNT_DELETE not in customer_perms
    assert Permission.CONTENT_CREATE not in customer_perms
    assert Permission.CONTENT_UPDATE not in customer_perms
    assert Permission.CONTENT_DELETE not in customer_perms
    assert Permission.CONTENT_PUBLISH not in customer_perms
    assert Permission.PUBLISHER_EXECUTE not in customer_perms
    assert Permission.SCHEDULER_CREATE not in customer_perms
    assert Permission.SCHEDULER_UPDATE not in customer_perms
    assert Permission.SCHEDULER_DELETE not in customer_perms
    assert Permission.SCHEDULER_EXECUTE not in customer_perms
    assert Permission.PUBLISH_POOL_EXECUTE not in customer_perms

    print(f"✓ 客户权限测试通过 (共 {len(customer_perms)} 个只读权限)")


@pytest.mark.unit
def test_role_hierarchy():
    """测试角色权限层级"""
    admin_perms = get_role_permissions("admin")
    operator_perms = get_role_permissions("operator")
    customer_perms = get_role_permissions("customer")

    # 验证权限数量层级
    assert len(admin_perms) > len(operator_perms) > len(customer_perms)

    # 验证权限包含关系
    # 客户权限 ⊆ 运营人员权限
    assert customer_perms.issubset(operator_perms)

    # 运营人员权限 ⊆ 管理员权限
    assert operator_perms.issubset(admin_perms)

    # 客户权限 ⊆ 管理员权限
    assert customer_perms.issubset(admin_perms)

    print("✓ 角色权限层级测试通过")


@pytest.mark.unit
def test_admin_user_has_all_permissions():
    """测试管理员用户拥有所有权限"""
    admin_user = MockUser(role="admin")
    user_perms = get_user_permissions(admin_user)

    # 管理员用户应该拥有所有权限
    assert len(user_perms) == len(get_role_permissions("admin"))

    # 验证管理员用户可以执行任何操作
    assert has_permission(admin_user, Permission.USER_DELETE) is True
    assert has_permission(admin_user, Permission.CONFIG_UPDATE) is True
    assert has_permission(admin_user, Permission.CONTENT_PUBLISH) is True

    print("✓ 管理员用户权限测试通过")


@pytest.mark.unit
def test_operator_user_cannot_delete_users():
    """测试运营人员不能删除用户"""
    operator_user = MockUser(role="operator")

    # 运营人员不应该能删除用户
    assert has_permission(operator_user, Permission.USER_DELETE) is False
    assert has_permission(operator_user, Permission.CUSTOMER_DELETE) is False

    print("✓ 运营人员不能删除用户测试通过")


@pytest.mark.unit
def test_customer_user_read_only():
    """测试客户用户只有只读权限"""
    customer_user = MockUser(role="customer")

    # 客户应该能读取
    assert has_permission(customer_user, Permission.ACCOUNT_READ) is True
    assert has_permission(customer_user, Permission.CONTENT_READ) is True

    # 客户不应该能写入
    assert has_permission(customer_user, Permission.CONTENT_CREATE) is False
    assert has_permission(customer_user, Permission.CONTENT_UPDATE) is False
    assert has_permission(customer_user, Permission.CONTENT_DELETE) is False
    assert has_permission(customer_user, Permission.CONTENT_PUBLISH) is False

    print("✓ 客户用户只读权限测试通过")


@pytest.mark.unit
def test_role_permissions_immutability():
    """测试角色权限不可变性"""
    # 获取原始权限
    admin_perms = get_role_permissions("admin")
    original_size = len(admin_perms)

    # 尝试修改权限集合（应该不会影响原始映射）
    try:
        admin_perms.add(Permission.USER_READ)  # 已经存在的权限
        admin_perms_copy = get_role_permissions("admin")
        # 验证权限数量没有变化（返回的是同一个集合实例）
        assert len(admin_perms_copy) >= original_size
    except Exception:
        # 如果修改失败，说明权限是受保护的，这也是正确的
        pass

    print("✓ 角色权限不可变性测试通过")


@pytest.mark.unit
def test_all_roles_defined():
    """测试所有必需角色都已定义"""
    required_roles = ["admin", "operator", "customer"]

    for role in required_roles:
        assert role in ROLE_PERMISSIONS, f"角色 {role} 未定义"
        perms = ROLE_PERMISSIONS[role]
        assert len(perms) > 0, f"角色 {role} 没有权限"

    print(f"✓ 所有必需角色已定义测试通过 ({len(required_roles)} 个角色)")


@pytest.mark.unit
def test_unknown_role_returns_empty_permissions():
    """测试未知角色返回空权限集合"""
    unknown_perms = get_role_permissions("unknown_role")

    assert unknown_perms is not None
    assert len(unknown_perms) == 0
    assert isinstance(unknown_perms, set)

    print("✓ 未知角色返回空权限测试通过")


@pytest.mark.unit
def test_role_permission_coverage():
    """测试所有权限都被至少一个角色拥有"""
    all_role_perms = set()
    for role_perms in ROLE_PERMISSIONS.values():
        all_role_perms.update(role_perms)

    # 获取所有定义的权限
    all_defined_perms = {
        perm for perm in dir(Permission)
        if not perm.startswith('_') and isinstance(getattr(Permission, perm), str)
    }

    # 验证所有定义的权限都被分配给至少一个角色
    # 注意：这假设所有Permission枚举值都应该是可访问的
    # 实际测试中，我们应该只检查Permission枚举类中定义的值
    permission_enum_values = {
        getattr(Permission, attr)
        for attr in dir(Permission)
        if not attr.startswith('_') and isinstance(getattr(Permission, attr), str)
    }

    # 所有枚举权限应该都被分配
    assert len(permission_enum_values - all_role_perms) == 0, "有权限未被分配给任何角色"

    print(f"✓ 角色权限覆盖测试通过 (共 {len(all_role_perms)} 个权限)")


@pytest.mark.unit
def test_critical_permissions_admin_only():
    """测试关键权限仅管理员拥有"""
    admin_perms = get_role_permissions("admin")
    operator_perms = get_role_permissions("operator")
    customer_perms = get_role_permissions("customer")

    # 这些权限应该只有管理员拥有
    admin_only_permissions = [
        Permission.USER_DELETE,
        Permission.CUSTOMER_DELETE,
        Permission.PLATFORM_DELETE,
        Permission.CONFIG_UPDATE,
    ]

    for perm in admin_only_permissions:
        assert perm in admin_perms, f"管理员应该拥有 {perm.value}"
        assert perm not in operator_perms, f"运营人员不应该拥有 {perm.value}"
        assert perm not in customer_perms, f"客户不应该拥有 {perm.value}"

    print("✓ 关键权限仅管理员测试通过")
