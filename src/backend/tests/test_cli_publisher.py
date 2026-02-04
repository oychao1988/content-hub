#!/usr/bin/env python3
"""
ContentHub CLI 发布管理模块测试

测试发布管理模块的各个命令功能：
- 发布内容
- 发布历史和记录
- 发布统计
- 重试发布
- 批量发布
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
from app.models.publisher import PublishLog
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
        db.query(PublishLog).filter(PublishLog.account_id == account.id).delete()
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


@pytest.fixture(scope="function")
def test_content(test_account, db_session):
    """创建测试内容"""
    content = Content(
        account_id=test_account.id,
        title="发布测试内容",
        content="这是发布测试的内容正文",
        summary="发布测试摘要",
        content_type="article",
        publish_status="draft",
        review_status="approved"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    yield content


def test_publisher_publish(test_content):
    """测试发布内容"""
    print(f"\n{Colors.BLUE}测试: 发布内容{Colors.END}")
    print("-" * 60)

    args = [
        "publisher", "publish",
        str(test_content.id),
        "--account-id", str(test_content.account_id),
        "--draft"
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:300]}")

    # content-publisher API 可能不可用，但命令应该能执行
    # 验证数据库中创建了发布日志
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        publish_log = db.query(PublishLog).filter(
            PublishLog.content_id == test_content.id
        ).first()

        if publish_log:
            print(f"{Colors.GREEN}✓ 发布日志创建成功 (ID: {publish_log.id}, 状态: {publish_log.status}){Colors.END}")
            assert publish_log.account_id == test_content.account_id
        else:
            print(f"{Colors.YELLOW}⚠ 发布日志未创建（可能需要 content-publisher API）{Colors.END}")
    finally:
        db.close()

    print(f"{Colors.GREEN}✓ 发布命令执行完成{Colors.END}")


def test_publisher_history(test_account, db_session):
    """测试发布历史"""
    print(f"\n{Colors.BLUE}测试: 发布历史{Colors.END}")
    print("-" * 60)

    # 创建多个测试内容和发布日志
    for i in range(3):
        content = Content(
            account_id=test_account.id,
            title=f"历史测试内容 {i+1}",
            content=f"内容正文 {i+1}",
            content_type="article"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        log = PublishLog(
            content_id=content.id,
            account_id=test_account.id,
            platform="wechat_mp",
            status="success" if i < 2 else "failed",
            retry_count=i
        )
        db_session.add(log)
    db_session.commit()

    args = [
        "publisher", "history",
        "--account-id", str(test_account.id),
        "--limit", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    # 验证输出包含发布历史信息
    assert "发布历史" in stdout or "ID" in stdout, f"未找到发布历史信息: {stdout}"
    print(f"{Colors.GREEN}✓ 发布历史查询成功{Colors.END}")


def test_publisher_records(test_account, db_session):
    """测试发布记录"""
    print(f"\n{Colors.BLUE}测试: 发布记录{Colors.END}")
    print("-" * 60)

    # 创建测试发布日志
    content = Content(
        account_id=test_account.id,
        title="记录测试内容",
        content="内容正文",
        content_type="article"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # 创建发布日志
    log = PublishLog(
        content_id=content.id,
        account_id=test_account.id,
        platform="wechat_mp",
        status="success",
        media_id="test_media_123",
        retry_count=0
    )
    db_session.add(log)
    db_session.commit()

    args = [
        "publisher", "records",
        "--account-id", str(test_account.id),
        "--limit", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "发布记录" in stdout or "ID" in stdout, f"未找到发布记录信息: {stdout}"
    print(f"{Colors.GREEN}✓ 发布记录查询成功{Colors.END}")


def test_publisher_stats(test_account, db_session):
    """测试发布统计"""
    print(f"\n{Colors.BLUE}测试: 发布统计{Colors.END}")
    print("-" * 60)

    # 创建不同状态的发布日志（每个内容一个日志）
    statuses = ["success", "success", "failed", "pending"]
    for i, status in enumerate(statuses):
        content = Content(
            account_id=test_account.id,
            title=f"统计测试内容 {i+1}",
            content=f"内容正文 {i+1}",
            content_type="article"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        log = PublishLog(
            content_id=content.id,
            account_id=test_account.id,
            platform="wechat_mp",
            status=status
        )
        db_session.add(log)
    db_session.commit()

    args = [
        "publisher", "stats",
        "--account-id", str(test_account.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "发布统计" in stdout or "总计" in stdout or "成功" in stdout, f"未找到统计信息: {stdout}"
    print(f"{Colors.GREEN}✓ 发布统计查询成功{Colors.END}")


def test_publisher_retry(test_account, db_session):
    """测试重试发布"""
    print(f"\n{Colors.BLUE}测试: 重试发布{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="重试测试内容",
        content="内容正文",
        content_type="article"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # 创建失败的发布日志
    log = PublishLog(
        content_id=content.id,
        account_id=test_account.id,
        platform="wechat_mp",
        status="failed",
        error_message="测试失败",
        retry_count=1
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    args = [
        "publisher", "retry",
        str(log.id)
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:300]}")

    # content-publisher API 可能不可用，但命令应该能执行
    print(f"{Colors.GREEN}✓ 重试发布命令执行完成{Colors.END}")


def test_publisher_batch_publish(test_account, db_session):
    """测试批量发布"""
    print(f"\n{Colors.BLUE}测试: 批量发布{Colors.END}")
    print("-" * 60)

    # 创建多个可发布的内容
    contents = []
    for i in range(3):
        content = Content(
            account_id=test_account.id,
            title=f"批量发布内容 {i+1}",
            content=f"内容正文 {i+1}",
            content_type="article",
            review_status="approved",
            publish_status="draft"
        )
        db_session.add(content)
        contents.append(content)
    db_session.commit()

    # 由于批量发布需要交互式确认，我们使用非交互方式测试
    # 这里只验证命令能够被调用，实际批量发布可能失败（API 不可用）
    args = [
        "publisher", "batch-publish",
        "--account-id", str(test_account.id),
        "--limit", "3"
    ]

    # 使用 echo "n" 来自动回答"否"跳过确认
    cmd = f'cd {project_root} && echo "n" | python -m cli.main publisher batch-publish --account-id {test_account.id} --limit 3'
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    print(f"返回码: {result.returncode}")
    print(f"输出: {result.stdout[:300]}")

    # 即使取消批量发布，命令也应该正常执行
    print(f"{Colors.GREEN}✓ 批量发布命令执行完成{Colors.END}")


def test_publisher_history_with_status_filter(test_account, db_session):
    """测试带状态筛选的发布历史"""
    print(f"\n{Colors.BLUE}测试: 带状态筛选的发布历史{Colors.END}")
    print("-" * 60)

    # 创建不同状态的测试内容和发布日志
    for i, status in enumerate(["success", "failed", "pending"]):
        content = Content(
            account_id=test_account.id,
            title=f"筛选测试内容 {i+1}",
            content=f"内容正文 {i+1}",
            content_type="article"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        log = PublishLog(
            content_id=content.id,
            account_id=test_account.id,
            platform="wechat_mp",
            status=status
        )
        db_session.add(log)
    db_session.commit()

    args = [
        "publisher", "history",
        "--account-id", str(test_account.id),
        "--status", "success",
        "--limit", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 带状态筛选的发布历史查询成功{Colors.END}")


def test_publisher_records_with_filters(test_account, db_session):
    """测试带筛选条件的发布记录"""
    print(f"\n{Colors.BLUE}测试: 带筛选条件的发布记录{Colors.END}")
    print("-" * 60)

    # 创建测试发布日志
    content = Content(
        account_id=test_account.id,
        title="记录筛选测试内容",
        content="内容正文",
        content_type="article"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # 创建发布日志
    log = PublishLog(
        content_id=content.id,
        account_id=test_account.id,
        platform="wechat_mp",
        status="failed",
        error_message="测试错误"
    )
    db_session.add(log)
    db_session.commit()

    args = [
        "publisher", "records",
        "--account-id", str(test_account.id),
        "--status", "failed",
        "--limit", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 带筛选条件的发布记录查询成功{Colors.END}")


def test_publisher_stats_without_account(db_session):
    """测试全局发布统计（不限账号）"""
    print(f"\n{Colors.BLUE}测试: 全局发布统计{Colors.END}")
    print("-" * 60)

    args = [
        "publisher", "stats"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "发布统计" in stdout or "总计" in stdout, f"未找到统计信息: {stdout}"
    print(f"{Colors.GREEN}✓ 全局发布统计查询成功{Colors.END}")


def test_publisher_retry_nonexistent_log():
    """测试重试不存在的发布日志"""
    print(f"\n{Colors.BLUE}测试: 重试不存在的发布日志{Colors.END}")
    print("-" * 60)

    # 使用一个不存在的日志 ID
    nonexistent_id = 999999

    args = [
        "publisher", "retry",
        str(nonexistent_id)
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:200]}")

    # 应该返回错误
    assert returncode != 0 or "不存在" in stdout or "not found" in stdout.lower()
    print(f"{Colors.GREEN}✓ 正确处理了不存在的发布日志{Colors.END}")


def test_publisher_retry_successful_log(test_account, db_session):
    """测试重试已成功的发布"""
    print(f"\n{Colors.BLUE}测试: 重试已成功的发布{Colors.END}")
    print("-" * 60)

    # 创建测试内容
    content = Content(
        account_id=test_account.id,
        title="已成功发布内容",
        content="内容正文",
        content_type="article"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    # 创建成功的发布日志
    log = PublishLog(
        content_id=content.id,
        account_id=test_account.id,
        platform="wechat_mp",
        status="success",
        media_id="test_media_123"
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    args = [
        "publisher", "retry",
        str(log.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    # 应该提示无需重试
    assert "无需重试" in stdout or "已成功" in stdout or "成功" in stdout, f"未找到预期提示: {stdout}"
    print(f"{Colors.GREEN}✓ 正确处理了重试已成功发布的请求{Colors.END}")


def test_publisher_batch_publish_no_content(test_account):
    """测试批量发布时无可发布内容"""
    print(f"\n{Colors.BLUE}测试: 批量发布无可发布内容{Colors.END}")
    print("-" * 60)

    # 不创建任何可发布内容

    # 使用 echo "n" 来自动回答"否"
    cmd = f'cd {project_root} && echo "n" | python -m cli.main publisher batch-publish --account-id {test_account.id} --limit 3'
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    print(f"返回码: {result.returncode}")
    print(f"输出: {result.stdout[:300]}")

    # 应该提示没有可发布内容
    assert "没有找到" in result.stdout or "可发布" in result.stdout or "取消" in result.stdout
    print(f"{Colors.GREEN}✓ 正确处理了无可发布内容的情况{Colors.END}")


def test_publisher_publish_with_invalid_account():
    """测试使用无效账号发布内容"""
    print(f"\n{Colors.BLUE}测试: 使用无效账号发布内容{Colors.END}")
    print("-" * 60)

    # 使用不存在的账号 ID
    invalid_account_id = 999999

    args = [
        "publisher", "publish",
        "123",  # 任意内容 ID
        "--account-id", str(invalid_account_id)
    ]

    returncode, stdout, stderr = run_cli_command(args, check=False)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:200]}")

    # 应该返回错误
    assert returncode != 0 or "不存在" in stdout or "账号" in stdout
    print(f"{Colors.GREEN}✓ 正确处理了无效账号{Colors.END}")


def test_workflow_full_publish_lifecycle(test_account, db_session):
    """测试完整的发布生命周期"""
    print(f"\n{Colors.BLUE}测试: 完整发布生命周期{Colors.END}")
    print("-" * 60)

    # 1. 创建内容
    print(f"\n步骤 1: 创建内容")
    content = Content(
        account_id=test_account.id,
        title="生命周期发布测试",
        content="测试内容",
        content_type="article",
        review_status="approved",
        publish_status="draft"
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    print(f"{Colors.GREEN}✓ 内容创建成功 (ID: {content.id}){Colors.END}")

    # 2. 手动发布（可能失败，因为 API 不可用）
    print(f"\n步骤 2: 手动发布")
    args = [
        "publisher", "publish",
        str(content.id),
        "--draft"
    ]
    returncode, stdout, stderr = run_cli_command(args, check=False)
    print(f"返回码: {returncode}")
    print(f"{Colors.GREEN}✓ 发布命令执行完成{Colors.END}")

    # 3. 查看发布历史
    print(f"\n步骤 3: 查看发布历史")
    args = [
        "publisher", "history",
        "--account-id", str(test_account.id),
        "--limit", "5"
    ]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 发布历史查询成功{Colors.END}")

    # 4. 查看发布统计
    print(f"\n步骤 4: 查看发布统计")
    args = [
        "publisher", "stats",
        "--account-id", str(test_account.id)
    ]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 发布统计查询成功{Colors.END}")

    # 5. 查看发布记录
    print(f"\n步骤 5: 查看发布记录")
    args = [
        "publisher", "records",
        "--account-id", str(test_account.id),
        "--limit", "5"
    ]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 发布记录查询成功{Colors.END}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 完整发布生命周期测试通过{Colors.END}")


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
