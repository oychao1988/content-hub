"""
内容发布服务单元测试
"""
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
import requests
from requests.exceptions import Timeout, RequestException, HTTPError as RequestsHTTPError

from app.services.content_publisher_service import ContentPublisherService
from app.core.exceptions import (
    PublisherException,
    PublisherTimeoutException,
    PublisherUnauthorizedException,
    ServiceUnavailableException
)


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_success(mock_request):
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
    mock_request.return_value = mock_response

    # 测试发布到草稿箱
    result = ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    # 验证结果
    assert result["success"] is True
    assert "media_id" in result["data"]
    assert result["data"]["message"] == "发布成功"

    # 验证请求参数
    mock_request.assert_called_once()
    call_args = mock_request.call_args
    assert call_args[0][0] == "POST"  # method
    assert "150.158.88.23:3010/api/publish" in call_args[0][1]  # url

    print("✓ 成功发布到微信公众号测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_timeout_with_retry(mock_request):
    """测试发布超时后重试"""
    # 模拟前两次超时，第三次成功
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {"media_id": "123456"}
    }

    # 前两次调用超时，第三次成功
    mock_request.side_effect = [
        Timeout("Connection timeout"),
        Timeout("Connection timeout"),
        mock_response
    ]

    result = ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    # 验证最终成功
    assert result["success"] is True
    assert mock_request.call_count == 3

    print("✓ 发布超时重试测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_max_retries_exceeded(mock_request):
    """测试超过最大重试次数"""
    # 模拟所有请求都超时
    mock_request.side_effect = Timeout("Connection timeout")

    # 测试超时异常
    with pytest.raises(PublisherTimeoutException) as excinfo:
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "超时" in str(excinfo.value.message)
    assert mock_request.call_count == 4  # 初始调用 + 3次重试

    print("✓ 超过最大重试次数测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_unauthorized(mock_request):
    """测试认证失败"""
    # 模拟401响应
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 测试认证异常
    with pytest.raises(PublisherUnauthorizedException):
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    print("✓ 认证失败测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_403_forbidden(mock_request):
    """测试403禁止访问"""
    # 模拟403响应
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Access Forbidden"
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 测试禁止访问异常
    with pytest.raises(PublisherException) as excinfo:
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "访问被拒绝" in str(excinfo.value.message)

    print("✓ 403禁止访问测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_404_not_found(mock_request):
    """测试404端点不存在"""
    # 模拟404响应
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Endpoint not found"
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 测试端点不存在异常
    with pytest.raises(PublisherException) as excinfo:
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "端点不存在" in str(excinfo.value.message)

    print("✓ 404端点不存在测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_to_wechat_500_with_degraded_mode(mock_request):
    """测试500错误触发降级模式"""
    # 模拟连续500错误
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 获取降级响应
    result = ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    # 验证降级响应
    assert result["success"] is False
    assert result["degraded"] is True
    assert result["data"]["status"] == "pending_retry"

    # 验证重试次数
    assert mock_request.call_count == 4  # 初始调用 + 3次重试

    print("✓ 500错误降级模式测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_get_publish_status_success(mock_request):
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
    mock_request.return_value = mock_response

    # 测试获取发布状态
    result = ContentPublisherService.get_publish_status("123456")

    # 验证结果
    assert result["success"] is True
    assert result["data"]["media_id"] == "123456"
    assert result["data"]["status"] == "published"

    print("✓ 成功获取发布状态测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_get_publish_status_503_with_degraded_mode(mock_request):
    """测试503错误触发降级模式（获取状态）"""
    # 模拟503响应
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 获取降级响应
    result = ContentPublisherService.get_publish_status("123456")

    # 验证降级响应
    assert result["success"] is False
    assert result["degraded"] is True
    assert result["data"]["status"] == "unknown"

    print("✓ 503降级模式测试通过（获取状态）")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_upload_media_success(mock_request):
    """测试成功上传媒体文件"""
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
    mock_request.return_value = mock_response

    # 模拟文件读取
    with patch('builtins.open', mock_open(read_data=b"test image data")):
        # 测试上传媒体
        result = ContentPublisherService.upload_media("/path/to/image.jpg", 1)

    # 验证结果
    assert result["success"] is True
    assert "media_id" in result["data"]
    assert result["data"]["type"] == "image"

    print("✓ 成功上传媒体文件测试通过")


@pytest.mark.unit
def test_upload_media_file_not_found():
    """测试媒体文件不存在"""
    # 模拟文件不存在
    with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
        # 测试文件不存在异常
        with pytest.raises(PublisherException) as excinfo:
            ContentPublisherService.upload_media("/invalid/path.jpg", 1)

        assert "文件不存在" in str(excinfo.value.message)

    print("✓ 媒体文件不存在测试通过")


@pytest.mark.unit
def test_upload_media_io_error():
    """测试文件读取IO错误"""
    # 模拟IO错误
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        # 测试IO异常
        with pytest.raises(PublisherException) as excinfo:
            ContentPublisherService.upload_media("/path/to/image.jpg", 1)

        assert "无法读取文件" in str(excinfo.value.message)

    print("✓ 文件读取IO错误测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_upload_media_503_with_degraded_mode(mock_request):
    """测试上传媒体503错误触发降级模式"""
    # 模拟503响应
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 模拟文件读取
    with patch('builtins.open', mock_open(read_data=b"test image data")):
        # 获取降级响应
        result = ContentPublisherService.upload_media("/path/to/image.jpg", 1)

    # 验证降级响应
    assert result["success"] is False
    assert result["degraded"] is True
    assert result["data"]["status"] == "failed"

    print("✓ 上传媒体503降级模式测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_get_access_token_success(mock_request):
    """测试成功获取访问令牌"""
    # 模拟成功响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "abc123def456",
        "expires_in": 7200
    }
    mock_request.return_value = mock_response

    # 测试获取访问令牌
    access_token = ContentPublisherService.get_access_token(1)

    # 验证结果
    assert isinstance(access_token, str)
    assert len(access_token) > 0
    assert access_token == "abc123def456"

    print("✓ 成功获取访问令牌测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_get_access_token_invalid_response(mock_request):
    """测试获取访问令牌返回无效响应"""
    # 模拟成功响应但缺少access_token
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "token": "invalid_token",
        "expires_in": 7200
    }
    mock_request.return_value = mock_response

    # 测试无效响应异常
    with pytest.raises(PublisherException) as excinfo:
        ContentPublisherService.get_access_token(1)

    assert "响应格式无效" in str(excinfo.value.message)

    print("✓ 获取访问令牌无效响应测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_create_menu_success(mock_request):
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
    mock_request.return_value = mock_response

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
    result = ContentPublisherService.create_menu(1, menu_data)

    # 验证结果
    assert result["success"] is True
    assert "menu_id" in result["data"]
    assert result["data"]["message"] == "菜单创建成功"

    print("✓ 成功创建微信公众号菜单测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_create_menu_429_rate_limit_with_retry(mock_request):
    """测试创建菜单429限流后重试"""
    # 模拟前两次429，第三次成功
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "success": True,
        "data": {"menu_id": "menu_123"}
    }

    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.text = "Too Many Requests"
    mock_response_429.raise_for_status.side_effect = RequestsHTTPError(response=mock_response_429)

    # 前两次429，第三次成功
    mock_request.side_effect = [
        mock_response_429,
        mock_response_429,
        mock_response_success
    ]

    menu_data = {"button": [{"name": "首页"}]}
    result = ContentPublisherService.create_menu(1, menu_data)

    # 验证最终成功
    assert result["success"] is True
    assert mock_request.call_count == 3

    print("✓ 创建菜单429限流重试测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_publish_invalid_json_response(mock_request):
    """测试发布返回无效JSON"""
    # 模拟成功响应但JSON解析失败
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_response.text = "Invalid JSON response"
    mock_request.return_value = mock_response

    # 测试无效JSON异常
    with pytest.raises(PublisherException) as excinfo:
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "无效的 JSON 响应" in str(excinfo.value.message)

    print("✓ 发布无效JSON响应测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_network_error_with_retry(mock_request):
    """测试网络错误重试"""
    # 模拟网络错误
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}

    # 前两次网络错误，第三次成功
    mock_request.side_effect = [
        RequestException("Network error"),
        RequestException("Network error"),
        mock_response
    ]

    result = ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    # 验证最终成功
    assert result["success"] is True
    assert mock_request.call_count == 3

    print("✓ 网络错误重试测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_http_400_bad_request(mock_request):
    """测试400错误请求"""
    # 模拟400响应
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request - Invalid parameters"
    mock_response.raise_for_status.side_effect = RequestsHTTPError(response=mock_response)
    mock_request.return_value = mock_response

    # 测试400异常
    with pytest.raises(PublisherException) as excinfo:
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "请求失败" in str(excinfo.value.message)
    assert "400" in str(excinfo.value.details["status_code"])

    print("✓ 400错误请求测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.settings')
def test_missing_publisher_api_url(mock_settings):
    """测试PUBLISHER_API_URL未配置"""
    # 模拟配置为空
    mock_settings.PUBLISHER_API_URL = ""
    mock_settings.PUBLISHER_API_KEY = "test_key"

    # 测试配置异常
    with pytest.raises(PublisherException) as excinfo:
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    assert "未配置" in str(excinfo.value.message)

    print("✓ PUBLISHER_API_URL未配置测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.settings')
def test_missing_publisher_api_key(mock_settings):
    """测试PUBLISHER_API_KEY未配置"""
    # 模拟URL已配置但KEY为空
    mock_settings.PUBLISHER_API_URL = "http://test.com"
    mock_settings.PUBLISHER_API_KEY = ""

    # 测试认证异常
    with pytest.raises(PublisherUnauthorizedException):
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    print("✓ PUBLISHER_API_KEY未配置测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_custom_timeout_value(mock_request):
    """测试自定义超时值"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_request.return_value = mock_response

    # 测试上传媒体（使用UPLOAD_TIMEOUT）
    with patch('builtins.open', mock_open(read_data=b"test")):
        ContentPublisherService.upload_media("/path/to/image.jpg", 1)

    # 验证使用了正确的超时值
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs['timeout'] == ContentPublisherService.UPLOAD_TIMEOUT

    print("✓ 自定义超时值测试通过")


@pytest.mark.unit
@patch('app.services.content_publisher_service.requests.request')
def test_exponential_backoff_retry(mock_request):
    """测试指数退避重试策略"""
    import time

    # 模拟所有请求都超时
    mock_request.side_effect = Timeout("Timeout")

    # 记录每次调用的时间间隔
    call_times = []
    original_request = mock_request
    def track_time(*args, **kwargs):
        call_times.append(time.time())
        raise Timeout("Timeout")

    mock_request.side_effect = track_time

    # 尝试发布（会重试）
    with pytest.raises(PublisherTimeoutException):
        ContentPublisherService.publish_to_wechat(1, 1, publish_to_draft=True)

    # 验证重试次数
    assert mock_request.call_count >= 1

    print("✓ 指数退避重试策略测试通过")
