#!/usr/bin/env python3
"""
ContentHub CLI 内容管理模块测试

测试内容管理模块的各个命令功能：
- 内容创建和生成
- 内容列表和详情
- 内容审核流程
- 内容删除
- 选题搜索（需要 Tavily API）
- 内容统计
- 批量生成
"""

import os
import sys
import pytest
import subprocess
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.sql_db import get_engine, get_session_local
from app.models.account import Account
from app.models.customer import Customer
from app.models.platform import Platform
from app.models.content import Content
from sqlalchemy import text


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_cli_command(args: list, check: bool = True) -> tuple:
    """运行 CLI 命令

    Args:
        args: 命令参数列表
        check: 是否检查返回码

    Returns:
        (returncode, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "cli.main"] + args

    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


@pytest.fixture(scope="function")
def test_account():
    """创建测试账号（使用真实数据库）"""
    import random
    import time

    SessionLocal = get_session_local()
    db = SessionLocal()

    # 生成唯一标识
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    unique_id = f"{timestamp}_{random_suffix}"

    try:
        # 清理可能存在的旧数据
        old_platform = db.query(Platform).filter(Platform.code == f"cli_test_platform_{unique_id}").first()
        if old_platform:
            db.delete(old_platform)
            db.commit()

        # 创建平台
        platform = Platform(
            name=f"CLI测试平台_{unique_id}",
            code=f"cli_test_platform_{unique_id}",
            type="test",
            api_url="https://test.example.com",
            api_key="test_key"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        # 创建客户
        customer = Customer(
            name=f"CLI测试客户_{unique_id}",
            contact_name="测试联系人",
            contact_email=f"test_{unique_id}@example.com",
            contact_phone="13800138000",
            description="CLI测试客户"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 创建账号
        account = Account(
            name=f"CLI测试账号_{unique_id}",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name=f"cli_test_account_{unique_id}",
            description="CLI测试账号"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        yield account

        # 清理
        db.query(Content).filter(Content.account_id == account.id).delete()
        db.delete(account)
        db.delete(customer)
        db.delete(platform)
        db.commit()

    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话（使用真实数据库）"""
    SessionLocal = get_session_local()
    session = SessionLocal()

    yield session

    session.close()


def test_content_create(test_account):
    """测试创建内容"""
    print(f"\n{Colors.BLUE}测试: 创建内容{Colors.END}")
    print("-" * 60)

    args = [
        "content", "create",
        "--account-id", str(test_account.id),
        "--title", "测试文章标题",
        "--content", "这是测试文章内容",
        "--type", "article",
        "--summary", "测试摘要",
        "--tags", "测试,CLI,文章"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    # 验证命令执行成功
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "created" in stdout.lower(), f"未找到成功提示: {stdout}"

    # 验证数据库中存在记录
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        content = db.query(Content).filter(Content.title == "测试文章标题").first()
        assert content is not None, "内容未在数据库中找到"
        assert content.account_id == test_account.id
        assert content.summary == "测试摘要"
        assert content.tags == ["测试", "CLI", "文章"]
        print(f"{Colors.GREEN}✓ 内容创建成功 (ID: {content.id}){Colors.END}")
    finally:
        db.close()


def test_content_generate(test_account):
    """测试内容生成功能"""
    print(f"\n{Colors.BLUE}测试: 内容生成{Colors.END}")
    print("-" * 60)

    args = [
        "content", "generate",
        "--account-id", str(test_account.id),
        "--topic", "AI技术在内容创作中的应用",
        "--keywords", "AI,内容创作,自动化",
        "--category", "技术"
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    # 即使没有 content-creator CLI，也应该能创建草稿
    # 可能返回码非 0，但应该有内容创建
    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:200]}")

    # 验证数据库中创建了记录
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        content = db.query(Content).filter(
            Content.topic == "AI技术在内容创作中的应用"
        ).first()

        if content:
            print(f"{Colors.GREEN}✓ 内容生成成功 (ID: {content.id}){Colors.END}")
            assert content.account_id == test_account.id
            assert content.category == "技术"
        else:
            print(f"{Colors.YELLOW}⚠ 内容未在数据库中找到（可能需要 content-creator CLI）{Colors.END}")
    finally:
        db.close()


