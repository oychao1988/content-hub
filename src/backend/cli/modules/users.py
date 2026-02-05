"""
用户管理模块

提供用户 CRUD、角色管理、密码管理等功能。
"""

import secrets
import string
from typing import Optional

import typer
from rich.table import Table
from sqlalchemy.orm import Session

from cli.utils import (
    print_info,
    print_success,
    print_warning,
    print_error,
    print_table,
    confirm_action,
    format_datetime,
    format_bool,
    handle_error,
    get_global_format,
)
from app.db.sql_db import get_session_local
from app.models.user import User
from app.modules.shared.schemas.user import UserCreate
from app.core.security import create_salt, get_password_hash

# 创建子应用
app = typer.Typer(help="用户管理")


def generate_password(length: int = 12) -> str:
    """生成随机密码

    Args:
        length: 密码长度

    Returns:
        随机密码
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def get_user(db: Session, user_id: int) -> Optional[User]:
    """获取用户

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        用户对象或 None
    """
    return db.query(User).filter(User.id == user_id).first()


def list_users_db(
    db: Session,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> list[User]:
    """查询用户列表

    Args:
        db: 数据库会话
        role: 角色筛选
        is_active: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        用户列表
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.offset(skip).limit(limit).all()


def create_user_db(db: Session, username: str, email: str, full_name: Optional[str],
                   role: str, password: str) -> User:
    """创建用户

    Args:
        db: 数据库会话
        username: 用户名
        email: 邮箱
        full_name: 全名
        role: 角色
        password: 密码

    Returns:
        创建的用户对象
    """
    # 生成密码哈希
    salt = create_salt()
    password_hash = get_password_hash(password, salt)

    # 创建用户
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_db(db: Session, user: User, **kwargs) -> User:
    """更新用户

    Args:
        db: 数据库会话
        user: 用户对象
        **kwargs: 更新字段

    Returns:
        更新后的用户对象
    """
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user_db(db: Session, user: User) -> None:
    """删除用户

    Args:
        db: 数据库会话
        user: 用户对象
    """
    db.delete(user)
    db.commit()


def change_password_db(db: Session, user: User, new_password: str) -> None:
    """修改密码

    Args:
        db: 数据库会话
        user: 用户对象
        new_password: 新密码
    """
    salt = create_salt()
    user.password_hash = get_password_hash(new_password, salt)
    db.commit()


def format_user_info(user: User, include_password: bool = False, password: Optional[str] = None) -> dict:
    """格式化用户信息

    Args:
        user: 用户对象
        include_password: 是否包含密码
        password: 明文密码（仅在创建时显示）

    Returns:
        格式化的用户信息字典
    """
    info = {
        "ID": user.id,
        "用户名": user.username,
        "邮箱": user.email,
        "全名": user.full_name or "-",
        "角色": user.role,
        "状态": "激活" if user.is_active else "停用",
        "创建时间": format_datetime(user.created_at),
        "更新时间": format_datetime(user.updated_at),
    }

    if include_password and password:
        info["密码"] = password

    return info


