# ContentHub 项目文档

## 项目概述

ContentHub 是一个内容运营管理系统，支持多账号管理、内容生成、审核和批量发布。

## 文档分类

| 分类 | 用途 | 文档类型 |
|------|------|----------|
| **design/** | 设计文档 | 功能设计（已实施+未实施） |
| **guides/** | 使用指南 | 面向用户的操作文档 |
| **architecture/** | 架构文档 | 系统设计和技术架构 |
| **development/** | 开发相关 | 计划和总结文档 |
| **references/** | 技术参考 | 工具使用和技术参考 |
| **reports/** | 项目报告 | 里程碑完成报告 |
| **archive/** | 归档文档 | 历史文档和临时记录 |

## 调度器和执行器文档

ContentHub 提供了强大的定时任务调度系统，支持多种执行器和工作流编排：

### 核心文档

1. **[调度器快速参考](./guides/scheduler-quick-reference.md)** - 定时任务快速入门
   - 创建定时任务
   - Cron 表达式参考
   - 任务类型详解
   - 工作流快速入门
   - 故障排查指南

2. **[工作流执行器使用指南](./guides/workflow-executor-guide.md)** - 工作流详细文档
   - 核心概念（步骤、上下文、变量引用）
   - 快速开始示例
   - 执行器详解
   - 常见工作流模式
   - 高级功能和最佳实践
   - 故障排查和 FAQ

3. **[定时任务系统设计](./design/scheduler-system-design.md)** - 系统架构设计
   - 任务执行器接口设计
   - 工作流执行器架构
   - 变量解析机制
   - 扩展性设计
   - 已注册的执行器列表

### 执行器类型

| 执行器类型 | 功能描述 | 文档链接 |
|-----------|---------|---------|
| `content_generation` | 自动生成内容 | [快速参考](./guides/scheduler-quick-reference.md#1-content_generation) |
| `publishing` | 批量发布内容 | [快速参考](./guides/scheduler-quick-reference.md#2-publishing) |
| `workflow` | 编排多个执行步骤 | [工作流指南](./guides/workflow-executor-guide.md) |
| `add_to_pool` | 将内容加入发布池 | [快速参考](./guides/scheduler-quick-reference.md#4-add_to_pool) |
| `approve` | 审核内容 | [快速参考](./guides/scheduler-quick-reference.md#5-approve) |

### 使用场景

- **每日自动内容发布**: 生成 → 审核 → 发布
- **批量内容生成**: 一次性生成多篇文章
- **定时发布**: 在指定时间发布内容
- **自定义工作流**: 组合多个执行器实现复杂流程

## 文档列表

### 项目报告 (reports/)
- [CLI 实现报告](./reports/CLI-IMPLEMENTATION-REPORT.md)
- [CLI 快速参考](./reports/CLI-QUICK-REFERENCE.md)
- [CLI 阶段5命令参考](./reports/CLI_STAGE5_COMMAND_REFERENCE.md)
- [性能测试指南](./reports/PERFORMANCE_TEST_GUIDE.md)
- [性能测试报告](./reports/PERFORMANCE_TEST_REPORT.md)
- [阶段5完成报告](./reports/STAGE5_COMPLETION_REPORT.md)
- [测试改进计划](./reports/TEST_IMPROVEMENT_PLAN.md)

### 开发文档 (development/)
- [工作流执行器实施报告](./development/WORKFLOW-EXECUTOR-IMPLEMENTATION-REPORT.md) - 工作流系统完整实施记录

### 架构文档 (architecture/)
- [模块注册系统](./architecture/README.md)

### 设计文档 (design/)
- [定时任务系统设计](./design/scheduler-system-design.md) - 任务执行器接口设计
- [工作流执行器架构](./design/scheduler-system-design.md#工作流执行器架构) - 工作流编排机制

### 技术参考 (references/)
- [性能测试](./references/README.md)

### 使用指南 (guides/)
- [调度器快速参考](./guides/scheduler-quick-reference.md) - 定时任务快速入门
- [工作流执行器使用指南](./guides/workflow-executor-guide.md) - 工作流详细文档
- [发布执行器快速入门](./guides/publishing-executor-quickstart.md) - 发布功能使用

## 快速开始

### 后端

```bash
cd src/backend
pip install -r requirements.txt
cp .env.example .env
python -c "from app.db.database import init_db; init_db()"
python main.py
```

### 前端

```bash
cd src/frontend
npm install
npm run dev
```

## 项目结构

### 后端结构

```
src/backend/
├── app/
│   ├── core/                    # 核心模块（来自 omni-cast）
│   │   ├── module_registry/     # 模块注册系统
│   │   ├── module_system/       # 模块基类和接口
│   │   ├── config.py            # 配置管理（Pydantic Settings）
│   │   └── custom_logger.py     # 日志系统
│   ├── models/                  # SQLAlchemy 数据模型
│   │   ├── account.py           # 账号模型
│   │   ├── content.py           # 内容模型
│   │   ├── scheduler.py         # 定时任务模型
│   │   └── publisher.py         # 发布模型
│   ├── services/                # 业务服务层
│   ├── modules/                 # 业务模块（API 路由）
│   │   ├── auth/                # 认证模块
│   │   ├── accounts/            # 账号管理模块
│   │   ├── content/             # 内容管理模块
│   │   ├── scheduler/           # 定时任务模块
│   │   ├── publisher/           # 发布管理模块
│   │   └── dashboard/           # 仪表板模块
│   ├── db/                      # 数据库
│   │   └── database.py          # 数据库配置和会话
│   ├── utils/                   # 工具函数
│   └── factory.py               # 应用工厂
├── data/                        # 数据目录
├── logs/                        # 日志目录
├── main.py                      # 应用入口
└── requirements.txt             # 依赖清单
```

### 前端结构

```
src/frontend/
└── src/
    ├── components/              # Vue 组件
    ├── views/                   # 页面视图
    ├── stores/                  # Pinia 状态管理
    ├── router/                  # 路由配置
    └── api/                     # API 客户端
```

