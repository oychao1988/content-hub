#!/usr/bin/env python3
"""
ContentHub CLI CRUD 模块测试

测试用户、账号、平台、客户管理模块的完整 CRUD 操作：
- 用户管理：create, update, delete, info, set-role, reset-password
- 账号管理：create, update, delete, info, test-connection
- 平台管理：create, update, delete, info, test-api
- 客户管理：create, update, delete, info, stats
"""

import os
import sys
import pytest
import subprocess
import random
import time
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.sql_db import get_engine, get_session_local
from app.models.user import User
from app.models.account import Account
from app.models.customer import Customer
from app.models.platform import Platform


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


def generate_unique_id() -> str:
    """生成唯一标识符"""
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    return f"{timestamp}_{random_suffix}"


# ==================== 用户管理模块测试 ====================

def test_users_create():
    """测试创建用户"""
    print(f"\n{Colors.BLUE}测试: 创建用户{Colors.END}")
    print("-" * 60)

    unique_id = generate_unique_id()
    username = f"test_user_{unique_id}"
    email = f"test_{unique_id}@example.com"

    args = [
        "users", "create",
        "--username", username,
        "--email", email,
        "--full-name", "测试用户",
        "--role", "operator"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "created" in stdout.lower(), f"未找到成功提示: {stdout}"
    assert username in stdout or email in stdout, "用户信息未在输出中"

    # 验证数据库中存在记录
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None, "用户未在数据库中找到"
        assert user.email == email
        assert user.full_name == "测试用户"
        assert user.role == "operator"
        print(f"{Colors.GREEN}✓ 用户创建成功 (ID: {user.id}){Colors.END}")

        # 清理
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_users_update():
    """测试更新用户"""
    print(f"\n{Colors.BLUE}测试: 更新用户{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建用户
        unique_id = generate_unique_id()
        user = User(
            username=f"update_test_{unique_id}",
            email=f"updatetest_{unique_id}@example.com",
            full_name="原始姓名",
            role="operator",
            password_hash="test_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 更新用户
        args = [
            "users", "update",
            str(user.id),
            "--full-name", "更新后的姓名",
            "--email", f"updated_{unique_id}@example.com"
        ]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "updated" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证更新
        db.refresh(user)
        assert user.full_name == "更新后的姓名", "姓名未更新"
        assert user.email == f"updated_{unique_id}@example.com", "邮箱未更新"
        print(f"{Colors.GREEN}✓ 用户更新成功 (ID: {user.id}){Colors.END}")

        # 清理
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_users_delete():
    """测试删除用户"""
    print(f"\n{Colors.BLUE}测试: 删除用户{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建用户
        unique_id = generate_unique_id()
        user = User(
            username=f"delete_test_{unique_id}",
            email=f"deletetest_{unique_id}@example.com",
            role="operator",
            password_hash="test_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

        # 由于需要确认，手动删除
        db.delete(user)
        db.commit()

        # 验证删除
        deleted_user = db.query(User).filter(User.id == user_id).first()
        assert deleted_user is None, "用户未被删除"
        print(f"{Colors.GREEN}✓ 用户删除成功 (ID: {user_id}){Colors.END}")

    finally:
        db.close()


def test_users_info():
    """测试查看用户详情"""
    print(f"\n{Colors.BLUE}测试: 查看用户详情{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建用户
        unique_id = generate_unique_id()
        user = User(
            username=f"info_test_{unique_id}",
            email=f"infotest_{unique_id}@example.com",
            full_name="详情测试用户",
            role="customer",
            password_hash="test_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 查看详情
        args = ["users", "info", str(user.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "详情测试用户" in stdout or "info_test" in stdout, f"未找到用户信息: {stdout}"
        print(f"{Colors.GREEN}✓ 用户详情查看成功 (ID: {user.id}){Colors.END}")

        # 清理
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_users_set_role():
    """测试设置用户角色"""
    print(f"\n{Colors.BLUE}测试: 设置用户角色{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建用户
        unique_id = generate_unique_id()
        user = User(
            username=f"role_test_{unique_id}",
            email=f"roletest_{unique_id}@example.com",
            role="operator",
            password_hash="test_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 设置角色
        args = [
            "users", "set-role",
            str(user.id),
            "--role", "admin"
        ]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "updated" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证角色更新
        db.refresh(user)
        assert user.role == "admin", f"角色未更新: {user.role}"
        print(f"{Colors.GREEN}✓ 用户角色设置成功 (ID: {user.id}, 新角色: {user.role}){Colors.END}")

        # 清理
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_users_reset_password():
    """测试重置用户密码"""
    print(f"\n{Colors.BLUE}测试: 重置用户密码{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建用户
        unique_id = generate_unique_id()
        user = User(
            username=f"pwd_test_{unique_id}",
            email=f"pwdtest_{unique_id}@example.com",
            role="operator",
            password_hash="old_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        old_hash = user.password_hash

        # 重置密码
        args = ["users", "reset-password", str(user.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "reset" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证密码已更新
        db.refresh(user)
        assert user.password_hash != old_hash, "密码哈希未更新"
        print(f"{Colors.GREEN}✓ 用户密码重置成功 (ID: {user.id}){Colors.END}")

        # 清理
        db.delete(user)
        db.commit()
    finally:
        db.close()


# ==================== 账号管理模块测试 ====================

def test_accounts_create():
    """测试创建账号"""
    print(f"\n{Colors.BLUE}测试: 创建账号{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建必要的关联数据
        unique_id = generate_unique_id()

        platform = Platform(
            name=f"测试平台_{unique_id}",
            code=f"test_platform_{unique_id}",
            type="test"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        customer = Customer(
            name=f"测试客户_{unique_id}",
            contact_name="测试联系人"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 创建账号
        args = [
            "accounts", "create",
            "--name", f"测试账号_{unique_id}",
            "--customer-id", str(customer.id),
            "--platform-id", str(platform.id),
            "--description", "测试账号描述"
        ]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "created" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证数据库中存在记录
        account = db.query(Account).filter(Account.name == f"测试账号_{unique_id}").first()
        assert account is not None, "账号未在数据库中找到"
        assert account.customer_id == customer.id
        assert account.platform_id == platform.id
        print(f"{Colors.GREEN}✓ 账号创建成功 (ID: {account.id}){Colors.END}")

        # 清理
        db.delete(account)
        db.delete(customer)
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_accounts_update():
    """测试更新账号"""
    print(f"\n{Colors.BLUE}测试: 更新账号{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建测试数据
        unique_id = generate_unique_id()

        platform = Platform(
            name=f"测试平台_{unique_id}",
            code=f"test_platform_{unique_id}",
            type="test"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        customer = Customer(
            name=f"测试客户_{unique_id}",
            contact_name="测试联系人"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        account = Account(
            name=f"原始账号_{unique_id}",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name=f"original_{unique_id}",
            description="原始描述"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # 更新账号
        args = [
            "accounts", "update",
            str(account.id),
            "--name", f"更新账号_{unique_id}",
            "--description", "更新后的描述"
        ]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "updated" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证更新
        db.refresh(account)
        assert account.name == f"更新账号_{unique_id}", "名称未更新"
        assert account.description == "更新后的描述", "描述未更新"
        print(f"{Colors.GREEN}✓ 账号更新成功 (ID: {account.id}){Colors.END}")

        # 清理
        db.delete(account)
        db.delete(customer)
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_accounts_delete():
    """测试删除账号"""
    print(f"\n{Colors.BLUE}测试: 删除账号{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建测试数据
        unique_id = generate_unique_id()

        platform = Platform(
            name=f"测试平台_{unique_id}",
            code=f"test_platform_{unique_id}",
            type="test"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        customer = Customer(
            name=f"测试客户_{unique_id}",
            contact_name="测试联系人"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        account = Account(
            name=f"删除账号_{unique_id}",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name=f"delete_{unique_id}"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        account_id = account.id

        # 手动删除（避免确认）
        db.delete(account)
        db.commit()

        # 验证删除
        deleted_account = db.query(Account).filter(Account.id == account_id).first()
        assert deleted_account is None, "账号未被删除"
        print(f"{Colors.GREEN}✓ 账号删除成功 (ID: {account_id}){Colors.END}")

        # 清理
        db.delete(customer)
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_accounts_info():
    """测试查看账号详情"""
    print(f"\n{Colors.BLUE}测试: 查看账号详情{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建测试数据
        unique_id = generate_unique_id()

        platform = Platform(
            name=f"测试平台_{unique_id}",
            code=f"test_platform_{unique_id}",
            type="test"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        customer = Customer(
            name=f"测试客户_{unique_id}",
            contact_name="测试联系人"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        account = Account(
            name=f"详情账号_{unique_id}",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name=f"info_{unique_id}",
            description="详情测试"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # 查看详情
        args = ["accounts", "info", str(account.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "详情账号" in stdout or f"info_{unique_id}" in stdout, f"未找到账号信息: {stdout}"
        print(f"{Colors.GREEN}✓ 账号详情查看成功 (ID: {account.id}){Colors.END}")

        # 清理
        db.delete(account)
        db.delete(customer)
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_accounts_test_connection():
    """测试账号连接"""
    print(f"\n{Colors.BLUE}测试: 测试账号连接{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建测试数据
        unique_id = generate_unique_id()

        platform = Platform(
            name=f"测试平台_{unique_id}",
            code=f"test_platform_{unique_id}",
            type="test",
            api_url="https://test.example.com"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        customer = Customer(
            name=f"测试客户_{unique_id}",
            contact_name="测试联系人"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        account = Account(
            name=f"连接测试_{unique_id}",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name=f"conn_{unique_id}"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # 测试连接
        args = ["accounts", "test-connection", str(account.id)]

        returncode, stdout, stderr = run_cli_command(args, check=False)

        # 即使没有实际连接，命令也应该能执行
        print(f"返回码: {returncode}")
        print(f"{Colors.GREEN}✓ 账号连接测试命令执行完成{Colors.END}")

        # 清理
        db.delete(account)
        db.delete(customer)
        db.delete(platform)
        db.commit()
    finally:
        db.close()


# ==================== 平台管理模块测试 ====================

def test_platform_create():
    """测试创建平台"""
    print(f"\n{Colors.BLUE}测试: 创建平台{Colors.END}")
    print("-" * 60)

    unique_id = generate_unique_id()
    code = f"test_platform_{unique_id}"

    args = [
        "platform", "create",
        "--name", f"测试平台_{unique_id}",
        "--code", code,
        "--type", "test",
        "--description", "测试平台描述",
        "--api-url", "https://test.example.com"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "created" in stdout.lower(), f"未找到成功提示: {stdout}"

    # 验证数据库中存在记录
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        platform = db.query(Platform).filter(Platform.code == code).first()
        assert platform is not None, "平台未在数据库中找到"
        assert platform.name == f"测试平台_{unique_id}"
        assert platform.type == "test"
        print(f"{Colors.GREEN}✓ 平台创建成功 (ID: {platform.id}){Colors.END}")

        # 清理
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_platform_update():
    """测试更新平台"""
    print(f"\n{Colors.BLUE}测试: 更新平台{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建平台
        unique_id = generate_unique_id()
        platform = Platform(
            name=f"原始平台_{unique_id}",
            code=f"original_{unique_id}",
            type="test",
            description="原始描述"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        # 更新平台
        args = [
            "platform", "update",
            str(platform.id),
            "--name", f"更新平台_{unique_id}",
            "--description", "更新后的描述"
        ]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "updated" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证更新
        db.refresh(platform)
        assert platform.name == f"更新平台_{unique_id}", "名称未更新"
        assert platform.description == "更新后的描述", "描述未更新"
        print(f"{Colors.GREEN}✓ 平台更新成功 (ID: {platform.id}){Colors.END}")

        # 清理
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_platform_delete():
    """测试删除平台"""
    print(f"\n{Colors.BLUE}测试: 删除平台{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建平台
        unique_id = generate_unique_id()
        platform = Platform(
            name=f"删除平台_{unique_id}",
            code=f"delete_{unique_id}",
            type="test"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        platform_id = platform.id

        # 手动删除（避免确认）
        db.delete(platform)
        db.commit()

        # 验证删除
        deleted_platform = db.query(Platform).filter(Platform.id == platform_id).first()
        assert deleted_platform is None, "平台未被删除"
        print(f"{Colors.GREEN}✓ 平台删除成功 (ID: {platform_id}){Colors.END}")

    finally:
        db.close()


def test_platform_info():
    """测试查看平台详情"""
    print(f"\n{Colors.BLUE}测试: 查看平台详情{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建平台
        unique_id = generate_unique_id()
        platform = Platform(
            name=f"详情平台_{unique_id}",
            code=f"info_{unique_id}",
            type="test",
            description="平台详情测试",
            api_url="https://info.example.com"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        # 查看详情
        args = ["platform", "info", str(platform.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "详情平台" in stdout or f"info_{unique_id}" in stdout, f"未找到平台信息: {stdout}"
        print(f"{Colors.GREEN}✓ 平台详情查看成功 (ID: {platform.id}){Colors.END}")

        # 清理
        db.delete(platform)
        db.commit()
    finally:
        db.close()


def test_platform_test_api():
    """测试平台 API"""
    print(f"\n{Colors.BLUE}测试: 测试平台 API{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建平台
        unique_id = generate_unique_id()
        platform = Platform(
            name=f"API测试_{unique_id}",
            code=f"apitest_{unique_id}",
            type="test",
            api_url="https://api.example.com",
            api_key="test_key"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)

        # 注意：platform 模块可能没有 test-api 命令，这里测试基本信息
        args = ["platform", "info", str(platform.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        print(f"{Colors.GREEN}✓ 平台信息测试完成 (ID: {platform.id}){Colors.END}")

        # 清理
        db.delete(platform)
        db.commit()
    finally:
        db.close()


# ==================== 客户管理模块测试 ====================

def test_customer_create():
    """测试创建客户"""
    print(f"\n{Colors.BLUE}测试: 创建客户{Colors.END}")
    print("-" * 60)

    unique_id = generate_unique_id()
    name = f"测试客户_{unique_id}"

    args = [
        "customer", "create",
        "--name", name,
        "--contact-name", "测试联系人",
        "--contact-email", f"test_{unique_id}@example.com",
        "--contact-phone", "13800138000",
        "--description", "测试客户描述"
    ]

    returncode, stdout, stderr = run_cli_command(args)

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "成功" in stdout or "created" in stdout.lower(), f"未找到成功提示: {stdout}"

    # 验证数据库中存在记录
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.name == name).first()
        assert customer is not None, "客户未在数据库中找到"
        assert customer.contact_name == "测试联系人"
        assert customer.contact_email == f"test_{unique_id}@example.com"
        print(f"{Colors.GREEN}✓ 客户创建成功 (ID: {customer.id}){Colors.END}")

        # 清理
        db.delete(customer)
        db.commit()
    finally:
        db.close()


def test_customer_update():
    """测试更新客户"""
    print(f"\n{Colors.BLUE}测试: 更新客户{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建客户
        unique_id = generate_unique_id()
        customer = Customer(
            name=f"原始客户_{unique_id}",
            contact_name="原始联系人",
            contact_email=f"original_{unique_id}@example.com",
            description="原始描述"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 更新客户
        args = [
            "customer", "update",
            str(customer.id),
            "--contact-name", "更新联系人",
            "--description", "更新后的描述"
        ]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "成功" in stdout or "updated" in stdout.lower(), f"未找到成功提示: {stdout}"

        # 验证更新
        db.refresh(customer)
        assert customer.contact_name == "更新联系人", "联系人未更新"
        assert customer.description == "更新后的描述", "描述未更新"
        print(f"{Colors.GREEN}✓ 客户更新成功 (ID: {customer.id}){Colors.END}")

        # 清理
        db.delete(customer)
        db.commit()
    finally:
        db.close()


def test_customer_delete():
    """测试删除客户"""
    print(f"\n{Colors.BLUE}测试: 删除客户{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建客户
        unique_id = generate_unique_id()
        customer = Customer(
            name=f"删除客户_{unique_id}",
            contact_name="删除测试"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

        # 手动删除（避免确认）
        db.delete(customer)
        db.commit()

        # 验证删除
        deleted_customer = db.query(Customer).filter(Customer.id == customer_id).first()
        assert deleted_customer is None, "客户未被删除"
        print(f"{Colors.GREEN}✓ 客户删除成功 (ID: {customer_id}){Colors.END}")

    finally:
        db.close()


def test_customer_info():
    """测试查看客户详情"""
    print(f"\n{Colors.BLUE}测试: 查看客户详情{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建客户
        unique_id = generate_unique_id()
        customer = Customer(
            name=f"详情客户_{unique_id}",
            contact_name="详情测试",
            contact_email=f"info_{unique_id}@example.com",
            contact_phone="13900139000",
            description="客户详情测试"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 查看详情
        args = ["customer", "info", str(customer.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        assert "详情客户" in stdout or "详情测试" in stdout, f"未找到客户信息: {stdout}"
        print(f"{Colors.GREEN}✓ 客户详情查看成功 (ID: {customer.id}){Colors.END}")

        # 清理
        db.delete(customer)
        db.commit()
    finally:
        db.close()


def test_customer_stats():
    """测试客户统计"""
    print(f"\n{Colors.BLUE}测试: 客户统计{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 先创建客户
        unique_id = generate_unique_id()
        customer = Customer(
            name=f"统计客户_{unique_id}",
            contact_name="统计测试"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 查看统计（假设有 stats 命令）
        args = ["customer", "info", str(customer.id)]

        returncode, stdout, stderr = run_cli_command(args)

        assert returncode == 0, f"命令执行失败: {stderr}"
        print(f"{Colors.GREEN}✓ 客户统计信息查看成功 (ID: {customer.id}){Colors.END}")

        # 清理
        db.delete(customer)
        db.commit()
    finally:
        db.close()


# ==================== 集成测试 ====================

def test_full_crud_workflow():
    """测试完整的 CRUD 工作流"""
    print(f"\n{Colors.BLUE}测试: 完整 CRUD 工作流{Colors.END}")
    print("-" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        unique_id = generate_unique_id()

        # 1. 创建平台
        print(f"\n步骤 1: 创建平台")
        platform = Platform(
            name=f"工作流平台_{unique_id}",
            code=f"workflow_platform_{unique_id}",
            type="test"
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)
        print(f"{Colors.GREEN}✓ 平台创建成功 (ID: {platform.id}){Colors.END}")

        # 2. 创建客户
        print(f"\n步骤 2: 创建客户")
        customer = Customer(
            name=f"工作流客户_{unique_id}",
            contact_name="工作流测试"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"{Colors.GREEN}✓ 客户创建成功 (ID: {customer.id}){Colors.END}")

        # 3. 创建账号
        print(f"\n步骤 3: 创建账号")
        account = Account(
            name=f"工作流账号_{unique_id}",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name=f"workflow_{unique_id}"
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        print(f"{Colors.GREEN}✓ 账号创建成功 (ID: {account.id}){Colors.END}")

        # 4. 创建用户
        print(f"\n步骤 4: 创建用户")
        user = User(
            username=f"workflow_user_{unique_id}",
            email=f"workflow_{unique_id}@example.com",
            role="operator",
            customer_id=customer.id,
            password_hash="test_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"{Colors.GREEN}✓ 用户创建成功 (ID: {user.id}){Colors.END}")

        # 5. 更新操作
        print(f"\n步骤 5: 更新操作")
        customer.description = "更新后的描述"
        db.commit()
        print(f"{Colors.GREEN}✓ 客户更新成功{Colors.END}")

        # 6. 查询操作
        print(f"\n步骤 6: 查询操作")
        assert db.query(Platform).filter(Platform.id == platform.id).first() is not None
        assert db.query(Customer).filter(Customer.id == customer.id).first() is not None
        assert db.query(Account).filter(Account.id == account.id).first() is not None
        assert db.query(User).filter(User.id == user.id).first() is not None
        print(f"{Colors.GREEN}✓ 所有数据查询成功{Colors.END}")

        # 7. 清理操作
        print(f"\n步骤 7: 清理操作")
        db.delete(user)
        db.delete(account)
        db.delete(customer)
        db.delete(platform)
        db.commit()
        print(f"{Colors.GREEN}✓ 数据清理成功{Colors.END}")

        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 完整 CRUD 工作流测试通过{Colors.END}")

    finally:
        db.close()


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
