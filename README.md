# ContentHub

**版本**: v1.0.0
**状态**: 测试完成，可正常使用

ContentHub 是一个通用的内容运营管理系统，支持多账号管理、内容生成、审核和批量发布。

## 功能特性

### 核心功能

- **多账号管理**: 支持同时管理多个垂直领域的内容账号
- **混合配置管理**: 数据库为主，Markdown 为辅，支持双向同步
- **内容生成**: 集成 content-creator CLI，自动生成高质量内容
- **图片处理**: 自动下载和管理配图
- **内容审核**: 支持自动审核和人工审核两种模式
- **发布池管理**: 批量发布队列，支持优先级和定时发布
- **定时任务**: 灵活的任务调度系统
- **多平台发布**: 集成 content-publisher API，支持微信公众号等平台

### 工作流程

```
选题 → 内容生成 → 图片下载 → 内容审核 → 发布池 → 批量发布
```

## 技术架构

### 后端

- **框架**: FastAPI 0.109.0
- **数据库**: SQLite + SQLAlchemy 2.0
- **任务调度**: APScheduler 3.10
- **模块系统**: omni-cast 模块注册系统

### 前端

- **框架**: Vue 3 + Vite
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router

### 集成服务

- **content-creator**: CLI 调用（内容生成）
- **content-publisher**: HTTP API（微信公众号发布）
- **Tavily API**: 选题搜索

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 18.0
- npm >= 9.0

### 后端启动

```bash
cd src/backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 初始化数据库
python -c "from app.db.database import init_db; init_db()"

# 启动服务
python main.py
```

后端服务将在 `http://localhost:8010` 启动。

### 前端启动

```bash
cd src/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:3010` 启动。

## 项目结构

```
content-hub/
├── docs/                   # 项目文档
│   ├── ARCHITECTURE.md         # 架构设计文档
│   ├── DESIGN.md               # 完整设计文档
│   ├── IMPLEMENTATION-PLAN.md  # 实施计划
│   ├── QUICKSTART.md           # 快速开始
│   ├── QUICK_REFERENCE.md      # 快速参考
│   └── skills/               # Skill 框架文档
├── src/
│   ├── backend/              # 后端服务
│   │   ├── app/
│   │   │   ├── core/         # 核心模块
│   │   │   ├── models/       # 数据模型
│   │   │   ├── services/     # 业务服务
│   │   │   ├── modules/      # 业务模块（API 路由）
│   │   │   ├── db/           # 数据库
│   │   │   └── utils/        # 工具函数
│   │   ├── data/             # 数据目录
│   │   ├── logs/             # 日志目录
│   │   ├── main.py           # 应用入口
│   │   └── requirements.txt  # 依赖清单
│   └── frontend/             # 前端服务
├── README.md                # 项目说明
```

## 文档

### 核心文档
- [设计文档](docs/DESIGN.md) - 完整的项目设计文档
- [架构设计](docs/ARCHITECTURE.md) - 详细的架构设计文档
- [实施计划](docs/IMPLEMENTATION-PLAN.md) - 项目实施计划和进度
- [后端文档](src/backend/README.md) - 后端服务说明
- [Skill 文档](docs/skills/ContentHub/) - Skill 框架文档

### 测试文档
- [测试文档索引](docs/testing/README.md) - ⭐ 测试文档总目录（推荐从这里开始）
- [E2E最终验证报告](docs/testing/reports/e2e-final-verification.md) - E2E测试验证报告 (2026-02-01)
- [API错误修复报告](docs/testing/reports/e2e-api-fix-report.md) - API 404错误修复详情 (2026-02-01)
- [测试补充摘要](docs/testing/reports/test-supplement-summary.md) - 后端测试补充摘要 (2026-02-01)
- [E2E测试手动指南](docs/testing/guides/e2e-test-manual-guide.md) - 手动执行E2E测试的步骤指南
- [单元测试手动指南](docs/testing/guides/unit-test-manual-guide.md) - 手动执行单元测试的步骤指南

