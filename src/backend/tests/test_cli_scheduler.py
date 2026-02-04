#!/usr/bin/env python3
"""
ContentHub CLI 定时任务模块测试

测试定时任务模块的各个命令功能：
- 任务创建和更新
- 任务列表和详情
- 任务手动触发
- 任务执行历史
- 任务暂停和恢复
- 调度器启动和停止
- 调度器状态查询
- 任务删除
"""

import os
import sys
import pytest
import subprocess
import time
import random
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.sql_db import get_engine, get_session_local
from app.models.scheduler import ScheduledTask, TaskExecution
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


def generate_unique_name() -> str:
    """生成唯一标识符"""
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    return f"test_task_{timestamp}_{random_suffix}"


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    SessionLocal = get_session_local()
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture(scope="function")
def test_task(db_session):
    """创建测试定时任务"""
    unique_name = generate_unique_name()

    task = ScheduledTask(
        name=unique_name,
        description="CLI测试任务",
        task_type="content_generation",
        cron_expression="0 0 * * *",
        is_active=True
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    yield task

    # 清理
    db_session.query(TaskExecution).filter(TaskExecution.task_id == task.id).delete()
    db_session.query(ScheduledTask).filter(ScheduledTask.id == task.id).delete()
    db_session.commit()


def test_scheduler_create(db_session):
    """测试创建定时任务"""
    print(f"\n{Colors.BLUE}测试: 创建定时任务{Colors.END}")
    print("-" * 60)

    unique_name = generate_unique_name()

    args = [
        "scheduler", "create",
        "--name", unique_name,
        "--type", "content_generation",
        "--cron", "0 9 * * *",
        "--enabled",
        "--description", "测试定时任务"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:500]}")

    # 验证命令执行成功
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("成功" in stdout or "created" in stdout.lower()), f"未找到成功提示: {stdout}"

    # 验证数据库中存在记录
    task = db_session.query(ScheduledTask).filter(ScheduledTask.name == unique_name).first()
    assert task is not None, "任务未在数据库中找到"
    assert task.task_type == "content_generation"
    assert task.cron_expression == "0 9 * * *"
    assert task.is_active == True
    assert task.description == "测试定时任务"

    print(f"{Colors.GREEN}✓ 定时任务创建成功 (ID: {task.id}){Colors.END}")

    # 清理
    db_session.query(TaskExecution).filter(TaskExecution.task_id == task.id).delete()
    db_session.delete(task)
    db_session.commit()


