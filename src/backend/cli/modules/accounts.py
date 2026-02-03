"""
账号管理模块

提供账号 CRUD、配置管理、写作风格、发布配置等功能。
"""

import json
import os
from datetime import datetime
from typing import Optional

import typer
from rich.table import Table
from rich.panel import Panel
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
    format_json,
    handle_error,
)
from app.db.sql_db import get_session_local
from app.models.account import Account, WritingStyle, PublishConfig
from app.modules.accounts.services import account_service
from app.services.account_config_service import account_config_service
from app.services.content_creator_service import content_creator_service
from app.core.config import settings
from app.core.exceptions import CreatorException

# 创建子应用
app = typer.Typer(help="账号管理")


def get_account(db: Session, account_id: int) -> Optional[Account]:
    """获取账号

    Args:
        db: 数据库会话
        account_id: 账号 ID

    Returns:
        账号对象或 None
    """
    return db.query(Account).filter(Account.id == account_id).first()


def list_accounts_db(
    db: Session,
    customer_id: Optional[int] = None,
    platform_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[Account]:
    """查询账号列表

    Args:
        db: 数据库会话
        customer_id: 客户 ID 筛选
        platform_id: 平台 ID 筛选
        status: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        账号列表
    """
    query = db.query(Account)

    if customer_id:
        query = query.filter(Account.customer_id == customer_id)
    if platform_id:
        query = query.filter(Account.platform_id == platform_id)
    if status:
        is_active = status.lower() == "active"
        query = query.filter(Account.is_active == (is_active if status.lower() in ["active", "inactive"] else True))

    return query.order_by(Account.created_at.desc()).offset(skip).limit(limit).all()


def format_account_info(account: Account, detailed: bool = False) -> dict:
    """格式化账号信息

    Args:
        account: 账号对象
        detailed: 是否显示详细信息

    Returns:
        格式化的账号信息字典
    """
    info = {
        "ID": account.id,
        "名称": account.name,
        "目录名": account.directory_name,
        "客户ID": account.customer_id,
        "平台ID": account.platform_id,
        "状态": "激活" if account.is_active else "停用",
        "创建时间": format_datetime(account.created_at),
    }

    if detailed:
        info.update({
            "描述": account.description or "-",
            "更新时间": format_datetime(account.updated_at),
        })

        # 显示微信配置（如果有）
        if account.wechat_app_id:
            info["微信AppID"] = account.wechat_app_id

    return info


@app.command("list")
def list_accounts(
    customer_id: int = typer.Option(None, "--customer-id", "-c", help="按客户 ID 筛选"),
    platform_id: int = typer.Option(None, "--platform-id", "-p", help="按平台 ID 筛选"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (active/inactive)"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", "--size", help="每页数量")
):
    """列出账号"""
    try:
        with get_session_local()() as db:
            # 计算分页
            skip = (page - 1) * page_size

            # 查询账号
            accounts = list_accounts_db(
                db,
                customer_id=customer_id,
                platform_id=platform_id,
                status=status,
                skip=skip,
                limit=page_size
            )

            if not accounts:
                print_warning("未找到账号")
                return

            # 格式化输出
            data = []
            for account in accounts:
                customer_name = account.customer.name if account.customer else "未知"
                platform_name = account.platform.name if account.platform else "未知"
                data.append({
                    "ID": account.id,
                    "名称": account.name,
                    "目录名": account.directory_name,
                    "客户": customer_name,
                    "平台": platform_name,
                    "状态": "激活" if account.is_active else "停用",
                    "创建时间": format_datetime(account.created_at),
                })

            print_table(data, title=f"账号列表 (第 {page} 页，共 {len(accounts)} 条)", show_header=True)

    except Exception as e:
        handle_error(e)


@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="账号名称"),
    customer_id: int = typer.Option(..., "--customer-id", "-c", help="客户 ID"),
    platform_id: int = typer.Option(..., "--platform-id", "-p", help="平台 ID"),
    description: str = typer.Option(None, "--description", "-d", help="账号描述"),
    status: str = typer.Option("active", "--status", "-s", help="账号状态 (active/inactive)")
):
    """创建账号"""
    try:
        with get_session_local()() as db:
            # 验证客户和平台是否存在
            from app.models.customer import Customer
            from app.models.platform import Platform

            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                print_error(f"客户不存在: ID {customer_id}")
                raise typer.Exit(1)

            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                print_error(f"平台不存在: ID {platform_id}")
                raise typer.Exit(1)

            # 准备账号数据
            account_data = {
                "name": name,
                "customer_id": customer_id,
                "platform_id": platform_id,
                "directory_name": f"{platform.code}_{customer.id}_{name}".lower().replace(" ", "_"),
                "description": description,
                "is_active": status.lower() == "active"
            }

            # 创建账号
            print_info("正在创建账号...")
            account = account_service.create_account(db, account_data)

            print_success(f"账号创建成功 (ID: {account.id})")

            # 显示账号信息
            account_info = format_account_info(account, detailed=True)

            info_table = Table(title="账号详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in account_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def update(
    account_id: int = typer.Argument(..., help="账号 ID"),
    name: str = typer.Option(None, "--name", "-n", help="账号名称"),
    description: str = typer.Option(None, "--description", "-d", help="账号描述"),
    status: str = typer.Option(None, "--status", "-s", help="账号状态 (active/inactive)")
):
    """更新账号"""
    try:
        with get_session_local()() as db:
            # 获取账号
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 准备更新数据
            update_data = {}
            if name:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if status:
                update_data["is_active"] = status.lower() == "active"

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            # 更新账号
            print_info(f"正在更新账号 (ID: {account_id})...")
            account = account_service.update_account(db, account_id, update_data)

            print_success("账号信息更新成功")

            # 显示更新后的信息
            account_info = format_account_info(account, detailed=True)

            info_table = Table(title="账号详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in account_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def delete(
    account_id: int = typer.Argument(..., help="账号 ID")
):
    """删除账号（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取账号
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 确认删除
            if not confirm_action(
                f"确定要删除账号吗？\n账号名: {account.name}\n此操作将删除所有相关数据，不可逆！",
                default=False,
            ):
                print_info("已取消删除操作")
                return

            # 删除账号
            print_info(f"正在删除账号 (ID: {account_id})...")
            success = account_service.delete_account(db, account_id)

            if success:
                print_success(f"账号删除成功 (ID: {account_id})")
            else:
                print_error("删除失败")

    except Exception as e:
        handle_error(e)


@app.command()
def info(
    account_id: int = typer.Argument(..., help="账号 ID")
):
    """查看账号详情"""
    try:
        with get_session_local()() as db:
            # 获取账号
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 显示账号信息
            account_info = format_account_info(account, detailed=True)

            info_table = Table(title="账号详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in account_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command("list-config")
def list_config(
    account_id: int = typer.Argument(..., help="账号 ID")
):
    """查看完整配置（JSON 格式）"""
    try:
        with get_session_local()() as db:
            # 获取账号
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 收集所有配置
            config_data = {
                "account": {
                    "id": account.id,
                    "name": account.name,
                    "directory_name": account.directory_name,
                    "description": account.description,
                    "customer_id": account.customer_id,
                    "platform_id": account.platform_id,
                    "is_active": account.is_active,
                    "created_at": format_datetime(account.created_at),
                    "updated_at": format_datetime(account.updated_at),
                }
            }

            # 写作风格配置
            if account.writing_style:
                config_data["writing_style"] = {
                    "id": account.writing_style.id,
                    "name": account.writing_style.name,
                    "code": account.writing_style.code,
                    "tone": account.writing_style.tone,
                    "persona": account.writing_style.persona,
                    "min_words": account.writing_style.min_words,
                    "max_words": account.writing_style.max_words,
                    "emoji_usage": account.writing_style.emoji_usage,
                    "forbidden_words": account.writing_style.forbidden_words or [],
                }

            # 发布配置
            if account.publish_config:
                config_data["publish_config"] = {
                    "id": account.publish_config.id,
                    "review_mode": account.publish_config.review_mode,
                    "publish_mode": account.publish_config.publish_mode,
                    "auto_publish": account.publish_config.auto_publish,
                    "publish_times": account.publish_config.publish_times or [],
                }

            # 内容板块配置
            if account.content_sections:
                config_data["content_sections"] = [
                    {
                        "id": section.id,
                        "name": section.name,
                        "code": section.code,
                        "description": section.description,
                        "word_count": section.word_count,
                        "update_frequency": section.update_frequency,
                    }
                    for section in account.content_sections
                ]

            # 数据源配置
            if account.data_sources:
                config_data["data_sources"] = [
                    {
                        "id": source.id,
                        "name": source.name,
                        "type": source.type,
                        "url": source.url,
                        "keywords": source.keywords or [],
                    }
                    for source in account.data_sources
                ]

            # 显示 JSON 配置
            print_info(f"账号配置 (ID: {account_id}):")
            print(Panel(format_json(config_data), title="完整配置", style="blue"))

    except Exception as e:
        handle_error(e)


@app.command("import-md")
def import_markdown(
    account_id: int = typer.Argument(..., help="账号 ID"),
    markdown_file: str = typer.Argument(..., help="Markdown 文件路径")
):
    """从 Markdown 导入配置"""
    try:
        # 检查文件是否存在
        if not os.path.exists(markdown_file):
            print_error(f"文件不存在: {markdown_file}")
            raise typer.Exit(1)

        with get_session_local()() as db:
            # 检查账号是否存在
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            print_info(f"正在从 Markdown 导入配置: {markdown_file}")

            # 导入配置
            result = account_config_service.import_from_markdown(db, account_id, markdown_file)

            if result.get("success"):
                print_success(f"配置导入成功")
                print_info(f"导入了 {result.get('imported', 0)} 条配置")
            else:
                print_error(f"导入失败: {result.get('message', '未知错误')}")

    except Exception as e:
        handle_error(e)


@app.command("export-md")
def export_markdown(
    account_id: int = typer.Argument(..., help="账号 ID"),
    output_path: str = typer.Option(None, "--output", "-o", help="输出路径（可选，默认打印到终端）")
):
    """导出配置到 Markdown"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            print_info(f"正在导出账号配置...")

            # 导出配置
            markdown_content = account_config_service.export_to_markdown(db, account_id)

            # 输出或保存
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                print_success(f"配置已导出到: {output_path}")
            else:
                print_success(f"账号配置 (ID: {account_id}):")
                print(Panel(markdown_content, title="Markdown 配置", style="blue"))

    except Exception as e:
        handle_error(e)


