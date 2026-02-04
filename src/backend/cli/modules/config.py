"""
配置管理模块

提供写作风格、内容主题、系统参数和平台配置的管理功能。
"""

import json
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
    format_json,
    handle_error,
)
from app.db.sql_db import get_session_local
from app.models.account import WritingStyle
from app.models.theme import ContentTheme
from app.models.platform import Platform

# 创建主应用
app = typer.Typer(help="配置管理")


@app.command("list")
def list_all_configs():
    """列出所有配置分类"""
    from rich.console import Console
    from rich.tree import Tree

    console = Console()

    tree = Tree("📋 ContentHub 配置管理")
    tree.add("写作风格配置 (writing-style)")
    tree.add("内容主题配置 (content-theme)")
    tree.add("系统参数配置 (system-params)")
    tree.add("平台配置 (platform-config)")

    console.print(tree)
    print_info("\n使用 'contenthub config <category> list' 查看具体配置")
    print_info("例如: contenthub config writing-style list")


# ==================== 写作风格配置 ====================
writing_style_app = typer.Typer(help="写作风格配置")
app.add_typer(writing_style_app, name="writing-style")


@writing_style_app.command("list")
def list_writing_styles(
    is_system: bool = typer.Option(None, "--system", help="仅显示系统级风格"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量")
):
    """列出写作风格"""
    try:
        with get_session_local()() as db:
            query = db.query(WritingStyle)

            if is_system is not None:
                query = query.filter(WritingStyle.is_system == (is_system == True))

            skip = (page - 1) * page_size
            styles = query.order_by(WritingStyle.created_at.desc()).offset(skip).limit(page_size).all()

            if not styles:
                print_warning("未找到写作风格")
                return

            data = []
            for style in styles:
                data.append({
                    "ID": style.id,
                    "名称": style.name,
                    "代码": style.code,
                    "语气": style.tone,
                    "字数范围": f"{style.min_words}-{style.max_words}",
                    "系统级": "是" if style.is_system else "否",
                    "账号ID": style.account_id or "-",
                    "创建时间": format_datetime(style.created_at),
                })

            print_table(data, title=f"写作风格列表 (第 {page} 页)", show_header=True)

    except Exception as e:
        handle_error(e)


@writing_style_app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="风格名称"),
    code: str = typer.Option(..., "--code", "-c", help="风格代码"),
    tone: str = typer.Option("专业", "--tone", help="语气"),
    persona: str = typer.Option(None, "--persona", help="人设"),
    min_words: int = typer.Option(800, "--min-words", help="最小字数"),
    max_words: int = typer.Option(1500, "--max-words", help="最大字数"),
    emoji_usage: str = typer.Option("适度", "--emoji", help="表情使用（不使用/适度/频繁）"),
    forbidden_words: str = typer.Option(None, "--forbidden", help="禁用词（逗号分隔）"),
    is_system: bool = typer.Option(False, "--system", help="是否系统级"),
    account_id: int = typer.Option(None, "--account-id", help="账号 ID（非系统级必需）")
):
    """创建写作风格"""
    try:
        with get_session_local()() as db:
            # 检查代码是否已存在
            existing = db.query(WritingStyle).filter(WritingStyle.code == code).first()
            if existing:
                print_error(f"风格代码已存在: {code}")
                raise typer.Exit(1)

            # 准备数据
            style_data = {
                "name": name,
                "code": code,
                "tone": tone,
                "persona": persona,
                "min_words": min_words,
                "max_words": max_words,
                "emoji_usage": emoji_usage,
                "forbidden_words": forbidden_words.split(",") if forbidden_words else [],
                "is_system": is_system,
                "account_id": account_id
            }

            # 创建风格
            print_info("正在创建写作风格...")
            style = WritingStyle(**style_data)
            db.add(style)
            db.commit()
            db.refresh(style)

            print_success(f"写作风格创建成功 (ID: {style.id})")

    except Exception as e:
        handle_error(e)


