"""
发布池管理模块

提供发布池的添加、移除、优先级设置、批量发布等功能。
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
)
from app.db.sql_db import get_session_local
from app.models.publisher import PublishPool
from app.models.content import Content
from app.services.publish_pool_service import publish_pool_service
from app.services.content_publisher_service import content_publisher_service

# 创建子应用
app = typer.Typer(help="发布池管理")


def get_pool_entry_by_content_id(db: Session, content_id: int) -> Optional[PublishPool]:
    """通过内容 ID 获取发布池条目

    Args:
        db: 数据库会话
        content_id: 内容 ID

    Returns:
        发布池条目或 None
    """
    return db.query(PublishPool).filter(PublishPool.content_id == content_id).first()


def list_pool_entries_db(
    db: Session,
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[PublishPool]:
    """查询发布池列表

    Args:
        db: 数据库会话
        account_id: 账号 ID 筛选
        status: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        发布池列表
    """
    query = db.query(PublishPool).join(Content)

    if account_id:
        query = query.filter(Content.account_id == account_id)
    if status:
        query = query.filter(PublishPool.status == status)

    return query.order_by(
        PublishPool.priority.asc(),
        PublishPool.scheduled_at.asc()
    ).offset(skip).limit(limit).all()


def format_pool_entry_info(entry: PublishPool, detailed: bool = False) -> dict:
    """格式化发布池条目信息

    Args:
        entry: 发布池条目对象
        detailed: 是否显示详细信息

    Returns:
        格式化的发布池条目信息字典
    """
    content_title = entry.content.title if entry.content else "未知"
    account_name = entry.content.account.name if entry.content and entry.content.account else "未知"

    info = {
        "ID": entry.id,
        "内容": content_title,
        "账号": account_name,
        "优先级": str(entry.priority),
        "状态": entry.status,
        "计划时间": format_datetime(entry.scheduled_at),
        "加入时间": format_datetime(entry.added_at),
    }

    if detailed:
        info.update({
            "重试次数": f"{entry.retry_count}/{entry.max_retries}",
            "最后错误": entry.last_error[:50] + "..." if entry.last_error and len(entry.last_error) > 50 else entry.last_error or "-",
            "发布时间": format_datetime(entry.published_at),
            "更新时间": format_datetime(entry.updated_at),
        })

    return info


@app.command("list")
def list_pool(
    account_id: int = typer.Option(None, "--account-id", "-a", help="按账号 ID 筛选"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选 (pending/publishing/published/failed)"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量")
):
    """列出发布池内容"""
    try:
        with get_session_local()() as db:
            # 查询发布池
            entries = list_pool_entries_db(
                db,
                account_id=account_id,
                status=status,
                limit=limit
            )

            if not entries:
                print_warning("发布池为空")
                return

            # 格式化输出
            data = []
            for entry in entries:
                content_title = entry.content.title if entry.content else "未知"
                account_name = entry.content.account.name if entry.content and entry.content.account else "未知"
                data.append({
                    "ID": entry.id,
                    "内容": content_title[:30],
                    "账号": account_name,
                    "优先级": entry.priority,
                    "状态": entry.status,
                    "计划时间": format_datetime(entry.scheduled_at),
                    "加入时间": format_datetime(entry.added_at),
                })

            print_table(data, title=f"发布池 (共 {len(entries)} 条)", show_header=True)

    except Exception as e:
        handle_error(e)


@app.command("add")
def add_to_pool(
    content_id: int = typer.Argument(..., help="内容 ID"),
    priority: int = typer.Option(5, "--priority", "-p", help="优先级 (1-10，数字越小优先级越高)"),
):
    """添加内容到发布池"""
    try:
        with get_session_local()() as db:
            # 检查内容是否存在
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            # 检查是否已在发布池中
            existing = get_pool_entry_by_content_id(db, content_id)
            if existing:
                print_warning("该内容已在发布池中")
                print_info(f"当前优先级: {existing.priority}")
                print_info(f"当前状态: {existing.status}")
                return

            # 验证优先级
            if priority < 1 or priority > 10:
                print_error("优先级必须在 1-10 之间")
                raise typer.Exit(1)

            print_info(f"正在添加内容到发布池...")
            print_info(f"内容: {content.title}")
            print_info(f"优先级: {priority}")

            # 添加到发布池
            entry = publish_pool_service.add_to_pool(
                db,
                content_id=content_id,
                priority=priority,
                scheduled_at=datetime.utcnow()
            )

            print_success(f"已添加到发布池 (ID: {entry.id})")
            print_info(f"状态: {entry.status}")
            print_info(f"计划发布时间: {format_datetime(entry.scheduled_at)}")

    except Exception as e:
        handle_error(e)


@app.command("remove")
def remove_from_pool(
    content_id: int = typer.Argument(..., help="内容 ID")
):
    """从发布池移除内容"""
    try:
        with get_session_local()() as db:
            # 获取发布池条目
            entry = get_pool_entry_by_content_id(db, content_id)
            if not entry:
                print_error(f"发布池中未找到该内容: ID {content_id}")
                raise typer.Exit(1)

            content_title = entry.content.title if entry.content else "未知"

            # 确认移除
            if not confirm_action(
                f"确定要从发布池移除该内容吗？\n内容: {content_title}\n状态: {entry.status}",
                default=False,
            ):
                print_info("已取消移除操作")
                return

            # 移除
            print_info(f"正在从发布池移除...")
            success = publish_pool_service.remove_from_pool(db, entry.id)

            if success:
                print_success(f"已从发布池移除 (内容 ID: {content_id})")
            else:
                print_error("移除失败")

    except Exception as e:
        handle_error(e)


@app.command("set-priority")
def set_priority(
    content_id: int = typer.Argument(..., help="内容 ID"),
    priority: int = typer.Option(..., "--priority", "-p", help="优先级 (1-10)")
):
    """设置发布池内容的优先级"""
    try:
        with get_session_local()() as db:
            # 获取发布池条目
            entry = get_pool_entry_by_content_id(db, content_id)
            if not entry:
                print_error(f"发布池中未找到该内容: ID {content_id}")
                raise typer.Exit(1)

            # 验证优先级
            if priority < 1 or priority > 10:
                print_error("优先级必须在 1-10 之间")
                raise typer.Exit(1)

            content_title = entry.content.title if entry.content else "未知"

            print_info(f"正在更新优先级...")
            print_info(f"内容: {content_title}")
            print_info(f"旧优先级: {entry.priority}")
            print_info(f"新优先级: {priority}")

            # 更新优先级
            entry = publish_pool_service.update_pool_entry(db, entry.id, {"priority": priority})

            print_success(f"优先级已更新")
            print_info(f"内容: {content_title}")
            print_info(f"新优先级: {entry.priority}")

    except Exception as e:
        handle_error(e)


@app.command("schedule")
def schedule_publish(
    content_id: int = typer.Argument(..., help="内容 ID"),
    time: str = typer.Option(..., "--time", "-t", help="计划发布时间 (格式: YYYY-MM-DD HH:MM:SS)")
):
    """设置内容的计划发布时间"""
    try:
        # 解析时间
        try:
            scheduled_at = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print_error("时间格式错误，请使用: YYYY-MM-DD HH:MM:SS")
            print_info("示例: 2026-02-04 14:30:00")
            raise typer.Exit(1)

        with get_session_local()() as db:
            # 获取发布池条目
            entry = get_pool_entry_by_content_id(db, content_id)
            if not entry:
                print_error(f"发布池中未找到该内容: ID {content_id}")
                raise typer.Exit(1)

            content_title = entry.content.title if entry.content else "未知"

            print_info(f"正在设置计划发布时间...")
            print_info(f"内容: {content_title}")
            print_info(f"旧计划时间: {format_datetime(entry.scheduled_at)}")
            print_info(f"新计划时间: {format_datetime(scheduled_at)}")

            # 更新计划时间
            entry = publish_pool_service.update_pool_entry(db, entry.id, {
                "scheduled_at": scheduled_at,
                "status": "pending"  # 重置为待发布
            })

            print_success(f"计划发布时间已设置")
            print_info(f"内容: {content_title}")
            print_info(f"计划时间: {format_datetime(entry.scheduled_at)}")

    except Exception as e:
        handle_error(e)


@app.command("publish")
def publish_from_pool(
    limit: int = typer.Option(10, "--limit", "-n", help="批量发布数量")
):
    """从发布池批量发布"""
    try:
        with get_session_local()() as db:
            # 获取待发布条目
            pending_entries = publish_pool_service.get_pending_entries(db)

            if not pending_entries:
                print_warning("发布池中没有待发布的内容")
                return

            # 限制发布数量
            entries_to_publish = pending_entries[:limit]

            print_info(f"找到 {len(pending_entries)} 条待发布内容")
            print_info(f"准备发布 {len(entries_to_publish)} 条")

            # 确认发布
            if not confirm_action(f"确定要发布 {len(entries_to_publish)} 条内容吗？", default=False):
                print_info("已取消发布操作")
                return

            # 批量发布
            succeeded = 0
            failed = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=typer.context.console
            ) as progress:
                task = progress.add_task("批量发布中...", total=len(entries_to_publish))

                for entry in entries_to_publish:
                    try:
                        content_title = entry.content.title if entry.content else "未知"
                        account_id = entry.content.account_id if entry.content else None

                        if not account_id:
                            failed += 1
                            print_error(f"  [{succeeded + failed}/{len(entries_to_publish)}] 发布失败: 内容缺少账号信息")
                            publish_pool_service.fail_publishing(db, entry.id, "内容缺少账号信息")
                            progress.update(task, advance=1)
                            continue

                        # 开始发布
                        publish_pool_service.start_publishing(db, entry.id)

                        # 调用发布服务
                        publish_result = content_publisher_service.publish_to_wechat(
                            content_id=entry.content_id,
                            account_id=account_id,
                            publish_to_draft=True
                        )

                        # 创建发布日志
                        from app.models.publisher import PublishLog
                        publish_log = PublishLog(
                            account_id=account_id,
                            content_id=entry.content_id,
                            platform="wechat",
                            media_id=publish_result.get("media_id"),
                            status="success",
                            result=str(publish_result)
                        )
                        db.add(publish_log)
                        db.commit()
                        db.refresh(publish_log)

                        # 完成发布
                        publish_pool_service.complete_publishing(db, entry.id, publish_log.id)

                        succeeded += 1
                        print_success(f"  [{succeeded + failed}/{len(entries_to_publish)}] 发布成功: {content_title[:30]}")

                    except Exception as e:
                        failed += 1
                        print_error(f"  [{succeeded + failed}/{len(entries_to_publish)}] 发布失败: {content_title if entry.content else '未知'} - {str(e)}")
                        publish_pool_service.fail_publishing(db, entry.id, str(e))

                    progress.update(task, advance=1)

            # 显示统计信息
            print_success(f"\n批量发布完成")
            print_info(f"成功: {succeeded}, 失败: {failed}, 总计: {len(entries_to_publish)}")

            if failed > 0:
                print_warning("部分内容发布失败，已更新为失败状态，可以使用 publish-pool list 查看")

    except Exception as e:
        handle_error(e)


@app.command("clear")
def clear_pool():
    """清空发布池（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取所有条目
            entries = db.query(PublishPool).all()

            if not entries:
                print_warning("发布池为空")
                return

            # 按状态分组统计
            pending_count = sum(1 for e in entries if e.status == "pending")
            publishing_count = sum(1 for e in entries if e.status == "publishing")
            published_count = sum(1 for e in entries if e.status == "published")
            failed_count = sum(1 for e in entries if e.status == "failed")

            print_info(f"发布池统计:")
            print_info(f"  待发布: {pending_count}")
            print_info(f"  发布中: {publishing_count}")
            print_info(f"  已发布: {published_count}")
            print_info(f"  已失败: {failed_count}")
            print_info(f"  总计: {len(entries)}")

            # 确认清空
            if not confirm_action(
                f"确定要清空发布池吗？\n这将删除所有 {len(entries)} 条记录，不可逆！",
                default=False,
            ):
                print_info("已取消清空操作")
                return

            # 清空
            print_info(f"正在清空发布池...")
            for entry in entries:
                db.delete(entry)
            db.commit()

            print_success(f"发布池已清空 (删除了 {len(entries)} 条记录)")

    except Exception as e:
        handle_error(e)


