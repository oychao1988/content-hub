# Webhook 签名验证使用示例

本文档演示如何使用 Webhook 签名验证功能。

## 功能概述

Webhook 签名验证使用 HMAC-SHA256 算法确保请求的真实性，防止伪造请求。

## 基本使用

### 1. 生成签名

```python
from app.utils.webhook_signature import generate_signature

payload = {"event": "content.completed", "content_id": 123}
secret = "my-secret-key"

signature = generate_signature(payload, secret)
print(f"签名: {signature}")
# 输出: 4R1sKIjCNQuxYokkm+pQo1RKkHrL6opvpVVdOvFrvhQ=
```

### 2. 验证签名

```python
from app.utils.webhook_signature import verify_signature

payload = {"event": "content.completed", "content_id": 123}
signature = "4R1sKIjCNQuxYokkm+pQo1RKkHrL6opvpVVdOvFrvhQ="
secret = "my-secret-key"

is_valid = verify_signature(payload, signature, secret)
if is_valid:
    print("签名有效")
else:
    print("签名无效")
```

## 使用验证器类

### 创建验证器

```python
from app.utils.webhook_signature import create_verifier

# 创建验证器（强制要求签名）
verifier = create_verifier(secret="my-secret-key", require_signature=True)

# 或创建不强制要求签名的验证器
verifier = create_verifier(secret="my-secret-key", require_signature=False)
```

### 从请求头验证签名

```python
from app.utils.webhook_signature import WebhookSignatureVerifier

verifier = WebhookSignatureVerifier(secret="my-secret-key")

# 假设从请求中获取的 Headers 和 Payload
headers = {
    "X-Webhook-Signature": "4R1sKIjCNQuxYokkm+pQo1RKkHrL6opvpVVdOvFrvhQ="
}
payload = {"event": "content.completed", "content_id": 123}

# 验证签名
is_valid = verifier.verify_from_headers(headers, payload)
if is_valid:
    print("签名验证通过")
else:
    print("签名验证失败")
```

### 使用自定义 Header 名称

```python
verifier = WebhookSignatureVerifier(secret="my-secret-key")

headers = {
    "X-Custom-Signature": "4R1sKIjCNQuxYokkm+pQo1RKkHrL6opvpVVdOvFrvhQ="
}
payload = {"event": "content.completed", "content_id": 123}

# 使用自定义 Header 名称验证
is_valid = verifier.verify_from_headers(
    headers,
    payload,
    header_name="X-Custom-Signature"
)
```

## FastAPI 集成示例

### 创建依赖注入函数

```python
from fastapi import Header, HTTPException, status
from typing import Optional
from app.utils.webhook_signature import create_verifier
from app.core.config import settings

# 创建签名验证器
webhook_verifier = None
if settings.WEBHOOK_SECRET_KEY:
    webhook_verifier = create_verifier(
        secret=settings.WEBHOOK_SECRET_KEY,
        require_signature=settings.WEBHOOK_REQUIRE_SIGNATURE
    )

async def verify_webhook_signature(
    x_webhook_signature: Optional[str] = Header(None),
    payload: dict = None
):
    """验证 Webhook 签名的依赖注入函数"""
    if webhook_verifier is None:
        # 如果未配置签名验证，直接通过
        return True

    headers = {"X-Webhook-Signature": x_webhook_signature} if x_webhook_signature else {}

    if not webhook_verifier.verify_from_headers(headers, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    return True
```

### 在路由中使用

```python
from fastapi import APIRouter, Depends
from app.modules.shared.schemas.api import ApiResponse

router = APIRouter()

@router.post("/webhook/callback")
async def webhook_callback(
    payload: dict,
    verified: bool = Depends(verify_webhook_signature)
):
    """Webhook 回调接口"""
    # 处理 webhook 数据
    event = payload.get("event")
    content_id = payload.get("content_id")

    return ApiResponse.success(
        data={"message": "Webhook received", "event": event},
        message="Webhook processed successfully"
    )
```

## 配置说明

在 `.env` 文件中添加以下配置：

```bash
# Webhook 签名配置
WEBHOOK_SECRET_KEY=your-secret-key-here        # 签名密钥（必需）
WEBHOOK_REQUIRE_SIGNATURE=True                  # 是否强制要求签名验证（生产环境推荐 True）
```

## 安全最佳实践

1. **使用强密钥**：签名密钥应该足够长且随机（至少 32 字符）
2. **生产环境启用验证**：设置 `WEBHOOK_REQUIRE_SIGNATURE=True`
3. **保护密钥**：不要将密钥硬编码在代码中，使用环境变量
4. **定期更换密钥**：定期轮换签名密钥以提高安全性
5. **HTTPS 传输**：确保 Webhook 回调使用 HTTPS 传输

## 测试

运行测试验证功能：

```bash
cd src/backend
pytest tests/test_webhook_signature.py -v
```

## 故障排查

### 签名验证失败

1. 检查密钥是否正确
2. 确认 payload 格式一致（JSON 键顺序）
3. 验证签名编码方式（Base64）
4. 检查 Header 名称是否匹配

### Header 名称大小写问题

验证器会自动处理大小写，以下格式都可以：

- `X-Webhook-Signature`
- `x-webhook-signature`
- `X-WEBHOOK-SIGNATURE`

## 与 content-creator 集成

当 content-creator 发送 Webhook 回调时，需要使用相同的密钥和算法生成签名：

```python
# content-creator 端的签名生成示例
import hmac
import hashlib
import base64
import json

def generate_webhook_signature(payload, secret):
    payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    payload_bytes = payload_str.encode('utf-8')
    secret_bytes = secret.encode('utf-8')

    signature_hmac = hmac.new(secret_bytes, payload_bytes, hashlib.sha256)
    return base64.b64encode(signature_hmac.digest()).decode('utf-8')

# 发送 Webhook
payload = {"event": "content.completed", "content_id": 123}
secret = "my-secret-key"  # 与 ContentHub 相同的密钥
signature = generate_webhook_signature(payload, secret)

headers = {
    "Content-Type": "application/json",
    "X-Webhook-Signature": signature
}

# 发送请求到 ContentHub
# requests.post(webhook_url, json=payload, headers=headers)
```

## 相关文档

- [配置参考](../../references/config-reference.md)
- [安全指南](../../security/security-guide.md)
- [测试文档](../../../testing/README.md)
