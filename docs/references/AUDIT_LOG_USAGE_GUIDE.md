# 审计日志使用指南

本文档介绍如何在 ContentHub 中使用审计日志系统。

## 1. 记录审计事件

### 基本用法

```python
from app.services.audit_service import AuditService

# 记录用户登录
AuditService.log_event(
    db=db,
    event_type="user_login",
    user_id=user.id,
    result="success",
    details={"username": user.username, "email": user.email},
    request=request  # FastAPI Request 对象（可选）
)
```

### 在端点中使用

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.services.audit_service import AuditService
from app.db.database import get_db

router = APIRouter()

@router.post("/content/create")
async def create_content(
    request: Request,
    content_data: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 创建内容
        content = create_content_logic(db, content_data)

        # 记录审计日志
        AuditService.log_event(
            db=db,
            event_type="content_create",
            user_id=current_user.id,
            result="success",
            details={
                "content_id": content.id,
                "title": content.title,
                "platform_id": content.platform_id
            },
            request=request
        )

        return {"success": True, "data": content}

    except Exception as e:
        # 记录失败的审计日志
        AuditService.log_event(
            db=db,
            event_type="content_create",
            user_id=current_user.id,
            result="failure",
            details={"error": str(e)},
            request=request
        )
        raise
```

### 使用审计装饰器（推荐）

```python
from app.core.audit_decorator import audit_log

@router.post("/content/update")
@audit_log("content_update")
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 业务逻辑
    content = update_content_logic(db, content_id, content_data)
    return content
```

### 带自定义详细信息的审计装饰器

```python
from app.core.audit_decorator import audit_log_with_details

@router.delete("/content/{content_id}")
@audit_log_with_details(
    "content_delete",
    lambda **kwargs: {"content_id": kwargs.get("content_id")}
)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 业务逻辑
    delete_content_logic(db, content_id)
    return {"success": True}
```

## 2. 查询审计日志

### 通过 API 查询

```bash
# 获取所有审计日志（分页）
GET /api/v1/audit/logs?page=1&page_size=20

# 按事件类型过滤
GET /api/v1/audit/logs?event_type=user_login

# 按用户过滤
GET /api/v1/audit/logs?user_id=1

# 按结果过滤
GET /api/v1/audit/logs?result=success

# 按日期范围过滤
GET /api/v1/audit/logs?start_date=2024-01-01&end_date=2024-01-31

# 搜索关键字
GET /api/v1/audit/logs?search=admin

# 组合过滤
GET /api/v1/audit/logs?event_type=content_create&user_id=1&result=success
```

### 通过代码查询

```python
from app.services.audit_service import AuditService

# 查询审计日志
result = AuditService.get_audit_logs(
    db=db,
    filters={
        "event_type": "user_login",
        "user_id": 1,
        "result": "success",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 1, 31)
    },
    page=1,
    page_size=20
)

print(f"总数: {result['total']}")
print(f"总页数: {result['total_pages']}")

for log in result['logs']:
    print(f"事件: {log.event_type}, 用户: {log.user_id}, 时间: {log.timestamp}")
```

## 3. 获取审计统计

### 通过 API

```bash
# 获取总体统计
GET /api/v1/audit/statistics

# 获取特定日期范围的统计
GET /api/v1/audit/statistics?start_date=2024-01-01&end_date=2024-01-31
```

### 通过代码

```python
from app.services.audit_service import AuditService

# 获取统计信息
stats = AuditService.get_audit_statistics(db)

print(f"总日志数: {stats['total_logs']}")
print(f"成功数: {stats['success_count']}")
print(f"失败数: {stats['failure_count']}")
print(f"成功率: {stats['success_rate']}%")

# 事件类型统计
for event_stat in stats['event_type_stats']:
    print(f"{event_stat['event_name']}: {event_stat['count']}")

# 活跃用户排行
for user_stat in stats['top_users']:
    print(f"用户 {user_stat['user_id']}: {user_stat['count']} 次操作")
```

## 4. 导出审计日志

### 通过 API

```bash
POST /api/v1/audit/logs/export
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "event_type": "user_login",
  "user_id": 1,
  "result": "success"
}
```

### 通过代码

```python
from app.services.audit_service import AuditService
from datetime import date

# 导出审计日志
logs = AuditService.export_audit_logs(
    db=db,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    filters={"event_type": "user_login"}
)

# 处理导出的日志
for log in logs:
    print(f"{log['timestamp']} - {log['event_name']} - 用户 {log['user_id']}")
```

## 5. 支持的事件类型

### 认证相关
- `user_login` - 用户登录
- `user_logout` - 用户登出
- `user_login_failed` - 用户登录失败
- `password_change` - 密码修改
- `password_reset` - 密码重置

### 数据操作
- `content_create` - 创建内容
- `content_update` - 更新内容
- `content_delete` - 删除内容
- `account_create/update/delete` - 账号操作
- `platform_create/update/delete` - 平台操作

### 发布相关
- `content_publish` - 发布内容
- `content_publish_failed` - 发布失败
- `batch_publish` - 批量发布
- `scheduled_publish` - 定时发布

### 配置相关
- `config_change` - 配置修改
- `writing_style_update` - 写作风格更新
- `content_theme_update` - 内容主题更新

### 权限相关
- `role_change` - 角色变更
- `permission_change` - 权限变更
- `user_create/update/delete` - 用户管理

### 系统相关
- `system_backup` - 系统备份
- `system_restore` - 系统恢复
- `data_export` - 数据导出
- `data_import` - 数据导入

## 6. 权限要求

审计日志功能需要管理员权限：

- `AUDIT_VIEW` - 查看审计日志
- `AUDIT_EXPORT` - 导出审计日志

## 7. 最佳实践

1. **在关键操作点添加审计日志**
   - 用户登录/登出
   - 数据创建/修改/删除
   - 权限变更
   - 配置修改
   - 发布操作

2. **使用装饰器简化代码**
   ```python
   @audit_log("content_create")
   async def create_content(...):
       pass
   ```

3. **提供有意义的详细信息**
   ```python
   details = {
       "content_id": content.id,
       "title": content.title,
       "platform": platform.name,
       "action": "created"
   }
   ```

4. **处理审计日志失败**
   审计日志失败不会影响主业务流程，但建议记录错误日志

5. **定期清理旧日志**
   建议实现定期清理任务，删除超过一定期限的审计日志

## 8. 示例：完整的审计日志集成

```python
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.services.audit_service import AuditService
from app.db.database import get_db
from app.core.audit_decorator import audit_log_with_details

router = APIRouter()

@router.post("/publish/{content_id}")
@audit_log_with_details(
    "content_publish",
    lambda **kwargs: {
        "content_id": kwargs.get("content_id"),
        "platform_id": kwargs.get("platform_id")
    }
)
async def publish_content(
    content_id: int,
    platform_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 发布内容
        result = publish_to_platform(db, content_id, platform_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        # 审计装饰器会自动记录失败
        raise HTTPException(
            status_code=500,
            detail=f"发布失败: {str(e)}"
        )
```

---

**文档版本**: 1.0
**更新日期**: 2026-01-29
