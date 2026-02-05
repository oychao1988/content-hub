"""
定时任务模块

提供定时任务的创建、查询、更新、删除、执行、调度器管理等功能。
"""

from datetime import datetime
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
from app.models.scheduler import ScheduledTask, TaskExecution
from app.modules.scheduler.services import scheduler_manager_service
from app.services.scheduler_service import scheduler_service

# 创建子应用
app = typer.Typer(help="定时任务管理")


def get_task(db: Session, task_id: int) -> Optional[ScheduledTask]:
    """获取定时任务

    Args:
        db: 数据库会话
        task_id: 任务 ID

    Returns:
        任务对象或 None
    """
    return db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()


def list_tasks_db(
    db: Session,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[ScheduledTask]:
    """查询任务列表

    Args:
        db: 数据库会话
        status: 状态筛选
        task_type: 任务类型筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        任务列表
    """
    query = db.query(ScheduledTask)

    if status:
        if status == "active":
            query = query.filter(ScheduledTask.is_active == True)
        elif status == "inactive":
            query = query.filter(ScheduledTask.is_active == False)

    if task_type:
        query = query.filter(ScheduledTask.task_type == task_type)

    return query.order_by(ScheduledTask.created_at.desc()).offset(skip).limit(limit).all()


def format_task_info(task: ScheduledTask, detailed: bool = False) -> dict:
    """格式化任务信息

    Args:
        task: 任务对象
        detailed: 是否显示详细信息

    Returns:
        格式化的任务信息字典
    """
    info = {
        "ID": task.id,
        "名称": task.name,
        "类型": task.task_type,
        "启用": "是" if task.is_active else "否",
        "Cron表达式": task.cron_expression or "-",
        "上次运行": format_datetime(task.last_run_time),
        "下次运行": format_datetime(task.next_run_time),
        "创建时间": format_datetime(task.created_at),
    }

    if detailed:
        info.update({
            "描述": task.description or "-",
            "间隔时间": str(task.interval) if task.interval else "-",
            "间隔单位": task.interval_unit or "-",
            "更新时间": format_datetime(task.updated_at),
        })

    return info


@app.command("list")
def list_tasks(
    ctx: typer.Context,
    status: str = typer.Option(None, "--status", "-s", help="状态筛选 (active/inactive)"),
    type: str = typer.Option(None, "--type", "-t", help="任务类型筛选 (content_generation/publishing)"),
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    page_size: int = typer.Option(20, "--page-size", "--size", help="每页数量")
):
    """列出定时任务"""
    try:
        with get_session_local()() as db:
            # 计算分页
            skip = (page - 1) * page_size

            # 查询任务
            tasks = list_tasks_db(
                db,
                status=status,
                task_type=type,
                skip=skip,
                limit=page_size
            )

            # 格式化输出
            data = []
            for task in tasks:
                data.append({
                    "ID": task.id,
                    "名称": task.name,
                    "类型": task.task_type,
                    "启用": "是" if task.is_active else "否",
                    "Cron表达式": task.cron_expression or "-",
                    "上次运行": format_datetime(task.last_run_time),
                    "下次运行": format_datetime(task.next_run_time),
                    "创建时间": format_datetime(task.created_at),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not tasks:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到定时任务")
                return

            print_table(data, title=f"定时任务列表 (第 {page} 页，共 {len(tasks)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="任务名称"),
    type: str = typer.Option(..., "--type", "-t", help="任务类型 (content_generation/publishing)"),
    cron: str = typer.Option(None, "--cron", "-c", help="Cron 表达式"),
    account_id: int = typer.Option(None, "--account-id", "-a", help="账号 ID（如果需要）"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="是否启用"),
    description: str = typer.Option(None, "--description", "-d", help="任务描述")
):
    """创建定时任务"""
    try:
        with get_session_local()() as db:
            # 检查任务名称是否已存在
            existing = db.query(ScheduledTask).filter(ScheduledTask.name == name).first()
            if existing:
                print_error(f"任务名称已存在: {name}")
                raise typer.Exit(1)

            # 如果指定了账号 ID，检查账号是否存在
            if account_id:
                from app.models.account import Account
                account = db.query(Account).filter(Account.id == account_id).first()
                if not account:
                    print_error(f"账号不存在: ID {account_id}")
                    raise typer.Exit(1)

            # 准备任务数据
            task_data = {
                "name": name,
                "task_type": type,
                "description": description,
                "cron_expression": cron,
                "is_active": enabled,
            }

            # 创建任务
            print_info("正在创建定时任务...")
            task = scheduler_manager_service.create_task(db, task_data)

            print_success(f"定时任务创建成功 (ID: {task.id})")

            # 显示任务信息
            task_info = format_task_info(task, detailed=True)

            info_table = Table(title="任务详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in task_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def update(
    task_id: int = typer.Argument(..., help="任务 ID"),
    cron: str = typer.Option(None, "--cron", "-c", help="Cron 表达式"),
    enabled: bool = typer.Option(None, "--enabled/--disabled", help="是否启用"),
    name: str = typer.Option(None, "--name", "-n", help="任务名称")
):
    """更新定时任务"""
    try:
        with get_session_local()() as db:
            # 获取任务
            task = get_task(db, task_id)
            if not task:
                print_error(f"任务不存在: ID {task_id}")
                raise typer.Exit(1)

            # 准备更新数据
            update_data = {}
            if cron:
                update_data["cron_expression"] = cron
            if enabled is not None:
                update_data["is_active"] = enabled
            if name:
                # 检查新名称是否已被其他任务使用
                existing = db.query(ScheduledTask).filter(
                    ScheduledTask.name == name,
                    ScheduledTask.id != task_id
                ).first()
                if existing:
                    print_error(f"任务名称已被使用: {name}")
                    raise typer.Exit(1)
                update_data["name"] = name

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            # 更新任务
            print_info(f"正在更新任务 (ID: {task_id})...")
            task = scheduler_manager_service.update_task(db, task_id, update_data)

            print_success("任务更新成功")

            # 显示更新后的信息
            task_info = format_task_info(task, detailed=True)

            info_table = Table(title="任务详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in task_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def delete(
    task_id: int = typer.Argument(..., help="任务 ID")
):
    """删除定时任务（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取任务
            task = get_task(db, task_id)
            if not task:
                print_error(f"任务不存在: ID {task_id}")
                raise typer.Exit(1)

            # 确认删除
            if not confirm_action(
                f"确定要删除定时任务吗？\n任务名: {task.name}\n此操作不可逆！",
                default=False,
            ):
                print_info("已取消删除操作")
                return

            # 删除任务
            print_info(f"正在删除任务 (ID: {task_id})...")
            success = scheduler_manager_service.delete_task(db, task_id)

            if success:
                print_success(f"任务删除成功 (ID: {task_id})")
            else:
                print_error("删除失败")

    except Exception as e:
        handle_error(e)


@app.command()
def info(
    task_id: int = typer.Argument(..., help="任务 ID")
):
    """查看任务详情"""
    try:
        with get_session_local()() as db:
            # 获取任务
            task = get_task(db, task_id)
            if not task:
                print_error(f"任务不存在: ID {task_id}")
                raise typer.Exit(1)

            # 显示任务信息
            task_info = format_task_info(task, detailed=True)

            info_table = Table(title="任务详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in task_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

            # 显示执行历史（最近 5 条）
            executions = db.query(TaskExecution).filter(
                TaskExecution.task_id == task_id
            ).order_by(TaskExecution.start_time.desc()).limit(5).all()

            if executions:
                execution_data = []
                for exe in executions:
                    execution_data.append({
                        "执行ID": exe.id,
                        "状态": exe.status,
                        "开始时间": format_datetime(exe.start_time),
                        "耗时": f"{exe.duration}s" if exe.duration else "-",
                        "错误": exe.error_message[:30] + "..." if exe.error_message and len(exe.error_message) > 30 else exe.error_message or "-",
                    })

                print_table(execution_data, title="最近执行记录 (5 条)", show_header=True)

    except Exception as e:
        handle_error(e)


@app.command()
def trigger(
    task_id: int = typer.Argument(..., help="任务 ID")
):
    """手动触发任务"""
    try:
        with get_session_local()() as db:
            # 检查任务是否存在
            task = get_task(db, task_id)
            if not task:
                print_error(f"任务不存在: ID {task_id}")
                raise typer.Exit(1)

            print_info(f"正在手动触发任务 (ID: {task_id})...")

            # 触发任务
            result = scheduler_manager_service.trigger_task(db, task_id)

            if result.get("success"):
                print_success(f"任务执行成功")
                print_info(f"消息: {result.get('message', '')}")
            else:
                print_error(f"任务执行失败: {result.get('error', '未知错误')}")

    except Exception as e:
        handle_error(e)


@app.command("history")
def execution_history(
    task_id: int = typer.Option(None, "--task-id", "-t", help="任务 ID"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量")
):
    """查看任务执行历史"""
    try:
        with get_session_local()() as db:
            query = db.query(TaskExecution)

            if task_id:
                # 检查任务是否存在
                task = get_task(db, task_id)
                if not task:
                    print_error(f"任务不存在: ID {task_id}")
                    raise typer.Exit(1)
                query = query.filter(TaskExecution.task_id == task_id)

            executions = query.order_by(TaskExecution.start_time.desc()).limit(limit).all()

            if not executions:
                print_warning("未找到执行记录")
                return

            # 格式化输出
            data = []
            for exe in executions:
                task_name = exe.task.name if exe.task else "未知"
                data.append({
                    "执行ID": exe.id,
                    "任务": task_name,
                    "状态": exe.status,
                    "开始时间": format_datetime(exe.start_time),
                    "结束时间": format_datetime(exe.end_time),
                    "耗时": f"{exe.duration}s" if exe.duration else "-",
                })

            print_table(data, title=f"执行历史 (共 {len(executions)} 条)", show_header=True)

    except Exception as e:
        handle_error(e)


@app.command("start")
def start_scheduler():
    """启动调度器"""
    try:
        print_info("正在启动调度器...")

        result = scheduler_manager_service.start_scheduler()

        print_success(result.get("message", "调度器已启动"))

        # 显示调度器状态
        status = scheduler_manager_service.get_scheduler_status()
        print_info(f"运行状态: {'运行中' if status['running'] else '已停止'}")
        print_info(f"任务数量: {status['jobs_count']}")

    except Exception as e:
        handle_error(e)


@app.command("stop")
def stop_scheduler():
    """停止调度器"""
    try:
        print_info("正在停止调度器...")

        result = scheduler_manager_service.stop_scheduler()

        print_success(result.get("message", "调度器已停止"))

        # 显示调度器状态
        status = scheduler_manager_service.get_scheduler_status()
        print_info(f"运行状态: {'运行中' if status['running'] else '已停止'}")

    except Exception as e:
        handle_error(e)


@app.command("status")
def scheduler_status():
    """查看调度器状态"""
    try:
        status = scheduler_manager_service.get_scheduler_status()

        # 显示状态信息
        status_table = Table(title="调度器状态", show_header=True)
        status_table.add_column("项目", style="cyan")
        status_table.add_column("值", style="green")

        status_table.add_row("运行状态", "运行中" if status['running'] else "已停止")
        status_table.add_row("任务数量", str(status['jobs_count']))

        from rich.console import Console
        console = Console()
        console.print(status_table)

        # 如果调度器正在运行，显示所有任务
        if status['running']:
            print_info("\n调度器任务列表:")
            jobs = scheduler_service.scheduler.get_jobs()
            if jobs:
                for job in jobs:
                    print_info(f"  - {job.name} (下次运行: {job.next_run_time})")
            else:
                print_warning("  暂无任务")

    except Exception as e:
        handle_error(e)


@app.command("pause")
def pause_task(
    task_id: int = typer.Argument(..., help="任务 ID")
):
    """暂停任务"""
    try:
        with get_session_local()() as db:
            # 获取任务
            task = get_task(db, task_id)
            if not task:
                print_error(f"任务不存在: ID {task_id}")
                raise typer.Exit(1)

            if not task.is_active:
                print_warning("任务已处于暂停状态")
                return

            # 更新任务状态
            task = scheduler_manager_service.update_task(db, task_id, {"is_active": False})

            print_success(f"任务已暂停 (ID: {task_id})")
            print_info(f"任务名称: {task.name}")

    except Exception as e:
        handle_error(e)


@app.command("resume")
def resume_task(
    task_id: int = typer.Argument(..., help="任务 ID")
):
    """恢复任务"""
    try:
        with get_session_local()() as db:
            # 获取任务
            task = get_task(db, task_id)
            if not task:
                print_error(f"任务不存在: ID {task_id}")
                raise typer.Exit(1)

            if task.is_active:
                print_warning("任务已处于启用状态")
                return

            # 更新任务状态
            task = scheduler_manager_service.update_task(db, task_id, {"is_active": True})

            print_success(f"任务已恢复 (ID: {task_id})")
            print_info(f"任务名称: {task.name}")

    except Exception as e:
        handle_error(e)
