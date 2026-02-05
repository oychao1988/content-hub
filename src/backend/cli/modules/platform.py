"""
平台管理模块

提供平台 CRUD 和 API 测试功能。
"""

import json
from typing import Optional
from datetime import datetime

import typer
import httpx
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
    handle_error,
    get_global_format,
)
from app.db.sql_db import get_session_local
from app.models.platform import Platform

# 创建子应用
app = typer.Typer(help="平台管理")


def get_platform(db: Session, platform_id: int) -> Optional[Platform]:
    """获取平台

    Args:
        db: 数据库会话
        platform_id: 平台 ID

    Returns:
        平台对象或 None
    """
    return db.query(Platform).filter(Platform.id == platform_id).first()


def list_platforms_db(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[Platform]:
    """查询平台列表

    Args:
        db: 数据库会话
        status: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        平台列表
    """
    query = db.query(Platform)

    if status:
        is_active = status.lower() == "active"
        query = query.filter(Platform.is_active == (is_active if status.lower() in ["active", "inactive"] else True))

    return query.order_by(Platform.created_at.desc()).offset(skip).limit(limit).all()


def format_platform_info(platform: Platform, detailed: bool = False) -> dict:
    """格式化平台信息

    Args:
        platform: 平台对象
        detailed: 是否显示详细信息

    Returns:
        格式化的平台信息字典
    """
    info = {
        "ID": platform.id,
        "名称": platform.name,
        "代码": platform.code,
        "类型": platform.type or "-",
        "状态": "激活" if platform.is_active else "停用",
        "创建时间": format_datetime(platform.created_at),
    }

    if detailed:
        info.update({
            "描述": platform.description or "-",
            "API地址": platform.api_url or "-",
            "更新时间": format_datetime(platform.updated_at),
        })

    return info


@app.command("list")
def list_platforms(
    ctx: typer.Context,
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (active/inactive)"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", "--size", help="每页数量")
):
    """列出平台"""
    try:
        with get_session_local()() as db:
            # 计算分页
            skip = (page - 1) * page_size

            # 查询平台
            platforms = list_platforms_db(
                db,
                status=status,
                skip=skip,
                limit=page_size
            )

            # 格式化输出
            data = []
            for platform in platforms:
                data.append({
                    "ID": platform.id,
                    "名称": platform.name,
                    "代码": platform.code,
                    "类型": platform.type or "-",
                    "状态": "激活" if platform.is_active else "停用",
                    "创建时间": format_datetime(platform.created_at),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not platforms:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到平台")
                return

            print_table(data, title=f"平台列表 (第 {page} 页，共 {len(platforms)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="平台名称"),
    code: str = typer.Option(..., "--code", "-c", help="平台代码"),
    platform_type: str = typer.Option(None, "--type", "-t", help="平台类型"),
    description: str = typer.Option(None, "--description", "-d", help="平台描述"),
    api_url: str = typer.Option(None, "--api-url", help="API 地址"),
    api_key: str = typer.Option(None, "--api-key", help="API 密钥"),
    status: str = typer.Option("active", "--status", "-s", help="平台状态 (active/inactive)")
):
    """创建平台"""
    try:
        with get_session_local()() as db:
            # 检查平台代码是否已存在
            existing = db.query(Platform).filter(Platform.code == code).first()
            if existing:
                print_error(f"平台代码已存在: {code}")
                raise typer.Exit(1)

            # 准备平台数据
            platform_data = {
                "name": name,
                "code": code,
                "type": platform_type,
                "description": description,
                "api_url": api_url,
                "api_key": api_key,
                "is_active": status.lower() == "active"
            }

            # 创建平台
            print_info("正在创建平台...")
            platform = Platform(**platform_data)
            db.add(platform)
            db.commit()
            db.refresh(platform)

            print_success(f"平台创建成功 (ID: {platform.id})")

            # 显示平台信息
            platform_info = format_platform_info(platform, detailed=True)

            info_table = Table(title="平台详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in platform_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def update(
    platform_id: int = typer.Argument(..., help="平台 ID"),
    name: str = typer.Option(None, "--name", "-n", help="平台名称"),
    code: str = typer.Option(None, "--code", "-c", help="平台代码"),
    platform_type: str = typer.Option(None, "--type", "-t", help="平台类型"),
    description: str = typer.Option(None, "--description", "-d", help="平台描述"),
    api_url: str = typer.Option(None, "--api-url", help="API 地址"),
    api_key: str = typer.Option(None, "--api-key", help="API 密钥"),
    status: str = typer.Option(None, "--status", "-s", help="平台状态 (active/inactive)")
):
    """更新平台"""
    try:
        with get_session_local()() as db:
            # 获取平台
            platform = get_platform(db, platform_id)
            if not platform:
                print_error(f"平台不存在: ID {platform_id}")
                raise typer.Exit(1)

            # 准备更新数据
            update_data = {}
            if name:
                update_data["name"] = name
            if code:
                # 检查新代码是否已被其他平台使用
                existing = db.query(Platform).filter(
                    Platform.code == code,
                    Platform.id != platform_id
                ).first()
                if existing:
                    print_error(f"平台代码已被使用: {code}")
                    raise typer.Exit(1)
                update_data["code"] = code
            if platform_type is not None:
                update_data["type"] = platform_type
            if description is not None:
                update_data["description"] = description
            if api_url is not None:
                update_data["api_url"] = api_url
            if api_key is not None:
                update_data["api_key"] = api_key
            if status:
                update_data["is_active"] = status.lower() == "active"

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            # 更新平台
            print_info(f"正在更新平台 (ID: {platform_id})...")
            for key, value in update_data.items():
                setattr(platform, key, value)

            db.commit()
            db.refresh(platform)

            print_success("平台信息更新成功")

            # 显示更新后的信息
            platform_info = format_platform_info(platform, detailed=True)

            info_table = Table(title="平台详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in platform_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def delete(
    platform_id: int = typer.Argument(..., help="平台 ID")
):
    """删除平台（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取平台
            platform = get_platform(db, platform_id)
            if not platform:
                print_error(f"平台不存在: ID {platform_id}")
                raise typer.Exit(1)

            # 检查是否有关联的账号
            from app.models.account import Account
            account_count = db.query(Account).filter(Account.platform_id == platform_id).count()
            if account_count > 0:
                print_warning(f"该平台下有 {account_count} 个账号，无法删除")
                print_info("请先删除或迁移相关账号")
                raise typer.Exit(1)

            # 确认删除
            if not confirm_action(
                f"确定要删除平台吗？\n平台名: {platform.name}\n此操作不可逆！",
                default=False,
            ):
                print_info("已取消删除操作")
                return

            # 删除平台
            print_info(f"正在删除平台 (ID: {platform_id})...")
            db.delete(platform)
            db.commit()

            print_success(f"平台删除成功 (ID: {platform_id})")

    except Exception as e:
        handle_error(e)


@app.command()
def info(
    platform_id: int = typer.Argument(..., help="平台 ID")
):
    """查看平台详情"""
    try:
        with get_session_local()() as db:
            # 获取平台
            platform = get_platform(db, platform_id)
            if not platform:
                print_error(f"平台不存在: ID {platform_id}")
                raise typer.Exit(1)

            # 显示平台信息
            platform_info = format_platform_info(platform, detailed=True)

            info_table = Table(title="平台详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in platform_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

            # 显示关联账号统计
            from app.models.account import Account
            account_count = db.query(Account).filter(Account.platform_id == platform_id).count()
            active_account_count = db.query(Account).filter(
                Account.platform_id == platform_id,
                Account.is_active == True
            ).count()

            print_info(f"\n关联账号: {account_count} 个 (激活: {active_account_count} 个)")

    except Exception as e:
        handle_error(e)


@app.command("test-api")
def test_api(
    platform_id: int = typer.Argument(..., help="平台 ID"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="超时时间（秒）")
):
    """测试平台 API 连接"""
    try:
        with get_session_local()() as db:
            # 获取平台
            platform = get_platform(db, platform_id)
            if not platform:
                print_error(f"平台不存在: ID {platform_id}")
                raise typer.Exit(1)

            if not platform.api_url:
                print_warning(f"平台未配置 API 地址")
                return

            print_info(f"正在测试平台 API 连接...")
            print_info(f"平台: {platform.name}")
            print_info(f"API 地址: {platform.api_url}")

            # 测试 API 连接
            try:
                with httpx.Client(timeout=timeout) as client:
                    # 尝试发送简单的 GET 请求
                    response = client.get(platform.api_url)

                    if response.status_code == 200:
                        print_success(f"API 连接测试成功")
                        print_info(f"状态码: {response.status_code}")
                        print_info(f"响应时间: {response.elapsed.total_seconds() * 1000:.2f} ms")

                        # 尝试显示响应内容摘要
                        try:
                            content = response.json()
                            print_info(f"响应类型: JSON")
                            if isinstance(content, dict):
                                print_info(f"响应字段: {', '.join(content.keys())}")
                            else:
                                print_info(f"响应数据: {str(content)[:100]}")
                        except:
                            print_info(f"响应内容: {response.text[:100]}")
                    else:
                        print_warning(f"API 连接异常")
                        print_info(f"状态码: {response.status_code}")
                        print_info(f"响应内容: {response.text[:200]}")

            except httpx.TimeoutException:
                print_error(f"API 连接超时（超过 {timeout} 秒）")
            except httpx.ConnectionError as e:
                print_error(f"API 连接失败: {str(e)}")
            except Exception as e:
                print_error(f"API 测试异常: {str(e)}")

    except Exception as e:
        handle_error(e)
