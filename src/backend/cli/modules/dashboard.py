"""
仪表盘模块

提供系统统计数据和趋势分析功能。
"""

from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.table import Table
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from cli.utils import (
    print_info,
    print_success,
    print_warning,
    print_error,
    print_table,
    format_datetime,
    handle_error,
)
from app.db.sql_db import get_session_local
from app.models.content import Content
from app.models.publisher import PublishLog
from app.models.account import Account
from app.models.scheduler import ScheduledTask
from app.models.user import User
from app.models.customer import Customer

# 创建子应用
app = typer.Typer(help="仪表盘统计")


@app.command("stats")
def dashboard_stats():
    """显示仪表盘统计数据"""
    try:
        with get_session_local()() as db:
            print_info("正在获取仪表盘统计数据...")

            # 账号统计
            account_count = db.query(Account).count()
            active_account_count = db.query(Account).filter(Account.is_active == True).count()

            # 内容统计
            content_count = db.query(Content).count()
            pending_review_count = db.query(Content).filter(Content.review_status == "pending").count()
            approved_count = db.query(Content).filter(Content.review_status == "approved").count()

            # 发布统计
            published_count = db.query(PublishLog).filter(PublishLog.status == "success").count()

            # 今日发布数
            today = datetime.utcnow().date()
            today_published_count = db.query(PublishLog).filter(
                func.date(PublishLog.created_at) == today,
                PublishLog.status == "success"
            ).count()

            # 本周发布数
            week_ago = datetime.utcnow() - timedelta(days=7)
            week_published_count = db.query(PublishLog).filter(
                PublishLog.created_at >= week_ago,
                PublishLog.status == "success"
            ).count()

            # 定时任务统计
            scheduled_task_count = db.query(ScheduledTask).filter(
                ScheduledTask.is_active == True
            ).count()

            # 用户和客户统计
            user_count = db.query(User).count()
            customer_count = db.query(Customer).count()

            # 显示统计表格
            stats_table = Table(title="仪表盘统计", show_header=True)
            stats_table.add_column("项目", style="cyan")
            stats_table.add_column("数量", style="green")
            stats_table.add_column("说明", style="dim")

            # 账号部分
            stats_table.add_row("账号总数", str(account_count), "系统中的所有账号")
            stats_table.add_row("激活账号", str(active_account_count), "当前激活的账号")
            stats_table.add_row("", "", "")  # 空行

            # 内容部分
            stats_table.add_row("内容总数", str(content_count), "生成的所有内容")
            stats_table.add_row("待审核", str(pending_review_count), "等待审核的内容")
            stats_table.add_row("已审核", str(approved_count), "通过审核的内容")
            stats_table.add_row("", "", "")  # 空行

            # 发布部分
            stats_table.add_row("发布成功", str(published_count), "累计成功发布次数")
            stats_table.add_row("今日发布", str(today_published_count), "今日成功发布次数")
            stats_table.add_row("本周发布", str(week_published_count), "本周成功发布次数")
            stats_table.add_row("", "", "")  # 空行

            # 其他部分
            stats_table.add_row("定时任务", str(scheduled_task_count), "激活的定时任务")
            stats_table.add_row("用户总数", str(user_count), "系统用户数")
            stats_table.add_row("客户总数", str(customer_count), "系统客户数")

            from rich.console import Console
            console = Console()
            console.print(stats_table)

    except Exception as e:
        handle_error(e)