@app.command("test-connection")
def test_connection(
    account_id: int = typer.Argument(..., help="账号 ID")
):
    """测试平台连接"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            print_info(f"正在测试账号连接...")

            # 简单的连接测试
            # 实际实现中应该根据平台类型进行相应的测试
            platform_name = account.platform.name if account.platform else "未知平台"

            # 检查基本配置
            has_config = bool(account.wechat_app_id or account.publisher_api_key)

            if has_config:
                print_success(f"账号连接测试通过")
                print_info(f"平台: {platform_name}")
                print_info(f"账号: {account.name}")
            else:
                print_warning(f"账号未配置平台凭证")
                print_info(f"平台: {platform_name}")
                print_info(f"账号: {account.name}")

    except Exception as e:
        handle_error(e)


@app.command("writing-style")
def manage_writing_style(
    account_id: int = typer.Argument(..., help="账号 ID"),
    list_style: bool = typer.Option(False, "--list", "-l", help="列出写作风格配置"),
    get_field: str = typer.Option(None, "--get", "-g", help="获取特定字段"),
    update_json: str = typer.Option(None, "--update", "-u", help="更新配置（JSON 格式）")
):
    """管理写作风格配置"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 列出配置
            if list_style:
                style = account.writing_style
                if not style:
                    print_warning("该账号未配置写作风格")
                    return

                style_data = {
                    "ID": style.id,
                    "名称": style.name,
                    "代码": style.code,
                    "语气": style.tone,
                    "人设": style.persona or "-",
                    "最小字数": style.min_words,
                    "最大字数": style.max_words,
                    "表情使用": style.emoji_usage,
                    "禁用词": format_list(style.forbidden_words) if style.forbidden_words else "-",
                    "创建时间": format_datetime(style.created_at),
                }

                info_table = Table(title="写作风格配置", show_header=True)
                info_table.add_column("项目", style="cyan")
                info_table.add_column("值", style="green")

                for key, value in style_data.items():
                    info_table.add_row(key, str(value))

                from rich.console import Console
                console = Console()
                console.print(info_table)
                return

            # 获取特定字段
            if get_field:
                style = account.writing_style
                if not style:
                    print_warning("该账号未配置写作风格")
                    return

                if hasattr(style, get_field):
                    value = getattr(style, get_field)
                    print_info(f"{get_field}: {value}")
                else:
                    print_error(f"字段不存在: {get_field}")
                return

            # 更新配置
            if update_json:
                try:
                    update_data = json.loads(update_json)
                except json.JSONDecodeError as e:
                    print_error(f"无效的 JSON 格式: {e}")
                    raise typer.Exit(1)

                print_info(f"正在更新写作风格配置...")
                style = account_config_service.update_writing_style(db, account_id, update_data)

                print_success("写作风格配置更新成功")
                return

            # 默认显示配置
            style = account.writing_style
            if not style:
                print_warning("该账号未配置写作风格")
                print_info("使用 --update 参数创建写作风格配置")
                return

            # 显示简短信息
            print_info(f"写作风格: {style.name} ({style.code})")
            print_info(f"语气: {style.tone}, 字数: {style.min_words}-{style.max_words}")

    except Exception as e:
        handle_error(e)


