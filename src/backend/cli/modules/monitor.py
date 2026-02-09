"""
监控 CLI 模块

提供异步任务监控和指标查询功能。
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from app.services.monitoring.async_task_monitor import AsyncTaskMonitor

app = typer.Typer(help="监控和管理异步任务")
console = Console()


@app.command()
def metrics():
    """
    显示异步任务指标

    示例:
        contenthub monitor metrics
    """
    monitor = AsyncTaskMonitor()
    metrics = monitor.get_metrics()

    # 创建指标面板
    status_counts = metrics['status_counts']

    content = f"""
[bold blue]异步任务监控指标[/bold blue]

[bright_black]总任务数:[/bright_black] {metrics['total_tasks']}

[bright_black]今日统计:[/bright_black]
  • 新任务: {metrics['today_tasks']}
  • 已完成: {metrics['today_completed']}
  • 成功率: [green]{metrics['success_rate']}%[/green]

[bright_black]当前状态:[/bright_black]
  • 待处理: [yellow]{status_counts.get('pending', 0)}[/yellow]
  • 已提交: [cyan]{status_counts.get('submitted', 0)}[/cyan]
  • 处理中: [blue]{status_counts.get('processing', 0)}[/blue]
  • 已完成: [green]{status_counts.get('completed', 0)}[/green]
  • 失败: [red]{status_counts.get('failed', 0)}[/red]
  • 超时: [red]{status_counts.get('timeout', 0)}[/red]

[bright_black]性能指标:[/bright_black]
  • 平均执行时间: {metrics['avg_duration_seconds']:.1f} 秒
  • 失败率: [red]{metrics['failed_rate']}%[/red]
  • 队列积压: [yellow]{metrics['pending_count']}[/yellow]

