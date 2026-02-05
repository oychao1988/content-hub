"""
数据库管理模块

提供数据库初始化、备份、恢复等功能。
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table
from sqlalchemy import inspect, text

from cli.utils import (
    print_info,
    print_success,
    print_warning,
    print_error,
    print_table,
    confirm_action,
    format_datetime,
    get_global_format,
    handle_error,
)
from app.db.sql_db import get_engine, get_session_local, init_db
from app.core.config import settings

# 创建子应用
app = typer.Typer(help="数据库管理")


def get_db_path() -> str:
    """获取数据库文件路径"""
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite:///"):
        return settings.DATABASE_URL.replace("sqlite:///", "", 1)
    return ""


def get_db_size() -> int:
    """获取数据库文件大小（字节）"""
    db_path = get_db_path()
    if os.path.exists(db_path):
        return os.path.getsize(db_path)
    return 0


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


@app.command()
def init():
    """初始化数据库"""
    try:
        print_info("正在初始化数据库...")
        init_db()
        print_success("数据库初始化成功")
    except Exception as e:
        handle_error(e)


@app.command()
def reset():
    """重置数据库（危险操作）"""
    db_path = get_db_path()

    if not db_path:
        print_error("无法确定数据库路径")
        raise typer.Exit(1)

    if not os.path.exists(db_path):
        print_warning("数据库文件不存在，无需重置")
        return

    # 确认操作
    if not confirm_action(
        f"确定要删除所有数据并重置数据库吗？\n数据库文件: {db_path}\n此操作不可逆！",
        default=False,
    ):
        print_info("已取消重置操作")
        return

    try:
        # 删除数据库文件
        os.remove(db_path)
        print_success("数据库文件已删除")

        # 重新初始化
        print_info("正在重新初始化数据库...")
        init_db()
        print_success("数据库重置成功")
    except Exception as e:
        handle_error(e)


@app.command()
def backup(
    output_path: str = typer.Argument(
        None,
        help="备份文件输出路径（默认：./data/backups/contenthub_<timestamp>.db）"
    )
):
    """备份数据库"""
    db_path = get_db_path()

    if not db_path:
        print_error("无法确定数据库路径")
        raise typer.Exit(1)

    if not os.path.exists(db_path):
        print_error(f"数据库文件不存在: {db_path}")
        raise typer.Exit(1)

    try:
        # 确定备份路径
        if output_path:
            backup_path = output_path
        else:
            # 创建备份目录
            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"contenthub_{timestamp}.db")

        # 复制数据库文件
        print_info(f"正在备份数据库到: {backup_path}")
        shutil.copy2(db_path, backup_path)

        # 显示备份信息
        backup_size = format_size(os.path.getsize(backup_path))
        print_success(f"数据库备份成功")
        print_info(f"备份文件: {backup_path}")
        print_info(f"备份大小: {backup_size}")

    except Exception as e:
        handle_error(e)


@app.command()
def restore(
    backup_file: str = typer.Argument(..., help="备份文件路径")
):
    """恢复数据库"""
    db_path = get_db_path()

    if not db_path:
        print_error("无法确定数据库路径")
        raise typer.Exit(1)

    if not os.path.exists(backup_file):
        print_error(f"备份文件不存在: {backup_file}")
        raise typer.Exit(1)

    # 确认操作
    if os.path.exists(db_path):
        if not confirm_action(
            f"确定要从备份恢复数据库吗？\n当前数据库将被覆盖！\n备份文件: {backup_file}",
            default=False,
        ):
            print_info("已取消恢复操作")
            return

    try:
        print_info(f"正在从备份恢复数据库: {backup_file}")

        # 确保目标目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 复制备份文件
        shutil.copy2(backup_file, db_path)

        # 显示恢复信息
        restored_size = format_size(os.path.getsize(db_path))
        print_success("数据库恢复成功")
        print_info(f"数据库文件: {db_path}")
        print_info(f"恢复大小: {restored_size}")

    except Exception as e:
        handle_error(e)


@app.command()
def migrate():
    """运行数据库迁移"""
    print_warning("暂无待执行的迁移")
    print_info("当前使用 SQLAlchemy 自动迁移，无需手动执行迁移命令")


@app.command()
def rollback(
    steps: int = typer.Option(1, "--steps", "-s", help="回滚步数")
):
    """回滚迁移"""
    print_warning("暂无可回滚的迁移")
    print_info("当前使用 SQLAlchemy 自动迁移，如需回滚请使用 db reset 命令")


@app.command()
def shell():
    """进入数据库 shell（SQLite）"""
    db_path = get_db_path()

    if not db_path:
        print_error("仅支持 SQLite 数据库")
        raise typer.Exit(1)

    if not os.path.exists(db_path):
        print_error(f"数据库文件不存在: {db_path}")
        raise typer.Exit(1)

    try:
        print_info(f"正在启动 SQLite shell...")
        print_info(f"数据库: {db_path}")
        print_info("输入 '.quit' 或 Ctrl+D 退出\n")

        # 调用 sqlite3 命令
        subprocess.run(["sqlite3", db_path])

    except FileNotFoundError:
        print_error("未找到 sqlite3 命令，请先安装 SQLite")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        print_info("\n已退出 SQLite shell")


@app.command()
def info(ctx: typer.Context):
    """显示数据库信息"""
    db_path = get_db_path()

    if not db_path:
        print_error("无法确定数据库路径")
        raise typer.Exit(1)

    # 获取数据库基本信息
    db_exists = os.path.exists(db_path)
    db_size = get_db_size() if db_exists else 0

    # 获取表信息
    table_count = 0
    table_names = []
    if db_exists:
        try:
            engine = get_engine()
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            table_count = len(table_names)
        except Exception as e:
            print_warning(f"无法获取表信息: {e}")

    # 获取全局输出格式
    output_format = get_global_format(ctx)

    # 准备数据
    data = {
        "数据库路径": db_path,
        "数据库状态": "存在" if db_exists else "不存在",
        "数据库大小": format_size(db_size),
        "数据库类型": "SQLite",
        "表数量": table_count,
        "数据表": sorted(table_names) if table_names else [],
    }

    if output_format == "json":
        import json
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    elif output_format == "csv":
        # CSV 格式不适合输出嵌套结构，使用简化版本
        flat_data = [
            {"项目": "数据库路径", "值": db_path},
            {"项目": "数据库状态", "值": "存在" if db_exists else "不存在"},
            {"项目": "数据库大小", "值": format_size(db_size)},
            {"项目": "数据库类型", "值": "SQLite"},
            {"项目": "表数量", "值": str(table_count)},
        ]
        print_table(flat_data, output_format="csv")
        if table_names:
            for table in sorted(table_names):
                typer.echo(f"  • {table}")
    else:  # table
        # 显示信息
        info_table = Table(title="数据库信息", show_header=True, header_style="bold magenta")
        info_table.add_column("项目", style="cyan")
        info_table.add_column("值", style="green")

        info_table.add_row("数据库路径", db_path)
        info_table.add_row("数据库状态", "✅ 存在" if db_exists else "❌ 不存在")
        info_table.add_row("数据库大小", format_size(db_size))
        info_table.add_row("数据库类型", "SQLite")
        info_table.add_row("表数量", str(table_count))

        from rich.console import Console
        console = Console()
        console.print(info_table)

        if table_names:
            print_info("数据表:")
            for table in sorted(table_names):
                print(f"  • {table}")


@app.command()
def stats(ctx: typer.Context):
    """数据库统计信息"""
    try:
        engine = get_engine()
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        if not table_names:
            print_warning("数据库中没有任何表")
            return

        # 获取每个表的记录数
        stats_data = []
        with get_session_local()() as db:
            for table_name in sorted(table_names):
                try:
                    # 使用 text() 包装原生 SQL 查询记录数
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    stats_data.append({
                        "表名": table_name,
                        "记录数": count,
                    })
                except Exception as e:
                    stats_data.append({
                        "表名": table_name,
                        "记录数": f"查询失败: {e}",
                    })

        # 计算总计
        total_records = sum(
            item["记录数"] if isinstance(item["记录数"], int) else 0
            for item in stats_data
        )

        # 获取全局输出格式
        output_format = get_global_format(ctx)

        if output_format == "json":
            import json
            result = {
                "表统计": stats_data,
                "总计": {
                    "表数量": len(table_names),
                    "记录总数": total_records
                }
            }
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif output_format == "csv":
            print_table(stats_data, title=f"数据库统计信息 (总计: {len(table_names)} 个表, {total_records} 条记录)", show_header=True, output_format="csv")
        else:  # table
            # 显示统计信息
            print_table(stats_data, title="数据库统计信息", show_header=True, output_format="table")
            # 显示总计
            print_info(f"总计: {len(table_names)} 个表, {total_records} 条记录")

    except Exception as e:
        handle_error(e)
