"""
Webhook 签名验证工具

使用 HMAC-SHA256 算法验证 Webhook 请求的真实性，防止伪造请求。
"""
import hmac
import hashlib
import base64
import json
from typing import Dict, Optional


def generate_signature(payload: Dict, secret: str) -> str:
    """
    生成 Webhook 签名

    使用 HMAC-SHA256 算法对请求负载生成签名，签名结果进行 Base64 编码。

    Args:
        payload: 请求负载（字典）
        secret: 签名密钥

    Returns:
        Base64 编码的签名字符串

    Raises:
        ValueError: 当 payload 为空或 secret 为空时
        TypeError: 当 JSON 序列化失败时

    Example:
        >>> payload = {"event": "content.completed", "content_id": 123}
        >>> secret = "my-secret-key"
        >>> signature = generate_signature(payload, secret)
        >>> print(signature)
        'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo='
    """
    if not payload:
        raise ValueError("Payload cannot be empty")
    if not secret:
        raise ValueError("Secret key cannot be empty")

    try:
        # 将 payload 序列化为 JSON 字符串（sort_keys=True 确保键顺序一致）
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        # 转换为字节
        payload_bytes = payload_str.encode('utf-8')
        secret_bytes = secret.encode('utf-8')

        # 使用 HMAC-SHA256 生成签名
        signature_hmac = hmac.new(secret_bytes, payload_bytes, hashlib.sha256)

        # Base64 编码签名结果
        signature_base64 = base64.b64encode(signature_hmac.digest()).decode('utf-8')

        return signature_base64

    except (TypeError, ValueError) as e:
        raise TypeError(f"Failed to serialize payload to JSON: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to generate signature: {str(e)}")


def verify_signature(payload: Dict, signature: str, secret: str) -> bool:
    """
    验证 Webhook 签名

    使用常量时间比较验证签名，防止时序攻击。

    Args:
        payload: 请求负载（字典）
        signature: 请求头中的签名（Base64 编码）
        secret: 签名密钥

    Returns:
        True=签名有效, False=签名无效

    Raises:
        ValueError: 当 payload 为空、signature 为空或 secret 为空时

    Example:
        >>> payload = {"event": "content.completed", "content_id": 123}
        >>> signature = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="
        >>> secret = "my-secret-key"
        >>> is_valid = verify_signature(payload, signature, secret)
        >>> print(is_valid)
        True
    """
    if not payload:
        raise ValueError("Payload cannot be empty")
    if not signature:
        raise ValueError("Signature cannot be empty")
    if not secret:
        raise ValueError("Secret key cannot be empty")

    try:
        # 生成期望的签名
        expected_signature = generate_signature(payload, secret)

        # 使用常量时间比较（防止时序攻击）
        return hmac.compare_digest(expected_signature, signature)

    except Exception:
        # 如果生成签名失败或比较失败，返回 False
        return False


class WebhookSignatureVerifier:
    """
    Webhook 签名验证器

    封装签名验证逻辑，提供更友好的 API。

    Attributes:
        secret: 签名密钥
        require_signature: 是否强制要求签名验证

    Example:
        >>> verifier = WebhookSignatureVerifier(secret="my-secret-key")
        >>>
        >>> # 从请求中提取签名
        >>> headers = {"X-Webhook-Signature": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="}
        >>> payload = {"event": "content.completed", "content_id": 123}
        >>>
        >>> # 验证签名
        >>> if verifier.verify_from_headers(headers, payload):
        ...     print("Signature is valid")
        ... else:
        ...     print("Signature is invalid")
    """

    # 默认的签名 Header 名称
    DEFAULT_SIGNATURE_HEADER = "X-Webhook-Signature"

    def __init__(self, secret: str, require_signature: bool = True):
        """
        初始化签名验证器

        Args:
            secret: 签名密钥
            require_signature: 是否强制要求签名验证（默认 True）

        Raises:
            ValueError: 当 secret 为空时
        """
        if not secret:
            raise ValueError("Secret key cannot be empty")

        self.secret = secret
        self.require_signature = require_signature

    def verify_from_headers(
        self,
        headers: Dict[str, str],
        payload: Dict,
        header_name: Optional[str] = None
    ) -> bool:
        """
        从请求头中提取签名并验证

        Args:
            headers: 请求头字典
            payload: 请求负载（字典）
            header_name: 签名 Header 名称（默认使用 DEFAULT_SIGNATURE_HEADER）

        Returns:
            True=签名有效或不需要验证, False=签名无效

        Example:
            >>> verifier = WebhookSignatureVerifier(secret="my-secret-key")
            >>> headers = {"X-Webhook-Signature": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="}
            >>> payload = {"event": "content.completed", "content_id": 123}
            >>> is_valid = verifier.verify_from_headers(headers, payload)
        """
        # 如果不强制要求签名，直接返回 True
        if not self.require_signature:
            return True

        # 确定使用的 Header 名称
        sig_header = header_name or self.DEFAULT_SIGNATURE_HEADER

        # 从 Header 中提取签名
        signature = headers.get(sig_header) or headers.get(sig_header.lower()) or headers.get(sig_header.upper())

        # 如果没有找到签名
        if not signature:
            return False

        # 验证签名
        return verify_signature(payload, signature, self.secret)

    def generate_signature(self, payload: Dict) -> str:
        """
        生成签名（便捷方法）

        Args:
            payload: 请求负载（字典）

        Returns:
            Base64 编码的签名字符串

        Example:
            >>> verifier = WebhookSignatureVerifier(secret="my-secret-key")
            >>> payload = {"event": "content.completed", "content_id": 123}
            >>> signature = verifier.generate_signature(payload)
        """
        return generate_signature(payload, self.secret)

    def verify(self, payload: Dict, signature: str) -> bool:
        """
        验证签名（便捷方法）

        Args:
            payload: 请求负载（字典）
            signature: 签名字符串

        Returns:
            True=签名有效, False=签名无效

        Example:
            >>> verifier = WebhookSignatureVerifier(secret="my-secret-key")
            >>> payload = {"event": "content.completed", "content_id": 123}
            >>> signature = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="
            >>> is_valid = verifier.verify(payload, signature)
        """
        return verify_signature(payload, signature, self.secret)


def create_verifier(secret: str, require_signature: bool = True) -> WebhookSignatureVerifier:
    """
    创建 Webhook 签名验证器（工厂函数）

    Args:
        secret: 签名密钥
        require_signature: 是否强制要求签名验证（默认 True）

    Returns:
        WebhookSignatureVerifier 实例

    Example:
        >>> verifier = create_verifier(secret="my-secret-key")
        >>> payload = {"event": "content.completed", "content_id": 123}
        >>> signature = verifier.generate_signature(payload)
        >>> is_valid = verifier.verify(payload, signature)
    """
    return WebhookSignatureVerifier(secret=secret, require_signature=require_signature)
