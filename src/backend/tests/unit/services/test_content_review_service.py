"""
内容审核服务单元测试
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import patch

from app.services.content_review_service import content_review_service
from app.models.content import Content
from app.models.customer import Customer
from app.models.platform import Platform
from app.models.account import Account


@pytest.mark.unit
def test_init():
    """测试初始化审核服务"""
    content_review_service.init()
    print("✓ 审核服务初始化测试通过")


@pytest.mark.unit
def test_get_pending_reviews(db_session: Session, test_customer: Customer):
    """测试获取待审核内容列表"""
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

    # 创建测试内容（包含待审核状态）
    contents_data = [
        {
            "account_id": account.id,
            "title": "待审核文章1",
            "content": "# 待审核内容1\n这是一篇待审核的文章",
            "word_count": 300,
            "publish_status": "draft",
            "review_status": "pending"
        },
        {
            "account_id": account.id,
            "title": "审核中文章",
            "content": "# 审核中内容\n这是一篇正在审核的文章",
            "word_count": 400,
            "publish_status": "draft",
            "review_status": "reviewing"
        },
        {
            "account_id": account.id,
            "title": "已审核文章",
            "content": "# 已审核内容\n这是一篇已审核的文章",
            "word_count": 500,
            "publish_status": "published",
            "review_status": "approved"
        }
    ]

    for data in contents_data:
        content = Content(**data)
        db_session.add(content)

    db_session.commit()

    # 获取待审核内容列表
    pending_reviews = content_review_service.get_pending_reviews(db_session)

    # 验证结果
    assert len(pending_reviews) == 1
    assert pending_reviews[0].title == "待审核文章1"
    assert pending_reviews[0].review_status == "pending"

    print(f"✓ 获取待审核内容列表测试通过 (找到 {len(pending_reviews)} 篇待审核内容)")


@pytest.mark.unit
def test_submit_for_review(db_session: Session, test_customer: Customer):
    """测试提交审核"""
    # 创建测试平台和账号
    platform = Platform(
        name="提交审核测试平台",
        code="submit_platform",
        type="social_media",
        description="用于提交审核测试的平台",
        api_url="https://api.submit.com",
        api_key="submit_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="提交审核测试账号",
        directory_name="submit_test_account",
        description="用于提交审核测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="待提交审核文章",
        content="# 待提交审核内容\n这是一篇待提交审核的文章",
        word_count=300,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()

    # 提交审核
    submitted_content = content_review_service.submit_for_review(db_session, content.id)

    # 验证审核状态已更改
    assert submitted_content is not None
    assert submitted_content.review_status == "reviewing"

    print(f"✓ 提交审核测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_approve_content(db_session: Session, test_customer: Customer):
    """测试审核通过"""
    # 创建测试平台和账号
    platform = Platform(
        name="审核通过测试平台",
        code="approve_platform",
        type="social_media",
        description="用于审核通过测试的平台",
        api_url="https://api.approve.com",
        api_key="approve_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="审核通过测试账号",
        directory_name="approve_test_account",
        description="用于审核通过测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="待审核通过文章",
        content="# 待审核通过内容\n这是一篇待审核通过的文章",
        word_count=300,
        publish_status="draft",
        review_status="reviewing"
    )
    db_session.add(content)
    db_session.commit()

    # 审核通过
    approved_content = content_review_service.approve_content(db_session, content.id, reviewer_id=1)

    # 验证审核结果
    assert approved_content is not None
    assert approved_content.review_status == "approved"
    assert approved_content.status == "approved"
    assert approved_content.reviewed_by == 1
    assert approved_content.reviewed_at is not None

    print(f"✓ 审核通过测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_reject_content(db_session: Session, test_customer: Customer):
    """测试审核拒绝"""
    # 创建测试平台和账号
    platform = Platform(
        name="审核拒绝测试平台",
        code="reject_platform",
        type="social_media",
        description="用于审核拒绝测试的平台",
        api_url="https://api.reject.com",
        api_key="reject_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="审核拒绝测试账号",
        directory_name="reject_test_account",
        description="用于审核拒绝测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="待审核拒绝文章",
        content="# 待审核拒绝内容\n这是一篇待审核拒绝的文章",
        word_count=300,
        publish_status="draft",
        review_status="reviewing"
    )
    db_session.add(content)
    db_session.commit()

    # 审核拒绝
    reject_reason = "内容不符合要求"
    rejected_content = content_review_service.reject_content(
        db_session, content.id, reason=reject_reason, reviewer_id=1
    )

    # 验证审核结果
    assert rejected_content is not None
    assert rejected_content.review_status == "rejected"
    assert rejected_content.status == "rejected"
    assert rejected_content.reviewed_by == 1
    assert rejected_content.reviewed_at is not None
    assert rejected_content.review_comment == reject_reason

    print(f"✓ 审核拒绝测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_auto_review_content_approve(db_session: Session, test_customer: Customer):
    """测试自动审核（通过）"""
    # 创建测试平台和账号
    platform = Platform(
        name="自动审核测试平台",
        code="auto_review_platform",
        type="social_media",
        description="用于自动审核测试的平台",
        api_url="https://api.auto.com",
        api_key="auto_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="自动审核测试账号",
        directory_name="auto_test_account",
        description="用于自动审核测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建符合要求的内容（字数≥500）
    content = Content(
        account_id=account.id,
        title="符合要求的文章",
        content="# 符合要求的内容\n" + "这是一篇符合要求的文章。" * 100,
        word_count=600,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()

    # 自动审核
    auto_reviewed_content = content_review_service.auto_review_content(db_session, content.id)

    # 验证审核结果
    assert auto_reviewed_content is not None
    assert auto_reviewed_content.review_status == "approved"
    assert auto_reviewed_content.status == "approved"
    assert auto_reviewed_content.reviewed_at is not None

    print(f"✓ 自动审核通过测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_auto_review_content_reject(db_session: Session, test_customer: Customer):
    """测试自动审核（拒绝）"""
    # 创建测试平台和账号
    platform = Platform(
        name="自动审核拒绝测试平台",
        code="auto_reject_platform",
        type="social_media",
        description="用于自动审核拒绝测试的平台",
        api_url="https://api.auto_reject.com",
        api_key="auto_reject_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="自动审核拒绝测试账号",
        directory_name="auto_reject_test_account",
        description="用于自动审核拒绝测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建不符合要求的内容（字数<500）
    content = Content(
        account_id=account.id,
        title="不符合要求的文章",
        content="# 不符合要求的内容\n这是一篇字数不足的文章。",
        word_count=200,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()

    # 自动审核
    auto_reviewed_content = content_review_service.auto_review_content(db_session, content.id)

    # 验证审核结果
    assert auto_reviewed_content is not None
    assert auto_reviewed_content.review_status == "rejected"
    assert auto_reviewed_content.status == "rejected"
    assert auto_reviewed_content.reviewed_at is not None
    assert "字数不足" in auto_reviewed_content.review_comment

    print(f"✓ 自动审核拒绝测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_get_review_history(db_session: Session, test_customer: Customer):
    """测试获取审核历史"""
    # 创建测试平台和账号
    platform = Platform(
        name="审核历史测试平台",
        code="history_platform",
        type="social_media",
        description="用于审核历史测试的平台",
        api_url="https://api.history.com",
        api_key="history_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="审核历史测试账号",
        directory_name="history_test_account",
        description="用于审核历史测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="有审核历史的文章",
        content="# 审核历史内容\n这是一篇有审核历史的文章",
        word_count=300,
        publish_status="draft",
        review_status="approved",
        review_comment="内容不错，通过审核"
    )
    db_session.add(content)
    db_session.commit()

    # 获取审核历史
    review_history = content_review_service.get_review_history(db_session, content.id)

    # 验证审核历史
    assert review_history is not None
    assert review_history.id == content.id
    assert review_history.review_status == "approved"
    assert review_history.review_comment == "内容不错，通过审核"

    print(f"✓ 获取审核历史测试通过 (ID: {content.id})")


@pytest.mark.unit
def test_batch_review(db_session: Session, test_customer: Customer):
    """测试批量审核"""
    # 创建测试平台和账号
    platform = Platform(
        name="批量审核测试平台",
        code="batch_platform",
        type="social_media",
        description="用于批量审核测试的平台",
        api_url="https://api.batch.com",
        api_key="batch_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="批量审核测试账号",
        directory_name="batch_test_account",
        description="用于批量审核测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建多个测试内容
    content_ids = []
    for i in range(5):
        content = Content(
            account_id=account.id,
            title=f"批量审核文章{i}",
            content=f"# 批量审核内容{i}\n这是第{i}篇待批量审核的文章",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="reviewing"
        )
        db_session.add(content)
        db_session.commit()
        content_ids.append(content.id)

    # 批量审核通过
    batch_result = content_review_service.batch_review(
        db_session, content_ids, action="approve", reviewer_id=1
    )

    # 验证批量审核结果
    assert batch_result["processed"] == 5
    assert batch_result["succeeded"] == 5
    assert batch_result["failed"] == 0

    # 验证所有内容已通过审核
    for content_id in content_ids:
        content = db_session.query(Content).filter(Content.id == content_id).first()
        assert content.review_status == "approved"

    print(f"✓ 批量审核测试通过 (处理 {batch_result['processed']} 篇，成功 {batch_result['succeeded']} 篇)")


@pytest.mark.unit
def test_batch_review_reject(db_session: Session, test_customer: Customer):
    """测试批量审核拒绝"""
    # 创建测试平台和账号
    platform = Platform(
        name="批量审核拒绝测试平台",
        code="batch_reject_platform",
        type="social_media",
        description="用于批量审核拒绝测试的平台",
        api_url="https://api.batch_reject.com",
        api_key="batch_reject_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="批量审核拒绝测试账号",
        directory_name="batch_reject_test_account",
        description="用于批量审核拒绝测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建多个测试内容
    content_ids = []
    for i in range(3):
        content = Content(
            account_id=account.id,
            title=f"批量审核拒绝文章{i}",
            content=f"# 批量审核拒绝内容{i}\n这是第{i}篇待批量审核拒绝的文章",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="reviewing"
        )
        db_session.add(content)
        db_session.commit()
        content_ids.append(content.id)

    # 批量审核拒绝
    batch_result = content_review_service.batch_review(
        db_session, content_ids, action="reject", reason="内容质量不符合要求", reviewer_id=1
    )

    # 验证批量审核结果
    assert batch_result["processed"] == 3
    assert batch_result["succeeded"] == 3
    assert batch_result["failed"] == 0

    # 验证所有内容已被拒绝
    for content_id in content_ids:
        content = db_session.query(Content).filter(Content.id == content_id).first()
        assert content.review_status == "rejected"
        assert content.review_comment == "内容质量不符合要求"

    print(f"✓ 批量审核拒绝测试通过 (处理 {batch_result['processed']} 篇，成功 {batch_result['succeeded']} 篇)")


@pytest.mark.unit
def test_batch_review_with_invalid_id(db_session: Session, test_customer: Customer):
    """测试批量审核包含无效ID"""
    # 创建测试平台和账号
    platform = Platform(
        name="批量审核异常测试平台",
        code="batch_exception_platform",
        type="social_media",
        description="用于批量审核异常测试的平台",
        api_url="https://api.batch_exception.com",
        api_key="batch_exception_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="批量审核异常测试账号",
        directory_name="batch_exception_test_account",
        description="用于批量审核异常测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建多个测试内容
    content_ids = []
    for i in range(2):
        content = Content(
            account_id=account.id,
            title=f"批量审核异常文章{i}",
            content=f"# 批量审核异常内容{i}\n这是第{i}篇待批量审核异常的文章",
            word_count=300 + i * 100,
            publish_status="draft",
            review_status="reviewing"
        )
        db_session.add(content)
        db_session.commit()
        content_ids.append(content.id)

    # 添加一个无效的内容ID
    content_ids.append(99999)

    # 批量审核
    batch_result = content_review_service.batch_review(
        db_session, content_ids, action="approve", reviewer_id=1
    )

    # 验证批量审核结果（无效ID不会触发异常，而是返回None）
    assert batch_result["processed"] == 3
    assert batch_result["succeeded"] == 3
    assert batch_result["failed"] == 0

    print(f"✓ 批量审核异常处理测试通过 (处理 {batch_result['processed']} 篇，成功 {batch_result['succeeded']} 篇，失败 {batch_result['failed']} 篇)")


@pytest.mark.unit
def test_batch_review_with_exception(db_session: Session, test_customer: Customer):
    """测试批量审核包含异常情况"""
    # 创建测试平台和账号
    platform = Platform(
        name="批量审核异常测试平台2",
        code="batch_exception_platform2",
        type="social_media",
        description="用于批量审核异常测试的平台2",
        api_url="https://api.batch_exception2.com",
        api_key="batch_exception_api_key2",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="批量审核异常测试账号2",
        directory_name="batch_exception_test_account2",
        description="用于批量审核异常测试的账号2",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="批量审核异常文章",
        content="# 批量审核异常内容\n这是一篇待批量审核异常的文章",
        word_count=300,
        publish_status="draft",
        review_status="reviewing"
    )
    db_session.add(content)
    db_session.commit()

    content_ids = [content.id]

    # 使用 mock 模拟 approve_content 抛出异常
    with patch('app.services.content_review_service.ContentReviewService.approve_content',
               side_effect=Exception("测试异常")):
        batch_result = content_review_service.batch_review(
            db_session, content_ids, action="approve", reviewer_id=1
        )

    # 验证批量审核结果
    assert batch_result["processed"] == 1
    assert batch_result["succeeded"] == 0
    assert batch_result["failed"] == 1

    print(f"✓ 批量审核异常处理测试通过 (处理 {batch_result['processed']} 篇，成功 {batch_result['succeeded']} 篇，失败 {batch_result['failed']} 篇)")


@pytest.mark.unit
def test_get_review_statistics(db_session: Session, test_customer: Customer):
    """测试获取审核统计信息"""
    # 创建测试平台和账号
    platform = Platform(
        name="统计测试平台",
        code="stats_platform",
        type="social_media",
        description="用于审核统计测试的平台",
        api_url="https://api.stats.com",
        api_key="stats_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="统计测试账号",
        directory_name="stats_test_account",
        description="用于审核统计测试的账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建不同审核状态的内容
    contents_data = [
        {"review_status": "pending"},
        {"review_status": "pending"},
        {"review_status": "reviewing"},
        {"review_status": "approved"},
        {"review_status": "approved"},
        {"review_status": "approved"},
        {"review_status": "rejected"}
    ]

    for data in contents_data:
        content = Content(
            account_id=account.id,
            title=f"统计测试文章{len(db_session.query(Content).all()) + 1}",
            content="# 统计测试内容\n这是一篇用于统计测试的文章",
            word_count=300,
            publish_status="draft",
            **data
        )
        db_session.add(content)

    db_session.commit()

    # 获取审核统计信息
    statistics = content_review_service.get_review_statistics(db_session)

    # 验证统计信息
    assert statistics["total"] == 7
    assert statistics["pending"] == 2
    assert statistics["reviewing"] == 1
    assert statistics["approved"] == 3
    assert statistics["rejected"] == 1

    print(f"✓ 审核统计信息测试通过 (总内容: {statistics['total']} 篇)")


@pytest.mark.unit
def test_content_review_service_comprehensive(db_session: Session, test_customer: Customer):
    """综合测试内容审核服务"""
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

    # 创建测试内容
    content = Content(
        account_id=account.id,
        title="综合测试文章",
        content="# 综合测试内容\n这是一篇综合测试文章",
        word_count=550,
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()

    # 测试完整审核流程
    content_id = content.id

    # 1. 提交审核
    submitted = content_review_service.submit_for_review(db_session, content_id)
    assert submitted is not None
    assert submitted.review_status == "reviewing"

    # 2. 审核通过
    approved = content_review_service.approve_content(db_session, content_id, reviewer_id=1)
    assert approved is not None
    assert approved.review_status == "approved"

    # 3. 获取审核历史
    history = content_review_service.get_review_history(db_session, content_id)
    assert history is not None
    assert history.reviewed_by == 1

    # 4. 获取审核统计
    stats = content_review_service.get_review_statistics(db_session)
    assert stats["total"] >= 1
    assert stats["approved"] >= 1

    print("✓ 内容审核服务综合测试通过")
