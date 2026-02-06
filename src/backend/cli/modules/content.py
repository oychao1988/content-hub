"""
内容管理模块

提供内容 CRUD、内容生成、审核流程等功能。
"""

import json
from datetime import datetime
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
    format_list,
    handle_error,
    get_global_format,
)
from app.db.sql_db import get_session_local
from app.models.content import Content
from app.modules.content.services import content_service
from app.services.content_creator_service import content_creator_service
from app.services.content_review_service import content_review_service
from app.core.config import settings

# 创建子应用
app = typer.Typer(help="内容管理")


def get_content(db: Session, content_id: int) -> Optional[Content]:
    """获取内容

    Args:
        db: 数据库会话
        content_id: 内容 ID

    Returns:
        内容对象或 None
    """
    return db.query(Content).filter(Content.id == content_id).first()


def list_contents_db(
    db: Session,
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[Content]:
    """查询内容列表

    Args:
        db: 数据库会话
        account_id: 账号 ID 筛选
        status: 状态筛选
        skip: 跳过记录数
        limit: 限制记录数

    Returns:
        内容列表
    """
    query = db.query(Content)

    if account_id:
        query = query.filter(Content.account_id == account_id)
    if status:
        query = query.filter(Content.publish_status == status)

    return query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()


def format_content_info(content: Content, detailed: bool = False) -> dict:
    """格式化内容信息

    Args:
        content: 内容对象
        detailed: 是否显示详细信息

    Returns:
        格式化的内容信息字典
    """
    account_name = content.account.name if content.account else "未知"

    info = {
        "ID": content.id,
        "标题": content.title,
        "账号": account_name,
        "状态": content.publish_status,
        "审核状态": content.review_status,
        "字数": content.word_count or 0,
        "创建时间": format_datetime(content.created_at),
    }

    if detailed:
        info.update({
            "内容类型": content.content_type or "-",
            "分类": content.category or "-",
            "选题": content.topic or "-",
            "摘要": content.summary or "-",
            "标签": format_list(content.tags) if content.tags else "-",
            "更新时间": format_datetime(content.updated_at),
        })

    return info


@app.command("list")
def list_contents(
    ctx: typer.Context,
    account_id: int = typer.Option(None, "--account-id", "-a", help="按账号 ID 筛选"),
    status: str = typer.Option(None, "--status", "-s", help="按状态筛选"),
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    page_size: int = typer.Option(20, "--page-size", "--size", help="每页数量")
):
    """列出内容"""
    try:
        with get_session_local()() as db:
            # 计算分页
            skip = (page - 1) * page_size

            # 查询内容
            contents = list_contents_db(
                db,
                account_id=account_id,
                status=status,
                skip=skip,
                limit=page_size
            )

            # 格式化输出
            data = []
            for content in contents:
                account_name = content.account.name if content.account else "未知"
                data.append({
                    "ID": content.id,
                    "标题": content.title,
                    "账号": account_name,
                    "状态": content.publish_status,
                    "审核状态": content.review_status,
                    "字数": content.word_count or 0,
                    "创建时间": format_datetime(content.created_at),
                })

            # 获取全局输出格式
            output_format = get_global_format(ctx)

            if not contents:
                if output_format != "table":
                    # JSON/CSV 格式时输出空列表
                    print_table([], output_format=output_format)
                else:
                    print_warning("未找到内容")
                return

            print_table(data, title=f"内容列表 (第 {page} 页，共 {len(contents)} 条)", show_header=True, output_format=output_format)

    except Exception as e:
        handle_error(e)


@app.command()
def create(
    account_id: int = typer.Option(..., "--account-id", "-a", help="账号 ID"),
    title: str = typer.Option(..., "--title", "-t", help="内容标题"),
    content_text: str = typer.Option(None, "--content", "-c", help="内容正文"),
    content_type: str = typer.Option("article", "--type", help="内容类型"),
    summary: str = typer.Option(None, "--summary", help="摘要"),
    tags: str = typer.Option(None, "--tags", help="标签（逗号分隔）")
):
    """创建内容（草稿）"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 准备内容数据
            content_data = {
                "title": title,
                "content_type": content_type,
                "content": content_text or "",
                "summary": summary,
                "status": "draft",
                "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
            }

            # 创建内容
            print_info("正在创建内容...")
            content = content_service.create_content(db, content_data, account_id)

            print_success(f"内容创建成功 (ID: {content.id})")

            # 显示内容信息
            content_info = format_content_info(content, detailed=True)

            info_table = Table(title="内容详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in content_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def generate(
    account_id: int = typer.Option(..., "--account-id", "-a", help="账号 ID"),
    topic: str = typer.Option(..., "--topic", "-t", help="选题"),
    keywords: str = typer.Option(None, "--keywords", "-k", help="关键词（逗号分隔）"),
    category: str = typer.Option("默认", "--category", "-c", help="内容板块"),
    requirements: str = typer.Option(None, "--requirements", "-r", help="创作要求"),
    tone: str = typer.Option("友好专业", "--tone", help="语气风格"),
):
    """生成内容（调用 content-creator）

    流程：
    1. 先创建草稿记录（状态：publishing-生成中）
    2. 调用 content-creator 生成内容
    3. 更新草稿记录（状态：draft-草稿）

    状态说明：
    - publishing: 正在生成内容
    - draft: 生成完成，等待审核
    """
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 检查是否配置了 CLI
            if not settings.CREATOR_CLI_PATH:
                print_warning("未配置 content-creator CLI")
                print_info("请在 .env 文件中设置 CREATOR_CLI_PATH")
                raise typer.Exit(1)

            print_info(f"准备生成内容...")
            print_info(f"账号: {account.name}")
            print_info(f"选题: {topic}")
            print_info(f"关键词: {keywords or '无'}")

            # 显示账号配置
            if account.writing_style:
                print_info(f"写作风格: {account.writing_style.tone}, {account.writing_style.min_words}-{account.writing_style.max_words}字")
            if account.publish_config and account.publish_config.theme_id:
                from app.models.theme import ContentTheme
                theme = db.query(ContentTheme).filter(
                    ContentTheme.id == account.publish_config.theme_id
                ).first()
                if theme:
                    print_info(f"内容主题: {theme.name}")

            # 说明 CLI 参数优先级
            if tone != "友好专业" or requirements:
                print_info("提示: CLI 参数将覆盖账号配置")

            # 构建创作要求
            if not requirements:
                requirements = f"写一篇关于'{topic}'的{category}类文章，要求内容详实、结构清晰"

            # 步骤1：先创建草稿记录（状态：生成中）
            print_info("步骤 1/3: 创建草稿记录...")

            initial_content_data = {
                "title": topic,
                "content_type": "article",
                "content": f"# {topic}\n\n正在生成内容，请稍候...",
                "summary": f"基于选题: {topic}",
                "category": category,
                "topic": topic,
                "publish_status": "publishing",  # 标记为生成中（使用 publishing 状态）
                "tags": [keyword.strip() for keyword in keywords.split(",")] if keywords else [],
            }

            content = content_service.create_content(db, initial_content_data, account_id)
            print_success(f"草稿记录创建成功 (ID: {content.id})")

            # 步骤2：调用 content-creator 生成内容
            print_info("步骤 2/3: 正在调用 AI 生成内容...")

            generated_content = None
            generated_images = []
            quality_score = None
            generation_error = None

            try:
                result = content_creator_service.create_content(
                    topic=topic,
                    requirements=requirements,
                    target_audience=category if category != "默认" else "普通读者",
                    tone=tone,
                    account_id=account_id,
                    db=db
                )

                # 从结果中提取内容
                if result and result.get("content"):
                    generated_content = result["content"]
                    generated_images = result.get("images", [])
                    quality_score = result.get("quality_score")

                    print_success("内容生成成功")
                    if generated_images:
                        print_info(f"生成 {len(generated_images)} 张配图")
                    if quality_score:
                        print_info(f"质量评分: {quality_score}/10")
                else:
                    generation_error = "生成器未返回内容"
                    print_warning(generation_error)

            except Exception as e:
                generation_error = str(e)
                print_warning(f"内容生成失败: {generation_error}")

            # 步骤3：更新草稿记录
            print_info("步骤 3/3: 更新内容记录...")

            update_data = {
                "content": generated_content if generated_content else f"# {topic}\n\n生成失败，请重试。\n错误信息: {generation_error}",
                "summary": f"基于选题: {topic}",
                "publish_status": "draft",  # 生成完成后改为草稿状态
            }

            # 更新摘要
            if generated_images:
                update_data["summary"] += f"\n包含 {len(generated_images)} 张配图"

            # 更新内容
            content = content_service.update_content(db, content.id, update_data)

            print_success(f"内容记录更新成功 (ID: {content.id})")

            # 显示最终内容信息
            content_info = format_content_info(content, detailed=True)

            # 添加生成信息
            if quality_score:
                content_info["质量评分"] = f"{quality_score}/10"
            if generated_images:
                content_info["配图数量"] = str(len(generated_images))
            if generation_error:
                content_info["生成状态"] = "失败"

            info_table = Table(title="内容详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in content_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

            # 如果生成失败，给出提示
            if not generated_content:
                print_warning("\n内容生成失败，但已创建草稿记录")
                print_info("您可以稍后手动编辑内容，或使用 update 命令重新生成")

    except Exception as e:
        handle_error(e)


@app.command("batch-generate")
def batch_generate(
    account_id: int = typer.Option(..., "--account-id", "-a", help="账号 ID"),
    count: int = typer.Option(5, "--count", "-n", help="生成数量"),
    keywords: str = typer.Option(..., "--keywords", "-k", help="关键词（逗号分隔）"),
    category: str = typer.Option("默认", "--category", "-c", help="内容板块")
):
    """批量生成内容"""
    try:
        with get_session_local()() as db:
            # 检查账号是否存在
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            # 解析关键词
            keyword_list = [keyword.strip() for keyword in keywords.split(",")]

            if len(keyword_list) < count:
                print_warning(f"关键词数量 ({len(keyword_list)}) 少于生成数量 ({count})")
                print_info("将重复使用关键词")

            print_info(f"正在批量生成 {count} 条内容...")

            succeeded = 0
            failed = 0

            # 批量生成
            for i in range(count):
                topic = keyword_list[i % len(keyword_list)]

                try:
                    # 尝试调用 content-creator
                    generated_content = None
                    if settings.CREATOR_CLI_PATH:
                        try:
                            result = content_creator_service.create_content(
                                account_id=account_id,
                                topic=topic,
                                category=category
                            )
                            if result and "content" in result:
                                generated_content = result["content"]
                        except Exception:
                            pass  # 继续创建草稿

                    # 创建内容记录
                    content_data = {
                        "title": topic,
                        "content_type": "article",
                        "content": generated_content or f"# {topic}\n\n待生成内容...",
                        "summary": f"基于选题: {topic}",
                        "category": category,
                        "topic": topic,
                        "status": "draft",
                        "tags": [topic],
                    }

                    content = content_service.create_content(db, content_data, account_id)
                    succeeded += 1

                    print_info(f"[{i+1}/{count}] 内容创建成功 (ID: {content.id})")

                except Exception as e:
                    failed += 1
                    print_error(f"[{i+1}/{count}] 内容创建失败: {e}")

            # 显示统计信息
            print_success(f"\n批量生成完成")
            print_info(f"成功: {succeeded}, 失败: {failed}, 总计: {count}")

    except Exception as e:
        handle_error(e)


@app.command("topic-search")
def topic_search(
    account_id: int = typer.Option(..., "--account-id", "-a", help="账号 ID"),
    keywords: str = typer.Option(..., "--keywords", "-k", help="关键词（逗号分隔）"),
    max_results: int = typer.Option(10, "--max-results", "-n", help="最大结果数")
):
    """选题搜索（调用 Tavily API）"""
    try:
        # 检查是否配置了 Tavily API
        if not settings.TAVILY_API_KEY:
            print_warning("未配置 Tavily API")
            print_info("请在 .env 文件中设置 TAVILY_API_KEY")
            raise typer.Exit(1)

        with get_session_local()() as db:
            # 检查账号是否存在
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                print_error(f"账号不存在: ID {account_id}")
                raise typer.Exit(1)

            print_info(f"正在搜索选题...")
            print_info(f"关键词: {keywords}")

            # 调用 Tavily API
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=settings.TAVILY_API_KEY)

                # 搜索结果
                search_result = client.search(
                    query=keywords,
                    search_depth="basic",
                    max_results=max_results
                )

                # 显示搜索结果
                if search_result.get("results"):
                    results_data = []
                    for idx, result in enumerate(search_result["results"], 1):
                        results_data.append({
                            "序号": idx,
                            "标题": result.get("title", "无标题")[:50],
                            "URL": result.get("url", "")[:60],
                            "评分": result.get("score", "-"),
                        })

                    print_table(results_data, title=f"选题搜索结果 (共 {len(results_data)} 条)", show_header=True)

                    print_success(f"\n找到 {len(search_result['results'])} 个相关选题")
                    print_info("使用 content generate --topic <标题> 生成内容")
                else:
                    print_warning("未找到相关选题")

            except ImportError:
                print_warning("未安装 Tavily SDK")
                print_info("请运行: pip install tavily-python")
            except Exception as e:
                print_error(f"搜索失败: {e}")

    except Exception as e:
        handle_error(e)


@app.command()
def update(
    content_id: int = typer.Argument(..., help="内容 ID"),
    title: str = typer.Option(None, "--title", "-t", help="内容标题"),
    content_text: str = typer.Option(None, "--content", "-c", help="内容正文"),
    summary: str = typer.Option(None, "--summary", help="摘要"),
):
    """更新内容"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = get_content(db, content_id)
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            # 准备更新数据
            update_data = {}
            if title:
                update_data["title"] = title
            if content_text is not None:
                update_data["content"] = content_text
            if summary is not None:
                update_data["summary"] = summary

            if not update_data:
                print_warning("没有提供任何更新内容")
                return

            # 更新内容
            print_info(f"正在更新内容 (ID: {content_id})...")
            content = content_service.update_content(db, content_id, update_data)

            print_success("内容更新成功")

            # 显示更新后的信息
            content_info = format_content_info(content, detailed=True)

            info_table = Table(title="内容详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in content_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

    except Exception as e:
        handle_error(e)


@app.command()
def delete(
    content_id: int = typer.Argument(..., help="内容 ID")
):
    """删除内容（需确认）"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = get_content(db, content_id)
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            # 确认删除
            if not confirm_action(
                f"确定要删除内容吗？\n标题: {content.title}\n此操作不可逆！",
                default=False,
            ):
                print_info("已取消删除操作")
                return

            # 删除内容
            print_info(f"正在删除内容 (ID: {content_id})...")
            success = content_service.delete_content(db, content_id)

            if success:
                print_success(f"内容删除成功 (ID: {content_id})")
            else:
                print_error("删除失败")

    except Exception as e:
        handle_error(e)


@app.command()
def info(
    content_id: int = typer.Argument(..., help="内容 ID")
):
    """查看内容详情"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = get_content(db, content_id)
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            # 显示内容信息
            content_info = format_content_info(content, detailed=True)

            info_table = Table(title="内容详情", show_header=True)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="green")

            for key, value in content_info.items():
                info_table.add_row(key, str(value))

            from rich.console import Console
            console = Console()
            console.print(info_table)

            # 显示内容预览
            if content.content:
                preview = content.content[:200] + "..." if len(content.content) > 200 else content.content
                print(Panel(preview, title="内容预览", style="blue"))

    except Exception as e:
        handle_error(e)


@app.command("submit-review")
def submit_review(
    content_id: int = typer.Argument(..., help="内容 ID")
):
    """提交审核"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = get_content(db, content_id)
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            print_info(f"正在提交审核...")

            # 提交审核
            content = content_service.submit_for_review(db, content_id)

            print_success(f"内容已提交审核 (ID: {content_id})")
            print_info(f"审核状态: {content.review_status}")

    except Exception as e:
        handle_error(e)


@app.command()
def approve(
    content_id: int = typer.Argument(..., help="内容 ID"),
    comment: str = typer.Option(None, "--comment", "-c", help="审核意见")
):
    """审核通过"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = get_content(db, content_id)
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            print_info(f"正在审核通过...")

            # 审核通过
            content = content_service.approve_content(db, content_id)

            print_success(f"内容审核通过 (ID: {content_id})")
            print_info(f"状态: {content.review_status}")

            if comment:
                print_info(f"审核意见: {comment}")

    except Exception as e:
        handle_error(e)


@app.command()
def reject(
    content_id: int = typer.Argument(..., help="内容 ID"),
    reason: str = typer.Option(..., "--reason", "-r", help="拒绝原因")
):
    """审核拒绝"""
    try:
        with get_session_local()() as db:
            # 获取内容
            content = get_content(db, content_id)
            if not content:
                print_error(f"内容不存在: ID {content_id}")
                raise typer.Exit(1)

            print_info(f"正在拒绝审核...")

            # 审核拒绝
            content = content_service.reject_content(db, content_id, reason)

            print_success(f"内容审核已拒绝 (ID: {content_id})")
            print_info(f"状态: {content.review_status}")
            print_info(f"拒绝原因: {reason}")

    except Exception as e:
        handle_error(e)


@app.command("review-list")
def review_list():
    """待审核列表"""
    try:
        with get_session_local()() as db:
            # 获取待审核列表
            contents = content_service.get_pending_reviews(db)

            if not contents:
                print_warning("没有待审核的内容")
                return

            # 格式化输出
            data = []
            for content in contents:
                account_name = content.account.name if content.account else "未知"
                data.append({
                    "ID": content.id,
                    "标题": content.title,
                    "账号": account_name,
                    "审核状态": content.review_status,
                    "创建时间": format_datetime(content.created_at),
                })

            print_table(data, title=f"待审核列表 (共 {len(contents)} 条)", show_header=True)

    except Exception as e:
        handle_error(e)


@app.command()
def statistics():
    """审核统计"""
    try:
        with get_session_local()() as db:
            # 获取审核统计
            stats = content_service.get_review_statistics(db)

            # 显示统计信息
            stats_table = Table(title="审核统计", show_header=True)
            stats_table.add_column("项目", style="cyan")
            stats_table.add_column("数量", style="green")

            stats_table.add_row("总计", str(stats["total"]))
            stats_table.add_row("待审核", str(stats["pending"]))
            stats_table.add_row("审核中", str(stats["reviewing"]))
            stats_table.add_row("已通过", str(stats["approved"]))
            stats_table.add_row("已拒绝", str(stats["rejected"]))

            from rich.console import Console
            console = Console()
            console.print(stats_table)

            # 计算通过率
            if stats["approved"] + stats["rejected"] > 0:
                approval_rate = stats["approved"] / (stats["approved"] + stats["rejected"]) * 100
                print_info(f"通过率: {approval_rate:.1f}%")

    except Exception as e:
        handle_error(e)
