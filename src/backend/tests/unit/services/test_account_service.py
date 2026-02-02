"""
账号管理服务单元测试
"""
import pytest
from sqlalchemy.orm import Session

from app.modules.accounts.services import account_service
from app.models.account import Account
from app.models.customer import Customer
from app.models.platform import Platform


@pytest.mark.unit
def test_create_account(db_session: Session, test_customer: Customer):
    """测试创建账号"""
    # 创建测试平台
    platform = Platform(
        name="测试平台",
        code="test_platform",
        type="social_media",
        description="用于测试的平台",
        api_url="https://api.test.com",
        api_key="test_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    # 创建账号
    account_data = {
        "customer_id": test_customer.id,
        "platform_id": platform.id,
        "name": "测试账号",
        "directory_name": "test_account_dir",
        "description": "这是一个测试账号",
        "wechat_app_id": "wx123456789",
        "wechat_app_secret": "test_secret",
        "publisher_api_key": "test_publisher_key",
        "is_active": True
    }
    
    account = account_service.create_account(db_session, account_data)
    
    # 验证账号创建
    assert account is not None
    assert account.id is not None
    assert account.name == "测试账号"
    assert account.directory_name == "test_account_dir"
    assert account.customer_id == test_customer.id
    assert account.platform_id == platform.id
    assert account.wechat_app_id == "wx123456789"
    
    print(f"✓ 账号创建测试通过 (ID: {account.id})")


@pytest.mark.unit
def test_get_account_detail(db_session: Session, test_customer: Customer):
    """测试获取账号详情"""
    # 创建测试平台和账号
    platform = Platform(
        name="详情测试平台",
        code="detail_platform",
        type="social_media",
        description="用于详情测试的平台",
        api_url="https://api.detail.com",
        api_key="detail_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="详情测试账号",
        directory_name="detail_account_dir",
        description="这是一个详情测试账号",
        wechat_app_id="wx987654321",
        wechat_app_secret="detail_secret",
        publisher_api_key="detail_publisher_key",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 获取账号详情
    retrieved = account_service.get_account_detail(db_session, account.id)
    
    # 验证账号详情
    assert retrieved is not None
    assert retrieved.id == account.id
    assert retrieved.name == "详情测试账号"
    assert retrieved.directory_name == "detail_account_dir"
    
    print(f"✓ 账号详情查询测试通过 (ID: {account.id})")


@pytest.mark.unit
def test_get_account_list(db_session: Session, test_customer: Customer):
    """测试获取账号列表"""
    # 创建测试平台
    platform = Platform(
        name="列表测试平台",
        code="list_platform",
        type="social_media",
        description="用于列表测试的平台",
        api_url="https://api.list.com",
        api_key="list_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    # 创建多个账号
    accounts_data = [
        {
            "customer_id": test_customer.id,
            "platform_id": platform.id,
            "name": f"测试账号{i}",
            "directory_name": f"test_account_{i}_dir",
            "description": f"这是第{i}个测试账号",
            "is_active": True
        }
        for i in range(3)
    ]
    
    for data in accounts_data:
        account = Account(**data)
        db_session.add(account)
    
    db_session.commit()
    
    # 获取账号列表
    account_list = account_service.get_account_list(db_session)
    
    # 验证账号列表
    assert len(account_list) >= 3
    
    # 检查是否包含我们创建的账号
    created_names = [f"测试账号{i}" for i in range(3)]
    for account in account_list:
        # account_list 返回的是字典，不是 Account 对象
        account_name = account.get("name") if isinstance(account, dict) else account.name
        if account_name in created_names:
            created_names.remove(account_name)
    
    assert len(created_names) == 0
    
    print(f"✓ 账号列表查询测试通过 (共 {len(account_list)} 个账号)")


@pytest.mark.unit
def test_update_account(db_session: Session, test_customer: Customer):
    """测试更新账号"""
    # 创建测试平台和账号
    platform = Platform(
        name="更新测试平台",
        code="update_platform",
        type="social_media",
        description="用于更新测试的平台",
        api_url="https://api.update.com",
        api_key="update_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="初始账号",
        directory_name="initial_account_dir",
        description="这是一个待更新的账号",
        wechat_app_id="wx000000000",
        wechat_app_secret="initial_secret",
        publisher_api_key="initial_publisher_key",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 更新账号信息
    update_data = {
        "name": "更新后的账号",
        "directory_name": "updated_account_dir",
        "description": "这是一个已更新的账号",
        "wechat_app_id": "wx111111111",
        "wechat_app_secret": "updated_secret",
        "publisher_api_key": "updated_publisher_key",
        "is_active": False
    }
    
    updated_account = account_service.update_account(db_session, account.id, update_data)
    
    # 验证更新
    assert updated_account is not None
    assert updated_account.name == "更新后的账号"
    assert updated_account.directory_name == "updated_account_dir"
    assert updated_account.description == "这是一个已更新的账号"
    assert updated_account.wechat_app_id == "wx111111111"
    assert updated_account.is_active is False
    
    print(f"✓ 账号更新测试通过 (ID: {account.id})")


@pytest.mark.unit
def test_delete_account(db_session: Session, test_customer: Customer):
    """测试删除账号"""
    # 创建测试平台和账号
    platform = Platform(
        name="删除测试平台",
        code="delete_platform",
        type="social_media",
        description="用于删除测试的平台",
        api_url="https://api.delete.com",
        api_key="delete_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="待删除账号",
        directory_name="delete_account_dir",
        description="这是一个待删除的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 记录账号ID
    account_id = account.id
    
    # 删除账号
    result = account_service.delete_account(db_session, account_id)
    
    # 验证删除
    assert result is True
    
    # 验证账号已不存在
    deleted_account = account_service.get_account_detail(db_session, account_id)
    assert deleted_account is None
    
    print("✓ 账号删除测试通过")


@pytest.mark.unit
def test_account_service_operations(db_session: Session, test_customer: Customer):
    """综合测试账号管理服务操作"""
    # 创建测试平台
    platform = Platform(
        name="综合测试平台",
        code="comprehensive_platform",
        type="social_media",
        description="用于综合测试的平台",
        api_url="https://api.comprehensive.com",
        api_key="comprehensive_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    # 创建账号
    account_data = {
        "customer_id": test_customer.id,
        "platform_id": platform.id,
        "name": "综合测试账号",
        "directory_name": "comprehensive_account_dir",
        "description": "这是一个综合测试账号",
        "is_active": True
    }
    
    account = account_service.create_account(db_session, account_data)
    assert account is not None
    
    # 查询账号列表
    account_list = account_service.get_account_list(db_session)
    assert len(account_list) >= 1
    
    # 更新账号
    update_data = {"description": "这是一个已更新的综合测试账号"}
    updated_account = account_service.update_account(db_session, account.id, update_data)
    assert updated_account.description == "这是一个已更新的综合测试账号"
    
    print("✓ 账号管理服务综合测试通过")
