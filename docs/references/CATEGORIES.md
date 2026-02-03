# 文档分类详解

本文档详细说明 ContentHub 项目文档的各个分类及其用途。

> **最后更新**: 2026-02-03

---

## 七大分类

### 1. design/ - 设计文档

**用途**: 存放功能设计和系统设计文档

**特点**:
- 包含已实施和未实施的设计
- 使用状态表清晰标记实施状态
- 保留设计历史以便追溯

**文档类型**:
- 功能设计文档：`<功能名>-design.md`
- 系统设计文档：`system-design.md`

**状态标记**:
| 状态 | 符号 | 说明 |
|------|------|------|
| 已实施 | ✅ | 功能已实现并投入使用 |
| 待实施 | ❌ | 设计完成，等待实现 |
| 进行中 | 🔄 | 正在开发中 |

---

### 2. guides/ - 用户指南

**用途**: 面向最终用户的操作和使用指南

**文档类型**:
- `quick-start.md` - 快速开始指南（固定命名）
- `user-guide.md` - 用户手册（固定命名）
- `<功能名>-guide.md` - 功能使用指南

**目标读者**: 新成员、最终用户、运营人员

---

### 3. architecture/ - 架构文档

**用途**: 系统架构、技术架构和设计模式说明

**文档类型**:
- `ARCHITECTURE.md` - 系统架构主文档
- `<模块>-architecture.md` - 模块架构文档
- `<组件>-design.md` - 组件设计文档

**目标读者**: 开发人员、架构师

---

### 4. development/ - 开发文档

**用途**: 当前活跃的开发计划和总结文档

**文档类型**:
- `<功能名>-PLAN.md` - 开发计划
- `<功能名>-SUMMARY.md` - 开发总结
- `<功能名>-COMPLETION-REPORT.md` - 完成报告

**注意事项**:
- 只保留当前活跃的文档
- 完成的文档移到 `archive/`

---

### 5. references/ - 技术参考

**用途**: 开发工具使用参考和技术规范

**文档类型**:
- 工具使用指南
- API 参考手册
- 最佳实践文档
- 代码规范文档

**示例**:
- `error-handling-quick-reference.md`
- `AUDIT_LOG_USAGE_GUIDE.md`
- `RATE_LIMITER_GUIDE.md`

---

### 6. reports/ - 项目报告

**用途**: 重要的里程碑完成报告

**文档类型**:
- `<阶段>-COMPLETION-REPORT.md` - 阶段完成报告
- `<项目>-FINAL-REPORT.md` - 项目最终报告

**特点**:
- 只包含重要的里程碑报告
- 临时和测试报告放入 `archive/`

---

### 7. archive/ - 归档文档

**用途**: 历史文档和已完成项目的记录

**子目录结构**:
```
archive/
├── phases/       # 各阶段完成报告
├── sessions/     # 开发会话记录
└── reports/      # 各类历史报告
    └── testing/  # 测试报告归档
```

---

## 文档分类决策树

```
需要创建文档
    │
    ├─ 是功能设计？ → design/
    ├─ 是用户指南？ → guides/
    ├─ 是系统架构？ → architecture/
    ├─ 是活跃开发计划？ → development/
    ├─ 是技术参考？ → references/
    ├─ 是重要里程碑报告？ → reports/
    ├─ 是历史/已完成文档？ → archive/
    └─ 不确定？ → 参考 README.md 快速导航
```

---

## 特殊目录

### agents/ - Agent 配置

Claude Code Agent 相关配置文档

### skills/ - 技能配置

ContentHub 技能定义和资源

### backup/ - 备份文档

数据库备份、恢复相关文档

### deployment/ - 部署文档

部署指南、环境配置文档

### testing/ - 测试文档

当前活跃的测试文档（E2E 测试、测试截图等）

---

## 常见问题

### Q: 设计文档应该放在哪里？

**A**: 如果是功能设计，放在 `design/`；如果是系统架构，放在 `architecture/`。

### Q: 测试报告应该放在哪里？

**A**:
- 当前活跃的测试计划 → `testing/`
- 已完成的测试报告 → `archive/reports/testing/`

### Q: 开发计划完成后怎么办？

**A**: 将完成后的计划文档和总结文档移到 `archive/sessions/` 或 `archive/phases/`。

---

**维护者**: ContentHub 开发团队