@app.command("stats")
def pool_statistics(
    account_id: int = typer.Option(None, "--account-id", "-a", help="按账号 ID 筛选")
):
    """查看发布池统计"""
    try:
        with get_session_local()() as db:
            query = db.query(PublishPool).join(Content)

            if account_id:
                # 检查账号是否存在
                from app.models.account import Account
                account = db.query(Account).filter(Account.id == account_id).first()
                if not account:
                    print_error(f"账号不存在: ID {account_id}")
                    raise typer.Exit(1)
                query = query.filter(Content.account_id == account_id)

            total = query.count()
            pending = query.filter(PublishPool.status == "pending").count()
            publishing = query.filter(PublishPool.status == "publishing").count()
            published = query.filter(PublishPool.status == "published").count()
            failed = query.filter(PublishPool.status == "failed").count()

            # 显示统计信息
            stats_table = Table(title="发布池统计", show_header=True)
            stats_table.add_column("项目", style="cyan")
            stats_table.add_column("数量", style="green")
            stats_table.add_column("占比", style="yellow")

            if total > 0:
                stats_table.add_row("总计", str(total), "100%")
                stats_table.add_row("待发布", str(pending), f"{pending/total*100:.1f}%")
                stats_table.add_row("发布中", str(publishing), f"{publishing/total*100:.1f}%")
                stats_table.add_row("已发布", str(published), f"{published/total*100:.1f}%")
                stats_table.add_row("已失败", str(failed), f"{failed/total*100:.1f}%")
            else:
                stats_table.add_row("总计", "0", "-")
                stats_table.add_row("待发布", "0", "-")
                stats_table.add_row("发布中", "0", "-")
                stats_table.add_row("已发布", "0", "-")
                stats_table.add_row("已失败", "0", "-")

            from rich.console import Console
            console = Console()
            console.print(stats_table)

            # 优先级分布
            print_info("\n优先级分布:")
            priority_stats = {}
            for entry in query.all():
                priority = entry.priority
                if priority not in priority_stats:
                    priority_stats[priority] = 0
                priority_stats[priority] += 1

            if priority_stats:
                for priority in sorted(priority_stats.keys()):
                    count = priority_stats[priority]
                    print_info(f"  优先级 {priority}: {count} 条")

            # 按账号统计
            if account_id is None:
                print_info("\n按账号统计:")
                from sqlalchemy import func
                account_stats = db.query(
                    Content.account_id,
                    func.count(PublishPool.id).label('count')
                ).join(Content).group_by(Content.account_id).all()

                for acct_id, count in account_stats:
                    account = db.query(Account).filter(Account.id == acct_id).first()
                    account_name = account.name if account else f"账号{acct_id}"
                    print_info(f"  {account_name}: {count} 条")

    except Exception as e:
        handle_error(e)