@writing_style_app.command()
def update(
    style_id: int = typer.Argument(..., help="风格 ID"),
    name: str = typer.Option(None, "--name", help="风格名称"),
    tone: str = typer.Option(None, "--tone", help="语气"),
    persona: str = typer.Option(None, "--persona", help="人设"),
    min_words: int = typer.Option(None, "--min-words", help="最小字数"),
    max_words: int = typer.Option(None, "--max-words", help="最大字数"),
    emoji_usage: str = typer.Option(None, "--emoji", help="表情使用"),
    forbidden_words: str = typer.Option(None, "--forbidden", help="禁用词（逗号分隔）")
):
    """更新写作风格"""
    try:
        with get_session_local()() as db:
            style = db.query(WritingStyle).filter(WritingStyle.id == style_id).first()
            if not style:
                print_error(f"写作风格不存在: ID {style_id}")
                raise typer.Exit(1)

            update_data = {}
            if name:
                update_data["name"] = name
            if tone:
                update_data["tone"] = tone
            if persona is not None:
                update_data["persona"] = persona
            if min_words is not None:
                update_data["min_words"] = min_words
            if max_words is not None:
                update_data["max_words"] = max_words
            if emoji_usage:
                update_data["emoji_usage"] = emoji_usage
            if forbidden_words is not None:
                update_data["forbidden_words"] = forbidden_words.split(",") if forbidden_words else []

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            print_info(f"正在更新写作风格 (ID: {style_id})...")
            for key, value in update_data.items():
                setattr(style, key, value)

            db.commit()
            print_success("写作风格更新成功")

    except Exception as e:
        handle_error(e)


@writing_style_app.command()
def delete(
    style_id: int = typer.Argument(..., help="风格 ID")
):
    """删除写作风格"""
    try:
        with get_session_local()() as db:
            style = db.query(WritingStyle).filter(WritingStyle.id == style_id).first()
            if not style:
                print_error(f"写作风格不存在: ID {style_id}")
                raise typer.Exit(1)

            if not confirm_action(f"确定要删除写作风格吗？\n名称: {style.name}", default=False):
                print_info("已取消删除操作")
                return

            print_info(f"正在删除写作风格 (ID: {style_id})...")
            db.delete(style)
            db.commit()

            print_success(f"写作风格删除成功 (ID: {style_id})")

    except Exception as e:
        handle_error(e)


@writing_style_app.command()
def info(
    style_id: int = typer.Argument(..., help="风格 ID")
):
    """查看写作风格详情"""
    try:
        with get_session_local()() as db:
            style = db.query(WritingStyle).filter(WritingStyle.id == style_id).first()
            if not style:
                print_error(f"写作风格不存在: ID {style_id}")
                raise typer.Exit(1)

            style_data = {
                "ID": style.id,
                "名称": style.name,
                "代码": style.code,
                "描述": style.description or "-",
                "语气": style.tone,
                "人设": style.persona or "-",
                "最小字数": style.min_words,
                "最大字数": style.max_words,
                "表情使用": style.emoji_usage,
                "禁用词": ", ".join(style.forbidden_words) if style.forbidden_words else "-",
                "系统级": "是" if style.is_system else "否",
                "账号ID": style.account_id or "-",
                "创建时间": format_datetime(style.created_at),
            }

            info_table = Table(title="写作风格详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in style_data.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


# ==================== 内容主题配置 ====================
content_theme_app = typer.Typer(help="内容主题配置")
app.add_typer(content_theme_app, name="content-theme")


@content_theme_app.command("list")
def list_content_themes(
    is_system: bool = typer.Option(None, "--system", help="仅显示系统级主题"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量")
):
    """列出内容主题"""
    try:
        with get_session_local()() as db:
            query = db.query(ContentTheme)

            if is_system is not None:
                query = query.filter(ContentTheme.is_system == (is_system == True))

            skip = (page - 1) * page_size
            themes = query.order_by(ContentTheme.created_at.desc()).offset(skip).limit(page_size).all()

            if not themes:
                print_warning("未找到内容主题")
                return

            data = []
            for theme in themes:
                data.append({
                    "ID": theme.id,
                    "名称": theme.name,
                    "代码": theme.code,
                    "类型": theme.type or "-",
                    "系统级": "是" if theme.is_system else "否",
                    "创建时间": format_datetime(theme.created_at),
                })

            print_table(data, title=f"内容主题列表 (第 {page} 页)", show_header=True)

    except Exception as e:
        handle_error(e)


@content_theme_app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="主题名称"),
    code: str = typer.Option(..., "--code", "-c", help="主题代码"),
    theme_type: str = typer.Option(None, "--type", "-t", help="主题类型"),
    description: str = typer.Option(None, "--description", "-d", help="主题描述"),
    is_system: bool = typer.Option(False, "--system", help="是否系统级")
):
    """创建内容主题"""
    try:
        with get_session_local()() as db:
            # 检查代码是否已存在
            existing = db.query(ContentTheme).filter(ContentTheme.code == code).first()
            if existing:
                print_error(f"主题代码已存在: {code}")
                raise typer.Exit(1)

            # 准备数据
            theme_data = {
                "name": name,
                "code": code,
                "type": theme_type,
                "description": description,
                "is_system": is_system
            }

            # 创建主题
            print_info("正在创建内容主题...")
            theme = ContentTheme(**theme_data)
            db.add(theme)
            db.commit()
            db.refresh(theme)

            print_success(f"内容主题创建成功 (ID: {theme.id})")

    except Exception as e:
        handle_error(e)


