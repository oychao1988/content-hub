"""
测试 Webhook 签名验证功能
"""
import pytest
from app.utils.webhook_signature import (
    generate_signature,
    verify_signature,
    WebhookSignatureVerifier,
    create_verifier
)


class TestGenerateSignature:
    """测试签名生成功能"""

    def test_generate_basic_signature(self):
        """测试生成基本签名"""
        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        signature = generate_signature(payload, secret)

        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_generate_signature_same_result(self):
        """测试相同输入生成相同签名"""
        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        signature1 = generate_signature(payload, secret)
        signature2 = generate_signature(payload, secret)

        assert signature1 == signature2

    def test_generate_signature_different_payloads(self):
        """测试不同 payload 生成不同签名"""
        secret = "my-secret-key"

        payload1 = {"event": "content.completed", "content_id": 123}
        payload2 = {"event": "content.completed", "content_id": 456}

        signature1 = generate_signature(payload1, secret)
        signature2 = generate_signature(payload2, secret)

        assert signature1 != signature2

    def test_generate_signature_different_secrets(self):
        """测试不同密钥生成不同签名"""
        payload = {"event": "content.completed", "content_id": 123}

        secret1 = "my-secret-key-1"
        secret2 = "my-secret-key-2"

        signature1 = generate_signature(payload, secret1)
        signature2 = generate_signature(payload, secret2)

        assert signature1 != signature2

    def test_generate_signature_sorted_keys(self):
        """测试 JSON 键排序一致性"""
        secret = "my-secret-key"

        payload1 = {"b": 2, "a": 1, "c": 3}
        payload2 = {"c": 3, "a": 1, "b": 2}

        signature1 = generate_signature(payload1, secret)
        signature2 = generate_signature(payload2, secret)

        # 虽然键顺序不同，但应该生成相同签名
        assert signature1 == signature2

    def test_generate_signature_complex_payload(self):
        """测试复杂 payload 的签名生成"""
        payload = {
            "event": "content.completed",
            "content_id": 123,
            "data": {
                "title": "测试标题",
                "body": "测试内容",
                "tags": ["tag1", "tag2", "tag3"]
            },
            "timestamp": 1234567890
        }
        secret = "my-secret-key"

        signature = generate_signature(payload, secret)

        assert signature is not None
        assert isinstance(signature, str)

    def test_generate_signature_empty_payload_raises_error(self):
        """测试空 payload 抛出异常"""
        secret = "my-secret-key"

        with pytest.raises(ValueError, match="Payload cannot be empty"):
            generate_signature({}, secret)

    def test_generate_signature_empty_secret_raises_error(self):
        """测试空密钥抛出异常"""
        payload = {"event": "content.completed", "content_id": 123}

        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            generate_signature(payload, "")

    def test_generate_signature_invalid_payload_raises_error(self):
        """测试无法序列化的 payload 抛出异常"""
        payload = {"event": lambda x: x}  # 函数无法序列化为 JSON
        secret = "my-secret-key"

        with pytest.raises(TypeError, match="Failed to serialize payload"):
            generate_signature(payload, secret)


class TestVerifySignature:
    """测试签名验证功能"""

    def test_verify_valid_signature(self):
        """测试验证有效签名"""
        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        signature = generate_signature(payload, secret)
        is_valid = verify_signature(payload, signature, secret)

        assert is_valid is True

    def test_verify_invalid_signature(self):
        """测试验证无效签名"""
        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        invalid_signature = "invalid-signature"
        is_valid = verify_signature(payload, invalid_signature, secret)

        assert is_valid is False

    def test_verify_tampered_payload(self):
        """测试篡改后的 payload 验证失败"""
        original_payload = {"event": "content.completed", "content_id": 123}
        tampered_payload = {"event": "content.completed", "content_id": 456}
        secret = "my-secret-key"

        signature = generate_signature(original_payload, secret)
        is_valid = verify_signature(tampered_payload, signature, secret)

        assert is_valid is False

    def test_verify_wrong_secret(self):
        """测试错误密钥验证失败"""
        payload = {"event": "content.completed", "content_id": 123}
        correct_secret = "my-secret-key"
        wrong_secret = "wrong-secret-key"

        signature = generate_signature(payload, correct_secret)
        is_valid = verify_signature(payload, signature, wrong_secret)

        assert is_valid is False

    def test_verify_empty_payload_raises_error(self):
        """测试空 payload 抛出异常"""
        secret = "my-secret-key"
        signature = "some-signature"

        with pytest.raises(ValueError, match="Payload cannot be empty"):
            verify_signature({}, signature, secret)

    def test_verify_empty_signature_raises_error(self):
        """测试空签名抛出异常"""
        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        with pytest.raises(ValueError, match="Signature cannot be empty"):
            verify_signature(payload, "", secret)

    def test_verify_empty_secret_raises_error(self):
        """测试空密钥抛出异常"""
        payload = {"event": "content.completed", "content_id": 123}
        signature = "some-signature"

        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            verify_signature(payload, signature, "")


