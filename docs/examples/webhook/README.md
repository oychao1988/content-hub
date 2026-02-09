# Webhook 使用示例

本目录包含 Webhook 回调功能的使用示例。

---

## 📚 示例清单

### 签名验证示例

| 文档 | 描述 |
|------|------|
| [webhook_signature_usage.md](webhook_signature_usage.md) | 签名生成和验证完整示例 |

---

## 📖 示例说明

### webhook_signature_usage.md

包含以下内容：
- 基本使用（函数式 API）
- 验证器类使用（面向对象 API）
- FastAPI 集成示例
- 配置说明
- 安全最佳实践
- 与 content-creator 集成指南

**适用场景**：
- 理解签名验证机制
- 在自己的代码中集成签名验证
- 配置生产环境签名验证

---

## 💡 快速开始

### 生成签名

```python
from app.utils.webhook_signature import generate_signature

payload = {"event": "completed", "taskId": "task-123"}
secret = "your-secret-key"
signature = generate_signature(payload, secret)
```

### 验证签名

```python
from app.utils.webhook_signature import verify_signature

is_valid = verify_signature(payload, signature, secret)
if is_valid:
    print("签名验证通过")
```

---

## 🔗 相关文档

### 用户指南
- [../../guides/webhook-configuration.md](../../guides/webhook-configuration.md) - 完整配置指南

### 开发文档
- [../../development/webhook/](../../development/webhook/) - 开发阶段文档

### API 文档
- [Swagger UI](http://localhost:18010/docs) - 交互式 API 文档

---

**维护人**: Claude Code
**最后更新**: 2026-02-08
