# Webhook 回调配置快速指南

本文档提供 Webhook 回调功能的快速配置指南。

---

## 一、功能概述

Webhook 回调功能允许 content-creator 服务在内容生成完成后主动通知 ContentHub。

**核心优势**：
- ✓ 实时接收生成结果
- ✓ 无需主动轮询
- ✓ 降低系统负载
- ✓ 提高响应速度

---

## 二、配置步骤

### 步骤 1：启用 Webhook

编辑 `.env` 文件：

```bash
# 启用 Webhook 功能
WEBHOOK_ENABLED=true
```

### 步骤 2：配置回调基础 URL

**开发环境**（使用默认值）：

```bash
# 留空即可，系统自动使用 http://0.0.0.0:18010
WEBHOOK_CALLBACK_BASE_URL=
```

**生产环境**（使用外部域名）：

```bash
# 配置外部可访问的域名
WEBHOOK_CALLBACK_BASE_URL=https://contenthub.yourdomain.com
```

**内网环境**（使用内网 IP）：

```bash
# 配置内网 IP 地址
WEBHOOK_CALLBACK_BASE_URL=http://192.168.1.100:18010
```

### 步骤 3：重启服务

```bash
# Docker 环境
make down
make up

# 本地开发
# Ctrl+C 停止服务
python main.py
```

---

## 三、验证配置

### 3.1 检查配置是否生效

```bash
# 查看日志
grep "Webhook callback" logs/contenthub.log

# 应该看到类似的日志
# INFO:app.services.async_content_generation_service:Webhook callback enabled for task task-abc123: https://example.com/api/v1/content/callback/task-abc123
```

### 3.2 创建测试任务

```bash
# 使用 CLI 创建内容生成任务
python -m cli.main content create \
  -a 1 \
  -t "测试 Webhook 回调" \
  --keywords "测试,webhook"

# 查看任务状态
python -m cli.main content info <task_id>

# 检查 callback_url 字段
```

---

## 四、回调 URL 格式

### 4.1 URL 结构

```
{WEBHOOK_CALLBACK_BASE_URL}/api/v1/content/callback/{task_id}
```

### 4.2 示例

```
# 生产环境
https://contenthub.example.com/api/v1/content/callback/task-abc123def456

# 开发环境
http://localhost:18010/api/v1/content/callback/task-abc123def456

# 内网环境
http://192.168.1.100:18010/api/v1/content/callback/task-abc123def456
```

---

## 五、数据库迁移

### 5.1 检查字段是否存在

```bash
sqlite3 data/contenthub.db "PRAGMA table_info(content_generation_tasks);" | grep callback_url
```

### 5.2 执行迁移（如果字段不存在）

```bash
cd src/backend
python -m migrations.add_callback_url_column
```

### 5.3 验证迁移结果

```bash
sqlite3 data/contenthub.db "SELECT task_id, callback_url FROM content_generation_tasks LIMIT 5;"
```

---

## 六、常见问题

### Q1: 回调 URL 是 localhost，外部无法访问

**原因**: 未配置 `WEBHOOK_CALLBACK_BASE_URL`

**解决**:
```bash
# 生产环境必须配置外部可访问的地址
WEBHOOK_CALLBACK_BASE_URL=https://your-domain.com
```

### Q2: CLI 命令中没有 --callback-url 参数

**原因**: `WEBHOOK_ENABLED=false`

**解决**:
```bash
WEBHOOK_ENABLED=true
```

### Q3: 数据库提示 callback_url 字段不存在

**原因**: 数据库未迁移

**解决**:
```bash
python -m migrations.add_callback_url_column
```

---

## 七、配置参考

### 7.1 完整配置示例

```bash
# ========== Webhook 配置 ==========
# 是否启用 Webhook 回调功能
WEBHOOK_ENABLED=true

# Webhook 回调基础 URL（外部访问地址）
# 开发环境：留空使用默认值 http://0.0.0.0:18010
# 生产环境：配置外部域名 https://contenthub.example.com
WEBHOOK_CALLBACK_BASE_URL=https://contenthub.example.com

# Webhook 请求超时时间（秒）
WEBHOOK_TIMEOUT=10

# Webhook 签名密钥（用于验证回调请求）
WEBHOOK_SECRET_KEY=your-secret-key-here

# 是否强制要求签名验证（生产环境推荐启用）
WEBHOOK_REQUIRE_SIGNATURE=false
```

### 7.2 环境变量优先级

```
WEBHOOK_CALLBACK_BASE_URL（最高优先级）
    ↓
http://{HOST}:{PORT}（默认值）
```

---

## 八、测试清单

- [ ] Webhook 功能已启用
- [ ] 回调基础 URL 已配置
- [ ] 数据库字段已添加
- [ ] 服务已重启
- [ ] 日志显示回调 URL
- [ ] CLI 命令包含回调参数
- [ ] 数据库记录包含回调 URL

---

## 九、相关文档

- **完整实现报告**: [STAGE4-CALLBACK-URL-IMPLEMENTATION.md](./STAGE4-CALLBACK-URL-IMPLEMENTATION.md)
- **配置参考**: [.env.example](../../.env.example)
- **迁移脚本**: [migrations/add_callback_url_column.py](../../migrations/add_callback_url_column.py)
- **测试用例**: [tests/test_webhook_callback_integration.py](../../tests/test_webhook_callback_integration.py)

---

**更新时间**: 2026-02-09
**文档版本**: 1.0
