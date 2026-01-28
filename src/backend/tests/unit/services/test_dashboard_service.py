"""
仪表盘服务单元测试
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.modules.dashboard.services import dashboard_service
from app.models.content import Content
from app.models.publisher import PublishLog
from app.models.account import Account
from app.models.platform import Platform


@pytest.mark.unit
def test_get_dashboard_stats(db_session: Session, test_customer: object):
    """测试获取仪表盘统计数据"""
    # 创建测试平台和账号
    platform = Platform(
        name="仪表盘测试平台",
        code="dashboard_test_platform",
        type="social_media",
        description="用于仪表盘测试的平台",
        api_url="https://api.dashboard.com",
        api_key="dashboard_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="仪表盘测试账号",
        directory_name="dashboard_test_account",
        description="用于仪表盘测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容（包含待审核和已发布的）
    contents_data = [
        {
            "account_id": account.id,
            "title": "待审核文章1",
            "content": "# 待审核内容1\n这是一篇待审核的文章",
            "category": "科技",
            "topic": "待审核选题1",
            "word_count": 300,
            "publish_status": "draft",
            "review_status": "pending"
        },
        {
            "account_id": account.id,
            "title": "待审核文章2",
            "content": "# 待审核内容2\n这是一篇待审核的文章",
            "category": "财经",
            "topic": "待审核选题2",
            "word_count": 400,
            "publish_status": "draft",
            "review_status": "pending"
        },
        {
            "account_id": account.id,
            "title": "已发布文章1",
            "content": "# 已发布内容1\n这是一篇已发布的文章",
            "category": "科技",
            "topic": "已发布选题1",
            "word_count": 500,
            "publish_status": "published",
            "review_status": "approved"
        }
    ]

    for data in contents_data:
        content = Content(**data)
        db_session.add(content)

    db_session.commit()

    # 创建测试发布日志（包含成功和失败的，每个content_id唯一）
    publish_logs_data = [
        {
            "account_id": account.id,
            "content_id": db_session.query(Content).filter(Content.title == "已发布文章1").first().id,
            "platform": "wechat",
            "media_id": "media_id_123",
            "status": "success",
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "account_id": account.id,
            "content_id": db_session.query(Content).filter(Content.title == "待审核文章1").first().id,
            "platform": "wechat",
            "status": "failed",
            "error_message": "发布失败",
            "created_at": datetime.now() - timedelta(days=2)
        },
        {
            "account_id": account.id,
            "content_id": db_session.query(Content).filter(Content.title == "待审核文章2").first().id,
            "platform": "wechat",
            "media_id": "media_id_456",
            "status": "success",
            "created_at": datetime.now()
        }
    ]

    for data in publish_logs_data:
        publish_log = PublishLog(**data)
        db_session.add(publish_log)

    db_session.commit()

    # 获取仪表盘统计数据
    stats = dashboard_service.get_dashboard_stats(db_session)

    # 验证统计数据
    assert stats["account_count"] >= 1
    assert stats["content_count"] >= 3
    assert stats["pending_review_count"] >= 2
    assert stats["published_count"] >= 1
    assert stats["today_published_count"] >= 1
    assert stats["week_published_count"] >= 2

    print("✓ 仪表盘统计数据测试通过")


@pytest.mark.unit
def test_get_content_trend(db_session: Session, test_customer: object):
    """测试获取内容生成趋势"""
    # 创建测试平台和账号
    platform = Platform(
        name="内容趋势测试平台",
        code="content_trend_test_platform",
        type="social_media",
        description="用于内容趋势测试的平台",
        api_url="https://api.trend.com",
        api_key="trend_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="内容趋势测试账号",
        directory_name="content_trend_test_account",
        description="用于内容趋势测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容（过去30天的内容）
    for i in range(30):
        content = Content(
            account_id=account.id,
            title=f"测试文章{i}",
            content=f"# 文章内容{i}\n这是第{i}篇测试文章",
            category="科技",
            topic=f"测试选题{i}",
            word_count=300 + i * 10,
            publish_status="published",
            review_status="approved",
            created_at=datetime.now() - timedelta(days=i)
        )
        db_session.add(content)

    db_session.commit()

    # 获取内容生成趋势（30天）
    trend = dashboard_service.get_content_trend(db_session, days=30)

    # 验证趋势数据
    assert trend["period_days"] == 30
    assert len(trend["trend"]) > 0

    print(f"✓ 内容生成趋势测试通过 (共 {len(trend['trend'])} 天数据)")


@pytest.mark.unit
def test_get_publish_stats(db_session: Session, test_customer: object):
    """测试获取发布统计"""
    # 创建测试平台和账号
    platform = Platform(
        name="发布统计测试平台",
        code="publish_stats_test_platform",
        type="social_media",
        description="用于发布统计测试的平台",
        api_url="https://api.stats.com",
        api_key="stats_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="发布统计测试账号",
        directory_name="publish_stats_test_account",
        description="用于发布统计测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="发布统计测试文章",
        content="# 发布统计测试内容\n这是一篇用于发布统计测试的文章",
        category="科技",
        topic="发布统计测试选题",
        word_count=300,
        publish_status="published",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()

    # 创建测试发布日志（包含成功和失败的，每个content_id唯一）
    # 先创建多个测试内容
    contents = []
    for i in range(5):
        test_content = Content(
            account_id=account.id,
            title=f"发布统计测试文章{i}",
            content=f"# 发布统计测试内容{i}\n这是第{i}篇用于发布统计测试的文章",
            category="科技",
            topic=f"发布统计测试选题{i}",
            word_count=300 + i * 100,
            publish_status="published",
            review_status="approved"
        )
        db_session.add(test_content)
        contents.append(test_content)

    db_session.commit()

    publish_logs_data = [
        {
            "account_id": account.id,
            "content_id": contents[0].id,
            "platform": "wechat",
            "media_id": "media_id_123",
            "status": "success"
        },
        {
            "account_id": account.id,
            "content_id": contents[1].id,
            "platform": "wechat",
            "status": "failed",
            "error_message": "发布失败"
        },
        {
            "account_id": account.id,
            "content_id": contents[2].id,
            "platform": "wechat",
            "media_id": "media_id_456",
            "status": "success"
        },
        {
            "account_id": account.id,
            "content_id": contents[3].id,
            "platform": "qq",
            "media_id": "qq_media_id",
            "status": "success"
        },
        {
            "account_id": account.id,
            "content_id": contents[4].id,
            "platform": "qq",
            "status": "failed",
            "error_message": "发布失败"
        }
    ]

    for data in publish_logs_data:
        publish_log = PublishLog(**data)
        db_session.add(publish_log)

    db_session.commit()

    # 获取发布统计
    publish_stats = dashboard_service.get_publish_stats(db_session)

    # 验证发布统计
    assert publish_stats["total_publish"] >= 5
    assert publish_stats["success_publish"] >= 3
    assert publish_stats["failed_publish"] >= 2
    assert publish_stats["success_rate"] > 0

    # 验证平台统计
    platforms = [item["platform"] for item in publish_stats["platform_stats"]]
    assert "wechat" in platforms
    assert "qq" in platforms

    print("✓ 发布统计测试通过")


@pytest.mark.unit
def test_dashboard_service_operations(db_session: Session, test_customer: object):
    """综合测试仪表盘服务操作"""
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

    # 测试所有仪表盘服务方法
    stats = dashboard_service.get_dashboard_stats(db_session)
    assert stats["account_count"] >= 1

    trend = dashboard_service.get_content_trend(db_session, days=7)
    assert trend["period_days"] == 7

    publish_stats = dashboard_service.get_publish_stats(db_session)
    assert publish_stats["total_publish"] >= 1

    print("✓ 仪表盘服务综合测试通过")