@app.command("list")
def list_users(
    ctx: typer.Context,
    role: str = typer.Option(None, "--role", "-r", help="按角色筛选 (admin/operator/customer)"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (active/inactive)"),
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    page_size: int = typer.Option(20, "--page-size", "--size", help="每页数量")
):
    """列出用户"""
    try:
        with get_session_local()() as db:
            # 解析状态参数
            is_active = None
            if status:
                if status.lower() == "active":
                    is_active = True
                elif status.lower() == "inactive":
                    is_active = False
                else:
                    print_error(f"无效的状态值: {status}，请使用 active 或 inactive")
                    raise typer.Exit(1)

            # 计算分页
            skip = (page - 1) * page_size

            # 查询用户
            users = list_users_db(db, role=role, is_active=is_active, skip=skip, limit=page_size)

            # 格式化输出
            data = []
            for user in users:
                data.append({
                    "ID": user.id,
                    "用户名": user.username,
                    "邮箱": user.email,
                    "全名": user.full_name or "-",
                    "角色": user.role,
                    "状态": "激活" if user.is_active else "停用",
                    "创建时间": format_datetime(user.created_at),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not users:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到用户")
                return

            print_table(data, title=f"用户列表 (第 {page} 页，共 {len(users)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command()
def create(
    username: str = typer.Option(..., "--username", "-u", help="用户名"),
    email: str = typer.Option(..., "--email", "-e", help="邮箱"),
    full_name: str = typer.Option(None, "--full-name", "-n", help="全名"),
    role: str = typer.Option("operator", "--role", "-r", help="角色 (admin/operator/customer)"),
    password: str = typer.Option(None, "--password", "-p", help="密码（可选，自动生成）")
):
    """创建用户"""
    try:
        with get_session_local()() as db:
            # 检查邮箱是否已存在
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print_error(f"邮箱已被使用: {email}")
                raise typer.Exit(1)

            # 检查用户名是否已存在
            existing_username = db.query(User).filter(User.username == username).first()
            if existing_username:
                print_error(f"用户名已被使用: {username}")
                raise typer.Exit(1)

            # 如果未提供密码，生成随机密码
            if not password:
                password = generate_password()
                print_info(f"已生成随机密码: {password}")

            # 创建用户
            print_info("正在创建用户...")
            user = create_user_db(
                db=db,
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                password=password
            )

            # 显示用户信息
            print_success(f"用户创建成功 (ID: {user.id})")

            # 显示详细信息（包含密码）
            user_info = format_user_info(user, include_password=True, password=password)
            info_table = Table(title="用户详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in user_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

            # 重要提示
            if full_name or password:
                print_warning("请妥善保管用户信息，尤其是密码！")

    except Exception as e:
        handle_error(e)


@app.command()
def update(
    user_id: int = typer.Argument(..., help="用户 ID"),
    email: str = typer.Option(None, "--email", "-e", help="邮箱"),
    full_name: str = typer.Option(None, "--full-name", "-n", help="全名"),
    role: str = typer.Option(None, "--role", "-r", help="角色 (admin/operator/customer)")
):
    """更新用户信息"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            # 检查邮箱是否已被其他用户使用
            if email and email != user.email:
                existing_user = db.query(User).filter(User.email == email).first()
                if existing_user:
                    print_error(f"邮箱已被使用: {email}")
                    raise typer.Exit(1)

            # 更新用户
            print_info(f"正在更新用户信息 (ID: {user_id})...")
            update_data = {}
            if email:
                update_data["email"] = email
            if full_name:
                update_data["full_name"] = full_name
            if role:
                update_data["role"] = role

            user = update_user_db(db, user, **update_data)

            # 显示更新后的信息
            print_success("用户信息更新成功")
            user_info = format_user_info(user)

            info_table = Table(title="用户详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in user_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def delete(
    user_id: int = typer.Argument(..., help="用户 ID")
):
    """删除用户（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            # 确认删除
            if not confirm_action(
                f"确定要删除用户吗？\n用户名: {user.username}\n邮箱: {user.email}\n此操作不可逆！",
                default=False,
            ):
                print_info("已取消删除操作")
                return

            # 删除用户
            print_info(f"正在删除用户 (ID: {user_id})...")
            delete_user_db(db, user)

            print_success(f"用户删除成功 (ID: {user_id})")

    except Exception as e:
        handle_error(e)


@app.command()
def info(
    user_id: int = typer.Argument(..., help="用户 ID")
):
    """查看用户详情"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            # 显示用户信息
            user_info = format_user_info(user)

            info_table = Table(title="用户详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in user_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def activate(
    user_id: int = typer.Argument(..., help="用户 ID")
):
    """激活用户"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            if user.is_active:
                print_warning(f"用户已经是激活状态: {user.username}")
                return

            # 激活用户
            print_info(f"正在激活用户 (ID: {user_id})...")
            update_user_db(db, user, is_active=True)

            print_success(f"用户激活成功 (ID: {user_id})")

    except Exception as e:
        handle_error(e)


@app.command()
def deactivate(
    user_id: int = typer.Argument(..., help="用户 ID")
):
    """停用用户"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            if not user.is_active:
                print_warning(f"用户已经是停用状态: {user.username}")
                return

            # 确认停用
            if not confirm_action(
                f"确定要停用用户吗？\n用户名: {user.username}\n邮箱: {user.email}",
                default=False,
            ):
                print_info("已取消停用操作")
                return

            # 停用用户
            print_info(f"正在停用用户 (ID: {user_id})...")
            update_user_db(db, user, is_active=False)

            print_success(f"用户停用成功 (ID: {user_id})")

    except Exception as e:
        handle_error(e)


@app.command()
def change_password(
    user_id: int = typer.Argument(..., help="用户 ID"),
    new_password: str = typer.Option(None, "--new-password", "-p", help="新密码（可选，自动生成）")
):
    """修改密码"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            # 如果未提供新密码，生成随机密码
            if not new_password:
                new_password = generate_password()
                print_info(f"已生成随机密码: {new_password}")

            # 修改密码
            print_info(f"正在修改用户密码 (ID: {user_id})...")
            change_password_db(db, user, new_password)

            print_success(f"密码修改成功 (ID: {user_id})")

            # 显示新密码
            if new_password:
                print_warning(f"新密码: {new_password}")
                print_warning("请妥善保管新密码！")

    except Exception as e:
        handle_error(e)


@app.command()
def set_role(
    user_id: int = typer.Argument(..., help="用户 ID"),
    role: str = typer.Option(..., "--role", "-r", help="角色 (admin/operator/customer)")
):
    """设置用户角色"""
    try:
        # 验证角色
        valid_roles = ["admin", "operator", "customer"]
        if role not in valid_roles:
            print_error(f"无效的角色: {role}，有效角色: {', '.join(valid_roles)}")
            raise typer.Exit(1)

        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            if user.role == role:
                print_warning(f"用户角色已经是 {role}")
                return

            # 更新角色
            print_info(f"正在更新用户角色 (ID: {user_id})...")
            update_user_db(db, user, role=role)

            print_success(f"用户角色更新成功 (ID: {user_id})")
            print_info(f"用户: {user.username}")
            print_info(f"新角色: {role}")

    except Exception as e:
        handle_error(e)


@app.command()
def reset_password(
    user_id: int = typer.Argument(..., help="用户 ID")
):
    """重置密码（生成随机密码）"""
    try:
        with get_session_local()() as db:
            # 获取用户
            user = get_user(db, user_id)
            if not user:
                print_error(f"用户不存在: ID {user_id}")
                raise typer.Exit(1)

            # 生成随机密码
            new_password = generate_password()

            # 修改密码
            print_info(f"正在重置用户密码 (ID: {user_id})...")
            change_password_db(db, user, new_password)

            print_success(f"密码重置成功 (ID: {user_id})")
            print_info(f"用户: {user.username}")
            print_warning(f"新密码: {new_password}")
            print_warning("请妥善保管新密码！")

    except Exception as e:
        handle_error(e)
