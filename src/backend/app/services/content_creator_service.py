"""
内容生成服务
负责调用 content-creator CLI 生成内容
"""
import subprocess
import json
import os
import time
import re
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.exceptions import (
    CreatorCLINotFoundException,
    CreatorTimeoutException,
    CreatorInvalidResponseException,
    CreatorException
)
from app.utils.custom_logger import log


class ContentCreatorService:
    """内容生成服务"""

    # 默认超时时间（秒）
    # content-creator CLI 通常需要 3-5 分钟完成
    DEFAULT_TIMEOUT = 300  # 5分钟
    COVER_TIMEOUT = 60

    # 最大重试次数
    MAX_RETRIES = 2

    # ContentHub 图片目录（目标路径）
    CONTENTHUB_IMAGES_DIR = "data/images"

    @staticmethod
    def _get_creator_project_path() -> str:
        """
        获取 content-creator 项目路径

        :return: content-creator 项目路径
        """
        # 优先从配置读取
        if settings.CREATOR_PROJECT_PATH:
            return settings.CREATOR_PROJECT_PATH

        # 尝试从环境变量读取
        creator_path = os.environ.get('CREATOR_PROJECT_PATH')
        if creator_path:
            return creator_path

        # 尝试从包装脚本中推断路径
        if os.path.exists(settings.CREATOR_CLI_PATH):
            try:
                with open(settings.CREATOR_CLI_PATH, 'r') as f:
                    content = f.read()
                    # 从包装脚本中提取 cd 命令的路径
                    import re
                    cd_match = re.search(r'cd\s+([^\s]+)', content)
                    if cd_match:
                        log.info(f"Inferred CREATOR_PROJECT_PATH from CLI wrapper script: {cd_match.group(1)}")
                        return cd_match.group(1)
            except Exception as e:
                log.warning(f"Failed to read CLI wrapper script: {str(e)}")

        # 未配置，使用相对路径
        log.warning("CREATOR_PROJECT_PATH not configured, image copying may not work properly")
        return "."

    @staticmethod
    def _copy_images_to_contenthub(image_paths: list) -> list:
        """
        将图片从 content-creator 项目复制到 ContentHub 项目

        :param image_paths: content-creator 返回的图片路径列表（相对路径）
        :return: ContentHub 中的图片路径列表
        """
        import shutil
        from pathlib import Path

        converted_paths = []

        # 获取 content-creator 项目路径
        creator_project_path = ContentCreatorService._get_creator_project_path()
        log.info(f"Using creator project path: {creator_project_path}")

        # 确保 ContentHub 图片目录存在
        contenthub_images_dir = Path(ContentCreatorService.CONTENTHUB_IMAGES_DIR)
        contenthub_images_dir.mkdir(parents=True, exist_ok=True)

        for img_path in image_paths:
            # 构造源图片的绝对路径（content-creator 项目）
            source_path = Path(creator_project_path) / img_path

            # 如果源文件存在，复制到 ContentHub
            if source_path.exists():
                filename = source_path.name
                dest_path = contenthub_images_dir / filename

                try:
                    # 复制文件
                    shutil.copy2(source_path, dest_path)
                    # 返回 ContentHub 中的相对路径
                    converted_paths.append(f"{ContentCreatorService.CONTENTHUB_IMAGES_DIR}/{filename}")
                    log.info(f"Copied image: {filename}")
                except Exception as e:
                    log.warning(f"Failed to copy image {filename}: {str(e)}")
                    # 保留原路径（即使复制失败）
                    converted_paths.append(img_path)
            else:
                log.warning(f"Source image not found: {source_path}")
                # 保留原路径
                converted_paths.append(img_path)

        return converted_paths

    @staticmethod
    def _parse_cli_output(stdout: str) -> Dict[str, Any]:
        """
        解析 content-creator CLI 的文本输出

        :param stdout: CLI 标准输出
        :return: 解析后的数据字典
        :raises: CreatorInvalidResponseException
        """
        try:
            # 初始化结果字典
            result = {
                "success": False,
                "task_id": None,
                "status": None,
                "duration": None,
                "content": None,
                "images": [],
                "quality_score": None,
                "quality_passed": None
            }

            # 提取任务ID
            task_id_match = re.search(r'任务ID:\s*(\S+)', stdout)
            if task_id_match:
                result["task_id"] = task_id_match.group(1)

            # 提取状态
            status_match = re.search(r'状态:\s*(\S+)', stdout)
            if status_match:
                result["status"] = status_match.group(1)
                if "完成" in result["status"] or "completed" in result["status"].lower():
                    result["success"] = True

            # 提取耗时（格式：3分23秒 或 23秒）
            duration_match = re.search(r'耗时:\s*((\d+)分)?(\d+)秒', stdout)
            if duration_match:
                minutes = int(duration_match.group(2)) if duration_match.group(2) else 0
                seconds = int(duration_match.group(3))
                result["duration"] = minutes * 60 + seconds
                log.info(f"Extracted duration: {minutes}m {seconds}s = {result['duration']}s")

            # 提取生成的内容（在 "📝 生成的内容:" 和下一个分隔符之间）
            content_match = re.search(
                r'📝 生成的内容:.*?────────────────────────────────────────\n(.*?)\n────────────────────────────────────────',
                stdout,
                re.DOTALL
            )
            if content_match:
                content = content_match.group(1).strip()
                result["content"] = content
                log.info(f"Extracted content length: {len(content)} characters")

            # 提取图片列表（在 "🖼️ 生成的配图:" 部分）
            images_section = re.search(
                r'🖼️ 生成的配图:.*?────────────────────────────────────────\n(.*?)\n────────────────────────────────────────',
                stdout,
                re.DOTALL
            )
            if images_section:
                images_text = images_section.group(1).strip()
                # 提取所有图片路径
                image_paths = re.findall(r'(data/images/[^\s]+)', images_text)

                # 复制图片到 ContentHub 目录并转换路径
                converted_paths = ContentCreatorService._copy_images_to_contenthub(image_paths)

                result["images"] = converted_paths
                log.info(f"Extracted and copied {len(converted_paths)} images")

            # 提取文本质检信息
            quality_match = re.search(r'🔍 文本质检:.*?状态:\s*(\S+).*?评分:\s*([\d.]+)', stdout, re.DOTALL)
            if quality_match:
                result["quality_passed"] = "通过" in quality_match.group(1) or "passed" in quality_match.group(1).lower()
                try:
                    result["quality_score"] = float(quality_match.group(2))
                except ValueError:
                    pass

            # 验证必要字段
            if not result["content"]:
                log.error(f"Failed to extract content from CLI output. Output preview: {stdout[:500]}")
                raise CreatorInvalidResponseException("无法从CLI输出中提取内容")

            if not result["success"]:
                log.warning(f"CLI task may not have completed successfully. Status: {result.get('status')}")

            return result

        except Exception as e:
            log.error(f"Error parsing CLI output: {str(e)}\nOutput preview: {stdout[:500]}")
            raise CreatorInvalidResponseException(f"解析CLI输出失败: {str(e)}")

    @staticmethod
    def _run_cli_command(
        command: list,
        timeout: int,
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        执行 CLI 命令并处理错误

        :param command: 命令列表
        :param timeout: 超时时间（秒）
        :param retries: 当前重试次数
        :return: 解析后的响应数据（从文本输出提取）
        :raises: CreatorException 及其子类
        """
        cli_path = command[0]

        # 检查 CLI 是否存在
        if not os.path.exists(cli_path):
            log.error(f"Creator CLI not found at: {cli_path}")
            raise CreatorCLINotFoundException(cli_path)

        try:
            log.info(f"Executing Creator CLI: {' '.join(command)}")

            start_time = time.time()

            # 设置环境变量，确保使用CLI模式和debug日志
            env = os.environ.copy()
            env['LLM_SERVICE_TYPE'] = 'cli'
            env['LOG_LEVEL'] = 'info'

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
                env=env
            )
            elapsed_time = time.time() - start_time

            log.info(f"Creator CLI completed in {elapsed_time:.2f}s")

            # 解析文本输出（content-creator CLI 输出纯文本，不是JSON）
            return ContentCreatorService._parse_cli_output(result.stdout)

        except subprocess.TimeoutExpired as e:
            elapsed_time = time.time() - start_time
            log.error(f"Creator CLI timeout after {elapsed_time:.2f}s (limit: {timeout}s)")

            # 如果还有重试次数，则重试
            if retries < ContentCreatorService.MAX_RETRIES:
                log.warning(f"Retrying Creator CLI command (attempt {retries + 1}/{ContentCreatorService.MAX_RETRIES})")
                time.sleep(2 ** retries)  # 指数退避：1s, 2s, 4s
                return ContentCreatorService._run_cli_command(command, timeout, retries + 1)

            raise CreatorTimeoutException(timeout)

        except subprocess.CalledProcessError as e:
            error_details = {
                "return_code": e.returncode,
                "stderr": e.stderr[:500] if e.stderr else "No error output",
                "stdout": e.stdout[:500] if e.stdout else "No output",
                "command": ' '.join(command)
            }

            # 如果还有重试次数且错误是可重试的，则重试
            is_retryable = e.returncode in [1, 2, 130]  # 1=通用错误, 2=误用, 130=SIGINT
            if retries < ContentCreatorService.MAX_RETRIES and is_retryable:
                log.warning(
                    f"Creator CLI failed with code {e.returncode}, "
                    f"retrying (attempt {retries + 1}/{ContentCreatorService.MAX_RETRIES})"
                )
                time.sleep(2 ** retries)  # 指数退避
                return ContentCreatorService._run_cli_command(command, timeout, retries + 1)

            log.error(f"Creator CLI execution failed: {error_details}")
            raise CreatorException(
                message=f"内容生成失败 (返回码: {e.returncode})",
                details=error_details
            )

        except CreatorException:
            # 重新抛出已知的 Creator 异常
            raise
        except Exception as e:
            log.exception(f"Unexpected error executing Creator CLI: {str(e)}")
            raise CreatorException(
                message=f"执行内容生成时发生意外错误: {str(e)}",
                details={"error_type": type(e).__name__}
            )

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
        调用 content-creator CLI 生成内容（支持读取账号配置）

        :param topic: 文章主题
        :param requirements: 创作要求（字数、结构等）
        :param target_audience: 目标受众
        :param tone: 语气风格（CLI 参数优先级高于账号配置）
        :param account_id: 账号 ID（用于读取账号配置）
        :param category: 内容分类（已废弃，保留兼容性）
        :param db: 数据库会话（用于读取账号配置）
        :return: 生成的内容信息
        """
        if not settings.CREATOR_CLI_PATH:
            raise CreatorCLINotFoundException("CREATOR_CLI_PATH 未配置")

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

        # 构建命令参数
        command = [
            settings.CREATOR_CLI_PATH,
            "create",
            "--type", "content-creator",  # 使用标准工作流，不是agent模式
            "--mode", "sync",              # 同步模式，等待结果
            "--topic", topic,
            "--requirements", requirements,
            "--target-audience", target_audience,
            "--tone", tone,
            "--priority", "normal"
        ]

        log.info(f"Generating content with account config: topic='{topic}', tone='{tone}'")

        # 执行命令并解析输出
        result = ContentCreatorService._run_cli_command(
            command,
            timeout=ContentCreatorService.DEFAULT_TIMEOUT
        )

        return result

    @staticmethod
    def generate_cover_image(topic: str) -> str:
        """
        生成封面图片

        :param topic: 选题
        :return: 图片路径
        """
        if not settings.CREATOR_CLI_PATH:
            raise CreatorCLINotFoundException("CREATOR_CLI_PATH 未配置")

        command = [
            settings.CREATOR_CLI_PATH,
            "generate-cover",
            "--topic", topic
        ]

        response = ContentCreatorService._run_cli_command(
            command,
            timeout=ContentCreatorService.COVER_TIMEOUT
        )

        # 验证响应格式
        if "image_path" not in response:
            log.error(f"Invalid cover generation response: {response}")
            raise CreatorInvalidResponseException(
                json.dumps(response)[:500]
            )

        return response["image_path"]

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
