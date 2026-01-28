"""
发布管理服务单元测试
"""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.modules.publisher.services import publisher_service
from app.models.publisher import PublishLog
from app.models.content import Content
from app.models.account import Account
from app.models.platform import Platform


@pytest.mark.unit
def test_get_publish_history(db_session: Session, test_customer: object):
    """测试获取发布历史"""
    # 创建测试平台和账号
    platform = Platform(
        name="发布测试平台",
        code="publish_test_platform",
        type="social_media",
        description="用于发布测试的平台",
        api_url="https://api.publish.com",
        api_key="publish_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="发布测试账号",
        directory_name="publish_test_account",
        description="用于发布测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容（多个内容，确保每个发布日志有唯一的content_id）
    contents = []
    for i in range(3):
        test_content = Content(
            account_id=account.id,
            title=f"发布测试文章{i}",
            content=f"# 发布测试内容{i}\n这是第{i}篇用于发布测试的文章",
            category="科技",
            topic=f"发布测试选题{i}",
            word_count=300 + i * 100,
            publish_status="published",
            review_status="approved"
        )
        db_session.add(test_content)
        contents.append(test_content)

    db_session.commit()

    # 创建测试发布日志
    publish_logs_data = [
        {
            "account_id": account.id,
            "content_id": contents[i].id,
            "platform": "wechat",
            "media_id": f"media_id_{i}",
            "status": "success"
        }
        for i in range(3)
    ]

    for data in publish_logs_data:
        publish_log = PublishLog(**data)
        db_session.add(publish_log)

    db_session.commit()

    # 获取发布历史
    history = publisher_service.get_publish_history(db_session)

    # 验证发布历史
    assert len(history) >= 3

    print(f"✓ 发布历史查询测试通过 (共 {len(history)} 条记录)")


@pytest.mark.unit
def test_get_publish_detail(db_session: Session, test_customer: object):
    """测试获取发布详情"""
    # 创建测试平台和账号
    platform = Platform(
        name="详情测试平台",
        code="detail_test_platform",
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
        category="科技",
        topic="详情测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 创建测试发布日志
    publish_log = PublishLog(
        account_id=account.id,
        content_id=content.id,
        platform="wechat",
        media_id="media_id_123",
        status="success"
    )
    db_session.add(publish_log)
    db_session.commit()

    # 获取发布详情
    detail = publisher_service.get_publish_detail(db_session, publish_log.id)

    # 验证发布详情
    assert detail is not None
    assert detail.id == publish_log.id
    assert detail.account_id == account.id
    assert detail.content_id == content.id
    assert detail.platform == "wechat"
    assert detail.media_id == "media_id_123"
    assert detail.status == "success"

    print(f"✓ 发布详情查询测试通过 (ID: {publish_log.id})")


@pytest.mark.unit
def test_manual_publish(db_session: Session, test_customer: object):
    """测试手动发布"""
    # 创建测试平台和账号
    platform = Platform(
        name="手动发布测试平台",
        code="manual_publish_test_platform",
        type="social_media",
        description="用于手动发布测试的平台",
        api_url="https://api.manual.com",
        api_key="manual_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="手动发布测试账号",
        directory_name="manual_publish_test_account",
        description="用于手动发布测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="手动发布测试文章",
        content="# 手动发布测试内容\n这是一篇用于手动发布测试的文章",
        category="科技",
        topic="手动发布测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 模拟 content_publisher_service.publish_to_wechat 方法
    mock_result = {
        "media_id": "mock_media_id",
        "message": "发布成功"
    }

    with patch('app.services.content_publisher_service.content_publisher_service.publish_to_wechat',
               return_value=mock_result) as mock_publish:

        # 手动发布
        request_data = {
            "content_id": content.id,
            "account_id": account.id
        }
        result = publisher_service.manual_publish(db_session, request_data)

        # 验证发布结果
        assert result["success"] is True
        assert "log_id" in result
        assert result["media_id"] == "mock_media_id"

        # 验证模拟方法被调用
        mock_publish.assert_called_once()

    print(f"✓ 手动发布测试通过 (日志ID: {result['log_id']})")


@pytest.mark.unit
def test_retry_publish(db_session: Session, test_customer: object):
    """测试重试发布"""
    # 创建测试平台和账号
    platform = Platform(
        name="重试发布测试平台",
        code="retry_publish_test_platform",
        type="social_media",
        description="用于重试发布测试的平台",
        api_url="https://api.retry.com",
        api_key="retry_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="重试发布测试账号",
        directory_name="retry_publish_test_account",
        description="用于重试发布测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="重试发布测试文章",
        content="# 重试发布测试内容\n这是一篇用于重试发布测试的文章",
        category="科技",
        topic="重试发布测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 创建测试发布日志（失败状态）
    publish_log = PublishLog(
        account_id=account.id,
        content_id=content.id,
        platform="wechat",
        status="failed",
        error_message="发布失败"
    )
    db_session.add(publish_log)
    db_session.commit()

    # 模拟 content_publisher_service.publish_to_wechat 方法
    mock_result = {
        "media_id": "retry_media_id",
        "message": "重试发布成功"
    }

    with patch('app.services.content_publisher_service.content_publisher_service.publish_to_wechat',
               return_value=mock_result) as mock_publish:

        # 重试发布
        result = publisher_service.retry_publish(db_session, publish_log.id)

        # 验证重试结果
        assert result["success"] is True
        assert result["log_id"] == publish_log.id
        assert result["media_id"] == "retry_media_id"

        # 验证模拟方法被调用
        mock_publish.assert_called_once()

    print(f"✓ 重试发布测试通过 (日志ID: {publish_log.id})")


@pytest.mark.unit
def test_publisher_service_operations(db_session: Session, test_customer: object):
    """综合测试发布管理服务操作"""
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

    # 模拟手动发布
    mock_result = {
        "media_id": "comprehensive_media_id",
        "message": "发布成功"
    }

    with patch('app.services.content_publisher_service.content_publisher_service.publish_to_wechat',
               return_value=mock_result):
        request_data = {
            "content_id": content.id,
            "account_id": account.id
        }
        publish_result = publisher_service.manual_publish(db_session, request_data)
        assert publish_result["success"] is True

    # 查询发布历史
    history = publisher_service.get_publish_history(db_session)
    assert len(history) >= 1

    print("✓ 发布管理服务综合测试通过")