def test_scheduler_create_with_account(db_session, test_task):
    """测试创建带账号ID的定时任务"""
    print(f"\n{Colors.BLUE}测试: 创建带账号ID的定时任务{Colors.END}")
    print("-" * 60)

    # 先创建一个账号
    from app.models.account import Account
    from app.models.customer import Customer
    from app.models.platform import Platform

    unique_name = generate_unique_name()

    # 创建平台
    platform = Platform(
        name=f"测试平台_{unique_name}",
        code=f"test_platform_{unique_name}",
        type="test",
        api_url="https://test.example.com",
        api_key="test_key"
    )
    db_session.add(platform)
    db_session.commit()
    db_session.refresh(platform)

    # 创建客户
    customer = Customer(
        name=f"测试客户_{unique_name}",
        contact_name="测试联系人",
        contact_email=f"test_{unique_name}@example.com",
        contact_phone="13800138000",
        description="测试客户"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    # 创建账号
    account = Account(
        name=f"测试账号_{unique_name}",
        customer_id=customer.id,
        platform_id=platform.id,
        directory_name=f"test_account_{unique_name}",
        description="测试账号"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # 创建带账号ID的任务
    task_unique_name = generate_unique_name()
    args = [
        "scheduler", "create",
        "--name", task_unique_name,
        "--type", "publishing",
        "--cron", "0 10 * * *",
        "--account-id", str(account.id),
        "--description", "测试发布任务"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    # 验证命令执行成功
    assert returncode == 0, f"命令执行失败: {stderr}"

    # 验证数据库中存在记录
    task = db_session.query(ScheduledTask).filter(ScheduledTask.name == task_unique_name).first()
    assert task is not None, "任务未在数据库中找到"

    print(f"{Colors.GREEN}✓ 带账号ID的定时任务创建成功 (ID: {task.id}){Colors.END}")

    # 清理
    db_session.query(TaskExecution).filter(TaskExecution.task_id == task.id).delete()
    db_session.delete(task)
    db_session.delete(account)
    db_session.delete(customer)
    db_session.delete(platform)
    db_session.commit()


def test_scheduler_create_duplicate_name(db_session, test_task):
    """测试创建重复名称的任务"""
    print(f"\n{Colors.BLUE}测试: 创建重复名称的任务{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "create",
        "--name", test_task.name,
        "--type", "content_generation",
        "--cron", "0 9 * * *"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:200]}")

    # 应该返回错误
    assert returncode != 0 or "已存在" in stdout or "already exists" in stdout.lower(), \
        "应该检测到重复名称"

    print(f"{Colors.GREEN}✓ 重复名称检测成功{Colors.END}")


def test_scheduler_list(db_session):
    """测试任务列表"""
    print(f"\n{Colors.BLUE}测试: 任务列表{Colors.END}")
    print("-" * 60)

    # 创建多个测试任务
    tasks = []
    for i in range(3):
        unique_name = generate_unique_name()
        task = ScheduledTask(
            name=unique_name,
            description=f"测试任务 {i+1}",
            task_type="content_generation" if i % 2 == 0 else "publishing",
            cron_expression="0 * * * *",
            is_active=(i % 2 == 0)
        )
        db_session.add(task)
        tasks.append(task)
    db_session.commit()

    # 测试列出所有任务
    args = [
        "scheduler", "list",
        "--page", "1",
        "--page-size", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 任务列表查询成功{Colors.END}")

    # 测试按状态筛选
    args = [
        "scheduler", "list",
        "--status", "active",
        "--page", "1",
        "--page-size", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 按状态筛选成功{Colors.END}")

    # 测试按类型筛选
    args = [
        "scheduler", "list",
        "--type", "content_generation",
        "--page", "1",
        "--page-size", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 按类型筛选成功{Colors.END}")

    # 清理
    for task in tasks:
        db_session.query(TaskExecution).filter(TaskExecution.task_id == task.id).delete()
        db_session.delete(task)
    db_session.commit()


def test_scheduler_info(test_task):
    """测试任务详情"""
    print(f"\n{Colors.BLUE}测试: 任务详情{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "info",
        str(test_task.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert test_task.name in stdout or "详情" in stdout, f"未找到任务名称: {stdout}"
    print(f"{Colors.GREEN}✓ 任务详情查看成功 (ID: {test_task.id}){Colors.END}")


def test_scheduler_info_nonexistent():
    """测试查看不存在的任务详情"""
    print(f"\n{Colors.BLUE}测试: 查看不存在的任务详情{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "info",
        "99999"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:200]}")

    # 应该返回错误
    assert returncode != 0 or "不存在" in stdout or "not found" in stdout.lower(), \
        "应该检测到任务不存在"

    print(f"{Colors.GREEN}✓ 不存在任务检测成功{Colors.END}")


def test_scheduler_update(test_task):
    """测试更新任务"""
    print(f"\n{Colors.BLUE}测试: 更新任务{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "update",
        str(test_task.id),
        "--cron", "0 8 * * *",
        "--disabled"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("成功" in stdout or "updated" in stdout.lower()), f"未找到成功提示: {stdout}"

    # 验证更新
    from app.db.sql_db import get_session_local
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        db.refresh(test_task)
        assert test_task.cron_expression == "0 8 * * *", "Cron表达式未更新"
        assert test_task.is_active == False, "启用状态未更新"
        print(f"{Colors.GREEN}✓ 任务更新成功 (ID: {test_task.id}){Colors.END}")
    finally:
        db.close()


def test_scheduler_update_name(db_session, test_task):
    """测试更新任务名称"""
    print(f"\n{Colors.BLUE}测试: 更新任务名称{Colors.END}")
    print("-" * 60)

    new_name = generate_unique_name()

    args = [
        "scheduler", "update",
        str(test_task.id),
        "--name", new_name
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"

    # 验证更新
    db_session.refresh(test_task)
    assert test_task.name == new_name, "任务名称未更新"
    print(f"{Colors.GREEN}✓ 任务名称更新成功 (ID: {test_task.id}){Colors.END}")


def test_scheduler_delete(db_session):
    """测试删除任务"""
    print(f"\n{Colors.BLUE}测试: 删除任务{Colors.END}")
    print("-" * 60)

    # 创建测试任务
    unique_name = generate_unique_name()
    task = ScheduledTask(
        name=unique_name,
        description="待删除任务",
        task_type="content_generation",
        cron_expression="0 * * * *"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    task_id = task.id

    # 使用环境变量跳过确认
    env = os.environ.copy()
    env['CONFIRM_DELETE'] = '1'

    cmd = [sys.executable, "-m", "cli.main", "scheduler", "delete", str(task_id)]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env=env,
        input="y\n"  # 提供确认输入
    )

    print(f"返回码: {result.returncode}")
    print(f"输出: {result.stdout[:200]}")

    # 验证任务已被删除
    deleted_task = db_session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    assert deleted_task is None, "任务未被删除"

    print(f"{Colors.GREEN}✓ 任务删除成功 (ID: {task_id}){Colors.END}")


def test_scheduler_trigger(test_task):
    """测试手动触发任务"""
    print(f"\n{Colors.BLUE}测试: 手动触发任务{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "trigger",
        str(test_task.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:300]}")

    # 验证命令执行成功
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("成功" in stdout or "success" in stdout.lower()), f"未找到成功提示: {stdout}"

    print(f"{Colors.GREEN}✓ 任务手动触发成功 (ID: {test_task.id}){Colors.END}")


def test_scheduler_trigger_nonexistent():
    """测试触发不存在的任务"""
    print(f"\n{Colors.BLUE}测试: 触发不存在的任务{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "trigger",
        "99999"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:200]}")

    # 应该返回错误
    assert returncode != 0 or "不存在" in stdout or "not found" in stdout.lower(), \
        "应该检测到任务不存在"

    print(f"{Colors.GREEN}✓ 不存在任务检测成功{Colors.END}")


def test_scheduler_history(db_session, test_task):
    """测试执行历史"""
    print(f"\n{Colors.BLUE}测试: 执行历史{Colors.END}")
    print("-" * 60)

    # 创建一些执行记录
    executions = []
    for i in range(3):
        execution = TaskExecution(
            task_id=test_task.id,
            status="success" if i % 2 == 0 else "failed",
            duration=10 + i,
            error_message=None if i % 2 == 0 else f"测试错误 {i}"
        )
        db_session.add(execution)
        executions.append(execution)
    db_session.commit()

    # 测试查看所有历史
    args = [
        "scheduler", "history",
        "--limit", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 执行历史查询成功{Colors.END}")

    # 测试按任务ID筛选
    args = [
        "scheduler", "history",
        "--task-id", str(test_task.id),
        "--limit", "10"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 按任务ID筛选历史成功{Colors.END}")


def test_scheduler_start():
    """测试启动调度器"""
    print(f"\n{Colors.BLUE}测试: 启动调度器{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "start"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:300]}")

    # 验证命令执行成功
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("启动" in stdout or "started" in stdout.lower()), f"未找到启动提示: {stdout}"

    print(f"{Colors.GREEN}✓ 调度器启动成功{Colors.END}")


def test_scheduler_stop():
    """测试停止调度器"""
    print(f"\n{Colors.BLUE}测试: 停止调度器{Colors.END}")
    print("-" * 60)

    # 先启动调度器
    start_args = ["scheduler", "start"]
    run_cli_command(start_args)

    # 等待一秒
    time.sleep(1)

    # 停止调度器
    args = [
        "scheduler", "stop"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    print(f"返回码: {returncode}")
    print(f"输出: {stdout[:300]}")

    # 验证命令执行成功
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("停止" in stdout or "stopped" in stdout.lower()), f"未找到停止提示: {stdout}"

    print(f"{Colors.GREEN}✓ 调度器停止成功{Colors.END}")


def test_scheduler_status():
    """测试调度器状态"""
    print(f"\n{Colors.BLUE}测试: 调度器状态{Colors.END}")
    print("-" * 60)

    args = [
        "scheduler", "status"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("状态" in stdout or "status" in stdout.lower()), f"未找到状态信息: {stdout}"

    print(f"{Colors.GREEN}✓ 调度器状态查询成功{Colors.END}")


def test_scheduler_pause(test_task):
    """测试暂停任务"""
    print(f"\n{Colors.BLUE}测试: 暂停任务{Colors.END}")
    print("-" * 60)

    # 确保任务处于启用状态
    from app.db.sql_db import get_session_local
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        test_task.is_active = True
        db.commit()
    finally:
        db.close()

    args = [
        "scheduler", "pause",
        str(test_task.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("暂停" in stdout or "paused" in stdout.lower() or "成功" in stdout), \
        f"未找到暂停提示: {stdout}"

    # 验证状态
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        db.refresh(test_task)
        assert test_task.is_active == False, "任务未被暂停"
        print(f"{Colors.GREEN}✓ 任务暂停成功 (ID: {test_task.id}){Colors.END}")
    finally:
        db.close()


def test_scheduler_resume(test_task):
    """测试恢复任务"""
    print(f"\n{Colors.BLUE}测试: 恢复任务{Colors.END}")
    print("-" * 60)

    # 确保任务处于暂停状态
    from app.db.sql_db import get_session_local
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        test_task.is_active = False
        db.commit()
    finally:
        db.close()

    args = [
        "scheduler", "resume",
        str(test_task.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert ("恢复" in stdout or "resumed" in stdout.lower() or "成功" in stdout), \
        f"未找到恢复提示: {stdout}"

    # 验证状态
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        db.refresh(test_task)
        assert test_task.is_active == True, "任务未被恢复"
        print(f"{Colors.GREEN}✓ 任务恢复成功 (ID: {test_task.id}){Colors.END}")
    finally:
        db.close()


def test_scheduler_pause_already_paused(test_task):
    """测试暂停已暂停的任务"""
    print(f"\n{Colors.BLUE}测试: 暂停已暂停的任务{Colors.END}")
    print("-" * 60)

    # 确保任务处于暂停状态
    from app.db.sql_db import get_session_local
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        test_task.is_active = False
        db.commit()
    finally:
        db.close()

    args = [
        "scheduler", "pause",
        str(test_task.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 暂停已暂停任务检测成功{Colors.END}")


def test_scheduler_resume_already_active(test_task):
    """测试恢复已启用的任务"""
    print(f"\n{Colors.BLUE}测试: 恢复已启用的任务{Colors.END}")
    print("-" * 60)

    # 确保任务处于启用状态
    from app.db.sql_db import get_session_local
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        test_task.is_active = True
        db.commit()
    finally:
        db.close()

    args = [
        "scheduler", "resume",
        str(test_task.id)
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    print(f"{Colors.GREEN}✓ 恢复已启用任务检测成功{Colors.END}")


def test_scheduler_lifecycle(db_session):
    """测试完整任务生命周期"""
    print(f"\n{Colors.BLUE}测试: 完整任务生命周期{Colors.END}")
    print("-" * 60)

    unique_name = generate_unique_name()

    # 1. 创建任务
    print(f"\n步骤 1: 创建任务")
    args = [
        "scheduler", "create",
        "--name", unique_name,
        "--type", "content_generation",
        "--cron", "0 9 * * *",
        "--description", "生命周期测试任务"
    ]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0

    task = db_session.query(ScheduledTask).filter(ScheduledTask.name == unique_name).first()
    assert task is not None
    task_id = task.id
    print(f"{Colors.GREEN}✓ 任务创建成功 (ID: {task_id}){Colors.END}")

    # 2. 查看详情
    print(f"\n步骤 2: 查看详情")
    args = ["scheduler", "info", str(task_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 查看详情成功{Colors.END}")

    # 3. 更新任务
    print(f"\n步骤 3: 更新任务")
    args = ["scheduler", "update", str(task_id), "--cron", "0 8 * * *"]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 更新任务成功{Colors.END}")

    # 4. 暂停任务
    print(f"\n步骤 4: 暂停任务")
    args = ["scheduler", "pause", str(task_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 暂停任务成功{Colors.END}")

    # 5. 恢复任务
    print(f"\n步骤 5: 恢复任务")
    args = ["scheduler", "resume", str(task_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 恢复任务成功{Colors.END}")

    # 6. 手动触发
    print(f"\n步骤 6: 手动触发")
    args = ["scheduler", "trigger", str(task_id)]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 手动触发成功{Colors.END}")

    # 7. 删除任务
    print(f"\n步骤 7: 删除任务")
    cmd = [sys.executable, "-m", "cli.main", "scheduler", "delete", str(task_id)]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        input="y\n"
    )
    print(f"{Colors.GREEN}✓ 删除任务成功{Colors.END}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 完整生命周期测试通过{Colors.END}")


def test_scheduler_multiple_tasks_with_filters(db_session):
    """测试多任务筛选"""
    print(f"\n{Colors.BLUE}测试: 多任务筛选{Colors.END}")
    print("-" * 60)

    # 创建不同类型的任务
    tasks = []
    for i in range(5):
        unique_name = generate_unique_name()
        task = ScheduledTask(
            name=unique_name,
            description=f"测试任务 {i+1}",
            task_type="content_generation" if i < 3 else "publishing",
            cron_expression=f"{i} * * * *",
            is_active=(i % 2 == 0)
        )
        db_session.add(task)
        tasks.append(task)
    db_session.commit()

    # 测试按状态筛选
    args = ["scheduler", "list", "--status", "active"]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 按启用状态筛选成功{Colors.END}")

    # 测试按类型筛选
    args = ["scheduler", "list", "--type", "content_generation"]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 按任务类型筛选成功{Colors.END}")

    # 测试分页
    args = ["scheduler", "list", "--page", "1", "--page-size", "3"]
    returncode, stdout, stderr = run_cli_command(args)
    assert returncode == 0
    print(f"{Colors.GREEN}✓ 分页查询成功{Colors.END}")

    # 清理
    for task in tasks:
        db_session.query(TaskExecution).filter(TaskExecution.task_id == task.id).delete()
        db_session.delete(task)
    db_session.commit()


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
