"""
内容发布服务
负责调用 content-publisher API 发布内容到微信公众号
"""
import requests
import json
import time
import re
import os
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
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
    def _extract_and_convert_images(content_text: str, base_dir: str = None) -> Tuple[str, List[str], str]:
        """
        从 markdown 中提取图片并转换为 uploads: 格式

        :param content_text: markdown 内容
        :param base_dir: 基础目录，用于解析相对路径
        :return: (处理后的 markdown, 图片文件路径列表, 封面图 uploads: 格式)
        """
        image_paths = []
        cover_upload = ""

        # 处理正文图片
        def replace_image(match):
            alt = match.group(1)
            img_path = match.group(2)

            # 跳过网络图片
            if img_path.startswith('http://') or img_path.startswith('https://'):
                return match.group(0)

            # 转换相对路径为绝对路径
            abs_path = img_path if os.path.isabs(img_path) else os.path.join(base_dir, img_path) if base_dir else img_path

            # 检查文件是否存在
            if os.path.exists(abs_path):
                image_paths.append(abs_path)
                filename = os.path.basename(abs_path)
                return f"![{alt}](uploads:{filename})"

            # 文件不存在，保留原文或移除
            log.warning(f"图片文件不存在: {abs_path}")
            return f"![{alt}]"

        # 替换正文中的图片引用
        processed_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, content_text)

        return processed_content, image_paths, cover_upload

    @staticmethod
    def publish_to_wechat(content_id: int, account_id: int, publish_to_draft: bool = True, db=None) -> dict:
        """
        发布到微信公众号

        :param content_id: 内容 ID
        :param account_id: 账号 ID
        :param publish_to_draft: 是否发布到草稿箱
        :param db: 数据库会话
        :return: 发布结果
        """
        if not settings.PUBLISHER_API_URL:
            raise PublisherException(
                message="PUBLISHER_API_URL 未配置",
                code="PUBLISHER_NOT_CONFIGURED"
            )

        if not settings.PUBLISHER_API_KEY:
            raise PublisherUnauthorizedException()

        # 从数据库获取内容和账号信息
        if not db:
            from app.db.database import get_db
            db = next(get_db())

        from app.models.content import Content
        from app.models.account import Account

        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise PublisherException(
                message=f"内容不存在 (ID: {content_id})",
                code="CONTENT_NOT_FOUND"
            )

        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise PublisherException(
                message=f"账号不存在 (ID: {account_id})",
                code="ACCOUNT_NOT_FOUND"
            )

        # 提取图片并转换路径
        content_text = content.content or ""

        # 处理封面图
        cover_upload = ""
        cover_file_path = None

        if content.cover_image:
            cover_path = content.cover_image

            # 检查是否是本地路径
            if not cover_path.startswith('http://') and not cover_path.startswith('https://'):
                # 尝试解析路径
                abs_cover_path = cover_path if os.path.isabs(cover_path) else cover_path

                if os.path.exists(abs_cover_path):
                    cover_file_path = abs_cover_path
                    cover_filename = os.path.basename(abs_cover_path)
                    cover_upload = f"uploads:{cover_filename}"
                    log.info(f"封面图: {cover_filename}")
                else:
                    log.warning(f"封面图文件不存在: {abs_cover_path}")
            else:
                # 网络封面图，直接使用
                cover_upload = cover_path

        # 处理正文图片（从 content.images JSON 字段或 content.content 中提取）
        image_paths = []

        # 方式1: 从 images 字段获取
        if content.images:
            for img in content.images:
                if isinstance(img, str):
                    img_path = img
                    if not img_path.startswith('http://') and not img_path.startswith('https://'):
                        abs_path = img_path if os.path.isabs(img_path) else img_path
                        if os.path.exists(abs_path):
                            image_paths.append(abs_path)

        # 方式2: 从 content content 中提取图片引用
        processed_content, extracted_images, _ = ContentPublisherService._extract_and_convert_images(
            content_text,
            None
        )

        # 合并图片列表（去重）
        for img_path in extracted_images:
            if img_path not in image_paths:
                image_paths.append(img_path)

        # 添加封面图到图片列表
        if cover_file_path and cover_file_path not in image_paths:
            image_paths.insert(0, cover_file_path)  # 封面图放在最前面

        log.info(f"发现 {len(image_paths)} 个本地图片文件")

        # 构造 markdown（包含 YAML front matter）
        front_matter = f"---\ntitle: {content.title}\n"
        if cover_upload:
            front_matter += f"cover: {cover_upload}\n"
        front_matter += "---\n\n"

        markdown = front_matter + processed_content

        # 构造请求
        # 如果没有本地图片，使用 JSON 格式
        if not image_paths:
            log.info("无本地图片，使用 JSON 格式")

            data = {
                "markdown": markdown,
                "title": content.title,
                "theme": "default",
                "highlightTheme": "solarized-light",
                "useMacStyle": True,
                "addFootnote": True,
                "account": {
                    "appId": account.wechat_app_id,
                    "appSecret": account.wechat_app_secret
                }
            }

            if cover_upload:
                data["cover"] = cover_upload

            return ContentPublisherService._make_request(
                "POST",
                "/api/publish",
                json=data,
                headers={"Content-Type": "application/json"}
            )

        # 有本地图片，使用 multipart/form-data 格式
        log.info(f"使用 multipart/form-data 格式，上传 {len(image_paths)} 个图片文件")

        # 准备 multipart/form-data
        files = []  # 使用列表格式支持多个文件
        data = {
            "markdown": markdown,
            "title": content.title,
            "theme": "default",
            "highlightTheme": "solarized-light",
            "useMacStyle": "true",
            "addFootnote": "true",
            "account": json.dumps({
                "appId": account.wechat_app_id,
                "appSecret": account.wechat_app_secret
            })
        }

        if cover_upload:
            data["cover"] = cover_upload

        # 添加图片文件
        for idx, img_path in enumerate(image_paths):
            if not os.path.exists(img_path):
                log.warning(f"跳过不存在的文件: {img_path}")
                continue

            filename = os.path.basename(img_path)

            # 确定 MIME 类型
            ext = os.path.splitext(filename)[1].lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

            try:
                with open(img_path, 'rb') as f:
                    file_content = f.read()
                    files.append(('files', (filename, file_content, mime_type)))
                    log.info(f"  + {filename} ({mime_type})")
            except Exception as e:
                log.error(f"读取图片失败 {filename}: {e}")
                continue

        url = f"{settings.PUBLISHER_API_URL}/api/publish"
        headers = {
            'Authorization': f"Bearer {settings.PUBLISHER_API_KEY}"
        }

        try:
            log.info(f"Publisher API request: POST {url}")
            log.info(f"  - 标题: {content.title}")
            log.info(f"  - 图片数量: {len(image_paths)}")
            log.info(f"  - 封面: {cover_upload or '(无)'}")

            response = requests.post(
                url,
                data=data,
                files=files,
                headers=headers,
                timeout=ContentPublisherService.UPLOAD_TIMEOUT
            )

            response.raise_for_status()

            # 解析 JSON 响应
            try:
                result = response.json()

                # 检查业务状态
                if not result.get('success'):
                    error_msg = result.get('message', '发布失败')
                    log.error(f"Publisher API 业务错误: {error_msg}")
                    raise PublisherException(
                        message=error_msg,
                        details={"response": result},
                        code="PUBLISHER_BUSINESS_ERROR"
                    )

                # 提取 media_id（适配两种格式）
                media_id = None
                if 'data' in result:
                    media_id = result['data'].get('mediaId') or result['data'].get('media_id')
                else:
                    media_id = result.get('mediaId') or result.get('media_id')

                log.info(f"发布成功: media_id={media_id}")
                return result
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

        except Exception as e:
            log.exception(f"Publisher API request failed: {str(e)}")
            raise PublisherException(
                message=f"调用 Publisher API 时发生错误: {str(e)}",
                details={"error_type": type(e).__name__}
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
