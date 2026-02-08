"""
异步任务管理模块

提供异步内容生成任务的查询、列表、取消和重试功能。
"""

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
    handle_error,
    get_global_format,
)
from app.db.sql_db import get_session_local
from app.models import ContentGenerationTask
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.services.task_result_handler import TaskResultHandler
from app.core.exceptions import InvalidStateException

# 创建子应用
app = typer.Typer(help="异步任务管理")


@app.command("status")
def task_status(
    ctx: typer.Context,
    task_id: str = typer.Argument(..., help="任务ID")
):
    """
    查询任务状态

    示例:
        contenthub task status task-abc123def456
    """
    try:
        with get_session_local()() as db:
            service = AsyncContentGenerationService(db)
            status_info = service.get_task_status(task_id)

            if not status_info:
                print_error(f"任务不存在: {task_id}")
                raise typer.Exit(1)

            # 获取任务详细信息
            task = service.get_task_by_id(task_id)

            # 状态图标映射
            status_icons = {
                "pending": "⏳",
                "submitted": "📤",
                "processing": "⚙️",
                "completed": "✅",
                "failed": "❌",
                "timeout": "⏰",
                "cancelled": "🚫"
            }
            status_icon = status_icons.get(status_info['status'], "❓")

            # 显示任务状态
            print_info(f"{status_icon} 任务信息")

            # 创建状态表格
            status_table = Table(show_header=False, box=None)
            status_table.add_column("项目", style="cyan")
            status_table.add_column("值", style="green")

            status_table.add_row("任务ID", status_info['task_id'])
            status_table.add_row("状态", f"{status_icon} {status_info['status']}")
            status_table.add_row("账号ID", str(status_info.get('account_id', 'N/A')))
            status_table.add_row("选题", status_info.get('topic', 'N/A') or 'N/A')

            if status_info.get('priority') is not None:
                status_table.add_row("优先级", str(status_info['priority']))

            if status_info.get('auto_approve') is not None:
                auto_approve_str = "是" if status_info['auto_approve'] else "否"
                status_table.add_row("自动审核", auto_approve_str)

            # 时间信息
            if status_info.get('created_at'):
                created_at = format_datetime(status_info['created_at'])
                status_table.add_row("创建时间", created_at)

            if status_info.get('submitted_at'):
                submitted_at = format_datetime(status_info['submitted_at'])
                status_table.add_row("提交时间", submitted_at)

            if status_info.get('started_at'):
                started_at = format_datetime(status_info['started_at'])
                status_table.add_row("开始时间", started_at)

            if status_info.get('completed_at'):
                completed_at = format_datetime(status_info['completed_at'])
                status_table.add_row("完成时间", completed_at)

            if status_info.get('timeout_at'):
                timeout_at = format_datetime(status_info['timeout_at'])
                status_table.add_row("超时时间", timeout_at)

            # 错误信息
            if status_info.get('error'):
                status_table.add_row("错误信息", f"[red]{status_info['error']}[/red]")

            # 内容ID
            if status_info.get('content_id'):
                status_table.add_row("内容ID", str(status_info['content_id']))

            from rich.console import Console
            console = Console()
            console.print(status_table)

            # 根据状态给出提示
            if status_info['status'] == "pending":
                print_info("\n提示: 任务正在排队等待处理")
            elif status_info['status'] == "submitted":
                print_info("\n提示: 任务已提交到生成器")
            elif status_info['status'] == "processing":
                print_info("\n提示: 任务正在处理中")
            elif status_info['status'] == "completed":
                print_success("\n任务已完成!")
                if status_info.get('content_id'):
                    print_info(f"内容ID: {status_info['content_id']}")
            elif status_info['status'] == "failed":
                print_warning("\n任务执行失败")
                if status_info.get('error'):
                    print_info(f"错误: {status_info['error']}")
                    print_info("可以使用 'contenthub task retry' 重试该任务")
            elif status_info['status'] == "timeout":
                print_warning("\n任务执行超时")
                print_info("可以使用 'contenthub task retry' 重试该任务")
            elif status_info['status'] == "cancelled":
                print_info("\n任务已取消")

    except Exception as e:
        handle_error(e)


