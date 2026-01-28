"""
内容发布服务
负责调用 content-publisher API 发布内容到微信公众号
"""
import requests
import json
from typing import Optional
from app.core.config import settings


class ContentPublisherService:
    """内容发布服务"""

    @staticmethod
    def publish_to_wechat(content_id: int, account_id: int, publish_to_draft: bool = True) -> dict:
        """
        发布到微信公众号
        :param content_id: 内容 ID
        :param account_id: 账号 ID
        :param publish_to_draft: 是否发布到草稿箱
        :return: 发布结果
        """
        try:
            url = f"{settings.PUBLISHER_API_URL}/api/publish"
            headers = {
                "Authorization": f"Bearer {settings.PUBLISHER_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "content_id": content_id,
                "account_id": account_id,
                "publish_to_draft": publish_to_draft
            }

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise Exception(f"发布失败: {str(e)}")

    @staticmethod
    def get_publish_status(media_id: str) -> dict:
        """
        获取发布状态
        :param media_id: 媒体 ID
        :return: 状态信息
        """
        try:
            url = f"{settings.PUBLISHER_API_URL}/api/status"
            headers = {
                "Authorization": f"Bearer {settings.PUBLISHER_API_KEY}"
            }
            params = {
                "media_id": media_id
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise Exception(f"获取发布状态失败: {str(e)}")

    @staticmethod
    def upload_media(image_path: str, account_id: int) -> dict:
        """
        上传媒体文件到微信
        :param image_path: 图片路径
        :param account_id: 账号 ID
        :return: 媒体信息
        """
        try:
            url = f"{settings.PUBLISHER_API_URL}/api/upload-media"
            headers = {
                "Authorization": f"Bearer {settings.PUBLISHER_API_KEY}"
            }

            with open(image_path, "rb") as f:
                files = {"media": f}
                data = {"account_id": account_id}

                response = requests.post(url, files=files, data=data, headers=headers)
                response.raise_for_status()

                return response.json()

        except Exception as e:
            raise Exception(f"媒体上传失败: {str(e)}")

    @staticmethod
    def get_access_token(account_id: int) -> str:
        """
        获取访问令牌
        :param account_id: 账号 ID
        :return: 访问令牌
        """
        try:
            url = f"{settings.PUBLISHER_API_URL}/api/access-token"
            headers = {
                "Authorization": f"Bearer {settings.PUBLISHER_API_KEY}"
            }
            params = {
                "account_id": account_id
            }

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            return response.json()["access_token"]

        except Exception as e:
            raise Exception(f"获取访问令牌失败: {str(e)}")

    @staticmethod
    def create_menu(account_id: int, menu_data: dict) -> dict:
        """
        创建微信公众号菜单
        :param account_id: 账号 ID
        :param menu_data: 菜单数据
        :return: 操作结果
        """
        try:
            url = f"{settings.PUBLISHER_API_URL}/api/menu"
            headers = {
                "Authorization": f"Bearer {settings.PUBLISHER_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "account_id": account_id,
                "menu_data": menu_data
            }

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise Exception(f"菜单创建失败: {str(e)}")


# 全局服务实例
content_publisher_service = ContentPublisherService()
