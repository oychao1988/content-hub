# ContentHub E2E 测试手动执行指南

本文档提供详细的步骤说明，帮助您手动执行端到端测试用例。

## 📋 前置准备

### 1. 启动服务

**启动后端服务**：
```bash
cd src/backend
python main.py
```
后端将运行在 `http://localhost:8010`

**启动前端服务**：
```bash
cd src/frontend
npm run dev
```
前端将运行在 `http://localhost:3010`

### 2. 确保数据库有初始数据

```bash
cd src/backend
python -c "from app.db.database import init_db; init_db()"
```

这会创建默认的 admin 用户：
- 用户名: `admin`
- 密码: `123456`

---

## 🧪 测试场景1: 内容生成完整流程

### 目标
验证从登录到创建内容的完整流程

### 测试步骤

#### 1.1 登录系统

1. 打开浏览器，访问 `http://localhost:3010`
2. 应该自动跳转到登录页面 `/login`
3. 输入用户名: `admin`
4. 输入密码: `123456`
5. 点击"登录"按钮

**预期结果**：
- ✅ 登录成功
- ✅ 自动跳转到主页/仪表板

#### 1.2 创建内容

1. 点击左侧菜单的"内容管理"
2. 点击页面右上角的"新建内容"按钮
3. 填写表单：
   - **标题**: `测试内容`
   - **内容类型**: 选择"文章"
   - **内容**: 输入 `这是一条测试内容`
   - **状态**: 选择"草稿"
4. 点击"确定"或"保存"按钮

**预期结果**：
- ✅ 内容创建成功提示
- ✅ 内容列表中出现新创建的内容
- ✅ 显示完整信息：`测试内容 这是一条测试内容`

#### 1.3 验证内容显示

1. 查看内容列表
2. 确认新创建的内容显示正确

**预期结果**：
- ✅ 标题显示: `测试内容`
- ✅ 内容显示: `这是一条测试内容`
- ✅ 状态显示: `草稿`
- ✅ Total 显示正确的数量

**验证命令**（可选）：
```bash
cd src/backend
python -c "
from app.db.database import SessionLocal
from app.models.content import Content
db = SessionLocal()
contents = db.query(Content).all()
for c in contents:
    print(f'ID: {c.id}, 标题: {c.title}, 状态: {c.status}')
"
```

---

## 🧪 测试场景2: 定时任务完整流程

### 目标
验证定时任务的创建、编辑和执行

### 测试步骤

#### 2.1 创建定时任务

1. 点击左侧菜单的"定时任务"
2. 点击"新建任务"按钮
3. 填写表单：
   - **任务名称**: `每日测试任务`
   - **任务类型**: 选择 `content_generation`
   - **Cron表达式**: 输入 `0 9 * * *`（每天早上9点）
   - **描述**: `每天早上9点自动生成内容`
4. 点击"确定"

**预期结果**：
- ✅ 任务创建成功
- ✅ 任务列表显示新任务

#### 2.2 查看任务列表

1. 刷新定时任务页面
2. 查看任务列表

**预期结果**：
- ✅ 显示任务: `每日测试任务`
- ✅ Total: 1
- ✅ 状态: idle 或 pending

#### 2.3 编辑任务

1. 找到刚创建的任务
2. 点击"编辑"按钮
3. 修改任务名称为: `每日测试任务（已修改）`
4. 点击"确定"

**预期结果**：
- ✅ 任务更新成功
- ✅ 列表显示新的任务名称

#### 2.4 立即执行任务

1. 找到任务，点击"立即执行"按钮
2. 在确认对话框中点击"确定"

**预期结果**：
- ✅ 显示"执行成功"提示
- ✅ "上次运行时间"更新为当前时间

**验证命令**（可选）：
```bash
cd src/backend
python -c "
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
db = SessionLocal()
tasks = db.query(ScheduledTask).all()
for t in tasks:
    print(f'任务: {t.name}, 上次运行: {t.last_run_at}, 下次运行: {t.next_run_at}')
"
```

---

## 🧪 测试场景3: 批量发布完整流程

### 目标
验证账号管理和发布池功能

### 测试步骤

#### 3.1 创建测试基础数据

**创建客户**：
```bash
cd src/backend
python -c "
from app.db.database import SessionLocal
from app.models.customer import Customer

db = SessionLocal()
customer = Customer(
    name='E2E测试客户',
    description='用于E2E测试的客户',
    contact_info='test@example.com'
)
db.add(customer)
db.commit()
print(f'客户创建成功，ID: {customer.id}')
"
```

