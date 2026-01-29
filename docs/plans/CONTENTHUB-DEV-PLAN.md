# ContentHub 开发任务计划文档

## 任务概述
完成 ContentHub 项目的剩余模块开发，并建立完整的测试体系，确保代码质量和功能正确性。

**任务目标**：
1. 实现缺失的 customer 和 platform 后端模块
2. 修复现有问题（system 模块路由前缀）
3. 建立完整的单元测试覆盖
4. 建立端到端测试体系
5. 确保所有测试通过

**项目背景**：
- ContentHub 是一个内容运营管理系统
- 使用 FastAPI + SQLAlchemy + SQLite（后端）
- 使用 Vue 3 + Vite + Element Plus（前端）
- 采用完全可插拔的模块系统
- 当前已有 7 个模块实现完成，缺失 customer 和 platform 模块

## 阶段划分

### 阶段 1: 修复 system 模块路由前缀 [✓ 已完成]
- **目标**: 修复 system 模块的路由前缀不一致问题
- **详细描述**:
  - 检查 `app/modules/system/module.py`
  - 将路由前缀从 `/v1/system` 修改为 `/system`
  - 验证修改后的路由可以正常访问
- **完成标准**:
  - system 模块的路由前缀与其他模块一致
  - 启动服务后可以访问 `/api/v1/system/*` 路由
- **执行结果**:
  - ✅ 已将路由前缀从 `/v1/system` 改为 `/system`
  - ✅ 模块加载器会自动添加 `/api/v1` 前缀
  - ✅ 最终路由为 `/api/v1/system/health`
  - ✅ MODULE 对象正确导出
- **状态**: 已完成

---

### 阶段 2: 实现 customer 模块 [✓ 已完成]
- **目标**: 完整实现客户管理模块
- **详细描述**:
  - 创建 `app/modules/customer/` 目录结构
  - 实现 `module.py` - 导出 MODULE 对象，使用 `/api/v1/customers` 前缀
  - 实现 `endpoints.py` - API 路由
    - `GET /api/v1/customers` - 获取客户列表（支持分页、搜索）
    - `GET /api/v1/customers/{id}` - 获取客户详情
    - `POST /api/v1/customers` - 创建客户
    - `PUT /api/v1/customers/{id}` - 更新客户
    - `DELETE /api/v1/customers/{id}` - 删除客户
  - 实现 `schemas.py` - Pydantic 数据模型
    - CustomerBase - 基础字段
    - CustomerCreate - 创建请求
    - CustomerUpdate - 更新请求
    - CustomerResponse - 响应模型
    - CustomerListResponse - 列表响应（含分页）
  - 实现 `services.py` - 业务逻辑
    - CustomerService 类封装 CRUD 操作
    - 复用 shared 模块的依赖注入
  - 更新 `.env` 中的 `MODULES_ENABLED`，添加 `customer` 模块
- **完成标准**:
  - 所有文件创建并符合项目架构
  - 模块可以正常加载和注册
  - API 端点可以通过 Swagger 文档访问
  - 基础 CRUD 功能可用
- **执行结果**:
  - ✅ 创建了完整的模块目录结构
  - ✅ 实现了 module.py, schemas.py, services.py, endpoints.py
  - ✅ 5 个 API 端点全部实现（GET, POST, PUT, DELETE）
  - ✅ 支持分页、搜索、CRUD 操作
  - ✅ 更新 .env 配置，添加 customer 模块
  - ✅ 模块成功加载并注册
- **状态**: 已完成
- **依赖**: 阶段 1

---

### 阶段 3: 实现 platform 模块 [✓ 已完成]
- **目标**: 完整实现平台管理模块
- **详细描述**:
  - 创建 `app/modules/platform/` 目录结构
  - 实现 `module.py` - 导出 MODULE 对象，使用 `/api/v1/platforms` 前缀
  - 实现 `endpoints.py` - API 路由
    - `GET /api/v1/platforms` - 获取平台列表
    - `GET /api/v1/platforms/{id}` - 获取平台详情
    - `POST /api/v1/platforms` - 创建平台
    - `PUT /api/v1/platforms/{id}` - 更新平台
    - `DELETE /api/v1/platforms/{id}` - 删除平台
  - 实现 `schemas.py` - Pydantic 数据模型
    - PlatformBase, PlatformCreate, PlatformUpdate, PlatformResponse
    - 支持平台配置字段（JSON）
  - 实现 `services.py` - 业务逻辑
    - PlatformService 类封装 CRUD 操作
  - 更新 `.env` 中的 `MODULES_ENABLED`，添加 `platform` 模块
