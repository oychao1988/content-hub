"""
客户管理模块

提供客户 CRUD、统计信息和账号查看功能。
"""

from typing import Optional
from datetime import datetime

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
    handle_error,
    get_global_format,
)
from app.db.sql_db import get_session_local
from app.models.customer import Customer
from app.models.account import Account
from app.models.content import Content
from app.models.publisher import PublishLog

# 创建子应用
app = typer.Typer(help="客户管理")


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """获取客户

    Args:
        db: 数据库会话
        customer_id: 客户 ID

    Returns:
        客户对象或 None
    """
    return db.query(Customer).filter(Customer.id == customer_id).first()


def list_customers_db(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[Customer]:
    """查询客户列表

    Args:
        db: 数据库会话
        status: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        客户列表
    """
    query = db.query(Customer)

    if status:
        is_active = status.lower() == "active"
        query = query.filter(Customer.is_active == (is_active if status.lower() in ["active", "inactive"] else True))

    return query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()


def format_customer_info(customer: Customer, detailed: bool = False) -> dict:
    """格式化客户信息

    Args:
        customer: 客户对象
        detailed: 是否显示详细信息

    Returns:
        格式化的客户信息字典
    """
    info = {
        "ID": customer.id,
        "名称": customer.name,
        "联系人": customer.contact_name or "-",
        "状态": "激活" if customer.is_active else "停用",
        "创建时间": format_datetime(customer.created_at),
    }

    if detailed:
        info.update({
            "联系邮箱": customer.contact_email or "-",
            "联系电话": customer.contact_phone or "-",
            "描述": customer.description or "-",
            "更新时间": format_datetime(customer.updated_at),
        })

    return info


@app.command("list")
def list_customers(
    ctx: typer.Context,
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (active/inactive)"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", "--size", help="每页数量")
):
    """列出客户"""
    try:
        with get_session_local()() as db:
            # 计算分页
            skip = (page - 1) * page_size

            # 查询客户
            customers = list_customers_db(
                db,
                status=status,
                skip=skip,
                limit=page_size
            )

            # 格式化输出
            data = []
            for customer in customers:
                data.append({
                    "ID": customer.id,
                    "名称": customer.name,
                    "联系人": customer.contact_name or "-",
                    "联系邮箱": customer.contact_email or "-",
                    "状态": "激活" if customer.is_active else "停用",
                    "创建时间": format_datetime(customer.created_at),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not customers:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到客户")
                return

            print_table(data, title=f"客户列表 (第 {page} 页，共 {len(customers)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="客户名称"),
    contact_name: str = typer.Option(None, "--contact-name", "-c", help="联系人姓名"),
    contact_email: str = typer.Option(None, "--contact-email", "-e", help="联系邮箱"),
    contact_phone: str = typer.Option(None, "--contact-phone", "-p", help="联系电话"),
    description: str = typer.Option(None, "--description", "-d", help="客户描述"),
    status: str = typer.Option("active", "--status", "-s", help="客户状态 (active/inactive)")
):
    """创建客户"""
    try:
        with get_session_local()() as db:
            # 检查客户名称是否已存在
            existing = db.query(Customer).filter(Customer.name == name).first()
            if existing:
                print_error(f"客户名称已存在: {name}")
                raise typer.Exit(1)

            # 准备客户数据
            customer_data = {
                "name": name,
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "description": description,
                "is_active": status.lower() == "active"
            }

            # 创建客户
            print_info("正在创建客户...")
            customer = Customer(**customer_data)
            db.add(customer)
            db.commit()
            db.refresh(customer)

            print_success(f"客户创建成功 (ID: {customer.id})")

            # 显示客户信息
            customer_info = format_customer_info(customer, detailed=True)

            info_table = Table(title="客户详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in customer_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def update(
    customer_id: int = typer.Argument(..., help="客户 ID"),
    name: str = typer.Option(None, "--name", "-n", help="客户名称"),
    contact_name: str = typer.Option(None, "--contact-name", "-c", help="联系人姓名"),
    contact_email: str = typer.Option(None, "--contact-email", "-e", help="联系邮箱"),
    contact_phone: str = typer.Option(None, "--contact-phone", "-p", help="联系电话"),
    description: str = typer.Option(None, "--description", "-d", help="客户描述"),
    status: str = typer.Option(None, "--status", "-s", help="客户状态 (active/inactive)")
):
    """更新客户"""
    try:
        with get_session_local()() as db:
            # 获取客户
            customer = get_customer(db, customer_id)
            if not customer:
                print_error(f"客户不存在: ID {customer_id}")
                raise typer.Exit(1)

            # 准备更新数据
            update_data = {}
            if name:
                # 检查新名称是否已被其他客户使用
                existing = db.query(Customer).filter(
                    Customer.name == name,
                    Customer.id != customer_id
                ).first()
                if existing:
                    print_error(f"客户名称已被使用: {name}")
                    raise typer.Exit(1)
                update_data["name"] = name
            if contact_name is not None:
                update_data["contact_name"] = contact_name
            if contact_email is not None:
                update_data["contact_email"] = contact_email
            if contact_phone is not None:
                update_data["contact_phone"] = contact_phone
            if description is not None:
                update_data["description"] = description
            if status:
                update_data["is_active"] = status.lower() == "active"

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            # 更新客户
            print_info(f"正在更新客户 (ID: {customer_id})...")
            for key, value in update_data.items():
                setattr(customer, key, value)

            db.commit()
            db.refresh(customer)

            print_success("客户信息更新成功")

            # 显示更新后的信息
            customer_info = format_customer_info(customer, detailed=True)

            info_table = Table(title="客户详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in customer_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def delete(
    customer_id: int = typer.Argument(..., help="客户 ID")
):
    """删除客户（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取客户
            customer = get_customer(db, customer_id)
            if not customer:
                print_error(f"客户不存在: ID {customer_id}")
                raise typer.Exit(1)

            # 检查是否有关联的账号
            account_count = db.query(Account).filter(Account.customer_id == customer_id).count()
            if account_count > 0:
                print_warning(f"该客户下有 {account_count} 个账号，无法删除")
                print_info("请先删除或迁移相关账号")
                raise typer.Exit(1)

            # 检查是否有关联的用户
            from app.models.user import User
            user_count = db.query(User).filter(User.customer_id == customer_id).count()
            if user_count > 0:
                print_warning(f"该客户下有 {user_count} 个用户，无法删除")
                print_info("请先删除或迁移相关用户")
                raise typer.Exit(1)

            # 确认删除
            if not confirm_action(
                f"确定要删除客户吗？\n客户名: {customer.name}\n此操作不可逆！",
                default=False,
            ):
                print_info("已取消删除操作")
                return

            # 删除客户
            print_info(f"正在删除客户 (ID: {customer_id})...")
            db.delete(customer)
            db.commit()

            print_success(f"客户删除成功 (ID: {customer_id})")

    except Exception as e:
        handle_error(e)


@app.command()
def info(
    customer_id: int = typer.Argument(..., help="客户 ID")
):
    """查看客户详情"""
    try:
        with get_session_local()() as db:
            # 获取客户
            customer = get_customer(db, customer_id)
            if not customer:
                print_error(f"客户不存在: ID {customer_id}")
                raise typer.Exit(1)

            # 显示客户信息
            customer_info = format_customer_info(customer, detailed=True)

            info_table = Table(title="客户详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in customer_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

            # 显示统计信息
            account_count = db.query(Account).filter(Account.customer_id == customer_id).count()
            active_account_count = db.query(Account).filter(
                Account.customer_id == customer_id,
                Account.is_active == True
            ).count()

            from app.models.user import User
            user_count = db.query(User).filter(User.customer_id == customer_id).count()

            print_info(f"\n关联统计:")
            print_info(f"  - 账号: {account_count} 个 (激活: {active_account_count} 个)")
            print_info(f"  - 用户: {user_count} 个")

    except Exception as e:
        handle_error(e)


@app.command("stats")
def stats(
    customer_id: int = typer.Argument(..., help="客户 ID")
):
    """查看客户统计信息"""
    try:
        with get_session_local()() as db:
            # 获取客户
            customer = get_customer(db, customer_id)
            if not customer:
                print_error(f"客户不存在: ID {customer_id}")
                raise typer.Exit(1)

            print_info(f"客户统计: {customer.name}")

            # 账号统计
            total_accounts = db.query(Account).filter(Account.customer_id == customer_id).count()
            active_accounts = db.query(Account).filter(
                Account.customer_id == customer_id,
                Account.is_active == True
            ).count()

            # 内容统计
            contents = db.query(Content).join(Account).filter(Account.customer_id == customer_id).all()
            total_contents = len(contents)
            pending_contents = len([c for c in contents if c.review_status == "pending"])
            approved_contents = len([c for c in contents if c.review_status == "approved"])

            # 发布统计
            publish_logs = db.query(PublishLog).join(Account).filter(Account.customer_id == customer_id).all()
            total_publish = len(publish_logs)
            success_publish = len([p for p in publish_logs if p.status == "success"])
            failed_publish = len([p for p in publish_logs if p.status == "failed"])

            # 显示统计表格
            stats_table = Table(title="统计详情", show_header=True)
            stats_table.add_column("项目", style="cyan")
            stats_table.add_column("数量", style="green")
            stats_table.add_column("说明", style="dim")

            stats_table.add_row("账号总数", str(total_accounts), "该客户下的所有账号")
            stats_table.add_row("激活账号", str(active_accounts), "当前激活的账号")
            stats_table.add_row("", "", "")  # 空行
            stats_table.add_row("内容总数", str(total_contents), "生成的所有内容")
            stats_table.add_row("待审核", str(pending_contents), "等待审核的内容")
            stats_table.add_row("已审核", str(approved_contents), "通过审核的内容")
            stats_table.add_row("", "", "")  # 空行
            stats_table.add_row("发布总数", str(total_publish), "尝试发布次数")
            stats_table.add_row("发布成功", str(success_publish), f"成功率 {success_publish/total_publish*100:.1f}%" if total_publish > 0 else "0%")
            stats_table.add_row("发布失败", str(failed_publish), f"失败率 {failed_publish/total_publish*100:.1f}%" if total_publish > 0 else "0%")

            from rich.console import Console
            console = Console()
            console.print(stats_table)

    except Exception as e:
        handle_error(e)


@app.command("accounts")
def list_customer_accounts(
    customer_id: int = typer.Argument(..., help="客户 ID"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (active/inactive)"),
):
    """列出客户的账号"""
    try:
        with get_session_local()() as db:
            # 获取客户
            customer = get_customer(db, customer_id)
            if not customer:
                print_error(f"客户不存在: ID {customer_id}")
                raise typer.Exit(1)

            print_info(f"客户账号列表: {customer.name}")

            # 查询账号
            query = db.query(Account).filter(Account.customer_id == customer_id)

            if status:
                is_active = status.lower() == "active"
                query = query.filter(Account.is_active == (is_active if status.lower() in ["active", "inactive"] else True))

            accounts = query.order_by(Account.created_at.desc()).all()

            if not accounts:
                print_warning("该客户暂无账号")
                return

            # 格式化输出
            data = []
            for account in accounts:
                platform_name = account.platform.name if account.platform else "未知"
                data.append({
                    "ID": account.id,
                    "名称": account.name,
                    "平台": platform_name,
                    "目录名": account.directory_name,
                    "状态": "激活" if account.is_active else "停用",
                    "创建时间": format_datetime(account.created_at),
                })

            print_table(data, title=f"共 {len(accounts)} 个账号", show_header=True)

    except Exception as e:
        handle_error(e)
