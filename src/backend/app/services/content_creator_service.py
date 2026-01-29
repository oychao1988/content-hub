"""
内容生成服务
负责调用 content-creator CLI 生成内容
"""
import subprocess
import json
import os
import time
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
    DEFAULT_TIMEOUT = 120
    COVER_TIMEOUT = 60

    # 最大重试次数
    MAX_RETRIES = 2

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
        :return: 解析后的 JSON 响应
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
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )
            elapsed_time = time.time() - start_time

            log.info(f"Creator CLI completed in {elapsed_time:.2f}s")

            # 解析 JSON 响应
            try:
                response = json.loads(result.stdout)
                return response
            except json.JSONDecodeError as e:
                log.error(
                    f"Failed to parse Creator CLI response: {e}\n"
                    f"stdout: {result.stdout[:500]}"
                )
                raise CreatorInvalidResponseException(result.stdout)

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
    def create_content(account_id: int, topic: str, category: str) -> dict:
        """
        调用 content-creator CLI 生成内容

        :param account_id: 账号 ID
        :param topic: 选题
        :param category: 内容板块
        :return: 生成的内容信息
        """
        if not settings.CREATOR_CLI_PATH:
            raise CreatorCLINotFoundException("CREATOR_CLI_PATH 未配置")

        command = [
            settings.CREATOR_CLI_PATH,
            "create",
            "--account-id", str(account_id),
            "--topic", topic,
            "--category", category
        ]

        return ContentCreatorService._run_cli_command(
            command,
            timeout=ContentCreatorService.DEFAULT_TIMEOUT
        )

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