@app.command("list")
def task_list(
    ctx: typer.Context,
    account_id: int = typer.Option(None, "--account-id", "-a", help="账号ID"),
    status: str = typer.Option(None, "--status", "-s", help="状态筛选"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量")
):
    """
    列出任务

    示例:
        contenthub task list
        contenthub task list -a 49
        contenthub task list -s pending
        contenthub task list -s failed -n 50
    """
    try:
        with get_session_local()() as db:
            service = AsyncContentGenerationService(db)
            tasks = service.list_tasks(account_id=account_id, status=status, limit=limit)

            if not tasks:
                print_warning("没有找到任务")
                return

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            # 如果不是 table 格式，使用标准表格输出
            if output_format != "table":
                data = []
                for task in tasks:
                    data.append({
                        "任务ID": task.task_id,
                        "账号ID": task.account_id,
                        "选题": task.topic or "N/A",
                        "状态": task.status,
                        "优先级": task.priority,
                        "创建时间": format_datetime(task.created_at) if task.created_at else "N/A",
                    })

                print_table(data, title=f"异步任务列表 (共 {len(tasks)} 条)", show_header=True, output_format=output_format)
                return

            # 使用 Rich 表格
            table = Table(title=f"异步任务列表 (共 {len(tasks)} 条)")
            table.add_column("任务ID", style="cyan")
            table.add_column("账号ID", style="magenta")
            table.add_column("选题", style="green")
            table.add_column("状态", style="yellow")
            table.add_column("优先级", style="blue")
            table.add_column("创建时间", style="dim")

            for task in tasks:
                # 状态图标
                status_emoji = {
                    "pending": "⏳",
                    "submitted": "📤",
                    "processing": "⚙️",
                    "completed": "✅",
                    "failed": "❌",
                    "timeout": "⏰",
                    "cancelled": "🚫"
                }.get(task.status, "❓")

                # 格式化选题（截断过长的选题）
                topic_display = task.topic[:30] + "..." if task.topic and len(task.topic) > 30 else task.topic or "N/A"

                # 格式化时间
                created_at_str = format_datetime(task.created_at) if task.created_at else "N/A"

                table.add_row(
                    f"{status_emoji} {task.task_id[:12]}...",
                    str(task.account_id),
                    topic_display,
                    task.status,
                    str(task.priority),
                    created_at_str
                )

            from rich.console import Console
            console = Console()
            console.print(table)

            print_info(f"总计: {len(tasks)} 个任务")

    except Exception as e:
        handle_error(e)


@app.command("cancel")
def task_cancel(
    ctx: typer.Context,
    task_id: str = typer.Argument(..., help="任务ID")
):
    """
    取消任务

    示例:
        contenthub task cancel task-abc123def456

    注意: 只有 pending 或 submitted 状态的任务可以取消
    """
    try:
        with get_session_local()() as db:
            # 先查询任务状态
            service = AsyncContentGenerationService(db)
            status_info = service.get_task_status(task_id)

            if not status_info:
                print_error(f"任务不存在: {task_id}")
                raise typer.Exit(1)

            # 显示任务信息
            print_info(f"任务ID: {task_id}")
            print_info(f"当前状态: {status_info['status']}")
            print_info(f"选题: {status_info.get('topic', 'N/A')}")

            # 检查是否可以取消
            if status_info['status'] not in ["pending", "submitted"]:
                print_warning(f"任务状态为 {status_info['status']}，无法取消")
                print_info("只有 pending 或 submitted 状态的任务可以取消")
                raise typer.Exit(1)

            # 确认取消
            if not confirm_action(
                f"确定要取消任务 {task_id} 吗？",
                default=False,
            ):
                print_info("已取消操作")
                return

            # 执行取消
            success = service.cancel_task(task_id)

            if success:
                print_success(f"任务已取消: {task_id}")
            else:
                print_error(f"取消失败: {task_id}")
                raise typer.Exit(1)

    except InvalidStateException as e:
        print_error(f"无效的状态操作: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        handle_error(e)


@app.command("retry")
def task_retry(
    ctx: typer.Context,
    task_id: str = typer.Argument(..., help="任务ID")
):
    """
    重试失败的任务

    示例:
        contenthub task retry task-abc123def456

    注意: 只有 failed、timeout 或 cancelled 状态的任务可以重试
    """
    try:
        with get_session_local()() as db:
            # 先查询任务状态
            service = AsyncContentGenerationService(db)
            task = service.get_task_by_id(task_id)

            if not task:
                print_error(f"任务不存在: {task_id}")
                raise typer.Exit(1)

            # 显示任务信息
            print_info(f"任务ID: {task_id}")
            print_info(f"当前状态: {task.status}")
            print_info(f"选题: {task.topic or 'N/A'}")
            print_info(f"已重试次数: {task.retry_count}/{task.max_retries}")

            # 检查是否可以重试
            if task.status not in ["failed", "timeout", "cancelled"]:
                print_warning(f"任务状态为 {task.status}，无法重试")
                print_info("只有 failed、timeout 或 cancelled 状态的任务可以重试")
                raise typer.Exit(1)

            # 检查重试次数
            if task.retry_count >= task.max_retries:
                print_error(f"任务已达到最大重试次数 ({task.max_retries})")
                raise typer.Exit(1)

            # 确认重试
            if not confirm_action(
                f"确定要重试任务 {task_id} 吗？",
                default=False,
            ):
                print_info("已取消操作")
                return

            # 执行重试
            handler = TaskResultHandler()
            success = handler.retry_task(db, task)

            if success:
                print_success(f"任务已重新提交: {task_id}")
                print_info(f"重试次数: {task.retry_count}/{task.max_retries}")
                print_info(f"状态: {task.status}")
                print_info(f"\n使用以下命令查看状态:")
                print_info(f"  contenthub task status {task_id}")
            else:
                print_error(f"重试失败: {task_id}")
                raise typer.Exit(1)

    except Exception as e:
        handle_error(e)


@app.command("cleanup")
def task_cleanup(
    ctx: typer.Context,
    days: int = typer.Option(7, "--days", "-d", help="保留天数"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="跳过确认")
):
    """
    清理旧任务记录

    示例:
        contenthub task cleanup --days 7
        contenthub task cleanup -d 30 --yes

    注意: 此操作将删除已完成的旧任务记录，不可恢复
    """
    try:
        with get_session_local()() as db:
            service = AsyncContentGenerationService(db)

            print_info(f"将清理 {days} 天前的已完成任务记录")

            # 确认清理
            if not confirm:
                if not confirm_action(
                    f"确定要清理 {days} 天前的旧任务记录吗？此操作不可恢复！",
                    default=False,
                ):
                    print_info("已取消操作")
                    return

            # 执行清理
            print_info("正在清理...")
            deleted_count = service.cleanup_old_tasks(days=days)

            print_success(f"清理完成: 删除了 {deleted_count} 条旧任务记录")

    except Exception as e:
        handle_error(e)


@app.command("stats")
def task_stats(
    ctx: typer.Context
):
    """
    显示任务统计信息

    示例:
        contenthub task stats
    """
    try:
        with get_session_local()() as db:
            from sqlalchemy import func

            # 查询各状态任务数量
            stats = db.query(
                ContentGenerationTask.status,
                func.count(ContentGenerationTask.id).label('count')
            ).group_by(ContentGenerationTask.status).all()

            if not stats:
                print_warning("没有任务记录")
                return

            # 创建统计表格
            stats_table = Table(title="任务统计")
            stats_table.add_column("状态", style="cyan")
            stats_table.add_column("数量", style="green")
            stats_table.add_column("占比", style="yellow")

            total = sum(count for _, count in stats)

            # 状态图标映射
            status_icons = {
                "pending": "⏳",
                "submitted": "📤",
                "processing": "⚙️",
                "completed": "✅",
                "failed": "❌",
                "timeout": "⏰",
                "cancelled": "🚫"
            }

            for status, count in sorted(stats, key=lambda x: x[1], reverse=True):
                icon = status_icons.get(status, "❓")
                percentage = (count / total * 100) if total > 0 else 0
                stats_table.add_row(
                    f"{icon} {status}",
                    str(count),
                    f"{percentage:.1f}%"
                )

            from rich.console import Console
            console = Console()
            console.print(stats_table)

            print_info(f"总计: {total} 个任务")

    except Exception as e:
        handle_error(e)