@app.command("activities")
def recent_activities(
    limit: int = typer.Option(20, "--limit", "-l", help="显示记录数")
):
    """显示最近的活动记录"""
    try:
        with get_session_local()() as db:
            print_info(f"正在获取最近活动记录 (最近 {limit} 条)...")

            # 合并多种活动的最近记录
            activities = []

            # 最近创建的内容
            contents = db.query(Content).order_by(desc(Content.created_at)).limit(limit // 4).all()
            for content in contents:
                account_name = content.account.name if content.account else "未知"
                activities.append({
                    "时间": format_datetime(content.created_at),
                    "类型": "内容创建",
                    "描述": f"账号 {account_name} 创建了内容",
                    "状态": content.review_status,
                })

            # 最近发布的记录
            publishes = db.query(PublishLog).order_by(desc(PublishLog.created_at)).limit(limit // 4).all()
            for pub in publishes:
                platform = pub.platform or "未知"
                status_text = "成功" if pub.status == "success" else "失败"
                activities.append({
                    "时间": format_datetime(pub.created_at),
                    "类型": "内容发布",
                    "描述": f"发布到 {platform} - {status_text}",
                    "状态": pub.status,
                })

            # 最近创建的账号
            accounts = db.query(Account).order_by(desc(Account.created_at)).limit(limit // 4).all()
            for acc in accounts:
                customer_name = acc.customer.name if acc.customer else "未知"
                platform_name = acc.platform.name if acc.platform else "未知"
                activities.append({
                    "时间": format_datetime(acc.created_at),
                    "类型": "账号创建",
                    "描述": f"客户 {customer_name} 在 {platform_name} 创建账号 {acc.name}",
                    "状态": "激活" if acc.is_active else "停用",
                })

            # 最近创建的用户
            users = db.query(User).order_by(desc(User.created_at)).limit(limit // 4).all()
            for user in users:
                customer_name = user.customer.name if user.customer else "未知"
                activities.append({
                    "时间": format_datetime(user.created_at),
                    "类型": "用户创建",
                    "描述": f"客户 {customer_name} 创建用户 {user.username}",
                    "状态": "激活" if user.is_active else "停用",
                })

            # 按时间排序并限制数量
            activities.sort(key=lambda x: x["时间"], reverse=True)
            activities = activities[:limit]

            if not activities:
                print_warning("暂无活动记录")
                return

            # 格式化输出
            data = []
            for activity in activities:
                data.append({
                    "时间": activity["时间"],
                    "类型": activity["类型"],
                    "描述": activity["描述"],
                    "状态": activity["状态"],
                })

            print_table(data, title=f"最近活动 (最近 {limit} 条)", show_header=True)

    except Exception as e:
        handle_error(e)


@app.command("content-trend")
def content_trend(
    days: int = typer.Option(30, "--days", "-d", help="统计天数")
):
    """显示内容生成趋势"""
    try:
        with get_session_local()() as db:
            print_info(f"正在分析内容生成趋势 (最近 {days} 天)...")

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # 按天统计内容创建数量
            content_trend = db.query(
                func.date(Content.created_at).label("date"),
                func.count(Content.id).label("count")
            ).filter(
                Content.created_at >= start_date
            ).group_by(
                func.date(Content.created_at)
            ).order_by(
                func.date(Content.created_at)
            ).all()

            if not content_trend:
                print_warning(f"最近 {days} 天没有内容生成记录")
                return

            # 计算统计信息
            total_count = sum(item.count for item in content_trend)
            avg_count = total_count / len(content_trend) if content_trend else 0
            max_count = max(item.count for item in content_trend) if content_trend else 0
            min_count = min(item.count for item in content_trend) if content_trend else 0

            # 显示趋势表格
            trend_table = Table(title=f"内容生成趋势 (最近 {days} 天)", show_header=True)
            trend_table.add_column("日期", style="cyan")
            trend_table.add_column("数量", style="green")
            trend_table.add_column("占比", style="yellow")

            for item in content_trend:
                percentage = (item.count / total_count * 100) if total_count > 0 else 0
                trend_table.add_row(
                    str(item.date),
                    str(item.count),
                    f"{percentage:.1f}%"
                )

            from rich.console import Console
            console = Console()
            console.print(trend_table)

            # 显示统计摘要
            print_info(f"\n统计摘要:")
            print_info(f"  总计: {total_count} 篇内容")
            print_info(f"  平均: {avg_count:.1f} 篇/天")
            print_info(f"  最高: {max_count} 篇/天")
            print_info(f"  最低: {min_count} 篇/天")

    except Exception as e:
        handle_error(e)


@app.command("publish-stats")
def publish_statistics():
    """显示发布统计信息"""
    try:
        with get_session_local()() as db:
            print_info("正在获取发布统计信息...")

            # 总体统计
            total_publish = db.query(PublishLog).count()
            success_publish = db.query(PublishLog).filter(PublishLog.status == "success").count()
            failed_publish = db.query(PublishLog).filter(PublishLog.status == "failed").count()
            pending_publish = db.query(PublishLog).filter(PublishLog.status == "pending").count()

            success_rate = (success_publish / total_publish * 100) if total_publish > 0 else 0

            # 显示总体统计
            overview_table = Table(title="发布统计概览", show_header=True)
            overview_table.add_column("项目", style="cyan")
            overview_table.add_column("数量", style="green")
            overview_table.add_column("占比", style="yellow")

            overview_table.add_row("总发布数", str(total_publish), "100%")
            overview_table.add_row("发布成功", str(success_publish), f"{success_rate:.1f}%")
            overview_table.add_row("发布失败", str(failed_publish), f"{failed_publish/total_publish*100:.1f}%" if total_publish > 0 else "0%")
            overview_table.add_row("待发布", str(pending_publish), f"{pending_publish/total_publish*100:.1f}%" if total_publish > 0 else "0%")

            from rich.console import Console
            console = Console()
            console.print(overview_table)

            # 按平台统计
            from sqlalchemy import case
            print_info("\n按平台统计:")
            platform_stats = db.query(
                PublishLog.platform,
                func.count(PublishLog.id).label("count"),
                func.sum(case((PublishLog.status == "success", 1), else_=0)).label("success_count")
            ).group_by(
                PublishLog.platform
            ).all()

            if platform_stats:
                platform_table = Table(show_header=True)
                platform_table.add_column("平台", style="cyan")
                platform_table.add_column("发布数", style="green")
                platform_table.add_column("成功数", style="yellow")
                platform_table.add_column("成功率", style="blue")

                for item in platform_stats:
                    success_count = item.success_count or 0
                    rate = (success_count / item.count * 100) if item.count > 0 else 0
                    platform_table.add_row(
                        item.platform or "未知",
                        str(item.count),
                        str(success_count),
                        f"{rate:.1f}%"
                    )

                console.print(platform_table)

    except Exception as e:
        handle_error(e)


@app.command("user-stats")
def user_statistics(
    limit: int = typer.Option(10, "--limit", "-l", help="显示用户数")
):
    """显示用户统计信息"""
    try:
        with get_session_local()() as db:
            print_info("正在获取用户统计信息...")

            # 总用户数
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()

            # 按客户统计用户
            customer_stats = db.query(
                Customer.name,
                func.count(User.id).label("user_count")
            ).outerjoin(
                User, Customer.id == User.customer_id
            ).group_by(
                Customer.id, Customer.name
            ).order_by(
                desc("user_count")
            ).limit(limit).all()

            # 显示总体统计
            overview_table = Table(title="用户统计概览", show_header=True)
            overview_table.add_column("项目", style="cyan")
            overview_table.add_column("数量", style="green")

            overview_table.add_row("总用户数", str(total_users))
            overview_table.add_row("激活用户", str(active_users))
            overview_table.add_row("停用用户", str(total_users - active_users))

            from rich.console import Console
            console = Console()
            console.print(overview_table)

            # 按客户统计
            if customer_stats:
                print_info(f"\n按客户统计 (TOP {limit}):")
                customer_table = Table(show_header=True)
                customer_table.add_column("客户", style="cyan")
                customer_table.add_column("用户数", style="green")

                for item in customer_stats:
                    customer_table.add_row(item.name or "未分配", str(item.user_count))

                console.print(customer_table)

    except Exception as e:
        handle_error(e)


@app.command("customer-stats")
def customer_statistics(
    limit: int = typer.Option(10, "--limit", "-l", help="显示客户数")
):
    """显示客户统计信息"""
    try:
        with get_session_local()() as db:
            print_info("正在获取客户统计信息...")

            # 总客户数
            total_customers = db.query(Customer).count()
            active_customers = db.query(Customer).filter(Customer.is_active == True).count()

            # 每个客户的账号和内容统计
            customer_stats = []
            customers = db.query(Customer).all()

            for customer in customers:
                account_count = db.query(Account).filter(Account.customer_id == customer.id).count()

                # 内容统计
                content_count = db.query(Content).join(Account).filter(
                    Account.customer_id == customer.id
                ).count()

                # 发布统计
                publish_count = db.query(PublishLog).join(Account).filter(
                    Account.customer_id == customer.id,
                    PublishLog.status == "success"
                ).count()

                customer_stats.append({
                    "customer": customer,
                    "account_count": account_count,
                    "content_count": content_count,
                    "publish_count": publish_count,
                })

            # 按内容数量排序
            customer_stats.sort(key=lambda x: x["content_count"], reverse=True)

            # 显示总体统计
            overview_table = Table(title="客户统计概览", show_header=True)
            overview_table.add_column("项目", style="cyan")
            overview_table.add_column("数量", style="green")

            overview_table.add_row("总客户数", str(total_customers))
            overview_table.add_row("激活客户", str(active_customers))
            overview_table.add_row("停用客户", str(total_customers - active_customers))

            from rich.console import Console
            console = Console()
            console.print(overview_table)

            # 客户详细统计
            if customer_stats:
                print_info(f"\n客户详细统计 (TOP {limit}):")
                detail_table = Table(show_header=True)
                detail_table.add_column("客户", style="cyan")
                detail_table.add_column("状态", style="white")
                detail_table.add_column("账号数", style="green")
                detail_table.add_column("内容数", style="yellow")
                detail_table.add_column("发布数", style="blue")

                for item in customer_stats[:limit]:
                    c = item["customer"]
                    status = "激活" if c.is_active else "停用"
                    detail_table.add_row(
                        c.name,
                        status,
                        str(item["account_count"]),
                        str(item["content_count"]),
                        str(item["publish_count"])
                    )

                console.print(detail_table)

    except Exception as e:
        handle_error(e)
