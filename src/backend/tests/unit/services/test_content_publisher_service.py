"""
内容发布服务单元测试
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
from app.services.content_publisher_service import content_publisher_service


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_publish_to_wechat_success(mock_requests):
    """测试成功发布到微信公众号"""
    # 模拟成功响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "media_id": "123456",
            "message": "发布成功"
        }
    }
    mock_requests.post.return_value = mock_response

    # 测试发布到草稿箱
    result = content_publisher_service.publish_to_wechat(1, 1, publish_to_draft=True)

    # 验证结果
    assert result["success"] is True
    assert "media_id" in result["data"]
    assert result["data"]["message"] == "发布成功"

    print("✓ 成功发布到微信公众号测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_publish_to_wechat_failure(mock_requests):
    """测试发布到微信公众号失败"""
    # 模拟请求异常
    mock_requests.post.side_effect = Exception("连接失败")

    # 测试发布失败
    with pytest.raises(Exception) as excinfo:
        content_publisher_service.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "发布失败" in str(excinfo.value)

    print("✓ 发布到微信公众号失败测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_get_publish_status_success(mock_requests):
    """测试成功获取发布状态"""
    # 模拟成功响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "media_id": "123456",
            "status": "published",
            "publish_time": "2024-01-01 10:00:00"
        }
    }
    mock_requests.get.return_value = mock_response

    # 测试获取发布状态
    result = content_publisher_service.get_publish_status("123456")

    # 验证结果
    assert result["success"] is True
    assert result["data"]["media_id"] == "123456"
    assert result["data"]["status"] == "published"

    print("✓ 成功获取发布状态测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_get_publish_status_failure(mock_requests):
    """测试获取发布状态失败"""
    # 模拟请求异常
    mock_requests.get.side_effect = Exception("请求超时")

    # 测试获取状态失败
    with pytest.raises(Exception) as excinfo:
        content_publisher_service.get_publish_status("123456")

    assert "获取发布状态失败" in str(excinfo.value)

    print("✓ 获取发布状态失败测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
@patch('app.services.content_publisher_service.open', new_callable=MagicMock)
def test_upload_media_success(mock_open, mock_requests):
    """测试成功上传媒体文件"""
    # 模拟文件读取
    mock_file = MagicMock()
    mock_file.read.return_value = b"test image data"
    mock_open.return_value.__enter__.return_value = mock_file

    # 模拟成功响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "media_id": "media_789",
            "url": "https://example.com/image.jpg",
            "type": "image"
        }
    }
    mock_requests.post.return_value = mock_response

    # 测试上传媒体
    result = content_publisher_service.upload_media("/path/to/image.jpg", 1)

    # 验证结果
    assert result["success"] is True
    assert "media_id" in result["data"]
    assert result["data"]["type"] == "image"

    print("✓ 成功上传媒体文件测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.open', new_callable=MagicMock)
def test_upload_media_file_error(mock_open):
    """测试媒体文件上传时文件读取错误"""
    # 模拟文件读取异常
    mock_open.side_effect = FileNotFoundError("文件不存在")

    # 测试文件读取错误
    with pytest.raises(Exception) as excinfo:
        content_publisher_service.upload_media("/invalid/path.jpg", 1)

    assert "媒体上传失败" in str(excinfo.value)

    print("✓ 媒体文件上传文件读取错误测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_get_access_token_success(mock_requests):
    """测试成功获取访问令牌"""
    # 模拟成功响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "abc123def456",
        "expires_in": 7200
    }
    mock_requests.get.return_value = mock_response

    # 测试获取访问令牌
    access_token = content_publisher_service.get_access_token(1)

    # 验证结果
    assert isinstance(access_token, str)
    assert len(access_token) > 0
    assert access_token == "abc123def456"

    print("✓ 成功获取访问令牌测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_get_access_token_failure(mock_requests):
    """测试获取访问令牌失败"""
    # 模拟请求异常
    mock_requests.get.side_effect = Exception("401 Unauthorized")

    # 测试获取访问令牌失败
    with pytest.raises(Exception) as excinfo:
        content_publisher_service.get_access_token(1)

    assert "获取访问令牌失败" in str(excinfo.value)

    print("✓ 获取访问令牌失败测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_create_menu_success(mock_requests):
    """测试成功创建微信公众号菜单"""
    # 模拟成功响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "menu_id": "menu_123",
            "message": "菜单创建成功"
        }
    }
    mock_requests.post.return_value = mock_response

    # 测试创建菜单
    menu_data = {
        "button": [
            {
                "name": "首页",
                "type": "view",
                "url": "https://example.com"
            }
        ]
    }
    result = content_publisher_service.create_menu(1, menu_data)

    # 验证结果
    assert result["success"] is True
    assert "menu_id" in result["data"]
    assert result["data"]["message"] == "菜单创建成功"

    print("✓ 成功创建微信公众号菜单测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_create_menu_failure(mock_requests):
    """测试创建微信公众号菜单失败"""
    # 模拟请求异常
    mock_requests.post.side_effect = Exception("服务器连接失败")

    # 测试创建菜单失败
    menu_data = {
        "button": [
            {
                "name": "首页",
                "type": "view",
                "url": "https://example.com"
            }
        ]
    }
    with pytest.raises(Exception) as excinfo:
        content_publisher_service.create_menu(1, menu_data)

    assert "菜单创建失败" in str(excinfo.value)

    print("✓ 创建微信公众号菜单失败测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_publish_to_wechat_with_invalid_response(mock_requests):
    """测试微信公众号发布返回无效响应"""
    # 模拟无效响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests.post.return_value = mock_response

    # 测试无效响应处理
    with pytest.raises(Exception):
        content_publisher_service.publish_to_wechat(1, 1, publish_to_draft=True)

    print("✓ 微信公众号发布无效响应测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests')
def test_publish_to_wechat_http_error(mock_requests):
    """测试微信公众号发布HTTP错误"""
    # 模拟HTTP错误响应
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = Exception("400 Bad Request")
    mock_requests.post.return_value = mock_response

    # 测试HTTP错误处理
    with pytest.raises(Exception) as excinfo:
        content_publisher_service.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "发布失败" in str(excinfo.value)

    print("✓ 微信公众号发布HTTP错误测试通过")
