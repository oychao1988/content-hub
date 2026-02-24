"""
内容生成服务
负责调用 content-creator HTTP API 生成内容
"""
import json
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.exceptions import (
    CreatorTimeoutException,
    CreatorInvalidResponseException,
    CreatorException
)
from app.utils.custom_logger import log
from app.services.creator_api_client import get_creator_api_client


class ContentCreatorService:
    """内容生成服务（使用 HTTP API）"""

    # 默认超时时间（秒）
    # content-creator API 通常需要 3-5 分钟完成
    DEFAULT_TIMEOUT = 300  # 5分钟
    COVER_TIMEOUT = 60

    # ContentHub 图片目录（目标路径）
    CONTENTHUB_IMAGES_DIR = "data/images"

    @staticmethod
    def _convert_image_urls(image_urls: list) -> list:
        """
        将 content-creator 返回的图片 URL 转换为本地路径

        :param image_urls: content-creator 返回的图片 URL 列表
        :return: ContentHub 中的图片路径列表
        """
        # 如果图片 URL 是完整的 HTTP URL，保留原样
        # 如果是相对路径，需要从 content-creator 下载
        converted_paths = []

        for url in image_urls:
            if url.startswith("http://") or url.startswith("https://"):
                # HTTP URL：保留原样，或者可以下载到本地
                # 这里暂时保留原 URL，由调用方决定是否下载
                converted_paths.append(url)
            else:
                # 相对路径：可能需要从 content-creator 项目复制
                # 但由于现在使用 HTTP API，图片应该都是 URL
                log.warning(f"Non-URL image path: {url}")
                converted_paths.append(url)

        return converted_paths

    @staticmethod
    def create_content(
        topic: str,
        requirements: Optional[str] = None,
        target_audience: str = "普通读者",
        tone: str = "友好专业",
        account_id: Optional[int] = None,
        category: Optional[str] = None,
        db: Optional['Session'] = None
    ) -> dict:
        """
        调用 content-creator HTTP API 生成内容（支持读取账号配置）

        :param topic: 文章主题
        :param requirements: 创作要求（字数、结构等）
        :param target_audience: 目标受众
        :param tone: 语气风格（CLI 参数优先级高于账号配置）
        :param account_id: 账号 ID（用于读取账号配置）
        :param category: 内容分类（已废弃，保留兼容性）
        :param db: 数据库会话（用于读取账号配置）
        :return: 生成的内容信息
        """
        # 检查 API 配置
        if not settings.CREATOR_API_BASE_URL:
            raise CreatorException("CREATOR_API_BASE_URL 未配置")

        # 读取账号配置
        account_config = {}
        if account_id and db:
            from app.models.account import Account
            from app.models.theme import ContentTheme

            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                # 读取写作风格配置
                if account.writing_style:
                    ws = account.writing_style
                    # 仅当 tone 使用默认值时，才使用账号配置的 tone
                    if tone == "友好专业":  # 使用默认值表示未指定
                        tone = ws.tone or tone

                    style_prompt = f"\n## 写作风格要求\n"
                    style_prompt += f"- 语气：{ws.tone}\n"
                    if ws.persona:
                        style_prompt += f"- 人设：{ws.persona}\n"
                    style_prompt += f"- 字数：{ws.min_words}-{ws.max_words}字\n"
                    if ws.emoji_usage:
                        style_prompt += f"- 表情使用：{ws.emoji_usage}\n"
                    if ws.forbidden_words:
                        style_prompt += f"- 禁用词：{', '.join(ws.forbidden_words)}\n"

                    account_config['style_prompt'] = style_prompt
                    log.info(f"Applied writing style config: tone={ws.tone}, words={ws.min_words}-{ws.max_words}")

                # 读取内容主题配置
                if account.publish_config and account.publish_config.theme_id:
                    theme = db.query(ContentTheme).filter(
                        ContentTheme.id == account.publish_config.theme_id
                    ).first()

                    if theme:
                        theme_prompt = f"\n## 内容主题\n"
                        theme_prompt += f"- 主题：{theme.name}\n"
                        if theme.description:
                            theme_prompt += f"- 描述：{theme.description}\n"
                        if theme.type:
                            theme_prompt += f"- 类型：{theme.type}\n"

                        account_config['theme_prompt'] = theme_prompt
                        log.info(f"Applied content theme: {theme.name}")

        # 构建默认创作要求
        if not requirements:
            requirements = f"写一篇关于'{topic}'的文章，要求内容详实、结构清晰"

        # 整合账号配置到 requirements
        if account_config:
            enhanced_requirements = requirements
            if 'style_prompt' in account_config:
                enhanced_requirements += account_config['style_prompt']
            if 'theme_prompt' in account_config:
                enhanced_requirements += account_config['theme_prompt']
            requirements = enhanced_requirements
            log.info(f"Enhanced requirements with account config")

        # 构建硬性约束（从写作风格配置中提取）
        hard_constraints = None
        if account_id and db:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account and account.writing_style:
                ws = account.writing_style
                hard_constraints = {
                    "minWords": ws.min_words,
                    "maxWords": ws.max_words,
                }
                if ws.forbidden_words:
                    hard_constraints["keywords"] = ws.forbidden_words

        log.info(f"Generating content with account config: topic='{topic}', tone='{tone}'")

        # 获取 API 客户端
        client = get_creator_api_client()

        try:
            # 调用 HTTP API 创建同步任务
            result = client.create_task_sync(
                topic=topic,
                requirements=requirements,
                target_audience=target_audience,
                tone=tone,
                hard_constraints=hard_constraints,
            )

            # 转换图片 URL
            if result.get("images"):
                result["images"] = ContentCreatorService._convert_image_urls(result["images"])

            return result

        except CreatorException:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_content: {str(e)}")
            raise CreatorException(
                message=f"生成内容时发生意外错误: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    @staticmethod
    def generate_cover_image(topic: str) -> str:
        """
        生成封面图片

        注意：此功能当前未在 content-creator HTTP API 中实现
        保留此方法以保持向后兼容性

        :param topic: 选题
        :return: 图片路径
        :raises: CreatorException - 功能暂未实现
        """
        # TODO: 等待 content-creator API 支持封面生成功能
        raise CreatorException(
            message="封面图片生成功能暂未在 HTTP API 中实现",
            details={"suggestion": "请使用 content-creator CLI 或等待 API 功能更新"}
        )

    @staticmethod
    def extract_images_from_content(content: Optional[str]) -> list:
        """
        从内容中提取图片
        :param content: 内容文本
        :return: 图片列表
        """
        images = []
        if not content:
            return images

        # 简单的图片提取逻辑，实际项目中可能需要更复杂的解析
        import re
        # 匹配 Markdown 图片语法：![alt](url)
        pattern = r"!\[.*?\]\((https?://[^\)]+)\)"
        images = re.findall(pattern, content)
        return images


# 全局服务实例
content_creator_service = ContentCreatorService()