class TestWebhookSignatureVerifier:
    """测试 WebhookSignatureVerifier 类"""

    def test_verifier_initialization(self):
        """测试验证器初始化"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")

        assert verifier.secret == "my-secret-key"
        assert verifier.require_signature is True

    def test_verifier_initialization_no_require(self):
        """测试不强制要求签名的验证器"""
        verifier = WebhookSignatureVerifier(
            secret="my-secret-key",
            require_signature=False
        )

        assert verifier.require_signature is False

    def test_verifier_initialization_empty_secret_raises_error(self):
        """测试空密钥初始化抛出异常"""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            WebhookSignatureVerifier(secret="")

    def test_verifier_generate_signature(self):
        """测试验证器生成签名"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        signature = verifier.generate_signature(payload)

        assert signature is not None
        assert isinstance(signature, str)

    def test_verifier_verify_signature(self):
        """测试验证器验证签名"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        signature = verifier.generate_signature(payload)
        is_valid = verifier.verify(payload, signature)

        assert is_valid is True

    def test_verifier_verify_from_headers_valid(self):
        """测试从请求头验证有效签名"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        signature = verifier.generate_signature(payload)
        headers = {"X-Webhook-Signature": signature}

        is_valid = verifier.verify_from_headers(headers, payload)

        assert is_valid is True

    def test_verifier_verify_from_headers_invalid(self):
        """测试从请求头验证无效签名"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        headers = {"X-Webhook-Signature": "invalid-signature"}

        is_valid = verifier.verify_from_headers(headers, payload)

        assert is_valid is False

    def test_verifier_verify_from_headers_missing_signature(self):
        """测试缺少签名的请求头"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        headers = {}  # 没有签名

        is_valid = verifier.verify_from_headers(headers, payload)

        assert is_valid is False

    def test_verifier_verify_from_headers_not_required(self):
        """测试不强制要求签名时总是返回 True"""
        verifier = WebhookSignatureVerifier(
            secret="my-secret-key",
            require_signature=False
        )
        payload = {"event": "content.completed", "content_id": 123}

        headers = {}  # 没有签名

        is_valid = verifier.verify_from_headers(headers, payload)

        # 不强制要求签名，应该返回 True
        assert is_valid is True

    def test_verifier_verify_from_headers_case_insensitive(self):
        """测试 Header 名称大小写不敏感"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        signature = verifier.generate_signature(payload)

        # 测试不同大小写的 Header
        headers1 = {"X-Webhook-Signature": signature}
        headers2 = {"x-webhook-signature": signature}
        headers3 = {"X-WEBHOOK-SIGNATURE": signature}

        assert verifier.verify_from_headers(headers1, payload) is True
        assert verifier.verify_from_headers(headers2, payload) is True
        assert verifier.verify_from_headers(headers3, payload) is True

    def test_verifier_verify_from_headers_custom_header_name(self):
        """测试自定义 Header 名称"""
        verifier = WebhookSignatureVerifier(secret="my-secret-key")
        payload = {"event": "content.completed", "content_id": 123}

        signature = verifier.generate_signature(payload)
        headers = {"X-Custom-Signature": signature}

        is_valid = verifier.verify_from_headers(
            headers,
            payload,
            header_name="X-Custom-Signature"
        )

        assert is_valid is True


class TestCreateVerifier:
    """测试工厂函数"""

    def test_create_verifier_default(self):
        """测试创建验证器（默认参数）"""
        verifier = create_verifier(secret="my-secret-key")

        assert isinstance(verifier, WebhookSignatureVerifier)
        assert verifier.secret == "my-secret-key"
        assert verifier.require_signature is True

    def test_create_verifier_no_require(self):
        """测试创建不强制要求签名的验证器"""
        verifier = create_verifier(
            secret="my-secret-key",
            require_signature=False
        )

        assert isinstance(verifier, WebhookSignatureVerifier)
        assert verifier.require_signature is False


class TestSignatureSecurity:
    """测试签名安全性"""

    def test_constant_time_comparison(self):
        """测试常量时间比较（防止时序攻击）"""
        # 这个测试主要确保使用了 hmac.compare_digest
        # 在实际应用中，时序攻击很难在单元测试中验证
        # 但我们可以验证功能正确性

        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        signature = generate_signature(payload, secret)

        # 正确的签名应该验证成功
        assert verify_signature(payload, signature, secret) is True

        # 错误的签名应该验证失败
        wrong_signature = "Y" + signature[1:]  # 改变一个字符
        assert verify_signature(payload, wrong_signature, secret) is False

    def test_signature_deterministic(self):
        """测试签名的确定性"""
        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        signatures = [generate_signature(payload, secret) for _ in range(10)]

        # 所有签名应该相同
        assert all(s == signatures[0] for s in signatures)

    def test_base64_encoding(self):
        """测试 Base64 编码"""
        import base64
        import hmac
        import hashlib
        import json

        payload = {"event": "content.completed", "content_id": 123}
        secret = "my-secret-key"

        # 手动生成签名
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        payload_bytes = payload_str.encode('utf-8')
        secret_bytes = secret.encode('utf-8')

        signature_hmac = hmac.new(secret_bytes, payload_bytes, hashlib.sha256)
        expected_signature = base64.b64encode(signature_hmac.digest()).decode('utf-8')

        # 使用函数生成签名
        actual_signature = generate_signature(payload, secret)

        # 应该相同
        assert actual_signature == expected_signature


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