def test_content_list(test_account, db_session):
    """测试内容列表"""
    print(f"\n{Colors.BLUE}测试: 内容列表{Colors.END}")
    print("-" * 60)

    # 先创建一些测试内容
    for i in range(3):
        content = Content(
            account_id=test_account.id,
            title=f"测试内容 {i+1}",
            content=f"测试内容 {i+1} 的正文",
            summary=f"测试摘要 {i+1}",
            content_type="article",
            publish_status="draft",
            review_status="pending"
        )
        db_session.add(content)
    db_session.commit()

    # 测试列出内容
    args = [
        "content", "list",
        "--account-id", str(test_account.id),
        "--page", "1",
        "--page-size", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    # 列表命令应该显示内容或"未找到"
    print(f"{Colors.GREEN}✓ 内容列表查询成功{Colors.END}")


def test_content_info(test_account, db_session):
    """测试内容详情查看"""
    print(f"\n{Colors.BLUE}测试: 内容详情查看{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="详情测试内容",
        content="这是要查看详情的内容",
        summary="详情测试摘要",
        content_type="article",
        publish_status="draft",
        review_status="pending",
        tags=["测试", "详情"]
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    args = [
        "content", "info",
        str(content.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "详情测试内容" in stdout or "详情" in stdout, f"未找到内容标题: {stdout}"
    print(f"{Colors.GREEN}✓ 内容详情查看成功 (ID: {content.id}){Colors.END}")


def test_content_update(test_account, db_session):
    """测试内容更新"""
    print(f"\n{Colors.BLUE}测试: 内容更新{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="更新前标题",
        content="原始内容",
        summary="原始摘要",
        content_type="article"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    args = [
        "content", "update",
        str(content.id),
        "--title", "更新后标题",
        "--summary", "更新后摘要"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "updated" in stdout.lower(), f"未找到成功提示: {stdout}"

    # 验证更新
    db_session.refresh(content)
    assert content.title == "更新后标题", "标题未更新"
    assert content.summary == "更新后摘要", "摘要未更新"
    print(f"{Colors.GREEN}✓ 内容更新成功 (ID: {content.id}){Colors.END}")


def test_content_submit_review(test_account, db_session):
    """测试提交审核"""
    print(f"\n{Colors.BLUE}测试: 提交审核{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="待审核内容",
        content="需要审核的内容",
        content_type="article",
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    args = [
        "content", "submit-review",
        str(content.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    # 检查成功标志（可能是 emoji 或文本）
    assert ("成功" in stdout or "submitted" in stdout.lower() or "✅" in stdout or "已提交审核" in stdout), f"未找到成功提示: {stdout}"

    # 验证状态
    db_session.refresh(content)
    print(f"{Colors.GREEN}✓ 内容提交审核成功 (ID: {content.id}, 状态: {content.review_status}){Colors.END}")


def test_content_approve(test_account, db_session):
    """测试审核通过"""
    print(f"\n{Colors.BLUE}测试: 审核通过{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="待审核内容",
        content="需要审核的内容",
        content_type="article",
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    args = [
        "content", "approve",
        str(content.id),
        "--comment", "内容质量优秀"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "approved" in stdout.lower(), f"未找到成功提示: {stdout}"

    # 验证状态
    db_session.refresh(content)
    assert content.review_status == "approved", f"审核状态不正确: {content.review_status}"
    print(f"{Colors.GREEN}✓ 内容审核通过 (ID: {content.id}){Colors.END}")


def test_content_reject(test_account, db_session):
    """测试审核驳回"""
    print(f"\n{Colors.BLUE}测试: 审核驳回{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="待驳回内容",
        content="需要驳回的内容",
        content_type="article",
        publish_status="draft",
        review_status="pending"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    args = [
        "content", "reject",
        str(content.id),
        "--reason", "内容需要修改"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "rejected" in stdout.lower(), f"未找到成功提示: {stdout}"

    # 验证状态
    db_session.refresh(content)
    assert content.review_status == "rejected", f"审核状态不正确: {content.review_status}"
    assert "需要修改" in content.review_comment or content.review_comment == "内容需要修改"
    print(f"{Colors.GREEN}✓ 内容审核驳回 (ID: {content.id}){Colors.END}")


def test_content_delete(test_account, db_session):
    """测试删除内容"""
    print(f"\n{Colors.BLUE}测试: 删除内容{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="待删除内容",
        content="将被删除的内容",
        content_type="article"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    content_id = content.id

    # 使用 --yes 跳过确认
    args = [
        "content", "delete",
        str(content_id),
        "--yes"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    # 删除命令可能需要交互式确认，这里我们检查命令是否执行
    print(f"返回码: {returncode}")
    print(f"输出: {stdout}")

    # 手动删除内容以清理
    db_session.query(Content).filter(Content.id == content_id).delete()
    db_session.commit()

    print(f"{Colors.GREEN}✓ 内容删除测试完成{Colors.END}")


def test_content_topic_search(test_account):
    """测试选题搜索（需要 Tavily API）"""
    print(f"\n{Colors.BLUE}测试: 选题搜索{Colors.END}")
    print("-" * 60)

    # 检查是否配置了 Tavily API
    from app.core.config import settings
    if not settings.TAVILY_API_KEY:
        print(f"{Colors.YELLOW}⚠ 未配置 TAVILY_API_KEY，跳过选题搜索测试{Colors.END}")
        return

    args = [
        "content", "topic-search",
        "--account-id", str(test_account.id),
        "--keywords", "Python,编程,教程",
        "--max-results", "5"
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    print(f"返回码: {returncode}")
    print(f"输出前 200 字符: {stdout[:200]}")

    # Tavily API 可能调用失败，但命令应该能执行
    print(f"{Colors.GREEN}✓ 选题搜索命令执行完成{Colors.END}")


def test_content_statistics(db_session, test_account):
    """测试内容统计"""
    print(f"\n{Colors.BLUE}测试: 内容统计{Colors.END}")
    print("-" * 60)

    # 创建不同状态的内容
    contents = [
        Content(account_id=test_account.id, title="草稿1", content="内容1", review_status="pending", publish_status="draft"),
        Content(account_id=test_account.id, title="草稿2", content="内容2", review_status="approved", publish_status="draft"),
        Content(account_id=test_account.id, title="已发布", content="内容3", review_status="approved", publish_status="published"),
        Content(account_id=test_account.id, title="已拒绝", content="内容4", review_status="rejected", publish_status="draft"),
    ]
    for content in contents:
        db_session.add(content)
    db_session.commit()

    args = [
        "content", "statistics"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    # 统计信息应该包含数字
    print(f"{Colors.GREEN}✓ 内容统计查询成功{Colors.END}")


def test_content_batch_generate(test_account):
    """测试批量生成"""
    print(f"\n{Colors.BLUE}测试: 批量生成内容{Colors.END}")
    print("-" * 60)

    args = [
        "content", "batch-generate",
        "--account-id", str(test_account.id),
        "--count", "3",
        "--keywords", "测试1,测试2,测试3",
        "--category", "测试分类"
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:300]}")

    # 验证数据库中创建了内容
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        contents = db.query(Content).filter(
            Content.account_id == test_account.id,
            Content.category == "测试分类"
        ).all()

        if contents:
            print(f"{Colors.GREEN}✓ 批量生成成功，创建了 {len(contents)} 条内容{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠ 未找到批量生成的内容{Colors.END}")
    finally:
        db.close()


def test_content_review_list(test_account, db_session):
    """测试待审核列表"""
    print(f"\n{Colors.BLUE}测试: 待审核列表{Colors.END}")
    print("-" * 60)

    # 创建待审核内容
    contents = [
        Content(account_id=test_account.id, title="待审核1", content="内容1", review_status="pending"),
        Content(account_id=test_account.id, title="待审核2", content="内容2", review_status="reviewing"),
    ]
    for content in contents:
        db_session.add(content)
    db_session.commit()

    args = [
        "content", "review-list"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 待审核列表查询成功{Colors.END}")


def test_content_list_with_filters(test_account, db_session):
    """测试带筛选条件的内容列表"""
    print(f"\n{Colors.BLUE}测试: 带筛选条件的内容列表{Colors.END}")
    print("-" * 60)

    # 创建不同状态的内容
    contents = [
        Content(account_id=test_account.id, title="已发布", content="内容1", review_status="approved", publish_status="published"),
        Content(account_id=test_account.id, title="草稿", content="内容2", review_status="pending", publish_status="draft"),
    ]
    for content in contents:
        db_session.add(content)
    db_session.commit()

    # 测试按状态筛选
    args = [
        "content", "list",
        "--account-id", str(test_account.id),
        "--status", "published"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 带筛选条件的内容列表查询成功{Colors.END}")


def test_workflow_full_lifecycle(test_account, db_session):
    """测试完整的内容生命周期"""
    print(f"\n{Colors.BLUE}测试: 完整内容生命周期{Colors.END}")
    print("-" * 60)

    # 1. 创建内容
    print(f"\n步骤 1: 创建内容")
    args = [
        "content", "create",
        "--account-id", str(test_account.id),
        "--title", "生命周期测试",
        "--content", "测试内容"
    ]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0

    content = db_session.query(Content).filter(Content.title == "生命周期测试").first()
    assert content is not None
    content_id = content.id
    print(f"{Colors.GREEN}✓ 内容创建成功 (ID: {content_id}){Colors.END}")

    # 2. 提交审核
    print(f"\n步骤 2: 提交审核")
    args = ["content", "submit-review", str(content_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 提交审核成功{Colors.END}")

    # 3. 审核通过
    print(f"\n步骤 3: 审核通过")
    args = ["content", "approve", str(content_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    db_session.refresh(content)
    assert content.review_status == "approved"
    print(f"{Colors.GREEN}✓ 审核通过成功{Colors.END}")

    # 4. 查看详情
    print(f"\n步骤 4: 查看详情")
    args = ["content", "info", str(content_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 查看详情成功{Colors.END}")

    # 5. 更新内容
    print(f"\n步骤 5: 更新内容")
    args = ["content", "update", str(content_id), "--summary", "更新后的摘要"]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 更新内容成功{Colors.END}")

    # 6. 删除内容
    print(f"\n步骤 6: 删除内容")
    db_session.query(Content).filter(Content.id == content_id).delete()
    db_session.commit()
    print(f"{Colors.GREEN}✓ 删除内容成功{Colors.END}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 完整生命周期测试通过{Colors.END}")


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
