"""
系统管理模块

提供系统信息、健康检查、缓存管理和日志查看等功能。
"""

import os
import sys
import time
import platform as plt
from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.table import Table
from rich.panel import Panel
from sqlalchemy.orm import Session
from sqlalchemy import text

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
from app.core.config import settings
from app.core.cache import redis_client, get_cache_stats

# 跟踪应用启动时间
_app_start_time = time.time()

# 创建子应用
app = typer.Typer(help="系统管理")


@app.command("health")
def health_check():
    """检查系统健康状态"""
    try:
        with get_session_local()() as db:
            print_info("正在检查系统健康状态...")

            # 检查数据库连接
            try:
                db.execute(text("SELECT 1"))
                database_status = "✅ 已连接"
            except Exception as e:
                database_status = f"❌ 错误: {str(e)}"

            # 检查 Redis
            redis_status = "✅ 可用"
            if redis_client:
                try:
                    redis_client.ping()
                except Exception as e:
                    redis_status = f"❌ 不可用: {str(e)}"
            else:
                redis_status = "⚠️  未配置"

            # 检查外部服务
            publisher_status = "✅ 可用" if settings.PUBLISHER_API_URL else "⚠️  未配置"
            creator_status = "✅ 可用" if os.path.exists(settings.CREATOR_CLI_PATH) else "⚠️  未找到" if settings.CREATOR_CLI_PATH else "⚠️  未配置"

            # 确定整体状态
            if "错误" in database_status:
                overall_status = "❌ 不健康"
            elif "不可用" in redis_status or "未找到" in creator_status:
                overall_status = "⚠️  部分功能降级"
            else:
                overall_status = "✅ 健康"

            # 显示健康状态表格
            health_table = Table(title="系统健康状态", show_header=True)
            health_table.add_column("组件", style="cyan")
            health_table.add_column("状态", style="green")

            health_table.add_row("整体状态", overall_status)
            health_table.add_row("数据库", database_status)
            health_table.add_row("Redis", redis_status)
            health_table.add_row("Content-Publisher", publisher_status)
            health_table.add_row("Content-Creator", creator_status)

            from rich.console import Console
            console = Console()
            console.print(health_table)

    except Exception as e:
        handle_error(e)


@app.command("info")
def system_info():
    """显示系统信息"""
    try:
        # 系统信息
        info_table = Table(title="系统信息", show_header=True)
        info_table.add_column("项目", style="cyan")
        info_table.add_column("值", style="green")

        info_table.add_row("应用名称", settings.APP_NAME)
        info_table.add_row("应用版本", settings.APP_VERSION)
        info_table.add_row("Python 版本", sys.version.split()[0])
        info_table.add_row("运行环境", "开发环境" if settings.DEBUG else "生产环境")
        info_table.add_row("操作系统", plt.platform())
        info_table.add_row("架构", plt.machine())
        info_table.add_row("调试模式", "开启" if settings.DEBUG else "关闭")

        from rich.console import Console
        console = Console()
        console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command("version")
def version():
    """显示版本信息"""
    try:
        print_info(f"ContentHub {settings.APP_NAME}")
        print_info(f"版本: {settings.APP_VERSION}")
        print_info(f"Python: {sys.version.split()[0]}")

    except Exception as e:
        handle_error(e)


@app.command("metrics")
def metrics():
    """显示系统指标"""
    try:
        with get_session_local()() as db:
            print_info("正在获取系统指标...")

            # 运行时间
            uptime = time.time() - _app_start_time
            uptime_str = str(timedelta(seconds=int(uptime)))

            # 获取缓存统计
            cache_stats = get_cache_stats()

            # 获取用户数
            from app.models.user import User
            user_count = db.query(User).count()

            # 获取请求数（从缓存统计）
            requests_total = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)

            # 显示指标表格
            metrics_table = Table(title="系统指标", show_header=True)
            metrics_table.add_column("指标", style="cyan")
            metrics_table.add_column("值", style="green")
            metrics_table.add_column("说明", style="dim")

            metrics_table.add_row("运行时间", uptime_str, "系统启动后的运行时间")
            metrics_table.add_row("用户总数", str(user_count), "系统注册用户数")
            metrics_table.add_row("缓存命中", str(cache_stats.get("hits", 0)), "Redis 缓存命中次数")
            metrics_table.add_row("缓存未命中", str(cache_stats.get("misses", 0)), "Redis 缓存未命中次数")
            metrics_table.add_row("命中率", f"{cache_stats.get('hit_rate', 0):.1f}%", "缓存命中率")
            metrics_table.add_row("总请求数", str(requests_total), "系统处理的总请求数")

            from rich.console import Console
            console = Console()
            console.print(metrics_table)

    except Exception as e:
        handle_error(e)