**创建平台**：
```bash
cd src/backend
python -c "
from app.db.database import SessionLocal
from app.models.platform import Platform

db = SessionLocal()
platform = Platform(
    name='E2E测试微信平台',
    platform_type='wechat',
    description='用于E2E测试',
    api_config='{}'
)
db.add(platform)
db.commit()
print(f'平台创建成功，ID: {platform.id}')
"
```

**创建账号**：
```bash
cd src/backend
python -c "
from app.db.database import SessionLocal
from app.models.account import Account

db = SessionLocal()
account = Account(
    name='E2E测试公众号',
    directory_name='test_account',
    description='用于E2E测试',
    platform_id=1,  # 使用刚创建的平台ID
    customer_id=1,  # 使用刚创建的客户ID
    is_active=True
)
db.add(account)
db.commit()
print(f'账号创建成功，ID: {account.id}')
"
```

#### 3.2 验证账号管理

1. 点击左侧菜单的"账号管理"
2. 查看账号列表

**预期结果**：
- ✅ 显示账号: `E2E测试公众号`
- ✅ 平台显示: `E2E测试微信平台`
- ✅ 状态显示: `启用`
- ✅ Total: 1

#### 3.3 测试发布池功能

1. 点击左侧菜单的"发布池"
2. 查看页面UI

**预期结果**：
- ✅ UI正常显示
- ✅ "添加到发布池"按钮可用
- ✅ 表格结构正常

#### 3.4 添加内容到发布池

**方法1: 通过API添加**
```bash
cd src/backend
python -c "
import requests
import json

# 先登录获取token
login_response = requests.post('http://localhost:8010/api/v1/auth/login', json={
    'username': 'admin',
    'password': '123456'
})
token = login_response.json()['access_token']

# 添加到发布池
headers = {'Authorization': f'Bearer {token}'}
add_response = requests.post('http://localhost:8010/api/v1/publish-pool/', headers=headers, json={
    'content_id': 1,  # 使用存在的内容ID
    'priority': 1
})
print('添加结果:', add_response.json())
"
```

**方法2: 通过界面操作**
1. 在内容管理页面，找到一条内容
2. 点击"添加到发布池"按钮
3. 在对话框中确认信息
4. 点击"确定"

**预期结果**：
- ✅ API返回成功
- ✅ 发布池列表显示新增内容

#### 3.5 测试批量发布功能

1. 在发布池页面，选择要发布的内容
2. 点击"批量发布"按钮
3. 确认发布操作

**预期结果**：
- ⚠️ 发布功能需要实际的内容发布服务支持
- ✅ 如果API已实现，应返回发布结果

---

## 🧪 测试场景4: 权限控制完整流程

### 目标
验证用户权限和访问控制

### 测试步骤

#### 4.1 用户管理页面访问

1. 点击左侧菜单的"用户管理"
2. 查看页面

**预期结果**：
- ✅ 页面正常加载
- ✅ "新建用户"按钮显示

#### 4.2 权限验证

**测试未登录访问**：
1. 打开新的隐身窗口
2. 访问 `http://localhost:3010`
3. 尝试直接访问 `http://localhost:3010/accounts`

**预期结果**：
- ✅ 自动跳转到登录页面
- ✅ 无法访问受保护的路由

**测试API权限**：
```bash
# 未登录访问API
curl http://localhost:8010/api/v1/accounts/
```

**预期结果**：
- ✅ 返回401或403错误
- ✅ 提示需要登录

---

## 🧪 测试场景5: 仪表板数据展示

### 目标
验证仪表板页面可访问性

### 测试步骤

1. 点击左侧菜单的"仪表板"或"首页"
2. 查看页面加载情况

**预期结果**：
- ✅ 页面可访问
- ✅ 菜单导航正常
- ✅ 页面布局正常

---

## 📊 测试检查清单

使用以下清单记录测试结果：

