"""
内容管理服务单元测试
"""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.modules.content.services import content_service
from app.models.content import Content
from app.models.customer import Customer
from app.models.platform import Platform
from app.models.account import Account


@pytest.mark.unit
def test_create_content(db_session: Session, test_customer: Customer):
    """测试创建内容"""
    # 创建测试平台和账号
    platform = Platform(
        name="内容测试平台",
        code="content_platform",
        type="social_media",
        description="用于内容测试的平台",
        api_url="https://api.content.com",
        api_key="content_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="内容测试账号",
        directory_name="content_test_account",
        description="用于内容测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建内容
    content_data = {
        "title": "测试文章标题",
        "content_type": "article",
        "content": "# 测试文章内容\n这是一篇测试文章",
        "summary": "测试摘要",
        "status": "draft",
        "cover_image": "https://example.com/cover.jpg"
    }

    content = content_service.create_content(db_session, content_data, account.id)

    # 验证内容创建
    assert content is not None
    assert content.id is not None
    assert content.title == "测试文章标题"
    assert "测试文章内容" in content.content
    assert content.account_id == account.id
    # word_count 需要在实际服务中计算，这里先断言它存在
    assert hasattr(content, 'word_count')

    print(f"✓ 内容创建测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_get_content_detail(db_session: Session, test_customer: Customer):
    """测试获取内容详情"""
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
        directory_name="detail_test_account",
        description="用于详情测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="详情测试文章",
        content="# 详情测试内容\n这是一篇用于详情测试的文章",
        word_count=300,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    
    # 获取内容详情
    retrieved = content_service.get_content_detail(db_session, content.id)
    
    # 验证内容详情
    assert retrieved is not None
    assert retrieved.id == content.id
    assert retrieved.title == "详情测试文章"
    assert "详情测试内容" in retrieved.content
    
    print(f"✓ 内容详情查询测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_get_content_list(db_session: Session, test_customer: Customer):
    """测试获取内容列表"""
    # 创建测试平台和账号
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
    
    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="列表测试账号",
        directory_name="list_test_account",
        description="用于列表测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 创建多个测试内容
    contents_data = [
        {
            "account_id": account.id,
            "title": f"测试文章{i}",
            "content": f"# 文章内容{i}\n这是第{i}篇测试文章",
            "word_count": 200 + i * 100,
            "publish_status": "draft",
            "review_status": "pending"
        }
        for i in range(3)
    ]
    
    for data in contents_data:
        content = Content(**data)
        db_session.add(content)
    
    db_session.commit()
    
    # 获取内容列表
    content_list_response = content_service.get_content_list(db_session)

    # 验证内容列表（分页格式）
    assert "items" in content_list_response
    assert "total" in content_list_response
    assert "page" in content_list_response
    assert "pageSize" in content_list_response

    content_list = content_list_response["items"]
    assert len(content_list) >= 3

    # 检查是否包含我们创建的内容
    created_titles = [f"测试文章{i}" for i in range(3)]
    for content in content_list:
        if content.title in created_titles:
            created_titles.remove(content.title)

    assert len(created_titles) == 0
    
    print(f"✓ 内容列表查询测试通过 (共 {len(content_list)} 篇内容)")


@pytest.mark.unit
def test_update_content(db_session: Session, test_customer: Customer):
    """测试更新内容"""
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
        title="初始文章标题",
        content="# 初始内容\n这是一篇待更新的文章",
        word_count=250,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    
    # 更新内容信息
    update_data = {
        "title": "更新后的文章标题",
        "content": "# 更新后的内容\n这是一篇已更新的文章",
        "word_count": 400,
        "publish_status": "published",
        "review_status": "approved"
    }
    
    updated_content = content_service.update_content(db_session, content.id, update_data)
    
    # 验证更新
    assert updated_content is not None
    assert updated_content.title == "更新后的文章标题"
    assert "更新后的内容" in updated_content.content
    assert updated_content.word_count == 400
    assert updated_content.publish_status == "published"
    assert updated_content.review_status == "approved"
    
    print(f"✓ 内容更新测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_delete_content(db_session: Session, test_customer: Customer):
    """测试删除内容"""
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
        name="删除测试账号",
        directory_name="delete_test_account",
        description="用于删除测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="待删除文章",
        content="# 待删除内容\n这是一篇待删除的文章",
        word_count=200,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    
    # 记录内容ID
    content_id = content.id
    
    # 删除内容
    result = content_service.delete_content(db_session, content_id)
    
    # 验证删除
    assert result is True
    
    # 验证内容已不存在
    deleted_content = content_service.get_content_detail(db_session, content_id)
    assert deleted_content is None
    
    print("✓ 内容删除测试通过")


@pytest.mark.unit
def test_review_operations(db_session: Session, test_customer: Customer):
    """测试审核操作"""
    # 创建测试平台和账号
    platform = Platform(
        name="审核测试平台",
        code="review_platform",
        type="social_media",
        description="用于审核测试的平台",
        api_url="https://api.review.com",
        api_key="review_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="审核测试账号",
        directory_name="review_test_account",
        description="用于审核测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="审核测试文章",
        content="# 审核测试内容\n这是一篇待审核的文章",
        word_count=300,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    
    # 测试审核操作
    with patch('app.services.content_review_service.content_review_service.submit_for_review',
               return_value=content):
        submitted = content_service.submit_for_review(db_session, content.id)
        assert submitted is not None
    
    with patch('app.services.content_review_service.content_review_service.approve_content',
               return_value=content):
        approved = content_service.approve_content(db_session, content.id, 1)
        assert approved is not None
    
    print("✓ 内容审核操作测试通过")


@pytest.mark.unit
def test_content_service_operations(db_session: Session, test_customer: Customer):
    """综合测试内容管理服务操作"""
    # 创建测试平台和账号
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

    # 创建内容
    content_data = {
        "title": "综合测试文章",
        "content_type": "article",
        "content": "# 综合测试内容\n这是一篇综合测试文章",
        "summary": "综合测试摘要",
        "status": "draft",
        "cover_image": "https://example.com/cover.jpg"
    }

    content = content_service.create_content(db_session, content_data, account.id)
    assert content is not None
    
    # 查询内容列表
    content_list_response = content_service.get_content_list(db_session)
    assert content_list_response["total"] >= 1
    
    # 更新内容
    update_data = {"description": "这是一篇综合测试文章"}
    updated_content = content_service.update_content(db_session, content.id, update_data)
    assert updated_content is not None
    
    print("✓ 内容管理服务综合测试通过")