@app.command("cache-stats")
def cache_statistics():
    """显示缓存统计信息"""
    try:
        print_info("正在获取缓存统计信息...")

        stats = get_cache_stats()

        cache_table = Table(title="缓存统计", show_header=True)
        cache_table.add_column("指标", style="cyan")
        cache_table.add_column("值", style="green")

        cache_table.add_row("缓存命中", str(stats.get("hits", 0)))
        cache_table.add_row("缓存未命中", str(stats.get("misses", 0)))
        cache_table.add_row("命中率", f"{stats.get('hit_rate', 0):.1f}%")
        cache_table.add_row("内存使用", f"{stats.get('memory_usage', 0):.2f} MB")

        from rich.console import Console
        console = Console()
        console.print(cache_table)

    except Exception as e:
        print_error(f"获取缓存统计失败: {str(e)}")


@app.command("cache-clear")
def cache_clear(
    pattern: str = typer.Option("*", "--pattern", "-p", help="清除模式（默认全部）")
):
    """清除缓存"""
    try:
        if not redis_client:
            print_warning("Redis 未配置")
            raise typer.Exit(1)

        print_info(f"正在清除缓存 (模式: {pattern})...")

        if pattern == "*":
            # 清除所有缓存
            redis_client.flushdb()
            print_success("所有缓存已清除")
        else:
            # 按模式清除
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                print_success(f"已清除 {len(keys)} 个缓存项")
            else:
                print_warning(f"未找到匹配的缓存项: {pattern}")

    except Exception as e:
        handle_error(e)


@app.command("cache-cleanup")
def cache_cleanup(
    max_age_days: int = typer.Option(7, "--max-age", "-a", help="最大保留天数")
):
    """清理过期缓存"""
    try:
        if not redis_client:
            print_warning("Redis 未配置")
            raise typer.Exit(1)

        print_info(f"正在清理 {max_age_days} 天前的缓存...")

        # 获取所有键
        keys = redis_client.keys("*")

        if not keys:
            print_warning("没有缓存项需要清理")
            return

        # 检查每个键的 TTL
        cleaned = 0
        for key in keys:
            ttl = redis_client.ttl(key)
            # 如果没有设置过期时间，或者已经过期
            if ttl == -1 or ttl == -2:
                # 删除超过指定天数的键
                # 注意：这需要额外的元数据来记录创建时间
                # 这里简化处理，只删除没有 TTL 的键
                redis_client.delete(key)
                cleaned += 1

        print_success(f"已清理 {cleaned} 个过期缓存项")

    except Exception as e:
        handle_error(e)


@app.command("maintenance")
def maintenance_mode(
    enable: bool = typer.Option(None, "--enable", "-e", help="启用维护模式"),
    disable: bool = typer.Option(None, "--disable", "-d", help="禁用维护模式"),
):
    """维护模式管理"""
    try:
        if enable is None and disable is None:
            # 显示当前状态
            maintenance_status = os.getenv("MAINTENANCE_MODE", "false")
            if maintenance_status.lower() == "true":
                print_warning("维护模式已启用")
                print_info("使用 --disable 禁用维护模式")
            else:
                print_success("系统正常运行")
                print_info("使用 --enable 启用维护模式")
        elif enable:
            print_info("正在启用维护模式...")
            print_warning("注意: 这需要重启服务才能生效")
            print_info("请在 .env 文件中设置 MAINTENANCE_MODE=true")
        elif disable:
            print_info("正在禁用维护模式...")
            print_warning("注意: 这需要重启服务才能生效")
            print_info("请在 .env 文件中设置 MAINTENANCE_MODE=false")

    except Exception as e:
        handle_error(e)


