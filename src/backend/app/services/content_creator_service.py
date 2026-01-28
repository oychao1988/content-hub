"""
内容生成服务
负责调用 content-creator CLI 生成内容
"""
import subprocess
import json
import os
from typing import Optional
from app.core.config import settings


class ContentCreatorService:
    """内容生成服务"""

    @staticmethod
    def create_content(account_id: int, topic: str, category: str) -> dict:
        """
        调用 content-creator CLI 生成内容
        :param account_id: 账号 ID
        :param topic: 选题
        :param category: 内容板块
        :return: 生成的内容信息
        """
        try:
            command = [
                settings.CREATOR_CLI_PATH,
                "create",
                "--account-id", str(account_id),
                "--topic", topic,
                "--category", category
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            return json.loads(result.stdout)

        except subprocess.CalledProcessError as e:
            raise Exception(f"内容生成失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception(f"content-creator CLI 未找到，请检查配置")

    @staticmethod
    def generate_cover_image(topic: str) -> str:
        """
        生成封面图片
        :param topic: 选题
        :return: 图片路径
        """
        try:
            command = [
                settings.CREATOR_CLI_PATH,
                "generate-cover",
                "--topic", topic
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            return json.loads(result.stdout)["image_path"]

        except subprocess.CalledProcessError as e:
            raise Exception(f"封面生成失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception(f"content-creator CLI 未找到，请检查配置")

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
