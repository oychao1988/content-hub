"""
发布池管理服务单元测试
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.modules.publish_pool.services import publish_pool_manager_service
from app.models.publisher import PublishPool
from app.models.content import Content
from app.models.account import Account
from app.models.platform import Platform


@pytest.mark.unit
def test_add_to_pool(db_session: Session, test_customer: object):
    """测试添加到发布池"""
    # 创建测试平台和账号
    platform = Platform(
        name="发布池测试平台",
        code="pool_test_platform",
        type="social_media",
        description="用于发布池测试的平台",
        api_url="https://api.pool.com",
        api_key="pool_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="发布池测试账号",
        directory_name="pool_test_account",
        description="用于发布池测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="发布池测试文章",
        content="# 发布池测试内容\n这是一篇用于发布池测试的文章",
        category="科技",
        topic="发布池测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 添加到发布池
    pool_entry = publish_pool_manager_service.add_to_pool(
        db_session, content.id, priority=3, scheduled_at=datetime(2024, 12, 31, 10, 0, 0)
    )

    # 验证添加到发布池
    assert pool_entry is not None
    assert pool_entry.content_id == content.id
    assert pool_entry.priority == 3
    assert pool_entry.scheduled_at == datetime(2024, 12, 31, 10, 0, 0)

    print(f"✓ 添加到发布池测试通过 (ID: {pool_entry.id})")


@pytest.mark.unit
def test_remove_from_pool(db_session: Session, test_customer: object):
    """测试从发布池移除"""
    # 创建测试平台和账号
    platform = Platform(
        name="移除测试平台",
        code="remove_test_platform",
        type="social_media",
        description="用于移除测试的平台",
        api_url="https://api.remove.com",
        api_key="remove_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="移除测试账号",
        directory_name="remove_test_account",
        description="用于移除测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="移除测试文章",
        content="# 移除测试内容\n这是一篇用于移除测试的文章",
        category="科技",
        topic="移除测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 创建测试发布池条目
    pool_entry = PublishPool(
        content_id=content.id,
        priority=5,
        scheduled_at=datetime(2024, 12, 31, 10, 0, 0)
    )
    db_session.add(pool_entry)
    db_session.commit()

    # 记录发布池条目ID
    pool_id = pool_entry.id

    # 从发布池移除
    result = publish_pool_manager_service.remove_from_pool(db_session, pool_id)

    # 验证移除
    assert result is True

    # 验证发布池条目已不存在
    removed_entry = db_session.query(PublishPool).filter(PublishPool.id == pool_id).first()
    assert removed_entry is None

    print("✓ 从发布池移除测试通过")


@pytest.mark.unit
def test_update_pool_entry(db_session: Session, test_customer: object):
    """测试更新发布池条目"""
    # 创建测试平台和账号
    platform = Platform(
        name="更新测试平台",
        code="update_test_platform",
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
        name="更新测试账号",
        directory_name="update_test_account",
        description="用于更新测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="更新测试文章",
        content="# 更新测试内容\n这是一篇用于更新测试的文章",
        category="科技",
        topic="更新测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 创建测试发布池条目
    pool_entry = PublishPool(
        content_id=content.id,
        priority=5,
        scheduled_at=datetime(2024, 12, 31, 10, 0, 0)
    )
    db_session.add(pool_entry)
    db_session.commit()

    # 更新发布池条目
    update_data = {
        "priority": 8,
        "scheduled_at": datetime(2025, 1, 1, 15, 30, 0)
    }
    updated_entry = publish_pool_manager_service.update_pool_entry(db_session, pool_entry.id, update_data)

    # 验证更新
    assert updated_entry is not None
    assert updated_entry.priority == 8
    assert updated_entry.scheduled_at == datetime(2025, 1, 1, 15, 30, 0)

    print(f"✓ 更新发布池条目测试通过 (ID: {pool_entry.id})")


@pytest.mark.unit
def test_get_pending_entries(db_session: Session, test_customer: object):
    """测试获取待发布条目"""
    # 创建测试平台和账号
    platform = Platform(
        name="待发布测试平台",
        code="pending_test_platform",
        type="social_media",
        description="用于待发布测试的平台",
        api_url="https://api.pending.com",
        api_key="pending_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="待发布测试账号",
        directory_name="pending_test_account",
        description="用于待发布测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    contents = []
    for i in range(3):
        content = Content(
            account_id=account.id,
            title=f"待发布测试文章{i}",
            content=f"# 待发布测试内容{i}\n这是第{i}篇用于待发布测试的文章",
            category="科技",
            topic=f"待发布测试选题{i}",
            word_count=300 + i * 100,
            publish_status="published",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 创建测试发布池条目（包含待发布和已发布的）
    pool_entries_data = [
        {
            "content_id": contents[0].id,
            "priority": 5,
            "scheduled_at": datetime(2024, 12, 31, 10, 0, 0)
        },
        {
            "content_id": contents[1].id,
            "priority": 3,
            "scheduled_at": datetime(2024, 12, 31, 14, 0, 0)
        },
        {
            "content_id": contents[2].id,
            "priority": 7,
            "scheduled_at": datetime(2024, 12, 30, 9, 0, 0)
        }
    ]

    for data in pool_entries_data:
        pool_entry = PublishPool(**data)
        db_session.add(pool_entry)

    db_session.commit()

    # 获取待发布条目
    pending_entries = publish_pool_manager_service.get_pending_entries(db_session)

    # 验证待发布条目
    assert len(pending_entries) >= 2

    print(f"✓ 获取待发布条目测试通过 (共 {len(pending_entries)} 个待发布条目)")


@pytest.mark.unit
def test_publish_pool_service_operations(db_session: Session, test_customer: object):
    """综合测试发布池管理服务操作"""
    # 创建测试平台和账号
    platform = Platform(
        name="综合测试平台",
        code="comprehensive_test_platform",
        type="social_media",
        description="用于综合测试的平台",
        api_url="https://api.comprehensive.com",
        api_key="comprehensive_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="综合测试账号",
        directory_name="comprehensive_test_account",
        description="用于综合测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="综合测试文章",
        content="# 综合测试内容\n这是一篇用于综合测试的文章",
        category="科技",
        topic="综合测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 添加到发布池
    pool_entry = publish_pool_manager_service.add_to_pool(
        db_session, content.id, priority=5, scheduled_at=datetime(2024, 12, 31, 10, 0, 0)
    )
    assert pool_entry is not None

    # 查询发布池列表
    pool_list = publish_pool_manager_service.get_publish_pool(db_session)
    assert len(pool_list) >= 1

    # 更新发布池条目
    update_data = {"priority": 8}
    updated_entry = publish_pool_manager_service.update_pool_entry(db_session, pool_entry.id, update_data)
    assert updated_entry.priority == 8

    print("✓ 发布池管理服务综合测试通过")
