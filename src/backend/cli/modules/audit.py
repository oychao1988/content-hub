"""
审计日志模块

提供审计日志查询、导出和统计功能。
"""

import json
from datetime import datetime, date
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
    format_datetime,
    format_json,
    handle_error,
)
from app.db.sql_db import get_session_local
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService

# 创建子应用
app = typer.Typer(help="审计日志")


@app.command("logs")
def list_logs(
    event_type: str = typer.Option(None, "--event-type", "-e", help="事件类型"),
    user_id: int = typer.Option(None, "--user-id", "-u", help="用户 ID"),
    result: str = typer.Option(None, "--result", "-r", help="结果筛选 (success/failure)"),
    start_date: str = typer.Option(None, "--start", help="开始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", help="结束日期 (YYYY-MM-DD)"),
    search: str = typer.Option(None, "--search", "-s", help="搜索关键字"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量")
):
    """查询审计日志"""
    try:
        with get_session_local()() as db:
            # 构建过滤条件
            filters = {}
            if event_type:
                filters["event_type"] = event_type
            if user_id:
                filters["user_id"] = user_id
            if result:
                filters["result"] = result
            if start_date:
                filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d").date()
            if search:
                filters["search"] = search

            # 查询日志
            result_data = AuditService.get_audit_logs(
                db,
                filters=filters,
                page=page,
                page_size=page_size
            )

            logs = result_data["logs"]
            total = result_data["total"]

            if not logs:
                print_warning("未找到审计日志")
                return

            # 格式化输出
            data = []
            for log in logs:
                # 获取事件名称
                event_name = AuditService.EVENT_TYPES.get(log.event_type, log.event_type)

                # 格式化详细信息
                details_str = "-"
                if log.details:
                    if isinstance(log.details, dict):
                        # 提取关键信息
                        if "action" in log.details:
                            details_str = f"操作: {log.details['action']}"
                        elif "message" in log.details:
                            details_str = log.details["message"]
                        else:
                            details_str = f"{len(log.details)} 个字段"
                    else:
                        details_str = str(log.details)[:50]

                data.append({
                    "ID": log.id,
                    "时间": format_datetime(log.timestamp),
                    "事件": event_name,
                    "类型": log.event_type,
                    "用户ID": log.user_id or "-",
                    "IP": log.ip_address or "-",
                    "结果": "成功" if log.result == "success" else "失败",
                    "详情": details_str,
                })

            print_table(data, title=f"审计日志列表 (第 {page} 页，共 {total} 条)", show_header=True)

    except ValueError as e:
        print_error(f"日期格式错误: {e}")
        print_info("请使用 YYYY-MM-DD 格式")
    except Exception as e:
        handle_error(e)


@app.command("log-detail")
def log_detail(
    log_id: int = typer.Argument(..., help="日志 ID")
):
    """查看审计日志详情"""
    try:
        with get_session_local()() as db:
            log = AuditService.get_audit_log_by_id(db, log_id)
            if not log:
                print_error(f"审计日志不存在: ID {log_id}")
                raise typer.Exit(1)

            # 获取事件名称
            event_name = AuditService.EVENT_TYPES.get(log.event_type, log.event_type)

            # 显示基本信息
            info_table = Table(title="审计日志详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            info_table.add_row("日志 ID", str(log.id))
            info_table.add_row("时间", format_datetime(log.timestamp))
            info_table.add_row("事件名称", event_name)
            info_table.add_row("事件类型", log.event_type)
            info_table.add_row("用户 ID", str(log.user_id) if log.user_id else "-")
            info_table.add_row("IP 地址", log.ip_address or "-")
            info_table.add_row("User-Agent", log.user_agent or "-")
            info_table.add_row("结果", "成功" if log.result == "success" else "失败")
            info_table.add_row("创建时间", format_datetime(log.created_at))

            from rich.console import Console
            from rich.panel import Panel
            console = Console()
            console.print(info_table)

            # 显示详细信息
            if log.details:
                print_info("\n详细信息:")
                console.print(Panel(format_json(log.details), title="Details", style="blue"))
            else:
                print_info("\n详细信息: 无")

    except Exception as e:
        handle_error(e)


@app.command("export")
def export_logs(
    start_date: str = typer.Option(..., "--start", "-s", help="开始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end", "-e", help="结束日期 (YYYY-MM-DD)"),
    event_type: str = typer.Option(None, "--event-type", help="事件类型筛选"),
    user_id: int = typer.Option(None, "--user-id", help="用户 ID 筛选"),
    result: str = typer.Option(None, "--result", help="结果筛选 (success/failure)"),
    output_file: str = typer.Option(None, "--output", "-o", help="输出文件路径（可选）")
):
    """导出审计日志"""
    try:
        with get_session_local()() as db:
            # 解析日期
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

            print_info(f"正在导出审计日志 ({start} 至 {end})...")

            # 构建过滤条件
            filters = {}
            if event_type:
                filters["event_type"] = event_type
            if user_id:
                filters["user_id"] = user_id
            if result:
                filters["result"] = result

            # 导出日志
            logs = AuditService.export_audit_logs(db, start, end, filters)

            if not logs:
                print_warning("指定时间段内没有审计日志")
                return

            # 格式化为 JSON
            export_data = {
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "filters": filters,
                "total_count": len(logs),
                "logs": logs
            }

            json_str = format_json(export_data)

            # 输出或保存
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(json_str)
                print_success(f"审计日志已导出到: {output_file}")
                print_info(f"共导出 {len(logs)} 条记录")
            else:
                print_success(f"审计日志 (共 {len(logs)} 条):")
                print(json_str)

    except ValueError as e:
        print_error(f"日期格式错误: {e}")
        print_info("请使用 YYYY-MM-DD 格式")
    except Exception as e:
        handle_error(e)


@app.command("statistics")
def statistics(
    start_date: str = typer.Option(None, "--start", "-s", help="开始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", "-e", help="结束日期 (YYYY-MM-DD)")
):
    """查看审计统计信息"""
    try:
        with get_session_local()() as db:
            # 解析日期
            start = None
            end = None
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()

            print_info("正在生成审计统计...")

            # 获取统计信息
            stats = AuditService.get_audit_statistics(db, start, end)

            # 显示统计概览
            overview_table = Table(title="审计统计概览", show_header=True)
            overview_table.add_column("项目", style="cyan")
            overview_table.add_column("数量", style="green")

            period_str = f"({start_date} 至 {end_date})" if start_date and end_date else "(全部)"
            overview_table.add_row("统计周期", period_str)
            overview_table.add_row("日志总数", str(stats["total_logs"]))
            overview_table.add_row("成功操作", str(stats["success_count"]))
            overview_table.add_row("失败操作", str(stats["failure_count"]))
            overview_table.add_row("成功率", f"{stats['success_rate']}%")

            from rich.console import Console
            console = Console()
            console.print(overview_table)

            # 显示事件类型统计
            if stats["event_type_stats"]:
                print_info("\n事件类型统计:")
                event_table = Table(show_header=True)
                event_table.add_column("事件类型", style="cyan")
                event_table.add_column("事件名称", style="white")
                event_table.add_column("数量", style="green")

                for item in stats["event_type_stats"]:
                    event_table.add_row(
                        item["event_type"],
                        item["event_name"],
                        str(item["count"])
                    )

                console.print(event_table)

            # 显示活跃用户
            if stats["top_users"]:
                print_info("\n活跃用户 TOP 10:")
                user_table = Table(show_header=True)
                user_table.add_column("用户 ID", style="cyan")
                user_table.add_column("操作次数", style="green")

                for item in stats["top_users"]:
                    user_table.add_row(str(item["user_id"]), str(item["count"]))

                console.print(user_table)

    except ValueError as e:
        print_error(f"日期格式错误: {e}")
        print_info("请使用 YYYY-MM-DD 格式")
    except Exception as e:
        handle_error(e)


@app.command("user-activity")
def user_activity(
    user_id: int = typer.Argument(..., help="用户 ID"),
    days: int = typer.Option(7, "--days", "-d", help="统计天数"),
    limit: int = typer.Option(50, "--limit", "-l", help="显示记录数")
):
    """查看用户活动记录"""
    try:
        with get_session_local()() as db:
            print_info(f"正在查询用户活动 (用户 ID: {user_id})...")

            # 查询用户最近的操作
            from sqlalchemy import desc

            logs = db.query(AuditLog).filter(
                AuditLog.user_id == user_id
            ).order_by(
                desc(AuditLog.timestamp)
            ).limit(limit).all()

            if not logs:
                print_warning(f"用户 {user_id} 暂无活动记录")
                return

            # 格式化输出
            data = []
            for log in logs:
                event_name = AuditService.EVENT_TYPES.get(log.event_type, log.event_type)

                data.append({
                    "时间": format_datetime(log.timestamp),
                    "事件": event_name,
                    "类型": log.event_type,
                    "结果": "成功" if log.result == "success" else "失败",
                    "IP": log.ip_address or "-",
                })

            print_table(data, title=f"用户活动记录 (最近 {limit} 条)", show_header=True)

            # 统计信息
            total = len(logs)
            success = len([l for l in logs if l.result == "success"])
            failure = len([l for l in logs if l.result == "failure"])

            print_info(f"\n统计概览 (最近 {days} 天):")
            print_info(f"  总操作: {total} 次")
            print_info(f"  成功: {success} 次 ({success/total*100:.1f}%)" if total > 0 else "  成功: 0 次")
            print_info(f"  失败: {failure} 次 ({failure/total*100:.1f}%)" if total > 0 else "  失败: 0 次")

    except Exception as e:
        handle_error(e)
