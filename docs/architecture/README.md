# 架构文档

本目录包含 ContentHub 系统的架构设计文档。

> **最后更新**: 2026-02-03

---

## 文档列表

| 文档 | 描述 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | ContentHub 系统架构说明 |

---

## 架构概述

ContentHub 采用模块化架构，基于 FastAPI + Vue 3 技术栈：

- **后端**: FastAPI + SQLAlchemy + APScheduler
- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **模块系统**: 完全可插拔的模块注册系统

### 核心特性

- 模块化架构，支持动态加载
- 混合配置管理（数据库 + Markdown）
- 多平台内容发布支持
- 定时任务调度系统

---

## 维护指南

### 添加新架构文档

1. 创建新文件：`<模块>-architecture.md`
2. 使用 [templates](../references/TEMPLATES.md) 中的架构文档模板
3. 在上表中添加文档条目

### 文档类型

- `ARCHITECTURE.md` - 系统架构主文档
- `<模块>-architecture.md` - 模块架构文档
- `<组件>-design.md` - 组件设计文档

---

**相关文档**:
- [系统设计](../design/system-design.md)
- [文档分类说明](../references/CATEGORIES.md)