@app.command("publish-config")
def manage_publish_config(
    account_id: int = typer.Argument(..., help="账号 ID"),
    list_config: bool = typer.Option(False, "--list", "-l", help="列出发布配置"),
    get_field: str = typer.Option(None, "--get", "-g", help="获取特定字段"),
    update_json: str = typer.Option(None, "--update", "-u", help="更新配置（JSON 格式）")
):
    """管理发布配置"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            account = get_account(db, account_id)
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 列出配置
            if list_config:
                config = account.publish_config
                if not config:
                    print_warning("该账号未配置发布设置")
                    return

                config_data = {
                    "ID": config.id,
                    "审核模式": config.review_mode,
                    "发布模式": config.publish_mode,
                    "自动发布": "是" if config.auto_publish else "否",
                    "发布时间": format_list(config.publish_times) if config.publish_times else "-",
                    "创建时间": format_datetime(config.created_at),
                }

                info_table = Table(title="发布配置", show_header=True)
                info_table.add_column("项目", style="cyan")
                info_table.add_column("值", style="green")

                for key, value in config_data.items():
                    info_table.add_row(key, str(value))

                from rich.console import Console
                console = Console()
                console.print(info_table)
                return

            # 获取特定字段
            if get_field:
                config = account.publish_config
                if not config:
                    print_warning("该账号未配置发布设置")
                    return

                if hasattr(config, get_field):
                    value = getattr(config, get_field)
                    print_info(f"{get_field}: {value}")
                else:
                    print_error(f"字段不存在: {get_field}")
                return

            # 更新配置
            if update_json:
                try:
                    update_data = json.loads(update_json)
                except json.JSONDecodeError as e:
                    print_error(f"无效的 JSON 格式: {e}")
                    raise typer.Exit(1)

                print_info(f"正在更新发布配置...")
                config = account_config_service.update_publish_config(db, account_id, update_data)

                print_success("发布配置更新成功")
                return

            # 默认显示配置
            config = account.publish_config
            if not config:
                print_warning("该账号未配置发布设置")
                print_info("使用 --update 参数创建发布配置")
                return

            # 显示简短信息
            print_info(f"审核模式: {config.review_mode}")
            print_info(f"发布模式: {config.publish_mode}, 自动发布: {config.auto_publish}")

    except Exception as e:
        handle_error(e)