[bright_black]系统状态:[/bright_black] {get_health_indicator(metrics['health'])}
    """

    console.print(Panel(content, title="📊 异步任务监控", border_style="blue"))


@app.command("recent")
def recent_tasks(limit: int = typer.Option(10, "--limit", "-l", help="显示数量")):
    """
    显示最近的任务

    示例:
        contenthub monitor recent
        contenthub monitor recent --limit 20
    """
    monitor = AsyncTaskMonitor()
    tasks = monitor.get_recent_tasks(limit=limit)

    if not tasks:
        console.print("[yellow]没有找到任务[/yellow]")
        return

    table = Table(title=f"最近 {len(tasks)} 个任务", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("任务ID")
    table.add_column("状态")
    table.add_column("选题")
    table.add_column("创建时间")
    table.add_column("完成时间")

    for task in tasks:
        status_style = get_status_style(task['status'])
        table.add_row(
            str(task['id']),
            task['task_id'],
            f"[{status_style}]{task['status']}[/{status_style}]",
            task['topic'][:50] if task['topic'] else '-',
            format_datetime(task['created_at']),
            format_datetime(task['completed_at'])
        )

    console.print(table)


@app.command("failed")
def failed_tasks(limit: int = typer.Option(10, "--limit", "-l", help="显示数量")):
    """
    显示失败的任务

    示例:
        contenthub monitor failed
        contenthub monitor failed --limit 20
    """
    monitor = AsyncTaskMonitor()
    tasks = monitor.get_failed_tasks(limit=limit)

    if not tasks:
        console.print("[green]没有失败的任务[/green]")
        return

    table = Table(title=f"失败任务（最近 {len(tasks)} 个）", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("任务ID")
    table.add_column("状态")
    table.add_column("选题")
    table.add_column("错误信息")
    table.add_column("重试次数")
    table.add_column("创建时间")

    for task in tasks:
        status_style = get_status_style(task['status'])
        table.add_row(
            str(task['id']),
            task['task_id'],
            f"[{status_style}]{task['status']}[/{status_style}]",
            task['topic'][:30] if task['topic'] else '-',
            task['error_message'][:50] if task['error_message'] else '-',
            str(task['retry_count']),
            format_datetime(task['created_at'])
        )

    console.print(table)


@app.command("pending")
def pending_tasks(limit: int = typer.Option(10, "--limit", "-l", help="显示数量")):
    """
    显示待处理的任务

    示例:
        contenthub monitor pending
        contenthub monitor pending --limit 20
    """
    monitor = AsyncTaskMonitor()
    tasks = monitor.get_pending_tasks(limit=limit)

    if not tasks:
        console.print("[green]没有待处理的任务[/green]")
        return

    table = Table(title=f"待处理任务（最近 {len(tasks)} 个）", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("任务ID")
    table.add_column("状态")
    table.add_column("选题")
    table.add_column("优先级")
    table.add_column("创建时间")

    for task in tasks:
        status_style = get_status_style(task['status'])
        priority_style = "red" if task['priority'] >= 8 else "yellow" if task['priority'] >= 5 else "dim"
        table.add_row(
            str(task['id']),
            task['task_id'],
            f"[{status_style}]{task['status']}[/{status_style}]",
            task['topic'][:50] if task['topic'] else '-',
            f"[{priority_style}]{task['priority']}[/{priority_style}]",
            format_datetime(task['created_at'])
        )

    console.print(table)


@app.command("stats")
def daily_stats(days: int = typer.Option(7, "--days", "-d", help="统计天数")):
    """
    显示每日统计

    示例:
        contenthub monitor stats
        contenthub monitor stats --days 14
    """
    monitor = AsyncTaskMonitor()
    stats = monitor.get_daily_stats(days=days)

    if not stats:
        console.print("[yellow]没有统计数据[/yellow]")
        return

    table = Table(title=f"每日统计（最近 {days} 天）", box=box.ROUNDED)
    table.add_column("日期")
    table.add_column("总数", justify="right")
    table.add_column("完成", justify="right")
    table.add_column("失败", justify="right")
    table.add_column("成功率", justify="right")

    for stat in stats:
        success_rate_style = "green" if stat['success_rate'] >= 80 else "yellow" if stat['success_rate'] >= 60 else "red"
        table.add_row(
            stat['date'],
            str(stat['total']),
            f"[green]{stat['completed']}[/green]",
            f"[red]{stat['failed']}[/red]",
            f"[{success_rate_style}]{stat['success_rate']}%[/{success_rate_style}]"
        )

    console.print(table)


@app.command("health")
def health_check():
    """
    显示系统健康状态

    示例:
        contenthub monitor health
    """
    monitor = AsyncTaskMonitor()
    metrics = monitor.get_metrics()

    health = metrics['health']
    health_indicator = get_health_indicator(health)

    console.print(f"\n系统状态: {health_indicator}\n")

    # 显示详细健康指标
    if health == 'unhealthy':
        console.print("[red]系统状态不健康，可能存在以下问题：[/red]")
        if metrics['failed_rate'] > 20:
            console.print(f"  • 失败率过高: {metrics['failed_rate']}%")
    elif health == 'warning':
        console.print("[yellow]系统状态警告，注意以下指标：[/yellow]")
        if metrics['failed_rate'] > 10:
            console.print(f"  • 失败率偏高: {metrics['failed_rate']}%")
        if metrics['pending_count'] > 50:
            console.print(f"  • 队列积压: {metrics['pending_count']} 个任务")
    else:
        console.print("[green]系统运行正常[/green]")


# 辅助函数


def get_health_indicator(health: str) -> str:
    """获取健康状态指示器"""
    if health == 'healthy':
        return "[green]✓ 健康[/green]"
    elif health == 'warning':
        return "[yellow]⚠ 警告[/yellow]"
    else:
        return "[red]✗ 不健康[/red]"


def get_status_style(status: str) -> str:
    """获取状态样式"""
    status_styles = {
        'pending': 'yellow',
        'submitted': 'cyan',
        'processing': 'blue',
        'completed': 'green',
        'failed': 'red',
        'timeout': 'red',
        'cancelled': 'dim'
    }
    return status_styles.get(status, 'white')


def format_datetime(dt_str: str) -> str:
    """格式化日期时间"""
    if not dt_str:
        return '-'

    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str
