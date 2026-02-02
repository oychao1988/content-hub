"""
内容生成服务单元测试
"""
import pytest
import subprocess
from unittest.mock import patch, MagicMock
import json
import os
from app.services.content_creator_service import ContentCreatorService
from app.core.config import settings


@pytest.mark.unit
@patch('os.path.exists')
@patch('app.services.content_creator_service.subprocess.run')
def test_create_content_success(mock_run, mock_exists):
    """测试成功生成内容"""
    # Mock CLI path exists
    mock_exists.return_value = True

    # 配置 mock
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({
        "title": "测试标题",
        "content": "测试内容",
        "summary": "测试摘要",
        "keywords": ["测试", "内容"]
    })
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    # 调用服务方法
    result = ContentCreatorService.create_content(1, "测试选题", "科技")

    # 验证结果
    assert result["title"] == "测试标题"
    assert result["content"] == "测试内容"
    assert "测试" in result["keywords"]
    assert len(result["keywords"]) == 2

    # 验证调用参数
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == settings.CREATOR_CLI_PATH
    assert call_args[1] == "create"
    assert call_args[2] == "--account-id"
    assert call_args[3] == "1"
    assert call_args[4] == "--topic"
    assert call_args[5] == "测试选题"
    assert call_args[6] == "--category"
    assert call_args[7] == "科技"

    print("✓ 内容生成成功测试通过")


@pytest.mark.unit
@patch('os.path.exists')
@patch('app.services.content_creator_service.subprocess.run')
def test_create_content_failure(mock_run, mock_exists):
    """测试内容生成失败"""
    # Mock CLI path exists
    mock_exists.return_value = True

    # 配置 mock 抛出 CalledProcessError
    mock_error = MagicMock()
    mock_error.stderr = "CLI 执行失败"
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="", stderr=mock_error.stderr)

    # 验证抛出异常
    with pytest.raises(Exception) as exc_info:
        ContentCreatorService.create_content(1, "测试选题", "科技")

    assert "内容生成失败" in str(exc_info.value)
    assert "返回码" in str(exc_info.value)

    print("✓ 内容生成失败测试通过")


@pytest.mark.unit
@patch('os.path.exists')
def test_create_content_cli_not_found(mock_exists):
    """测试 content-creator CLI 未找到"""
    # 配置 mock 返回 False (CLI 不存在)
    mock_exists.return_value = False

    # 验证抛出异常
    with pytest.raises(Exception) as exc_info:
        ContentCreatorService.create_content(1, "测试选题", "科技")

    assert "Content-Creator CLI 未找到" in str(exc_info.value) or "content-creator CLI 未找到" in str(exc_info.value)

    print("✓ CLI 未找到测试通过")


@pytest.mark.unit
@patch('os.path.exists')
@patch('app.services.content_creator_service.subprocess.run')
def test_generate_cover_image_success(mock_run, mock_exists):
    """测试成功生成封面图片"""
    # Mock CLI path exists
    mock_exists.return_value = True

    # 配置 mock
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({
        "image_path": "/path/to/cover.jpg"
    })
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    # 调用服务方法
    result = ContentCreatorService.generate_cover_image("测试选题")

    # 验证结果
    assert result == "/path/to/cover.jpg"

    # 验证调用参数
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == settings.CREATOR_CLI_PATH
    assert call_args[1] == "generate-cover"
    assert call_args[2] == "--topic"
    assert call_args[3] == "测试选题"

    print("✓ 封面生成成功测试通过")


@pytest.mark.unit
@patch('os.path.exists')
@patch('app.services.content_creator_service.subprocess.run')
def test_generate_cover_image_failure(mock_run, mock_exists):
    """测试封面生成失败"""
    # Mock CLI path exists
    mock_exists.return_value = True

    # 配置 mock 抛出异常
    mock_run.side_effect = Exception("封面生成失败")

    # 验证抛出异常
    with pytest.raises(Exception) as exc_info:
        ContentCreatorService.generate_cover_image("测试选题")

    assert "封面生成失败" in str(exc_info.value)

    print("✓ 封面生成失败测试通过")


@pytest.mark.unit
@patch('os.path.exists')
def test_generate_cover_image_cli_not_found(mock_exists):
    """测试生成封面时 CLI 未找到"""
    # 配置 mock 返回 False (CLI 不存在)
    mock_exists.return_value = False

    # 验证抛出异常
    with pytest.raises(Exception) as exc_info:
        ContentCreatorService.generate_cover_image("测试选题")

    assert "Content-Creator CLI 未找到" in str(exc_info.value) or "content-creator CLI 未找到" in str(exc_info.value)

    print("✓ 生成封面时 CLI 未找到测试通过")


@pytest.mark.unit
def test_extract_images_from_content_with_images():
    """测试从包含图片的内容中提取图片"""
    content = """
# 测试标题

![测试图片1](https://example.com/image1.jpg)

这是测试内容。

![测试图片2](https://example.com/image2.png)

更多内容。
    """.strip()

    images = ContentCreatorService.extract_images_from_content(content)

    assert len(images) == 2
    assert "https://example.com/image1.jpg" in images
    assert "https://example.com/image2.png" in images

    print("✓ 从内容中提取图片测试通过")


@pytest.mark.unit
def test_extract_images_from_content_no_images():
    """测试从不含图片的内容中提取图片"""
    content = """
# 测试标题

这是不含图片的测试内容。

只有文字内容。
    """.strip()

    images = ContentCreatorService.extract_images_from_content(content)

    assert len(images) == 0

    print("✓ 从无图片内容中提取图片测试通过")


@pytest.mark.unit
def test_extract_images_from_content_invalid_format():
    """测试从包含无效格式图片的内容中提取图片"""
    content = """
# 测试标题

![无效图片](invalid-url)

这是测试内容。

![格式错误的图片]https://example.com/image.jpg

更多内容。
    """.strip()

    images = ContentCreatorService.extract_images_from_content(content)

    # 只有格式正确的图片会被提取
    assert len(images) == 0

    print("✓ 从包含无效格式图片的内容中提取图片测试通过")


@pytest.mark.unit
def test_extract_images_from_content_empty_content():
    """测试从空内容中提取图片"""
    content = ""
    images = ContentCreatorService.extract_images_from_content(content)
    assert len(images) == 0

    content = None
    images = ContentCreatorService.extract_images_from_content(content)
    assert len(images) == 0

    print("✓ 从空内容中提取图片测试通过")


@pytest.mark.unit
def test_extract_images_from_content_complex_format():
    """测试从复杂格式的内容中提取图片"""
    content = """
![图片1](https://example.com/image1.jpg) ![图片2](https://example.com/image2.png)

段落中的![图片3](https://example.com/image3.gif)图片。

*   ![列表图片1](https://example.com/list1.jpg)
*   ![列表图片2](https://example.com/list2.jpg)

> 引用中的![引用图片](https://example.com/quote.jpg)
    """.strip()

    images = ContentCreatorService.extract_images_from_content(content)

    assert len(images) == 6
    assert "https://example.com/image1.jpg" in images
    assert "https://example.com/image2.png" in images
    assert "https://example.com/image3.gif" in images
    assert "https://example.com/list1.jpg" in images
    assert "https://example.com/list2.jpg" in images
    assert "https://example.com/quote.jpg" in images

    print("✓ 从复杂格式内容中提取图片测试通过")