| 测试项 | 操作步骤 | 预期结果 | 实际结果 | 状态 |
|-------|---------|---------|---------|------|
| 场景1.1 | 登录系统 | 成功登录并跳转 | | ☐ 通过 ☐ 失败 |
| 场景1.2 | 创建内容 | 内容创建成功 | | ☐ 通过 ☐ 失败 |
| 场景1.3 | 验证内容显示 | 内容正确显示 | | ☐ 通过 ☐ 失败 |
| 场景2.1 | 创建定时任务 | 任务创建成功 | | ☐ 通过 ☐ 失败 |
| 场景2.2 | 查看任务列表 | 任务正确显示 | | ☐ 通过 ☐ 失败 |
| 场景2.3 | 编辑任务 | 任务更新成功 | | ☐ 通过 ☐ 失败 |
| 场景2.4 | 立即执行任务 | 执行成功 | | ☐ 通过 ☐ 失败 |
| 场景3.1 | 创建测试数据 | 数据创建成功 | | ☐ 通过 ☐ 失败 |
| 场景3.2 | 验证账号管理 | 账号正确显示 | | ☐ 通过 ☐ 失败 |
| 场景3.3 | 测试发布池UI | UI正常显示 | | ☐ 通过 ☐ 失败 |
| 场景3.4 | 添加到发布池 | 添加成功 | | ☐ 通过 ☐ 失败 |
| 场景3.5 | 批量发布 | 发布功能正常 | | ☐ 通过 ☐ 失败 |
| 场景4.1 | 用户管理页面 | 页面可访问 | | ☐ 通过 ☐ 失败 |
| 场景4.2 | 权限验证 | 权限控制有效 | | ☐ 通过 ☐ 失败 |
| 场景5.1 | 仪表板页面 | 页面可访问 | | ☐ 通过 ☐ 失败 |

---

## 🔧 故障排查

### 问题1: 登录失败

**检查**：
```bash
# 确认admin用户存在
cd src/backend
python -c "
from app.db.database import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    print(f'Admin用户存在: {admin.username}')
else:
    print('Admin用户不存在，需要创建')
"
```

**解决方案**：重新初始化数据库
```bash
python -c "from app.db.database import init_db; init_db()"
```

### 问题2: API返回404

**检查**：
- 确认后端服务正常运行: `curl http://localhost:8010/health`
- 查看后端日志: `tail -f logs/app.log`

### 问题3: 前端页面空白

**检查**：
- 打开浏览器开发者工具（F12）
- 查看Console是否有错误
- 查看Network标签，确认API请求状态

### 问题4: 数据库字段错误

**解决方案**：删除数据库文件，重新初始化
```bash
cd src/backend
rm data/contenthub.db
python -c "from app.db.database import init_db; init_db()"
```

---

## 📝 测试报告模板

测试完成后，可以使用以下模板记录测试结果：

```markdown
# E2E 测试执行报告

**测试日期**: [填写日期]
**测试执行者**: [填写姓名]
**测试环境**: 前端 http://localhost:3010, 后端 http://localhost:8010

## 测试结果总览

- 测试用例总数: [总数]
- 通过数量: [数量]
- 失败数量: [数量]
- 通过率: [百分比]%

## 详细测试结果

### 场景1: 内容生成完整流程
- [ ] 1.1 登录系统 - [通过/失败] - [备注]
- [ ] 1.2 创建内容 - [通过/失败] - [备注]
- [ ] 1.3 验证内容显示 - [通过/失败] - [备注]

### 场景2: 定时任务完整流程
- [ ] 2.1 创建定时任务 - [通过/失败] - [备注]
- [ ] 2.2 查看任务列表 - [通过/失败] - [备注]
- [ ] 2.3 编辑任务 - [通过/失败] - [备注]
- [ ] 2.4 立即执行任务 - [通过/失败] - [备注]

[继续其他场景...]

## 发现的问题

1. [问题描述]
   - 重现步骤:
   - 错误信息:
   - 严重程度: [高/中/低]

## 建议和改进

[填写建议]
```

---

## 🎯 快速测试脚本

如果您想快速验证所有核心功能，可以按顺序执行：

```bash
# 1. 启动服务（在两个终端窗口中）
cd src/backend && python main.py
cd src/frontend && npm run dev

# 2. 在浏览器中执行测试
# 访问: http://localhost:3010
# 使用 admin/123456 登录

# 3. 快速创建测试数据
cd src/backend
python prepare_test_data.py  # 如果存在
# 或手动执行上面的Python脚本

# 4. 验证数据库记录
python -c "
from app.db.database import SessionLocal
from app.models.content import Content
from app.models.scheduler import ScheduledTask
from app.models.account import Account

db = SessionLocal()
print(f'内容数量: {db.query(Content).count()}')
print(f'定时任务数量: {db.query(ScheduledTask).count()}')
print(f'账号数量: {db.query(Account).count()}')
"
```

---

## 📚 相关文档

- [E2E测试最终报告](E2E_TEST_FINAL_REPORT.md) - 完整的测试结果报告
- [测试总结报告](测试总结报告.md) - 页面交互逻辑和测试结果
- [API文档](http://localhost:8010/docs) - FastAPI Swagger文档

---

**提示**: 在执行测试时，建议使用浏览器的开发者工具（F12）查看网络请求和控制台输出，这有助于快速定位问题。
