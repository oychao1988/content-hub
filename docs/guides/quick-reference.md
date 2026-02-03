# ContentHub 数据库模型快速参考

## 📚 模型文件位置

```
src/backend/app/models/
├── __init__.py          # 模型导出
├── user.py              # 用户模型
├── customer.py          # 客户模型
├── platform.py          # 平台模型
├── theme.py             # 内容主题模型
├── account.py           # 账号及配置模型
├── content.py           # 内容模型
├── scheduler.py         # 定时任务模型
└── publisher.py         # 发布管理模型
```

## 🗂️ 数据库表分类

### 核心实体（4个表）
- `users` - 用户信息
- `customers` - 客户信息
- `platforms` - 平台信息
- `content_themes` - 内容主题

### 账号配置（6个表）
- `accounts` - 账号信息
- `writing_styles` - 写作风格配置
- `content_sections` - 内容板块配置
- `data_sources` - 数据源配置
- `publish_configs` - 发布配置
- `account_configs` - 通用配置

### 内容管理（2个表）
- `contents` - 内容信息
- `topic_history` - 选题历史

### 定时任务（2个表）
- `scheduled_tasks` - 定时任务
- `task_executions` - 任务执行记录

### 发布管理（2个表）
- `publish_logs` - 发布日志
- `publish_pool` - 发布池

## 🔗 关键关系

### 用户 - 客户 - 账号
```
Customer (1) ──< (N) User
Customer (1) ──< (N) Account
```

### 账号 - 平台
```
Platform (1) ──< (N) Account
```

### 账号 - 内容
```
Account (1) ──< (N) Content
Account (1) ──< (1) WritingStyle
Account (1) ──< (N) ContentSection
Account (1) ──< (N) DataSource
Account (1) ──< (1) PublishConfig
```

### 内容 - 发布
```
Content (1) ──< (1) PublishLog
Content (1) ──< (1) PublishPool
```

### 发布配置 - 主题
```
ContentTheme (1) ──< (N) PublishConfig
```

## 📝 常用查询示例

### 查询客户的所有账号
```python
from app.models import Account, Customer

customer = db.query(Customer).first()
accounts = db.query(Account).filter(Account.customer_id == customer.id).all()
```

### 查询账号的所有内容
```python
from app.models import Content, Account

account = db.query(Account).first()
contents = db.query(Content).filter(Content.account_id == account.id).all()
```

### 查询用户信息（含客户）
```python
from app.models import User

user = db.query(User).options(joinedload(User.customer)).first()
print(user.customer.name)
```

### 查询账号配置（完整信息）
```python
from app.models import Account

account = db.query(Account).options(
    joinedload(Account.customer),
    joinedload(Account.platform),
    joinedload(Account.writing_style),
    joinedload(Account.publish_config)
).first()
```

## 🚀 数据库初始化

### 创建所有表
```python
from app.db.database import init_db

init_db()
```

### 获取数据库会话
```python
from app.db.database import SessionLocal

db = SessionLocal()
try:
    # 执行数据库操作
    pass
finally:
    db.close()
```

### 使用依赖注入（FastAPI）
```python
from app.db.database import get_db
from fastapi import Depends

@app.get("/accounts")
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    return accounts
```

## 🧪 测试脚本

### 模型验证
```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
python -m scripts.verify_models
```

### 数据库操作测试
```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
python -m scripts.test_db_operations
```

## 📊 数据库统计

- **总表数**: 16
- **外键关系**: 16
- **唯一约束**: 11
- **复合索引**: 2

## ⚠️ 注意事项

### 时区处理
所有 DateTime 字段使用 `timezone=True`:
```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### JSON 字段
使用 SQLAlchemy 的 JSON 类型存储复杂数据:
```python
keywords = Column(JSON, default=list)
modules = Column(JSON, default=list)
```

### 级联删除
配置了适当的级联删除规则:
```python
relationship("Content", back_populates="account", cascade="all, delete-orphan")
```

### 外键约束
所有外键都有对应的数据库约束:
```python
customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
```

## 🔍 故障排查

### 常见问题

1. **外键关系错误**
   - 检查 `relationship()` 配置
   - 检查 `ForeignKey()` 配置
   - 确保关联表存在

2. **索引创建失败**
   - 检查索引名称是否重复
   - 检查字段是否存在

3. **查询性能问题**
   - 添加必要的索引
   - 使用 `joinedload()` 预加载关系
   - 使用查询优化

### 调试技巧

1. **查看SQL语句**
```python
from app.db.database import engine

echo = True  # 在引擎配置中启用
```

2. **查看表结构**
```bash
sqlite3 data/contenthub.db ".schema table_name"
```

3. **查看所有表**
```bash
sqlite3 data/contenthub.db ".tables"
```

## 📖 相关文档

- [DESIGN.md](/Users/Oychao/Documents/Projects/content-hub/docs/DESIGN.md) - 设计文档
- [stage2-database-models-report.md](/Users/Oychao/Documents/Projects/content-hub/docs/stage2-database-models-report.md) - 阶段2详细报告
- [STAGE2_SUMMARY.md](/Users/Oychao/Documents/Projects/content-hub/docs/STAGE2_SUMMARY.md) - 阶段2总结

---
**更新时间**: 2026-01-28
