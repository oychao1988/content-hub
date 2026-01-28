"""
批量发布服务单元测试
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.batch_publish_service import batch_publish_service
from app.models.publisher import PublishLog, PublishPool
from app.models.content import Content
from app.models.account import Account
from app.models.platform import Platform


@pytest.mark.unit
@patch('app.services.batch_publish_service.content_publisher_service')
@patch('app.services.batch_publish_service.publish_pool_service')
def test_process_batch_publish_success(mock_publish_pool_service, mock_content_publisher_service, db_session: Session, test_customer: object):
    """测试批量发布成功"""
    # 创建测试平台和账号
    platform = Platform(
        name="批量发布测试平台",
        code="batch_publish_test_platform",
        type="social_media",
        description="用于批量发布测试的平台",
        api_url="https://api.batch.com",
        api_key="batch_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="批量发布测试账号",
        directory_name="batch_publish_test_account",
        description="用于批量发布测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容（approved 状态）
    contents = []
    for i in range(3):
        content = Content(
            account_id=account.id,
            title=f"批量发布测试文章{i}",
            content=f"# 批量发布测试内容{i}\n这是第{i}篇用于批量发布测试的文章",
            category="科技",
            topic=f"批量发布测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 模拟发布池服务
    mock_pool_entry = MagicMock()
    mock_pool_entry.id = 1
    mock_publish_pool_service.add_to_pool.return_value = mock_pool_entry
    mock_publish_pool_service.complete_publishing.return_value = mock_pool_entry

    # 模拟内容发布服务
    mock_publish_result = {
        "media_id": f"test_media_id_{datetime.now().timestamp()}",
        "message": "发布成功"
    }
    mock_content_publisher_service.publish_to_wechat.return_value = mock_publish_result

    # 执行批量发布
    content_ids = [content.id for content in contents]
    result = batch_publish_service.process_batch_publish(db_session, account.id, content_ids)

    # 验证结果
    assert result["total"] == 3
    assert result["success"] == 3
    assert result["fail"] == 0
    assert len(result["results"]) == 3

    # 验证每个结果
    for i, res in enumerate(result["results"]):
        assert res["success"] is True
        assert res["content_id"] == content_ids[i]
        assert "media_id" in res
        assert "published_at" in res

    # 验证发布池服务被调用
    assert mock_publish_pool_service.add_to_pool.call_count == 3
    assert mock_publish_pool_service.complete_publishing.call_count == 3

    # 验证内容发布服务被调用
    assert mock_content_publisher_service.publish_to_wechat.call_count == 3

    # 验证数据库中的发布日志
    publish_logs = db_session.query(PublishLog).filter(PublishLog.account_id == account.id).all()
    assert len(publish_logs) == 3

    # 验证内容状态已更新
    for content in contents:
        db_session.refresh(content)
        assert content.publish_status == "published"
        assert content.published_at is not None

    print("✓ 批量发布成功测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.content_publisher_service')
@patch('app.services.batch_publish_service.publish_pool_service')
def test_process_batch_publish_content_not_found(mock_publish_pool_service, mock_content_publisher_service, db_session: Session, test_customer: object):
    """测试批量发布时内容不存在"""
    # 创建测试平台和账号
    platform = Platform(
        name="内容不存在测试平台",
        code="content_not_found_platform",
        type="social_media",
        description="用于内容不存在测试的平台",
        api_url="https://api.notfound.com",
        api_key="notfound_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="内容不存在测试账号",
        directory_name="content_not_found_account",
        description="用于内容不存在测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 使用不存在的内容ID
    non_existent_content_ids = [99999, 99998, 99997]

    # 执行批量发布
    result = batch_publish_service.process_batch_publish(db_session, account.id, non_existent_content_ids)

    # 验证结果
    assert result["total"] == 3
    assert result["success"] == 0
    assert result["fail"] == 3
    assert len(result["results"]) == 3

    # 验证每个结果都失败
    for res in result["results"]:
        assert res["success"] is False
        assert res["error"] == "内容不存在"

    # 验证发布池服务未被调用
    assert mock_publish_pool_service.add_to_pool.call_count == 0
    assert mock_content_publisher_service.publish_to_wechat.call_count == 0

    print("✓ 批量发布内容不存在测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.content_publisher_service')
@patch('app.services.batch_publish_service.publish_pool_service')
def test_process_batch_publish_invalid_status(mock_publish_pool_service, mock_content_publisher_service, db_session: Session, test_customer: object):
    """测试批量发布时内容状态不正确"""
    # 创建测试平台和账号
    platform = Platform(
        name="状态错误测试平台",
        code="invalid_status_platform",
        type="social_media",
        description="用于状态错误测试的平台",
        api_url="https://api.invalidstatus.com",
        api_key="invalid_status_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="状态错误测试账号",
        directory_name="invalid_status_account",
        description="用于状态错误测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容（非 approved 状态）
    contents = []
    statuses = ["pending", "rejected", "draft"]
    for i, status in enumerate(statuses):
        content = Content(
            account_id=account.id,
            title=f"状态错误测试文章{i}",
            content=f"# 状态错误测试内容{i}\n这是第{i}篇用于状态错误测试的文章",
            category="科技",
            topic=f"状态错误测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status=status
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 执行批量发布
    content_ids = [content.id for content in contents]
    result = batch_publish_service.process_batch_publish(db_session, account.id, content_ids)

    # 验证结果
    assert result["total"] == 3
    assert result["success"] == 0
    assert result["fail"] == 3
    assert len(result["results"]) == 3

    # 验证每个结果都失败
    for i, res in enumerate(result["results"]):
        assert res["success"] is False
        assert "内容状态不正确" in res["error"]
        assert statuses[i] in res["error"]

    # 验证发布池服务未被调用
    assert mock_publish_pool_service.add_to_pool.call_count == 0
    assert mock_content_publisher_service.publish_to_wechat.call_count == 0

    print("✓ 批量发布状态错误测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.content_publisher_service')
@patch('app.services.batch_publish_service.publish_pool_service')
def test_process_batch_publish_partial_success(mock_publish_pool_service, mock_content_publisher_service, db_session: Session, test_customer: object):
    """测试批量发布部分成功"""
    # 创建测试平台和账号
    platform = Platform(
        name="部分成功测试平台",
        code="partial_success_platform",
        type="social_media",
        description="用于部分成功测试的平台",
        api_url="https://api.partial.com",
        api_key="partial_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="部分成功测试账号",
        directory_name="partial_success_account",
        description="用于部分成功测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容：2个 approved，1个 pending，1个不存在
    contents = []
    for i in range(2):
        content = Content(
            account_id=account.id,
            title=f"部分成功测试文章{i}",
            content=f"# 部分成功测试内容{i}\n这是第{i}篇用于部分成功测试的文章",
            category="科技",
            topic=f"部分成功测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    # 添加一个状态不正确的内容
    invalid_content = Content(
        account_id=account.id,
        title="部分成功无效文章",
        content="# 部分成功无效内容",
        category="科技",
        topic="部分成功无效选题",
        word_count=300,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(invalid_content)

    db_session.commit()

    # 模拟发布池服务
    mock_pool_entry = MagicMock()
    mock_pool_entry.id = 1
    mock_publish_pool_service.add_to_pool.return_value = mock_pool_entry
    mock_publish_pool_service.complete_publishing.return_value = mock_pool_entry

    # 模拟内容发布服务
    mock_publish_result = {
        "media_id": f"test_media_id_{datetime.now().timestamp()}",
        "message": "发布成功"
    }
    mock_content_publisher_service.publish_to_wechat.return_value = mock_publish_result

    # 执行批量发布（包含不存在的内容ID）
    content_ids = [contents[0].id, contents[1].id, invalid_content.id, 99999]
    result = batch_publish_service.process_batch_publish(db_session, account.id, content_ids)

    # 验证结果
    assert result["total"] == 4
    assert result["success"] == 2
    assert result["fail"] == 2
    assert len(result["results"]) == 4

    # 验证成功的结果
    success_results = [r for r in result["results"] if r["success"]]
    assert len(success_results) == 2

    # 验证失败的结果
    fail_results = [r for r in result["results"] if not r["success"]]
    assert len(fail_results) == 2

    # 验证发布池服务被调用2次（只有成功的内容）
    assert mock_publish_pool_service.add_to_pool.call_count == 2
    assert mock_content_publisher_service.publish_to_wechat.call_count == 2

    print("✓ 批量发布部分成功测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.content_publisher_service')
@patch('app.services.batch_publish_service.publish_pool_service')
def test_process_batch_publish_exception_handling(mock_publish_pool_service, mock_content_publisher_service, db_session: Session, test_customer: object):
    """测试批量发布异常处理"""
    # 创建测试平台和账号
    platform = Platform(
        name="异常处理测试平台",
        code="exception_test_platform",
        type="social_media",
        description="用于异常处理测试的平台",
        api_url="https://api.exception.com",
        api_key="exception_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="异常处理测试账号",
        directory_name="exception_test_account",
        description="用于异常处理测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    contents = []
    for i in range(3):
        content = Content(
            account_id=account.id,
            title=f"异常处理测试文章{i}",
            content=f"# 异常处理测试内容{i}\n这是第{i}篇用于异常处理测试的文章",
            category="科技",
            topic=f"异常处理测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 模拟发布池服务
    mock_pool_entry = MagicMock()
    mock_pool_entry.id = 1
    mock_publish_pool_service.add_to_pool.return_value = mock_pool_entry

    # 模拟内容发布服务抛出异常
    mock_content_publisher_service.publish_to_wechat.side_effect = Exception("发布服务异常")

    # 执行批量发布
    content_ids = [content.id for content in contents]
    result = batch_publish_service.process_batch_publish(db_session, account.id, content_ids)

    # 验证结果
    assert result["total"] == 3
    assert result["success"] == 0
    assert result["fail"] == 3
    assert len(result["results"]) == 3

    # 验证每个结果都失败
    for res in result["results"]:
        assert res["success"] is False
        assert "error" in res

    print("✓ 批量发布异常处理测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.BatchPublishService.process_batch_publish')
def test_process_scheduled_batch_publish_no_pending(mock_process_batch_publish, db_session: Session, test_customer: object):
    """测试处理定时批量发布任务（无待发布内容）"""
    # 模拟发布池服务返回空列表
    with patch('app.services.batch_publish_service.publish_pool_service') as mock_publish_pool_service:
        mock_publish_pool_service.get_pending_entries.return_value = []

        # 执行定时批量发布
        result = batch_publish_service.process_scheduled_batch_publish(db_session)

        # 验证结果
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["fail"] == 0
        assert len(result["results"]) == 0

        # 验证未被调用
        assert mock_process_batch_publish.call_count == 0

    print("✓ 处理定时批量发布任务（无待发布内容）测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.BatchPublishService.process_batch_publish')
def test_process_scheduled_batch_publish_with_pending(mock_process_batch_publish, db_session: Session, test_customer: object):
    """测试处理定时批量发布任务（有待发布内容）"""
    # 创建测试平台和账号
    platform = Platform(
        name="定时发布测试平台",
        code="scheduled_publish_platform",
        type="social_media",
        description="用于定时发布测试的平台",
        api_url="https://api.scheduled.com",
        api_key="scheduled_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="定时发布测试账号",
        directory_name="scheduled_publish_account",
        description="用于定时发布测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    contents = []
    for i in range(3):
        content = Content(
            account_id=account.id,
            title=f"定时发布测试文章{i}",
            content=f"# 定时发布测试内容{i}\n这是第{i}篇用于定时发布测试的文章",
            category="科技",
            topic=f"定时发布测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 创建发布池条目
    for content in contents:
        pool_entry = PublishPool(
            content_id=content.id,
            priority=5,
            scheduled_at=datetime.utcnow(),
            status="pending"
        )
        db_session.add(pool_entry)

    db_session.commit()

    # 模拟批量发布结果
    mock_process_batch_publish.return_value = {
        "total": 3,
        "success": 3,
        "fail": 0,
        "results": [
            {
                "content_id": content.id,
                "success": True,
                "media_id": f"test_media_id_{content.id}",
                "published_at": datetime.utcnow().isoformat()
            }
            for content in contents
        ]
    }

    # 执行定时批量发布
    result = batch_publish_service.process_scheduled_batch_publish(db_session)

    # 验证结果
    assert result["total"] == 3
    assert result["success"] == 3
    assert result["fail"] == 0
    assert len(result["results"]) == 3

    # 验证被调用
    assert mock_process_batch_publish.call_count == 1

    print("✓ 处理定时批量发布任务（有待发布内容）测试通过")


@pytest.mark.unit
def test_get_batch_publish_history(db_session: Session, test_customer: object):
    """测试获取批量发布历史记录"""
    # 创建测试平台和账号
    platform = Platform(
        name="历史记录测试平台",
        code="history_test_platform",
        type="social_media",
        description="用于历史记录测试的平台",
        api_url="https://api.history.com",
        api_key="history_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="历史记录测试账号",
        directory_name="history_test_account",
        description="用于历史记录测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    contents = []
    for i in range(5):
        content = Content(
            account_id=account.id,
            title=f"历史记录测试文章{i}",
            content=f"# 历史记录测试内容{i}\n这是第{i}篇用于历史记录测试的文章",
            category="科技",
            topic=f"历史记录测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 创建发布日志
    publish_logs = []
    for i in range(5):
        publish_log = PublishLog(
            account_id=account.id,
            content_id=contents[i].id,
            platform="wechat",
            status="success" if i % 2 == 0 else "failed",
            media_id=f"test_media_id_{i}" if i % 2 == 0 else None,
            error_message=f"测试错误{i}" if i % 2 != 0 else None,
        )
        db_session.add(publish_log)
        publish_logs.append(publish_log)

    db_session.commit()

    # 获取批量发布历史记录
    history = batch_publish_service.get_batch_publish_history(db_session, account.id, limit=10)

    # 验证结果
    assert len(history) == 5

    # 验证历史记录内容
    for i, log in enumerate(history):
        assert "id" in log
        assert "content_id" in log
        assert "status" in log
        assert "platform" in log
        assert "created_at" in log
        assert "updated_at" in log
        assert log["platform"] == "wechat"

    print("✓ 获取批量发布历史记录测试通过")


@pytest.mark.unit
def test_get_batch_publish_history_with_limit(db_session: Session, test_customer: object):
    """测试获取批量发布历史记录（带限制）"""
    # 创建测试平台和账号
    platform = Platform(
        name="限制测试平台",
        code="limit_test_platform",
        type="social_media",
        description="用于限制测试的平台",
        api_url="https://api.limit.com",
        api_key="limit_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="限制测试账号",
        directory_name="limit_test_account",
        description="用于限制测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    contents = []
    for i in range(10):
        content = Content(
            account_id=account.id,
            title=f"限制测试文章{i}",
            content=f"# 限制测试内容{i}\n这是第{i}篇用于限制测试的文章",
            category="科技",
            topic=f"限制测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 创建发布日志
    for i in range(10):
        publish_log = PublishLog(
            account_id=account.id,
            content_id=contents[i].id,
            platform="wechat",
            status="success",
            media_id=f"test_media_id_{i}",
        )
        db_session.add(publish_log)

    db_session.commit()

    # 获取批量发布历史记录（限制5条）
    history = batch_publish_service.get_batch_publish_history(db_session, account.id, limit=5)

    # 验证结果
    assert len(history) == 5

    print("✓ 获取批量发布历史记录（带限制）测试通过")


@pytest.mark.unit
def test_get_batch_publish_statistics(db_session: Session, test_customer: object):
    """测试获取批量发布统计信息"""
    # 创建测试平台和账号
    platform = Platform(
        name="统计测试平台",
        code="statistics_test_platform",
        type="social_media",
        description="用于统计测试的平台",
        api_url="https://api.statistics.com",
        api_key="statistics_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="统计测试账号",
        directory_name="statistics_test_account",
        description="用于统计测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    contents = []
    for i in range(5):
        content = Content(
            account_id=account.id,
            title=f"统计测试文章{i}",
            content=f"# 统计测试内容{i}\n这是第{i}篇用于统计测试的文章",
            category="科技",
            topic=f"统计测试选题{i}",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="approved"
        )
        db_session.add(content)
        contents.append(content)

    db_session.commit()

    # 创建发布日志（3个成功，2个失败）
    for i in range(3):
        publish_log = PublishLog(
            account_id=account.id,
            content_id=contents[i].id,
            platform="wechat",
            status="success",
            media_id=f"test_media_id_{i}",
        )
        db_session.add(publish_log)

    for i in range(2):
        publish_log = PublishLog(
            account_id=account.id,
            content_id=contents[i + 3].id,
            platform="wechat",
            status="failed",
            error_message=f"测试错误{i}"
        )
        db_session.add(publish_log)

    db_session.commit()

    # 获取批量发布统计信息
    statistics = batch_publish_service.get_batch_publish_statistics(db_session, account.id)

    # 验证结果
    assert statistics["total"] == 5
    assert statistics["success"] == 3
    assert statistics["failed"] == 2
    assert statistics["success_rate"] == 0.6

    print("✓ 获取批量发布统计信息测试通过")


@pytest.mark.unit
def test_get_batch_publish_statistics_no_logs(db_session: Session, test_customer: object):
    """测试获取批量发布统计信息（无日志）"""
    # 创建测试平台和账号
    platform = Platform(
        name="无日志统计测试平台",
        code="no_log_statistics_platform",
        type="social_media",
        description="用于无日志统计测试的平台",
        api_url="https://api.nolog.com",
        api_key="nolog_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="无日志统计测试账号",
        directory_name="no_log_statistics_account",
        description="用于无日志统计测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 获取批量发布统计信息
    statistics = batch_publish_service.get_batch_publish_statistics(db_session, account.id)

    # 验证结果
    assert statistics["total"] == 0
    assert statistics["success"] == 0
    assert statistics["failed"] == 0
    assert statistics["success_rate"] == 0

    print("✓ 获取批量发布统计信息（无日志）测试通过")


@pytest.mark.unit
@patch('app.services.batch_publish_service.content_publisher_service')
@patch('app.services.batch_publish_service.publish_pool_service')
def test_process_batch_publish_mixed_accounts(mock_publish_pool_service, mock_content_publisher_service, db_session: Session, test_customer: object):
    """测试批量发布混合账号内容"""
    # 创建测试平台和账号
    platform = Platform(
        name="混合账号测试平台",
        code="mixed_account_platform",
        type="social_media",
        description="用于混合账号测试的平台",
        api_url="https://api.mixed.com",
        api_key="mixed_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account1 = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="混合账号测试账号1",
        directory_name="mixed_account_1",
        description="用于混合账号测试的账号1",
        is_active=True
    )
    db_session.add(account1)

    account2 = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="混合账号测试账号2",
        directory_name="mixed_account_2",
        description="用于混合账号测试的账号2",
        is_active=True
    )
    db_session.add(account2)

    db_session.commit()

    # 创建测试内容（属于不同账号）
    content1 = Content(
        account_id=account1.id,
        title="混合账号测试文章1",
        content="# 混合账号测试内容1",
        category="科技",
        topic="混合账号测试选题1",
        word_count=300,
        publish_status="draft",
        review_status="approved"
    )
    db_session.add(content1)

    content2 = Content(
        account_id=account2.id,
        title="混合账号测试文章2",
        content="# 混合账号测试内容2",
        category="科技",
        topic="混合账号测试选题2",
        word_count=300,
        publish_status="draft",
        review_status="approved"
    )
    db_session.add(content2)

    db_session.commit()

    # 模拟发布池服务
    mock_pool_entry = MagicMock()
    mock_pool_entry.id = 1
    mock_publish_pool_service.add_to_pool.return_value = mock_pool_entry
    mock_publish_pool_service.complete_publishing.return_value = mock_pool_entry

    # 模拟内容发布服务
    mock_publish_result = {
        "media_id": f"test_media_id_{datetime.now().timestamp()}",
        "message": "发布成功"
    }
    mock_content_publisher_service.publish_to_wechat.return_value = mock_publish_result

    # 使用账号1发布content2（不匹配）- 应该失败
    result = batch_publish_service.process_batch_publish(db_session, account1.id, [content2.id])

    # 验证结果
    assert result["total"] == 1
    assert result["success"] == 0
    assert result["fail"] == 1
    assert result["results"][0]["success"] is False
    assert result["results"][0]["error"] == "内容不存在"

    print("✓ 批量发布混合账号内容测试通过")