@content_theme_app.command()
def update(
    theme_id: int = typer.Argument(..., help="主题 ID"),
    name: str = typer.Option(None, "--name", help="主题名称"),
    theme_type: str = typer.Option(None, "--type", help="主题类型"),
    description: str = typer.Option(None, "--description", help="主题描述")
):
    """更新内容主题"""
    try:
        with get_session_local()() as db:
            theme = db.query(ContentTheme).filter(ContentTheme.id == theme_id).first()
            if not theme:
                print_error(f"内容主题不存在: ID {theme_id}")
                raise typer.Exit(1)

            update_data = {}
            if name:
                update_data["name"] = name
            if theme_type is not None:
                update_data["type"] = theme_type
            if description is not None:
                update_data["description"] = description

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            print_info(f"正在更新内容主题 (ID: {theme_id})...")
            for key, value in update_data.items():
                setattr(theme, key, value)

            db.commit()
            print_success("内容主题更新成功")

    except Exception as e:
        handle_error(e)


@content_theme_app.command()
def delete(
    theme_id: int = typer.Argument(..., help="主题 ID")
):
    """删除内容主题"""
    try:
        with get_session_local()() as db:
            theme = db.query(ContentTheme).filter(ContentTheme.id == theme_id).first()
            if not theme:
                print_error(f"内容主题不存在: ID {theme_id}")
                raise typer.Exit(1)

            if not confirm_action(f"确定要删除内容主题吗？\n名称: {theme.name}", default=False):
                print_info("已取消删除操作")
                return

            print_info(f"正在删除内容主题 (ID: {theme_id})...")
            db.delete(theme)
            db.commit()

            print_success(f"内容主题删除成功 (ID: {theme_id})")

    except Exception as e:
        handle_error(e)


