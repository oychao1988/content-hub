"""
内容发布服务
负责调用 content-publisher API 发布内容到微信公众号
"""
import requests
import json
import time
from typing import Optional, Dict, Any
from requests.exceptions import RequestException, Timeout, HTTPError as RequestsHTTPError
from app.core.config import settings
from app.core.exceptions import (
    PublisherException,
    PublisherTimeoutException,
    PublisherUnauthorizedException,
    ServiceUnavailableException
)
from app.utils.custom_logger import log


class ContentPublisherService:
    """内容发布服务"""

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 30
    UPLOAD_TIMEOUT = 60  # 上传文件可能需要更长时间

    # 最大重试次数
    MAX_RETRIES = 3

    # 重试的 HTTP 状态码
    RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]

    # 降级策略配置
    DEGRADE_ENABLED = True  # 是否启用降级
    DEGRADE_AFTER_RETRIES = 3  # 重试失败多少次后降级
    DEGRADE_RETURN_PARTIAL = True  # 降级时是否返回部分结果

    @staticmethod
    def _make_request(
        method: str,
        endpoint: str,
        retries: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求并处理错误

        :param method: HTTP 方法
        :param endpoint: API 端点
        :param retries: 当前重试次数
        :param kwargs: requests 其他参数
        :return: 解析后的 JSON 响应
        :raises: PublisherException 及其子类
        """
        url = f"{settings.PUBLISHER_API_URL}{endpoint}"

        # 设置默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = ContentPublisherService.DEFAULT_TIMEOUT

        # 添加认证头
        headers = kwargs.get('headers', {})
        if 'Authorization' not in headers:
            api_key = kwargs.pop('api_key', settings.PUBLISHER_API_KEY)
            headers['Authorization'] = f"Bearer {api_key}"
        kwargs['headers'] = headers

        try:
            log.info(f"Publisher API request: {method} {url}")

            response = requests.request(method, url, **kwargs)
            response.raise_for_status()

            # 解析 JSON 响应
            try:
                return response.json()
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse Publisher API response: {e}")
                raise PublisherException(
                    message="Publisher API 返回了无效的 JSON 响应",
                    details={
                        "status_code": response.status_code,
                        "response_preview": response.text[:200]
                    },
                    code="PUBLISHER_INVALID_RESPONSE"
                )

        except Timeout as e:
            log.error(f"Publisher API timeout: {str(e)}")

            # 指数退避重试
            if retries < ContentPublisherService.MAX_RETRIES:
                wait_time = 2 ** retries  # 1s, 2s, 4s
                log.warning(
                    f"Retrying Publisher API request after {wait_time}s "
                    f"(attempt {retries + 1}/{ContentPublisherService.MAX_RETRIES})"
                )
                time.sleep(wait_time)
                return ContentPublisherService._make_request(method, endpoint, retries + 1, **kwargs)

            raise PublisherTimeoutException(kwargs.get('timeout', ContentPublisherService.DEFAULT_TIMEOUT))

        except RequestsHTTPError as e:
            status_code = e.response.status_code
            error_details = {
                "status_code": status_code,
                "response": e.response.text[:500] if e.response.text else "No response body"
            }

            # 401 未授权
            if status_code == 401:
                log.error("Publisher API authentication failed")
                raise PublisherUnauthorizedException()

            # 403 禁止访问
            elif status_code == 403:
                log.error("Publisher API access forbidden")
                raise PublisherException(
                    message="Publisher API 访问被拒绝，请检查权限配置",
                    details=error_details,
                    code="PUBLISHER_FORBIDDEN"
                )

            # 404 未找到
            elif status_code == 404:
                log.error(f"Publisher API endpoint not found: {endpoint}")
                raise PublisherException(
                    message=f"Publisher API 端点不存在: {endpoint}",
                    details=error_details,
                    code="PUBLISHER_NOT_FOUND"
                )

            # 可重试的状态码
            elif status_code in ContentPublisherService.RETRYABLE_STATUS_CODES:
                if retries < ContentPublisherService.MAX_RETRIES:
                    wait_time = 2 ** retries
                    log.warning(
                        f"Publisher API returned {status_code}, retrying after {wait_time}s "
                        f"(attempt {retries + 1}/{ContentPublisherService.MAX_RETRIES})"
                    )
                    time.sleep(wait_time)
                    return ContentPublisherService._make_request(method, endpoint, retries + 1, **kwargs)

                # 重试次数用尽，检查是否启用降级
                if ContentPublisherService.DEGRADE_ENABLED:
                    log.error(
                        f"Publisher API failed after {ContentPublisherService.MAX_RETRIES} retries, "
                        f"degrading service (status: {status_code})"
                    )
                    return ContentPublisherService._degraded_response(method, endpoint, status_code)
                else:
                    log.error(f"Publisher API failed after retries: {status_code}")
                    raise ServiceUnavailableException(
                        service_name="Content-Publisher",
                        details=error_details
                    )

            # 其他 HTTP 错误
            else:
                log.error(f"Publisher API HTTP error: {status_code} - {e.response.text[:200]}")
                raise PublisherException(
                    message=f"Publisher API 请求失败 (HTTP {status_code})",
                    details=error_details
                )

        except RequestException as e:
            log.exception(f"Publisher API request failed: {str(e)}")

            # 网络错误重试
            if retries < ContentPublisherService.MAX_RETRIES:
                wait_time = 2 ** retries
                log.warning(
                    f"Network error, retrying after {wait_time}s "
                    f"(attempt {retries + 1}/{ContentPublisherService.MAX_RETRIES})"
                )
                time.sleep(wait_time)
                return ContentPublisherService._make_request(method, endpoint, retries + 1, **kwargs)

            raise PublisherException(
                message=f"Publisher API 网络请求失败: {str(e)}",
                details={"error_type": type(e).__name__}
            )

        except PublisherException:
            # 重新抛出已知的 Publisher 异常
            raise
        except Exception as e:
            log.exception(f"Unexpected error calling Publisher API: {str(e)}")
            raise PublisherException(
                message=f"调用 Publisher API 时发生意外错误: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    @staticmethod
    def _degraded_response(method: str, endpoint: str, status_code: int) -> Dict[str, Any]:
        """
        返回降级响应

        :param method: HTTP 方法
        :param endpoint: API 端点
        :param status_code: 失败时的状态码
        :return: 降级响应
        """
        log.warning(f"Returning degraded response for {method} {endpoint}")

        # 根据不同的端点返回不同的降级响应
        if endpoint == "/api/publish":
            return {
                "success": False,
                "degraded": True,
                "message": "发布服务暂时不可用，已加入重试队列",
                "data": {
                    "status": "pending_retry",
                    "retry_at": None  # 可以计算重试时间
                }
            }
        elif endpoint == "/api/status":
            return {
                "success": False,
                "degraded": True,
                "message": "无法获取发布状态",
                "data": {
                    "status": "unknown",
                    "last_error": f"HTTP {status_code}"
                }
            }
        elif endpoint == "/api/upload-media":
            return {
                "success": False,
                "degraded": True,
                "message": "媒体上传服务暂时不可用",
                "data": {
                    "media_id": None,
                    "status": "failed"
                }
            }
        else:
            return {
                "success": False,
                "degraded": True,
                "message": "服务暂时不可用，请稍后重试",
                "data": None
            }

    @staticmethod
    def publish_to_wechat(content_id: int, account_id: int, publish_to_draft: bool = True) -> dict:
        """
        发布到微信公众号

        :param content_id: 内容 ID
        :param account_id: 账号 ID
        :param publish_to_draft: 是否发布到草稿箱
        :return: 发布结果
        """
        if not settings.PUBLISHER_API_URL:
            raise PublisherException(
                message="PUBLISHER_API_URL 未配置",
                code="PUBLISHER_NOT_CONFIGURED"
            )

        if not settings.PUBLISHER_API_KEY:
            raise PublisherUnauthorizedException()

        data = {
            "content_id": content_id,
            "account_id": account_id,
            "publish_to_draft": publish_to_draft
        }

        return ContentPublisherService._make_request(
            "POST",
            "/api/publish",
            json=data,
            headers={"Content-Type": "application/json"}
        )

    @staticmethod
    def get_publish_status(media_id: str) -> dict:
        """
        获取发布状态

        :param media_id: 媒体 ID
        :return: 状态信息
        """
        if not settings.PUBLISHER_API_URL:
            raise PublisherException(
                message="PUBLISHER_API_URL 未配置",
                code="PUBLISHER_NOT_CONFIGURED"
            )

        if not settings.PUBLISHER_API_KEY:
            raise PublisherUnauthorizedException()

        params = {"media_id": media_id}

        return ContentPublisherService._make_request(
            "GET",
            "/api/status",
            params=params
        )

    @staticmethod
    def upload_media(image_path: str, account_id: int) -> dict:
        """
        上传媒体文件到微信

        :param image_path: 图片路径
        :param account_id: 账号 ID
        :return: 媒体信息
        """
        if not settings.PUBLISHER_API_URL:
            raise PublisherException(
                message="PUBLISHER_API_URL 未配置",
                code="PUBLISHER_NOT_CONFIGURED"
            )

        if not settings.PUBLISHER_API_KEY:
            raise PublisherUnauthorizedException()

        try:
            with open(image_path, "rb") as f:
                files = {"media": f}
                data = {"account_id": account_id}

                return ContentPublisherService._make_request(
                    "POST",
                    "/api/upload-media",
                    files=files,
                    data=data,
                    timeout=ContentPublisherService.UPLOAD_TIMEOUT
                )

        except FileNotFoundError:
            raise PublisherException(
                message=f"文件不存在: {image_path}",
                details={"file_path": image_path},
                code="PUBLISHER_FILE_NOT_FOUND"
            )
        except IOError as e:
            raise PublisherException(
                message=f"无法读取文件: {image_path}",
                details={"file_path": image_path, "error": str(e)},
                code="PUBLISHER_FILE_READ_ERROR"
            )

    @staticmethod
    def get_access_token(account_id: int) -> str:
        """
        获取访问令牌

        :param account_id: 账号 ID
        :return: 访问令牌
        """
        if not settings.PUBLISHER_API_URL:
            raise PublisherException(
                message="PUBLISHER_API_URL 未配置",
                code="PUBLISHER_NOT_CONFIGURED"
            )

        if not settings.PUBLISHER_API_KEY:
            raise PublisherUnauthorizedException()

        params = {"account_id": account_id}

        response = ContentPublisherService._make_request(
            "GET",
            "/api/access-token",
            params=params
        )

        # 验证响应格式
        if "access_token" not in response:
            raise PublisherException(
                message="Publisher API 返回的响应格式无效",
                details={"response_keys": list(response.keys())},
                code="PUBLISHER_INVALID_RESPONSE"
            )

        return response["access_token"]

    @staticmethod
    def create_menu(account_id: int, menu_data: dict) -> dict:
        """
        创建微信公众号菜单

        :param account_id: 账号 ID
        :param menu_data: 菜单数据
        :return: 操作结果
        """
        if not settings.PUBLISHER_API_URL:
            raise PublisherException(
                message="PUBLISHER_API_URL 未配置",
                code="PUBLISHER_NOT_CONFIGURED"
            )

        if not settings.PUBLISHER_API_KEY:
            raise PublisherUnauthorizedException()

        data = {
            "account_id": account_id,
            "menu_data": menu_data
        }

        return ContentPublisherService._make_request(
            "POST",
            "/api/menu",
            json=data,
            headers={"Content-Type": "application/json"}
        )


# 全局服务实例
content_publisher_service = ContentPublisherService()