- **完成标准**:
  - 所有文件创建并符合项目架构
  - 模块可以正常加载和注册
  - API 端点可以通过 Swagger 文档访问
  - 基础 CRUD 功能可用
- **执行结果**:
  - ✅ 创建了完整的模块目录结构
  - ✅ 实现了 module.py, schemas.py, services.py, endpoints.py
  - ✅ 5 个 API 端点全部实现（GET, POST, PUT, DELETE）
  - ✅ 支持分页、搜索、CRUD 操作
  - ✅ 更新 .env 配置，添加 platform 模块
  - ✅ 模块成功加载并注册
  - ✅ 额外增加 get_by_code() 方法
- **状态**: 已完成
- **依赖**: 阶段 1

---

### 阶段 4: 建立测试基础设施 [进行中]
- **目标**: 搭建测试环境和基础配置
- **详细描述**:
  - 创建 `tests/` 目录结构
    - `tests/unit/` - 单元测试
    - `tests/integration/` - 集成测试
    - `tests/e2e/` - 端到端测试
    - `tests/conftest.py` - pytest 配置和 fixtures
  - 安装测试依赖（添加到 requirements.txt）
    - pytest
    - pytest-asyncio
    - pytest-cov
    - httpx
    - faker
  - 创建 `pytest.ini` 配置文件
  - 实现 pytest fixtures
    - `db_session` - 测试数据库会话
    - `client` - FastAPI 测试客户端
    - `test_user` - 测试用户
    - `auth_headers` - 认证头
  - 创建测试用的 SQLite 数据库配置
- **完成标准**:
  - 测试目录结构完整
  - pytest 可以正常运行
  - 基础 fixtures 可用
  - 测试配置文件就绪
- **执行结果**: 待填写
- **状态**: 待开始
- **依赖**: 阶段 2, 阶段 3

---

### 阶段 5: 编写单元测试
- **目标**: 为所有服务层编写单元测试
- **详细描述**:
  为以下服务编写单元测试（`tests/unit/services/`）：

  1. **auth 模块**
     - `test_auth_service.py` - 测试认证逻辑、token 生成

  2. **accounts 模块**
     - `test_account_service.py` - 测试账号 CRUD
     - `test_account_config_service.py` - 测试配置管理

  3. **content 模块**
     - `test_content_service.py` - 测试内容 CRUD
     - `test_content_creator_service.py` - 测试内容生成（mock）
     - `test_content_review_service.py` - 测试审核流程

  4. **scheduler 模块**
     - `test_scheduler_service.py` - 测试任务调度

  5. **publisher 模块**
     - `test_publisher_service.py` - 测试发布逻辑（mock）
     - `test_batch_publish_service.py` - 测试批量发布

  6. **publish_pool 模块**
     - `test_publish_pool_service.py` - 测试发布池

  7. **customer 模块**
     - `test_customer_service.py` - 测试客户 CRUD

  8. **platform 模块**
     - `test_platform_service.py` - 测试平台 CRUD

  9. **dashboard 模块**
     - `test_dashboard_service.py` - 测试统计数据

  测试要求：
  - 使用 mock 隔离外部依赖
  - 覆盖正常流程和异常情况
  - 测试覆盖率 >= 70%
- **完成标准**:
  - 所有服务都有对应的单元测试
  - 测试覆盖率 >= 70%
  - 所有单元测试通过
- **执行结果**: 待填写
- **状态**: 待开始
- **依赖**: 阶段 4

---