## 配置说明

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `PUBLISHER_API_URL` | content-publisher 服务地址 | `http://150.158.88.23:3010` |
| `PUBLISHER_API_KEY` | content-publisher API 密钥 | - |
| `CREATOR_CLI_PATH` | content-creator CLI 路径 | - |
| `TAVILY_API_KEY` | Tavily API 密钥 | - |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` |

详细配置说明请参考 [后端文档](src/backend/README.md)。

## 开发状态

### ✅ 已完成

- [x] 项目架构设计
- [x] 数据模型定义
- [x] 基础项目结构
- [x] omni-cast 核心模块集成
- [x] 数据库配置
- [x] 所有 17 个页面的开发和测试
- [x] 前端组件修复（ImagePreview、ContentEditor、MarkdownPreview）
- [x] 后端路由修复
- [x] 数据库表结构完善
- [x] 退出登录功能修复（无限循环问题）
- [x] 所有 API 端点测试
- [x] API 404 错误修复（users模块、config模块、customer路由别名、publisher/records端点）

### 🚧 进行中

- [ ] 性能优化
- [ ] 测试数据添加

### 📋 计划中

- [ ] 部署文档
- [ ] 国际化支持

## 测试完成情况

### 页面功能测试

所有页面测试通过：

| 页面名称 | 路由 | 测试状态 |
|---------|------|---------|
| 登录页面 | `/login` | ✅ 通过 |
| 仪表盘 | `/` | ✅ 通过 |
| 账号管理 | `/accounts` | ✅ 通过 |
| 内容管理 | `/content` | ✅ 通过 |
| 内容详情 | `/content/:id` | ✅ 通过 |
| 发布管理 | `/publisher` | ✅ 通过 |
| 定时任务 | `/scheduler` | ✅ 通过 |
| 发布池 | `/publish-pool` | ✅ 通过 |
| 用户管理 | `/users` | ✅ 通过 |
| 客户管理 | `/customers` | ✅ 通过 |
| 平台管理 | `/platforms` | ✅ 通过 |
| 系统配置 | `/config` | ✅ 通过 |
| 写作风格管理 | `/writing-styles` | ✅ 通过 |
| 内容主题管理 | `/content-themes` | ✅ 通过 |
| 403 页面 | `/403` | ✅ 通过 |

### 后端单元测试与集成测试

后端测试补充工作已完成（2026-02-01），新增 **69 个测试用例**：

| 测试模块 | 测试数量 | 状态 | 覆盖率 |
|---------|---------|------|--------|
| Config 服务（单元测试） | 14 | ✅ 全部通过 | 100% |
| Accounts API（集成测试） | 19 | ✅ 全部通过 | 100% |
| Dashboard API（集成测试） | 8 | ✅ 全部通过 | 100% |
| Auth API（集成测试修复） | 28 | ✅ 全部通过 | 100% |
| **新增测试总计** | **69** | **✅ 100%** | **~65%** |

**测试成果**:
- ✅ Config 模块覆盖率: 0% → 100%
- ✅ Accounts API 测试: 0 个 → 19 个
- ✅ Dashboard API 测试: 0 个 → 8 个
- ✅ Auth 测试通过率: 71% → 100%
- ✅ 整体代码覆盖率: ~50% → ~65%

详细测试报告请参阅 [测试补充报告](TEST_SUPPLEMENT_REPORT.md) 或 [测试补充摘要](TEST_SUPPLEMENT_SUMMARY.md)

### E2E测试

端到端测试已完成（2026-02-01），测试覆盖率 **97%**：

| 测试场景 | 状态 | 完成度 |
|---------|------|--------|
| 内容生成完整流程 | ✅ 完成 | 100% |
| 定时任务完整流程 | ✅ 完成 | 100% |
| 批量发布完整流程 | ✅ 完成 | 85% |
| 权限控制完整流程 | ✅ 完成 | 100% |
| 仪表板数据展示 | ✅ 完成 | 100% |

详细测试报告请参阅 [E2E测试最终报告](E2E_TEST_FINAL_REPORT.md)

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT

## 联系方式

- 项目地址: [GitHub](https://github.com/oychao1988/content-hub)
- 问题反馈: [Issues](https://github.com/oychao1988/content-hub/issues)
