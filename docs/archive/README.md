# 归档文档

本目录包含 ContentHub 项目的历史文档和已完成项目的记录。

> **最后更新**: 2026-02-03

---

## 目录结构

```
archive/
├── phases/       # 各阶段完成报告（PHASE 1-7）
├── sessions/     # 开发会话记录和临时总结
└── reports/      # 各类历史报告
    └── testing/  # 测试报告归档（37+ 份）
```

---

## 归档内容

### phases/ - 阶段报告

各开发阶段的完成报告和执行记录。

**主要内容**:
- PHASE 1-7 的完成报告
- 阶段执行报告
- 进度总结和项目状态快照

### sessions/ - 会话记录

开发会话的临时总结和计划文档。

**主要内容**:
- 实施计划（IMPLEMENTATION-PLAN.md）
- 临时总结（SUMMARY.md, STAGE2_SUMMARY.md）
- 重构计划（SIDEBAR_MENU_REFACTOR-*.md）
- 截图和视觉资料

### reports/ - 历史报告

各类历史报告的统一归档。

#### testing/ - 测试报告

37+ 份测试相关报告，包括：

- **完整测试报告**: COMPLETE-TEST-REPORT.md, FINAL-TEST-REPORT.md
- **执行总结**: TEST-EXECUTION-SUMMARY.md, TEST-SUMMARY.md
- **Bug 报告**: BUG-REPORT.md, BUG_FIX_REPORT.md
- **前端分析**: FRONTEND-ANALYSIS.md
- **E2E 测试**: E2E_*.md
- **测试计划**: 各种 *_PLAN.md
- **测试用例**: TEST-CHECKLIST.md

---

## 归档原则

### 何时归档

文档满足以下条件之一时应该归档：

- [ ] 功能完成并稳定运行
- [ ] 阶段性项目结束
- [ ] 文档不再需要频繁更新
- [ ] 被更新的文档替代

### 归档位置

| 文档类型 | 归档位置 |
|---------|---------|
| 阶段完成报告 | `phases/` |
| 开发会话记录 | `sessions/` |
| 测试报告 | `reports/testing/` |
| 其他报告 | `reports/` |

---

## 搜索归档文档

```bash
# 查找阶段报告
ls docs/archive/phases/

# 查找测试报告
ls docs/archive/reports/testing/

# 查找会话记录
ls docs/archive/sessions/
```

---

## 注意事项

1. **归档文档是历史记录，不应再修改**
2. 如需更新，应在活跃目录创建新文档
3. 定期审查归档结构，保持组织清晰

---

**相关文档**:
- [文档生命周期](../references/LIFECYCLE.md)
- [文档分类说明](../references/CATEGORIES.md)
