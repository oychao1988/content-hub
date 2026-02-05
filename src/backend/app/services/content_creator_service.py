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
                result["images"] = image_paths
                log.info(f"Extracted {len(image_paths)} images")

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
        category: Optional[str] = None
    ) -> dict:
        """
        调用 content-creator CLI 生成内容

        :param topic: 文章主题
        :param requirements: 创作要求（字数、结构等）
        :param target_audience: 目标受众
        :param tone: 语气风格
        :param account_id: 账号 ID（已废弃，保留兼容性）
        :param category: 内容分类（已废弃，保留兼容性）
        :return: 生成的内容信息
        """
        if not settings.CREATOR_CLI_PATH:
            raise CreatorCLINotFoundException("CREATOR_CLI_PATH 未配置")

        # 构建默认创作要求
        if not requirements:
            requirements = f"写一篇关于'{topic}'的文章，要求内容详实、结构清晰"

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

        log.info(f"Generating content with Creator CLI: topic='{topic}', requirements='{requirements[:50]}...'")

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