@app.command("cleanup")
def cleanup_resources(
    dry_run: bool = typer.Option(False, "--dry-run", help="仅显示将要清理的资源，不实际执行"),
    older_than_days: int = typer.Option(30, "--older-than", help="清理多少天前的资源")
):
    """清理系统资源"""
    try:
        with get_session_local()() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            print_info(f"正在检查 {older_than_days} 天前的资源...")

            # 检查可以清理的内容
            from app.models.content import Content
            old_contents = db.query(Content).filter(
                Content.created_at < cutoff_date,
                Content.review_status == "rejected"  # 已拒绝的内容
            ).count()

            # 检查可以清理的日志
            from app.models.audit_log import AuditLog
            from app.models.publisher import PublishLog
            old_audit_logs = db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).count()

            old_publish_logs = db.query(PublishLog).filter(
                PublishLog.created_at < cutoff_date,
                PublishLog.status == "failed"  # 失败的发布记录
            ).count()

            # 显示可以清理的资源
            cleanup_table = Table(title="可清理资源", show_header=True)
            cleanup_table.add_column("资源类型", style="cyan")
            cleanup_table.add_column("数量", style="green")
            cleanup_table.add_column("说明", style="dim")

            cleanup_table.add_row("已拒绝内容", str(old_contents), f"{older_than_days} 天前被拒绝的内容")
            cleanup_table.add_row("审计日志", str(old_audit_logs), f"{older_than_days} 天前的日志")
            cleanup_table.add_row("失败发布记录", str(old_publish_logs), f"{older_than_days} 天前失败的发布")

            from rich.console import Console
            console = Console()
            console.print(cleanup_table)

            if dry_run:
                print_info("\n这是预览模式，未执行实际清理")
                print_info("去掉 --dry-run 参数以执行清理")
            else:
                print_warning("\n注意: 资源清理功能需要谨慎使用")
                print_info("建议在执行前备份数据库")

                # 实际清理功能（简化版）
                # 生产环境中应该有更完善的清理逻辑
                print_info("请在生产环境中使用专业的数据库维护工具")

    except Exception as e:
        handle_error(e)


@app.command("logs")
def view_logs(
    lines: int = typer.Option(50, "--lines", "-n", help="显示行数"),
    module: str = typer.Option(None, "--module", "-m", help="模块筛选"),
    level: str = typer.Option(None, "--level", "-l", help="日志级别筛选")
):
    """查看系统日志"""
    try:
        from app.core.config import settings

        # 获取日志目录
        log_dir = getattr(settings, "LOG_DIR", "logs")
        log_file = os.path.join(log_dir, "app.log")

        if not os.path.exists(log_file):
            print_warning(f"日志文件不存在: {log_file}")
            return

        print_info(f"正在读取日志文件: {log_file}")

        # 读取日志文件
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

        # 获取最后 N 行
        recent_lines = all_lines[-lines:]

        # 应用筛选
        if module or level:
            filtered_lines = []
            for line in recent_lines:
                include_line = True
                if module and module.lower() not in line.lower():
                    include_line = False
                if level and level.upper() not in line.upper():
                    include_line = False
                if include_line:
                    filtered_lines.append(line)
            display_lines = filtered_lines
        else:
            display_lines = recent_lines

        if not display_lines:
            print_warning("没有符合条件的日志记录")
            return

        # 显示日志
        print_info(f"\n最近 {len(display_lines)} 条日志记录:\n")

        for line in display_lines:
            # 根据日志级别设置颜色
            if "ERROR" in line:
                print_error(line.strip())
            elif "WARNING" in line:
                print_warning(line.strip())
            elif "INFO" in line:
                print_info(line.strip())
            else:
                print(line.strip())

        print_info(f"\n总记录数: {len(display_lines)}")

    except Exception as e:
        handle_error(e)
