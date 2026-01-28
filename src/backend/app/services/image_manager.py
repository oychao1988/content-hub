"""
图片管理服务
负责图片上传、存储、处理和管理
"""
import os
import requests
from typing import Optional
from app.core.config import settings


class ImageManager:
    """图片管理服务"""

    def __init__(self):
        self.upload_dir = settings.IMAGE_UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def upload_image(self, image_file, account_id: int) -> str:
        """
        上传图片
        :param image_file: 图片文件对象
        :param account_id: 账号 ID
        :return: 图片路径
        """
        try:
            # 创建账号图片目录
            account_dir = os.path.join(self.upload_dir, str(account_id))
            os.makedirs(account_dir, exist_ok=True)

            # 生成文件名
            filename = os.path.basename(image_file.filename)
            file_path = os.path.join(account_dir, filename)

            # 保存图片
            with open(file_path, "wb") as f:
                f.write(image_file.file.read())

            # 返回相对路径
            return file_path

        except Exception as e:
            raise Exception(f"图片上传失败: {str(e)}")

    def download_image(self, image_url: str, account_id: int) -> str:
        """
        下载图片
        :param image_url: 图片 URL
        :param account_id: 账号 ID
        :return: 图片路径
        """
        try:
            # 创建账号图片目录
            account_dir = os.path.join(self.upload_dir, str(account_id))
            os.makedirs(account_dir, exist_ok=True)

            # 下载图片
            response = requests.get(image_url)
            response.raise_for_status()

            # 生成文件名
            filename = os.path.basename(image_url.split("?")[0]) or "image.jpg"
            file_path = os.path.join(account_dir, filename)

            # 保存图片
            with open(file_path, "wb") as f:
                f.write(response.content)

            return file_path

        except Exception as e:
            raise Exception(f"图片下载失败: {str(e)}")

    def get_image_path(self, image_path: str) -> str:
        """
        获取图片的完整路径
        :param image_path: 图片路径
        :return: 完整路径
        """
        if image_path.startswith("/"):
            return image_path
        return os.path.join(self.upload_dir, image_path)

    def delete_image(self, image_path: str) -> bool:
        """
        删除图片
        :param image_path: 图片路径
        :return: 是否成功
        """
        try:
            full_path = self.get_image_path(image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            return True
        except Exception as e:
            raise Exception(f"图片删除失败: {str(e)}")

    def optimize_image(self, image_path: str) -> str:
        """
        优化图片
        :param image_path: 图片路径
        :return: 优化后的图片路径
        """
        try:
            # 图片优化逻辑，这里可以使用 Pillow 等库
            from PIL import Image
            full_path = self.get_image_path(image_path)
            with Image.open(full_path) as img:
                # 简单的压缩优化
                img.save(full_path, optimize=True, quality=85)
            return full_path
        except Exception as e:
            raise Exception(f"图片优化失败: {str(e)}")


# 全局服务实例
image_manager = ImageManager()