@content_theme_app.command()
def info(
    theme_id: int = typer.Argument(..., help="主题 ID")
):
    """查看内容主题详情"""
    try:
        with get_session_local()() as db:
            theme = db.query(ContentTheme).filter(ContentTheme.id == theme_id).first()
            if not theme:
                print_error(f"内容主题不存在: ID {theme_id}")
                raise typer.Exit(1)

            theme_data = {
                "ID": theme.id,
                "名称": theme.name,
                "代码": theme.code,
                "类型": theme.type or "-",
                "描述": theme.description or "-",
                "系统级": "是" if theme.is_system else "否",
                "创建时间": format_datetime(theme.created_at),
                "更新时间": format_datetime(theme.updated_at),
            }

            info_table = Table(title="内容主题详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in theme_data.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


# ==================== 系统参数配置 ====================
system_params_app = typer.Typer(help="系统参数配置")
app.add_typer(system_params_app, name="system-params")


@system_params_app.command("get")
def get_param(
    key: str = typer.Argument(..., help="参数键")
):
    """获取系统参数"""
    try:
        # 从环境变量或配置文件读取
        import os
        from app.core.config import settings

        value = os.getenv(key)
        if value is None:
            # 尝试从 settings 获取
            value = getattr(settings, key.upper(), None)

        if value is None:
            print_warning(f"参数不存在: {key}")
            return

        print_info(f"{key}: {value}")

    except Exception as e:
        handle_error(e)


@system_params_app.command("set")
def set_param(
    key: str = typer.Argument(..., help="参数键"),
    value: str = typer.Argument(..., help="参数值")
):
    """设置系统参数（仅限当前会话）"""
    try:
        import os
        print_info(f"设置系统参数: {key} = {value}")
        print_warning("注意: 此设置仅在当前会话有效")
        print_info("如需永久设置，请修改 .env 文件或系统环境变量")

        os.environ[key] = value
        print_success(f"参数已设置: {key} = {value}")

    except Exception as e:
        handle_error(e)


@system_params_app.command("list")
def list_params(
    filter: str = typer.Option(None, "--filter", "-f", help="过滤前缀")
):
    """列出所有系统参数"""
    try:
        import os
        from app.core.config import settings

        print_info("系统参数列表:")

        # 显示环境变量
        env_vars = dict(os.environ)
        if filter:
            env_vars = {k: v for k, v in env_vars.items() if k.startswith(filter)}

        # 显示主要配置
        important_vars = [
            "APP_NAME", "APP_VERSION", "DEBUG",
            "DATABASE_URL", "REDIS_URL",
            "PUBLISHER_API_URL", "CREATOR_CLI_PATH",
            "TAVILY_API_KEY", "SECRET_KEY"
        ]

        data = []
        for var in important_vars:
            if var in env_vars:
                value = env_vars[var]
                # 隐藏敏感信息
                if any(secret in var.upper() for secret in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
                    value = "***HIDDEN***"
                data.append({"变量": var, "值": value})

        if data:
            print_table(data, title="重要系统参数", show_header=True)

        if filter:
            print_info(f"\n过滤后的环境变量 ({filter}*):")
            for k, v in sorted(env_vars.items()):
                print(f"  {k} = {v}")

    except Exception as e:
        handle_error(e)


# ==================== 平台配置 ====================
platform_config_app = typer.Typer(help="平台配置")
app.add_typer(platform_config_app, name="platform-config")


@platform_config_app.command("list")
def list_platform_configs(
    platform_id: int = typer.Option(None, "--platform-id", "-p", help="平台 ID")
):
    """列出平台配置"""
    try:
        with get_session_local()() as db:
            query = db.query(Platform)

            if platform_id:
                query = query.filter(Platform.id == platform_id)

            platforms = query.all()

            if not platforms:
                print_warning("未找到平台")
                return

            data = []
            for platform in platforms:
                # 隐藏敏感信息
                api_key = "***HIDDEN***" if platform.api_key else "-"
                data.append({
                    "ID": platform.id,
                    "名称": platform.name,
                    "代码": platform.code,
                    "API地址": platform.api_url or "-",
                    "API密钥": api_key,
                    "状态": "激活" if platform.is_active else "停用",
                })

            print_table(data, title="平台配置列表", show_header=True)

    except Exception as e:
        handle_error(e)


@platform_config_app.command()
def update(
    platform_id: int = typer.Argument(..., help="平台 ID"),
    api_url: str = typer.Option(None, "--api-url", help="API 地址"),
    api_key: str = typer.Option(None, "--api-key", help="API 密钥"),
):
    """更新平台配置"""
    try:
        with get_session_local()() as db:
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                print_error(f"平台不存在: ID {platform_id}")
                raise typer.Exit(1)

            update_data = {}
            if api_url is not None:
                update_data["api_url"] = api_url
            if api_key is not None:
                update_data["api_key"] = api_key

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            print_info(f"正在更新平台配置 (ID: {platform_id})...")
            for key, value in update_data.items():
                setattr(platform, key, value)

            db.commit()
            print_success("平台配置更新成功")

            # 显示更新后的信息（隐藏敏感信息）
            print_info(f"API 地址: {platform.api_url or '-'}")
            print_info(f"API 密钥: {'***已设置***' if platform.api_key else '未设置'}")

    except Exception as e:
        handle_error(e)
