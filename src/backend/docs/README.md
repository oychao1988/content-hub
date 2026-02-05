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

## 文档列表

### 项目报告 (reports/)
- [CLI 实现报告](./reports/CLI-IMPLEMENTATION-REPORT.md)
- [CLI 快速参考](./reports/CLI-QUICK-REFERENCE.md)
- [CLI 阶段5命令参考](./reports/CLI_STAGE5_COMMAND_REFERENCE.md)
- [性能测试指南](./reports/PERFORMANCE_TEST_GUIDE.md)
- [性能测试报告](./reports/PERFORMANCE_TEST_REPORT.md)
- [阶段5完成报告](./reports/STAGE5_COMPLETION_REPORT.md)
- [测试改进计划](./reports/TEST_IMPROVEMENT_PLAN.md)

### 架构文档 (architecture/)
- [模块注册系统](./architecture/README.md)

### 技术参考 (references/)
- [性能测试](./references/README.md)

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