### 阶段 6: 编写集成测试
- **目标**: 为 API 端点编写集成测试
- **详细描述**:
  为所有模块的 API 端点编写集成测试（`tests/integration/`）：

  1. **test_auth.py** - 认证接口
     - POST /api/v1/auth/login
     - POST /api/v1/auth/register
     - GET /api/v1/auth/me

  2. **test_accounts.py** - 账号接口
     - CRUD 操作测试
     - 分页和筛选测试

  3. **test_content.py** - 内容接口
     - 内容 CRUD
     - 内容生成触发
     - 审核流程

  4. **test_customers.py** - 客户接口
     - CRUD 操作

  5. **test_platforms.py** - 平台接口
     - CRUD 操作

  6. **test_publishers.py** - 发布接口
     - 发布操作
     - 批量发布

  7. **test_publish_pool.py** - 发布池接口

  8. **test_schedulers.py** - 调度接口

  9. **test_dashboard.py** - 仪表板接口

  测试要求：
  - 使用真实的数据库会话
  - 在测试间清理数据
  - 测试认证和权限
- **完成标准**:
  - 所有 API 端点都有集成测试
  - 测试通过
  - API 行为符合预期
- **执行结果**: 待填写
- **状态**: 待开始
- **依赖**: 阶段 5

---

### 阶段 7: 编写端到端测试
- **目标**: 实现端到端测试覆盖关键业务流程
- **详细描述**:
  创建端到端测试（`tests/e2e/`），覆盖完整业务流程：

  1. **内容运营完整流程**
     - 用户登录 → 创建账号 → 生成内容 → 审核内容 → 发布内容 → 查看统计

  2. **客户管理流程**
     - 创建客户 → 关联账号 → 查看客户内容

  3. **批量发布流程**
     - 准备多个内容 → 添加到发布池 → 批量发布 → 验证结果

  4. **定时任务流程**
     - 创建定时任务 → 等待执行 → 验证结果

  技术方案：
  - 使用 Playwright 或 Cypress（前端 E2E）
  - 或使用 httpx + pytest（后端 E2E）
  - 考虑当前主要测试后端，先使用 httpx 实现后端 E2E
- **完成标准**:
  - 至少 4 个核心业务流程的 E2E 测试
  - 测试可以独立运行
  - 测试通过
- **执行结果**: 待填写
- **状态**: 待开始
- **依赖**: 阶段 6

---

### 阶段 8: 运行所有测试并修复
- **目标**: 确保所有测试通过
- **详细描述**:
  - 运行完整的测试套件
    - `pytest tests/unit/ -v --cov`
    - `pytest tests/integration/ -v`
    - `pytest tests/e2e/ -v`
  - 生成测试覆盖率报告
  - 修复所有失败的测试
  - 修复发现的 bug
  - 确保测试覆盖率 >= 70%
- **完成标准**:
  - 所有单元测试通过
  - 所有集成测试通过
  - 所有 E2E 测试通过
  - 测试覆盖率 >= 70%
  - 无已知 bug
- **执行结果**: 待填写
- **状态**: 待开始
- **依赖**: 阶段 7

---

### 阶段 9: 生成测试文档
- **目标**: 创建测试相关的文档
- **详细描述**:
  - 创建 `tests/README.md`
    - 测试结构说明
    - 如何运行测试
    - 测试覆盖率报告位置
    - 测试编写指南
  - 更新项目主 README.md
    - 添加测试部分
    - 说明如何运行测试
    - CI/CD 集成建议
- **完成标准**:
  - 测试文档完整
  - 用户可以根据文档独立运行测试
  - 项目 README 包含测试说明
- **执行结果**: 待填写
- **状态**: 待开始
- **依赖**: 阶段 8

---

## 整体进展
- 已完成: 3 / 9
- 当前阶段: 阶段 4 - 建立测试基础设施

## 重要备注
1. 项目采用模块化架构，新增模块需要遵循现有模式
2. 测试数据库应使用独立的 SQLite 文件，避免污染开发数据库
3. 外部服务（content-creator, content-publisher）需要在测试中使用 mock
4. 测试应快速且可重复，避免使用实际的网络调用
5. 所有新代码应遵循项目的编码规范

## 阶段依赖关系
```
阶段 1 (system 模块修复)
    ↓
阶段 2 (customer 模块) ──┐
    ↓                     │
阶段 3 (platform 模块) ───┤
    ↓                     │
阶段 4 (测试基础设施) ◄────┘
    ↓
阶段 5 (单元测试)
    ↓
阶段 6 (集成测试)
    ↓
阶段 7 (E2E 测试)
    ↓
阶段 8 (运行并修复)
    ↓
阶段 9 (生成文档)
```
