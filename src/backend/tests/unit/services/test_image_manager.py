"""图片管理服务单元测试"""

import os
import pytest
from unittest.mock import Mock, patch
from app.services.image_manager import ImageManager


class TestImageManager:
    """图片管理服务测试类"""

    def test_initialization(self):
        """测试初始化"""
        # 执行测试
        manager = ImageManager()

        # 断言结果
        assert manager is not None
        assert hasattr(manager, "upload_dir")
        assert os.path.exists(manager.upload_dir)

    def test_upload_image_success(self, tmpdir):
        """测试成功上传图片"""
        # 准备测试数据
        mock_file = Mock()
        mock_file.filename = "test_image.jpg"
        mock_file.file.read.return_value = b"dummy image data"

        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()
            file_path = manager.upload_image(mock_file, 1)

            # 断言结果
            assert file_path is not None
            assert os.path.exists(file_path)
            assert "1" in file_path
            assert "test_image.jpg" in file_path

            # 验证文件内容
            with open(file_path, "rb") as f:
                assert f.read() == b"dummy image data"

    def test_upload_image_failure(self, tmpdir):
        """测试图片上传失败"""
        # 准备测试数据
        mock_file = Mock()
        mock_file.filename = "test_image.jpg"
        mock_file.file.read.side_effect = Exception("Read error")

        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()

            # 断言会抛出异常
            with pytest.raises(Exception) as exc_info:
                manager.upload_image(mock_file, 1)

            assert "图片上传失败" in str(exc_info.value)

    @patch("app.services.image_manager.requests.get")
    def test_download_image_success(self, mock_get, tmpdir):
        """测试成功下载图片"""
        # 准备测试数据
        mock_response = Mock()
        mock_response.content = b"downloaded image data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()
            file_path = manager.download_image("https://example.com/image.jpg", 1)

            # 断言结果
            assert file_path is not None
            assert os.path.exists(file_path)
            assert "1" in file_path
            assert "image.jpg" in file_path

            # 验证文件内容
            with open(file_path, "rb") as f:
                assert f.read() == b"downloaded image data"

    @patch("app.services.image_manager.requests.get")
    def test_download_image_failure(self, mock_get, tmpdir):
        """测试图片下载失败"""
        # 准备测试数据
        mock_get.side_effect = Exception("Network error")

        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()

            # 断言会抛出异常
            with pytest.raises(Exception) as exc_info:
                manager.download_image("https://example.com/image.jpg", 1)

            assert "图片下载失败" in str(exc_info.value)

    def test_get_image_path_absolute(self, tmpdir):
        """测试获取绝对路径的图片路径"""
        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()
            abs_path = "/absolute/path/to/image.jpg"
            result = manager.get_image_path(abs_path)

            # 断言结果
            assert result == abs_path

    def test_get_image_path_relative(self, tmpdir):
        """测试获取相对路径的图片路径"""
        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()
            rel_path = "1/image.jpg"
            result = manager.get_image_path(rel_path)

            # 断言结果
            assert result == os.path.join(str(tmpdir), rel_path)

    def test_delete_image_success(self, tmpdir):
        """测试成功删除图片"""
        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()

            # 创建测试文件
            account_dir = os.path.join(str(tmpdir), "1")
            os.makedirs(account_dir, exist_ok=True)
            file_path = os.path.join(account_dir, "test_image.jpg")
            with open(file_path, "wb") as f:
                f.write(b"dummy data")

            # 执行测试
            result = manager.delete_image(file_path)

            # 断言结果
            assert result is True
            assert not os.path.exists(file_path)

    def test_delete_image_nonexistent(self, tmpdir):
        """测试删除不存在的图片"""
        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()

            # 尝试删除不存在的文件
            result = manager.delete_image("nonexistent_file.jpg")

            # 断言结果
            assert result is True

    def test_optimize_image_success(self, tmpdir):
        """测试成功优化图片"""
        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()

            # 创建测试图片文件（简单的 PNG 文件）
            account_dir = os.path.join(str(tmpdir), "1")
            os.makedirs(account_dir, exist_ok=True)
            file_path = os.path.join(account_dir, "test_image.png")

            # 创建一个简单的 PNG 文件
            from PIL import Image
            img = Image.new("RGB", (100, 100), color="red")
            img.save(file_path)

            # 执行测试
            optimized_path = manager.optimize_image(file_path)

            # 断言结果
            assert optimized_path is not None
            assert os.path.exists(optimized_path)
            assert optimized_path == file_path

    def test_optimize_image_failure(self, tmpdir):
        """测试图片优化失败"""
        # 使用临时目录作为上传目录
        with patch("app.services.image_manager.settings.IMAGE_UPLOAD_DIR", str(tmpdir)):
            manager = ImageManager()

            # 创建一个无效的图片文件
            account_dir = os.path.join(str(tmpdir), "1")
            os.makedirs(account_dir, exist_ok=True)
            file_path = os.path.join(account_dir, "invalid_image.txt")
            with open(file_path, "w") as f:
                f.write("This is not an image file")

            # 执行测试
            with pytest.raises(Exception) as exc_info:
                manager.optimize_image(file_path)

            # 断言结果
            assert "图片优化失败" in str(exc_info.value)
