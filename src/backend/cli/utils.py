"""
CLI 工具函数

提供输出格式化、交互确认等工具函数。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm

console = Console()


# 输出格式化
def print_table(
    data: List[Dict[str, Any]],
    title: Optional[str] = None,
    show_header: bool = True,
    header_style: str = "bold magenta"
):
    """打印表格

    Args:
        data: 数据列表
        title: 表格标题
        show_header: 是否显示表头
        header_style: 表头样式
    """
    if not data:
        console.print("[dim]无数据[/dim]")
        return

    table = Table(
        title=title,
        show_header=show_header,
        header_style=header_style,
        show_lines=True
    )

    # 添加列
    for key in data[0].keys():
        table.add_column(str(key))

    # 添加行
    for row in data:
        table.add_row(*[str(v) if v is not None else "" for v in row.values()])

    console.print(table)


def print_success(message: str):
    """打印成功消息

    Args:
        message: 消息内容
    """
    console.print(f"✅ {message}")


def print_error(message: str):
    """打印错误消息

    Args:
        message: 错误消息
    """
    console.print(f"❌ {message}", style="red")


def print_warning(message: str):
    """打印警告消息

    Args:
        message: 警告消息
    """
    console.print(f"⚠️  {message}", style="yellow")


def print_info(message: str):
    """打印信息消息

    Args:
        message: 信息消息
    """
    console.print(f"ℹ️  {message}", style="blue")


def print_panel(content: str, title: str = "", style: str = "blue"):
    """打印面板

    Args:
        content: 面板内容
        title: 面板标题
        style: 面板样式
    """
    console.print(Panel(content, title=title, style=style))


# 交互确认
def confirm_action(message: str, default: bool = False) -> bool:
    """确认操作

    Args:
        message: 确认消息
        default: 默认值

    Returns:
        用户选择结果
    """
    return Confirm.ask(message, default=default)


# 数据格式化
def format_datetime(dt: Optional[datetime]) -> str:
    """格式化日期时间

    Args:
        dt: 日期时间对象

    Returns:
        格式化后的字符串
    """
    if not dt:
        return "-"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_bool(value: Optional[bool]) -> str:
    """格式化布尔值

    Args:
        value: 布尔值

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"
    return "✅" if value else "❌"


def format_json(data: Dict) -> str:
    """格式化 JSON

    Args:
        data: 字典数据

    Returns:
        格式化后的 JSON 字符串
    """
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)


def format_list(items: List[Any], separator: str = ", ") -> str:
    """格式化列表

    Args:
        items: 列表项
        separator: 分隔符

    Returns:
        格式化后的字符串
    """
    if not items:
        return "-"
    return separator.join(str(item) for item in items)


# 进度条
def show_progress(tasks: List[Dict[str, Any]]):
    """显示进度条

    Args:
        tasks: 任务列表，每个任务包含 description 和 total
    """
    with Progress() as progress:
        task_ids = []
        for task in tasks:
            task_id = progress.add_task(task["description"], total=task["total"])
            task_ids.append(task_id)

        # 这里可以添加实际的进度更新逻辑
        # task_ids 可以用来更新进度


# 错误处理
def handle_error(error: Exception, exit_code: int = 1):
    """处理错误

    Args:
        error: 异常对象
        exit_code: 退出码
    """
    print_error(f"{error.__class__.__name__}: {str(error)}")
    raise typer.Exit(exit_code)


# 输出格式化
def format_output(data: Any, output_format: str = "table") -> str:
    """格式化输出

    Args:
        data: 输出数据
        output_format: 输出格式 (table/json/csv)

    Returns:
        格式化后的字符串
    """
    if output_format == "json":
        if isinstance(data, (list, dict)):
            return format_json(data)
        return format_json({"result": data})
    elif output_format == "csv":
        if isinstance(data, list) and data:
            import csv
            import io
            output = io.StringIO()
            if isinstance(data[0], dict):
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(output)
                writer.writerows(data)
            return output.getvalue()
        return str(data)
    else:  # table
        return str(data)


# 导入 typer 用于错误处理
import typer
