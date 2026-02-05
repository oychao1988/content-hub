"""
发布管理模块

提供发布历史、手动发布、重试发布、批量发布等功能。
"""

from datetime import datetime
from typing import Optional

import typer
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
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
from app.models.publisher import PublishLog
from app.models.content import Content
from app.modules.publisher.services import publisher_service
from app.services.content_publisher_service import content_publisher_service

# 创建子应用
app = typer.Typer(help="发布管理")


def get_publish_log(db: Session, log_id: int) -> Optional[PublishLog]:
    """获取发布日志

    Args:
        db: 数据库会话
        log_id: 发布日志 ID

    Returns:
        发布日志对象或 None
    """
    return db.query(PublishLog).filter(PublishLog.id == log_id).first()


def list_publish_logs_db(
    db: Session,
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[PublishLog]:
    """查询发布日志列表

    Args:
        db: 数据库会话
        account_id: 账号 ID 筛选
        status: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        发布日志列表
    """
    query = db.query(PublishLog)

    if account_id:
        query = query.filter(PublishLog.account_id == account_id)
    if status:
        query = query.filter(PublishLog.status == status)

    return query.order_by(PublishLog.created_at.desc()).offset(skip).limit(limit).all()


def format_publish_log_info(log: PublishLog, detailed: bool = False) -> dict:
    """格式化发布日志信息

    Args:
        log: 发布日志对象
        detailed: 是否显示详细信息

    Returns:
        格式化的发布日志信息字典
    """
    account_name = log.account.name if log.account else "未知"
    content_title = log.content.title if log.content else "未知"

    info = {
        "ID": log.id,
        "内容": content_title,
        "账号": account_name,
        "平台": log.platform,
        "状态": log.status,
        "发布时间": format_datetime(log.publish_time),
        "创建时间": format_datetime(log.created_at),
    }

    if detailed:
        info.update({
            "媒体ID": log.media_id or "-",
            "重试次数": str(log.retry_count),
            "错误信息": log.error_message[:50] + "..." if log.error_message and len(log.error_message) > 50 else log.error_message or "-",
            "更新时间": format_datetime(log.updated_at),
        })

    return info


@app.command("history")
def publish_history(
    ctx: typer.Context,
    account_id: int = typer.Option(None, "--account-id", "-a", help="按账号 ID 筛选"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (pending/success/failed)"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量")
):
    """查看发布历史"""
    try:
        with get_session_local()() as db:
            # 查询发布日志
            logs = list_publish_logs_db(
                db,
                account_id=account_id,
                status=status,
                limit=limit
            )

            # 格式化输出
            data = []
            for log in logs:
                account_name = log.account.name if log.account else "未知"
                content_title = log.content.title if log.content else "未知"
                data.append({
                    "ID": log.id,
                    "内容": content_title[:30],
                    "账号": account_name,
                    "平台": log.platform,
                    "状态": log.status,
                    "发布时间": format_datetime(log.publish_time),
                    "创建时间": format_datetime(log.created_at),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not logs:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到发布记录")
                return

            print_table(data, title=f"发布历史 (共 {len(logs)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command()
def publish(
    content_id: int = typer.Argument(..., help="内容 ID"),
    account_id: int = typer.Option(None, "--account-id", "-a", help="账号 ID（可选，默认使用内容的账号）"),
    draft: bool = typer.Option(True, "--draft/--no-draft", help="发布到草稿箱")
):
    """手动发布内容"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            # 使用内容的账号或指定的账号
            target_account_id = account_id or content.account_id

            # 检查账号是否存在
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == target_account_id).first()
            if not account:
                print_error(f"账号不存在: ID {target_account_id}")
                raise typer.Exit(1)

            print_info(f"正在发布内容...")
            print_info(f"内容: {content.title}")
            print_info(f"账号: {account.name}")
            print_info(f"平台: {account.platform.name if account.platform else '未知'}")
            print_info(f"发布到草稿箱: {'是' if draft else '否'}")

            # 调用发布服务
            request = {
                "content_id": content_id,
                "account_id": target_account_id,
                "publish_to_draft": draft
            }

            result = publisher_service.manual_publish(db, request)

            if result.get("success"):
                print_success(f"发布成功")
                print_info(f"发布日志 ID: {result.get('log_id')}")
                if result.get("media_id"):
                    print_info(f"媒体 ID: {result.get('media_id')}")
            else:
                print_error(f"发布失败: {result.get('error', '未知错误')}")
                raise typer.Exit(1)

    except Exception as e:
        handle_error(e)


@app.command()
def retry(
    log_id: int = typer.Argument(..., help="发布日志 ID")
):
    """重试失败的发布"""
    try:
        with get_session_local()() as db:
            # 获取发布日志
            log = get_publish_log(db, log_id)
            if not log:
                print_error(f"发布日志不存在: ID {log_id}")
                raise typer.Exit(1)

            # 检查状态
            if log.status == "success":
                print_warning("该发布已成功，无需重试")
                return

            content_title = log.content.title if log.content else "未知"
            account_name = log.account.name if log.account else "未知"

            print_info(f"正在重试发布...")
            print_info(f"内容: {content_title}")
            print_info(f"账号: {account_name}")
            print_info(f"平台: {log.platform}")

            # 调用重试服务
            result = publisher_service.retry_publish(db, log_id)

            if result.get("success"):
                print_success(f"重试发布成功")
                print_info(f"发布日志 ID: {result.get('log_id')}")
                if result.get("media_id"):
                    print_info(f"媒体 ID: {result.get('media_id')}")
            else:
                print_error(f"重试失败: {result.get('error', '未知错误')}")
                raise typer.Exit(1)

    except Exception as e:
        handle_error(e)


@app.command("batch-publish")
def batch_publish(
    account_id: int = typer.Option(..., "--account-id", "-a", help="账号 ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="批量发布数量")
):
    """批量发布待发布内容"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 获取待发布的内容（审核通过且未发布的）
            contents = db.query(Content).filter(
                Content.account_id == account_id,
                Content.review_status == "approved",
                Content.publish_status == "draft"
            ).limit(limit).all()

            if not contents:
                print_warning("没有找到可发布的内容")
                print_info("需要满足以下条件：")
                print_info("  - 内容审核状态为 approved")
                print_info("  - 内容发布状态为 draft")
                return

            print_info(f"找到 {len(contents)} 条可发布的内容")
            print_info(f"账号: {account.name}")

            # 确认批量发布
            if not confirm_action(f"确定要批量发布 {len(contents)} 条内容吗？", default=False):
                print_info("已取消批量发布")
                return

            # 批量发布
            succeeded = 0
            failed = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=typer.context.console
            ) as progress:
                task = progress.add_task("批量发布中...", total=len(contents))

                for content in contents:
                    try:
                        request = {
                            "content_id": content.id,
                            "account_id": account_id,
                            "publish_to_draft": True
                        }

                        result = publisher_service.manual_publish(db, request)

                        if result.get("success"):
                            succeeded += 1
                            print_success(f"  [{succeeded + failed}/{len(contents)}] 发布成功: {content.title[:30]}")
                        else:
                            failed += 1
                            print_error(f"  [{succeeded + failed}/{len(contents)}] 发布失败: {content.title[:30]} - {result.get('error', '未知错误')}")

                    except Exception as e:
                        failed += 1
                        print_error(f"  [{succeeded + failed}/{len(contents)}] 发布失败: {content.title[:30]} - {str(e)}")

                    progress.update(task, advance=1)

            # 显示统计信息
            print_success(f"\n批量发布完成")
            print_info(f"成功: {succeeded}, 失败: {failed}, 总计: {len(contents)}")

            if failed > 0:
                print_warning("部分内容发布失败，请使用 publisher retry 命令重试")

    except Exception as e:
        handle_error(e)


@app.command("records")
def publish_records(
    ctx: typer.Context,
    account_id: int = typer.Option(None, "--account-id", "-a", help="按账号 ID 筛选"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量")
):
    """查看发布记录（与 history 相同）"""
    try:
        with get_session_local()() as db:
            # 查询发布日志
            logs = list_publish_logs_db(
                db,
                account_id=account_id,
                status=status,
                limit=limit
            )

            # 格式化输出（更详细的格式）
            data = []
            for log in logs:
                account_name = log.account.name if log.account else "未知"
                content_title = log.content.title if log.content else "未知"
                data.append({
                    "ID": log.id,
                    "内容": content_title,
                    "账号": account_name,
                    "平台": log.platform,
                    "状态": log.status,
                    "媒体ID": log.media_id or "-",
                    "重试次数": log.retry_count,
                    "发布时间": format_datetime(log.publish_time),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not logs:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到发布记录")
                return

            print_table(data, title=f"发布记录 (共 {len(logs)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command("stats")
def publish_statistics(
    account_id: int = typer.Option(None, "--account-id", "-a", help="按账号 ID 筛选")
):
    """查看发布统计"""
    try:
        with get_session_local()() as db:
            query = db.query(PublishLog)

            if account_id:
                # 检查账号是否存在
                from app.models.account import Account
                account = db.query(Account).filter(Account.id == account_id).first()
                if not account:
                    print_error(f"账号不存在: ID {account_id}")
                    raise typer.Exit(1)
                query = query.filter(PublishLog.account_id == account_id)

            total = query.count()
            success = query.filter(PublishLog.status == "success").count()
            failed = query.filter(PublishLog.status == "failed").count()
            pending = query.filter(PublishLog.status == "pending").count()

            # 显示统计信息
            stats_table = Table(title="发布统计", show_header=True)
            stats_table.add_column("项目", style="cyan")
            stats_table.add_column("数量", style="green")
            stats_table.add_column("占比", style="yellow")

            if total > 0:
                stats_table.add_row("总计", str(total), "100%")
                stats_table.add_row("成功", str(success), f"{success/total*100:.1f}%")
                stats_table.add_row("失败", str(failed), f"{failed/total*100:.1f}%")
                stats_table.add_row("待发布", str(pending), f"{pending/total*100:.1f}%")

                # 计算成功率
                success_rate = success / total * 100
                stats_table.add_row("成功率", f"{success_rate:.1f}%", "-")
            else:
                stats_table.add_row("总计", "0", "-")
                stats_table.add_row("成功", "0", "-")
                stats_table.add_row("失败", "0", "-")
                stats_table.add_row("待发布", "0", "-")
                stats_table.add_row("成功率", "-", "-")

            from rich.console import Console
            console = Console()
            console.print(stats_table)

            # 按平台统计
            if account_id is None:
                print_info("\n按平台统计:")
                platforms = db.query(PublishLog.platform).distinct().all()
                for (platform_name,) in platforms:
                    platform_query = query.filter(PublishLog.platform == platform_name)
                    platform_total = platform_query.count()
                    platform_success = platform_query.filter(PublishLog.status == "success").count()
                    if platform_total > 0:
                        platform_rate = platform_success / platform_total * 100
                        print_info(f"  {platform_name}: {platform_success}/{platform_total} ({platform_rate:.1f}%)")

            # 按账号统计
            if account_id:
                print_info(f"\n账号统计:")
                print_info(f"  账号: {account.name}")
                print_info(f"  成功: {success}/{total} ({success/total*100:.1f}%)" if total > 0 else "  成功: 0/0")

    except Exception as e:
        handle_error(e)
