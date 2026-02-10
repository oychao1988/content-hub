"""
Content-Creator HTTP API 客户端
使用 HTTP API 替代 CLI subprocess 调用
"""
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx
from app.core.config import settings
from app.core.exceptions import (
    CreatorTimeoutException,
    CreatorInvalidResponseException,
    CreatorException,
)
from app.utils.custom_logger import log


class CreatorApiClient:
    """Content-Creator HTTP API 客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        """
        初始化 API 客户端

        Args:
            base_url: API 基础地址（默认从配置读取）
            timeout: 请求超时时间（秒，默认从配置读取）
            max_retries: 最大重试次数（默认从配置读取）
        """
        self.base_url = (base_url or settings.CREATOR_API_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.CREATOR_API_TIMEOUT
        self.max_retries = max_retries or settings.CREATOR_API_MAX_RETRIES

        # 创建 HTTP 客户端（同步和异步）
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.Client:
        """获取同步 HTTP 客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def _get_async_client(self) -> httpx.AsyncClient:
        """获取异步 HTTP 客户端（懒加载）"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._async_client

    def close(self):
        """关闭客户端连接"""
        if self._client:
            self._client.close()
            self._client = None

    async def close_async(self):
        """关闭异步客户端连接"""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def _handle_error(self, response: httpx.Response) -> None:
        """
        处理 API 错误响应

        Args:
            response: HTTP 响应对象

        Raises:
            CreatorException: 根据状态码抛出相应异常
        """
        if response.status_code >= 500:
            raise CreatorException(
                message=f"API 服务器错误: {response.status_code}",
                details={"status_code": response.status_code, "url": str(response.url)}
            )
        elif response.status_code == 404:
            raise CreatorException(
                message="资源不存在",
                details={"status_code": 404, "url": str(response.url)}
            )
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "请求失败")
                error_code = error_data.get("error", {}).get("code", "UNKNOWN_ERROR")
            except Exception:
                error_msg = f"请求失败: {response.text[:200]}"
                error_code = "UNKNOWN_ERROR"

            raise CreatorException(
                message=error_msg,
                details={"status_code": response.status_code, "code": error_code}
            )

    def _parse_sync_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析同步任务的响应数据

        Args:
            data: API 响应数据

        Returns:
            解析后的结果字典（兼容旧 CLI 输出格式）
        """
        if not data.get("success"):
            error = data.get("error", {})
            raise CreatorException(
                message=error.get("message", "创建任务失败"),
                details=error
            )

        result_data = data.get("data", {})

        # 如果是异步模式，立即返回
        if result_data.get("status") == "pending":
            return {
                "success": True,
                "task_id": result_data.get("taskId"),
                "status": "pending",
                "message": result_data.get("message")
            }

        # 同步模式：解析完整结果
        return {
            "success": True,
            "task_id": result_data.get("taskId"),
            "status": result_data.get("status"),
            "content": result_data.get("content"),
            "html_content": result_data.get("htmlContent"),
            "images": [img.get("url") for img in result_data.get("images", [])],
            "quality_score": result_data.get("qualityScore"),
            "word_count": result_data.get("wordCount"),
            "duration": result_data.get("metrics", {}).get("duration", 0) / 1000,  # 转换为秒
        }

    # ==================== 同步 API ====================

    def create_task_sync(
        self,
        topic: str,
        requirements: Optional[str] = None,
        target_audience: str = "普通读者",
        tone: str = "友好专业",
        keywords: Optional[List[str]] = None,
        image_size: str = "1920x1080",
        priority: int = 2,
        hard_constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建同步内容生成任务

        Args:
            topic: 文章主题
            requirements: 创作要求
            target_audience: 目标受众
            tone: 语气风格
            keywords: 关键词列表
            image_size: 图片尺寸
            priority: 优先级 (1-4)
            hard_constraints: 硬性约束（如字数限制）

        Returns:
            生成结果字典

        Raises:
            CreatorTimeoutException: 请求超时
            CreatorException: API 调用失败
        """
        client = self._get_client()

        payload = {
            "mode": "sync",
            # type 不设置或设置为 'content-creator' 作为工作流类型
            "topic": topic,
            "requirements": requirements or f"写一篇关于'{topic}'的文章",
            "targetAudience": target_audience,
            "tone": tone,
            "imageSize": image_size,
            "priority": priority,
        }

        if keywords:
            payload["keywords"] = keywords
        if hard_constraints:
            payload["hardConstraints"] = hard_constraints

        log.info(f"Creating sync task: topic='{topic}', tone='{tone}'")
        log.debug(f"Request payload: {payload}")

        try:
            response = client.post("/api/tasks", json=payload)
            self._handle_error(response)

            data = response.json()
            result = self._parse_sync_response(data)

            log.info(f"Sync task completed: task_id={result.get('task_id')}, status={result.get('status')}")
            return result

        except httpx.TimeoutException:
            log.error(f"API request timeout after {self.timeout}s")
            raise CreatorTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            log.error(f"HTTP request failed: {str(e)}")
            raise CreatorException(message=f"HTTP 请求失败: {str(e)}")
        except CreatorException:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_task_sync: {str(e)}")
            raise CreatorException(message=f"创建任务时发生意外错误: {str(e)}")

    def create_task_async(
        self,
        topic: str,
        task_id: str,
        requirements: Optional[str] = None,
        target_audience: str = "普通读者",
        tone: str = "友好专业",
        keywords: Optional[List[str]] = None,
        callback_url: Optional[str] = None,
        callback_events: Optional[List[str]] = None,
        priority: int = 2,
    ) -> Dict[str, Any]:
        """
        创建异步内容生成任务

        Args:
            topic: 文章主题
            task_id: 任务 ID
            requirements: 创作要求
            target_audience: 目标受众
            tone: 语气风格
            keywords: 关键词列表
            callback_url: Webhook 回调 URL
            callback_events: 触发回调的事件列表
            priority: 优先级 (1-4)

        Returns:
            包含 task_id 和 status 的字典

        Raises:
            CreatorException: API 调用失败
        """
        client = self._get_client()

        payload = {
            "mode": "async",
            # type 不设置，使用默认的 'content-creator' 工作流
            "topic": topic,
            "requirements": requirements or f"写一篇关于'{topic}'的文章",
            "targetAudience": target_audience,
            "tone": tone,
            "priority": priority,
        }

        if keywords:
            payload["keywords"] = keywords
        if callback_url:
            payload["callbackUrl"] = callback_url
            payload["callbackEnabled"] = True
            payload["callbackEvents"] = callback_events or ["completed", "failed"]

        log.info(f"Creating async task: task_id={task_id}, topic='{topic}'")
        log.debug(f"Request payload: {payload}")

        try:
            response = client.post("/api/tasks", json=payload)
            self._handle_error(response)

            data = response.json()
            result = {
                "success": True,
                "task_id": data.get("data", {}).get("taskId"),
                "status": data.get("data", {}).get("status"),
                "message": data.get("data", {}).get("message"),
            }

            log.info(f"Async task created: task_id={result['task_id']}")
            return result

        except httpx.TimeoutException:
            log.error(f"API request timeout after {self.timeout}s")
            raise CreatorTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            log.error(f"HTTP request failed: {str(e)}")
            raise CreatorException(message=f"HTTP 请求失败: {str(e)}")
        except CreatorException:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_task_async: {str(e)}")
            raise CreatorException(message=f"创建异步任务时发生意外错误: {str(e)}")

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态字典
        """
        client = self._get_client()

        try:
            response = client.get(f"/api/tasks/{task_id}/status")
            self._handle_error(response)

            data = response.json()
            return data.get("data", {})

        except httpx.HTTPError as e:
            log.error(f"Failed to get task status: {str(e)}")
            raise CreatorException(message=f"查询任务状态失败: {str(e)}")

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务结果

        Args:
            task_id: 任务 ID

        Returns:
            任务结果字典

        Raises:
            CreatorInvalidResponseException: 任务未完成
        """
        client = self._get_client()

        try:
            response = client.get(f"/api/tasks/{task_id}/result")
            self._handle_error(response)

            data = response.json()
            result_data = data.get("data", {})

            # 转换为兼容格式
            return {
                "success": True,
                "task_id": result_data.get("taskId"),
                "status": result_data.get("status"),
                "content": result_data.get("content"),
                "html_content": result_data.get("htmlContent"),
                "images": [img.get("url") for img in result_data.get("images", [])],
                "quality_score": result_data.get("qualityScore"),
                "word_count": result_data.get("wordCount"),
            }

        except httpx.HTTPError as e:
            if "not completed" in str(e).lower():
                raise CreatorInvalidResponseException("任务尚未完成")
            log.error(f"Failed to get task result: {str(e)}")
            raise CreatorException(message=f"获取任务结果失败: {str(e)}")

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        取消任务

        Args:
            task_id: 任务 ID

        Returns:
            取消结果字典
        """
        client = self._get_client()

        try:
            response = client.delete(f"/api/tasks/{task_id}")
            self._handle_error(response)

            data = response.json()
            return data.get("data", {})

        except httpx.HTTPError as e:
            log.error(f"Failed to cancel task: {str(e)}")
            raise CreatorException(message=f"取消任务失败: {str(e)}")

    def retry_task(self, task_id: str) -> Dict[str, Any]:
        """
        重试失败的任务

        Args:
            task_id: 任务 ID

        Returns:
            重试结果字典
        """
        client = self._get_client()

        try:
            response = client.post(f"/api/tasks/{task_id}/retry")
            self._handle_error(response)

            data = response.json()
            return data.get("data", {})

        except httpx.HTTPError as e:
            log.error(f"Failed to retry task: {str(e)}")
            raise CreatorException(message=f"重试任务失败: {str(e)}")

    def list_tasks(
        self,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        列出任务

        Args:
            status: 按状态过滤
            page: 页码
            limit: 每页数量

        Returns:
            任务列表字典
        """
        client = self._get_client()

        params = {"page": page, "limit": limit}
        if status:
            params["status"] = status

        try:
            response = client.get("/api/tasks", params=params)
            self._handle_error(response)

            data = response.json()
            return data.get("data", {})

        except httpx.HTTPError as e:
            log.error(f"Failed to list tasks: {str(e)}")
            raise CreatorException(message=f"获取任务列表失败: {str(e)}")

    # ==================== 异步 API ====================

    async def create_task_async_async(
        self,
        topic: str,
        task_id: str,
        requirements: Optional[str] = None,
        target_audience: str = "普通读者",
        tone: str = "友好专业",
        keywords: Optional[List[str]] = None,
        callback_url: Optional[str] = None,
        callback_events: Optional[List[str]] = None,
        priority: int = 2,
    ) -> Dict[str, Any]:
        """
        异步创建内容生成任务

        Args:
            topic: 文章主题
            task_id: 任务 ID
            requirements: 创作要求
            target_audience: 目标受众
            tone: 语气风格
            keywords: 关键词列表
            callback_url: Webhook 回调 URL
            callback_events: 触发回调的事件列表
            priority: 优先级 (1-4)

        Returns:
            包含 task_id 和 status 的字典
        """
        client = await self._get_async_client()

        payload = {
            "mode": "async",
            # type 不设置，使用默认的 'content-creator' 工作流
            "topic": topic,
            "requirements": requirements or f"写一篇关于'{topic}'的文章",
            "targetAudience": target_audience,
            "tone": tone,
            "priority": priority,
        }

        if keywords:
            payload["keywords"] = keywords
        if callback_url:
            payload["callbackUrl"] = callback_url
            payload["callbackEnabled"] = True
            payload["callbackEvents"] = callback_events or ["completed", "failed"]

        log.info(f"Creating async task (async): task_id={task_id}, topic='{topic}'")

        try:
            response = await client.post("/api/tasks", json=payload)
            self._handle_error(response)

            data = response.json()
            result = {
                "success": True,
                "task_id": data.get("data", {}).get("taskId"),
                "status": data.get("data", {}).get("status"),
                "message": data.get("data", {}).get("message"),
            }

            log.info(f"Async task created (async): task_id={result['task_id']}")
            return result

        except httpx.TimeoutException:
            log.error(f"API request timeout after {self.timeout}s")
            raise CreatorTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            log.error(f"HTTP request failed: {str(e)}")
            raise CreatorException(message=f"HTTP 请求失败: {str(e)}")
        except CreatorException:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_task_async_async: {str(e)}")
            raise CreatorException(message=f"创建异步任务时发生意外错误: {str(e)}")

    async def get_task_status_async(self, task_id: str) -> Dict[str, Any]:
        """
        异步查询任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态字典
        """
        client = await self._get_async_client()

        try:
            response = await client.get(f"/api/tasks/{task_id}/status")
            self._handle_error(response)

            data = response.json()
            return data.get("data", {})

        except httpx.HTTPError as e:
            log.error(f"Failed to get task status: {str(e)}")
            raise CreatorException(message=f"查询任务状态失败: {str(e)}")

    async def get_task_result_async(self, task_id: str) -> Dict[str, Any]:
        """
        异步获取任务结果

        Args:
            task_id: 任务 ID

        Returns:
            任务结果字典
        """
        client = await self._get_async_client()

        try:
            response = await client.get(f"/api/tasks/{task_id}/result")
            self._handle_error(response)

            data = response.json()
            result_data = data.get("data", {})

            return {
                "success": True,
                "task_id": result_data.get("taskId"),
                "status": result_data.get("status"),
                "content": result_data.get("content"),
                "html_content": result_data.get("htmlContent"),
                "images": [img.get("url") for img in result_data.get("images", [])],
                "quality_score": result_data.get("qualityScore"),
                "word_count": result_data.get("wordCount"),
            }

        except httpx.HTTPError as e:
            if "not completed" in str(e).lower():
                raise CreatorInvalidResponseException("任务尚未完成")
            log.error(f"Failed to get task result: {str(e)}")
            raise CreatorException(message=f"获取任务结果失败: {str(e)}")


# 全局单例客户端实例
_creator_api_client: Optional[CreatorApiClient] = None


def get_creator_api_client() -> CreatorApiClient:
    """获取全局 API 客户端实例（单例模式）"""
    global _creator_api_client
    if _creator_api_client is None:
        _creator_api_client = CreatorApiClient()
    return _creator_api_client
