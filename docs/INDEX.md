# ContentHub 文档快速查找指南

> **最后更新**: 2026-02-05
> **文档版本**: 1.0.0

本文档提供多种查找方式，帮助你快速找到需要的文档。

---

## 按角色查找

### 新成员入门

**阅读顺序**：
1. [../README.md](../README.md) - 项目概述
2. [guides/quick-start.md](guides/quick-start.md) - 快速开始指南
3. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - 系统架构
4. [guides/cli-quick-start.md](guides/cli-quick-start.md) - CLI 使用入门

**预计时间**: 1-2 小时

---

### CLI 使用者

**常用文档**：
- [guides/cli-quick-start.md](guides/cli-quick-start.md) - CLI 快速入门
- [references/CLI-REFERENCE.md](references/CLI-REFERENCE.md) - 完整命令参考（123个命令）
- [references/content-creator-integration.md](references/content-creator-integration.md) - Content-Creator集成指南
- [development/CLI-TEST-REPORT.md](development/CLI-TEST-REPORT.md) - CLI 测试报告

**快速查找命令**：
```bash
# 查看所有命令
contenthub --help

# 查看特定模块命令
contenthub accounts --help
contenthub content --help
```

---

### 开发人员

**必读文档**：
1. [../CLAUDE.md](../CLAUDE.md) - Claude Code 开发指南
2. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - 系统架构
3. [design/](design/) - 设计文档
4. [references/](references/) - 技术参考

**模块开发**：
- [development/CLI-IMPLEMENTATION-SUMMARY.md](development/CLI-IMPLEMENTATION-SUMMARY.md) - CLI 实施总结
- [development/2026-02-05-content-creator-integration.md](development/2026-02-05-content-creator-integration.md) - Content-Creator集成报告
- [references/CATEGORIES.md](references/CATEGORIES.md) - 文档分类规范
- [references/TEMPLATES.md](references/TEMPLATES.md) - 文档模板

---

### 测试人员

**测试文档**：
- [testing/](testing/) - 当前活跃的测试文档
  - [testing/e2e/](testing/e2e/) - E2E 测试文档
  - [testing/guides/](testing/guides/) - 测试指南
- [archive/reports/testing/](archive/reports/testing/) - 历史测试报告（37+份）
- [archive/cli-testing/](archive/cli-testing/) - CLI 测试项目归档

**运行测试**：
```bash
cd src/backend
pytest                          # 运行所有测试
pytest tests/test_cli_*.py      # 运行 CLI 测试
pytest --cov                    # 生成覆盖率报告
```

---

### 项目经理

**项目报告**：
- [archive/phases/](archive/phases/) - 各阶段完成报告（PHASE 1-7）
- [archive/sessions/](archive/sessions/) - 开发会话记录
- [plans/](plans/) - 项目实施计划

**最新成果**：
- [development/CLI-TEST-REPORT.md](development/CLI-TEST-REPORT.md) - CLI 测试报告
- [archive/cli-testing/README.md](archive/cli-testing/README.md) - CLI 测试项目总结

---

### 系统管理员

**部署相关**：
- [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md) - 部署指南
- [guides/cli-quick-start.md](guides/cli-quick-start.md) - CLI 管理
- [backup/](backup/) - 备份相关文档

**常用命令**：
```bash
# 系统管理
contenthub scheduler status    # 查看调度器状态
contenthub audit list          # 查看审计日志
contenthub config list         # 查看系统配置
```

---

## 按功能查找

### CLI 系统

**设计与实施**：
- [design/cli-system-design.md](design/cli-system-design.md) - CLI 系统设计
- [development/CLI-IMPLEMENTATION-SUMMARY.md](development/CLI-IMPLEMENTATION-SUMMARY.md) - 实施总结
- [plans/CLI-IMPLEMENTATION-PLAN.md](plans/CLI-IMPLEMENTATION-PLAN.md) - 实施计划

**测试与质量**：
- [development/CLI-TEST-REPORT.md](development/CLI-TEST-REPORT.md) - 测试报告
- [development/CLI-TEST-FIX-SUMMARY.md](development/CLI-TEST-FIX-SUMMARY.md) - Bug 修复总结
- [archive/cli-testing/](archive/cli-testing/) - 测试项目归档

**使用文档**：
- [guides/cli-quick-start.md](guides/cli-quick-start.md) - 快速入门
- [references/CLI-REFERENCE.md](references/CLI-REFERENCE.md) - 命令参考

---

### 内容管理

**相关文档**：
- [references/CLI-REFERENCE.md#内容管理模块](references/CLI-REFERENCE.md) - 命令参考
- [testing/e2e/](testing/e2e/) - E2E 测试文档

**常用命令**：
```bash
contenthub content generate      # 生成内容
contenthub content list          # 内容列表
contenthub content approve       # 审核通过
contenthub content submit-review # 提交审核
```

---

### 定时任务

**相关文档**：
- [references/CLI-REFERENCE.md#定时任务模块](references/CLI-REFERENCE.md) - 命令参考

**常用命令**：
```bash
contenthub scheduler create      # 创建任务
contenthub scheduler list        # 任务列表
contenthub scheduler trigger     # 手动触发
contenthub scheduler start       # 启动调度器
```

---

### 发布管理

**相关文档**：
- [references/CLI-REFERENCE.md#发布管理模块](references/CLI-REFERENCE.md) - 命令参考

**常用命令**：
```bash
contenthub publisher publish     # 发布内容
contenthub publisher history     # 发布历史
contenthub publisher stats       # 发布统计
```

---

### 账号管理

**相关文档**：
- [references/CLI-REFERENCE.md#账号管理模块](references/CLI-REFERENCE.md) - 命令参考

**常用命令**：
```bash
contenthub accounts create       # 创建账号
contenthub accounts list         # 账号列表
contenthub accounts test-connection  # 测试连接
```

---

## 按时间线查找

### 2026-02-05：CLI 测试完成

- [archive/cli-testing/README.md](archive/cli-testing/README.md) - 项目总结
- [development/CLI-TEST-REPORT.md](development/CLI-TEST-REPORT.md) - 测试报告 v2.0.0
- **成果**: 测试覆盖率从 8.13% 提升至 72.36%

### 2026-02-04：CLI 测试启动

- [archive/cli-testing/CLI-TEST-ENHANCEMENT-PLAN.md](archive/cli-testing/CLI-TEST-ENHANCEMENT-PLAN.md) - 测试计划
- **目标**: 将覆盖率从 8.13% 提升至 60%+

### 2026-02-03：CLI 系统实施

- [development/CLI-IMPLEMENTATION-SUMMARY.md](development/CLI-IMPLEMENTATION-SUMMARY.md) - 实施总结
- **成果**: 13 个模块，123 个命令

### 历史阶段

- [archive/phases/](archive/phases/) - PHASE 1-7 完成报告
- [archive/sessions/](archive/sessions/) - 开发会话记录

---

## 按文档类型查找

### 设计文档 (design/)

- [design/system-design.md](design/system-design.md) - 系统设计
- [design/cli-system-design.md](design/cli-system-design.md) - CLI 设计

### 用户指南 (guides/)

- [guides/quick-start.md](guides/quick-start.md) - 快速开始
- [guides/cli-quick-start.md](guides/cli-quick-start.md) - CLI 入门
- [guides/quick-reference.md](guides/quick-reference.md) - 快速参考

### 开发文档 (development/)

- [development/CLI-IMPLEMENTATION-SUMMARY.md](development/CLI-IMPLEMENTATION-SUMMARY.md) - CLI 实施总结
- [development/CLI-TEST-REPORT.md](development/CLI-TEST-REPORT.md) - CLI 测试报告
- [development/CLI-TEST-FIX-SUMMARY.md](development/CLI-TEST-FIX-SUMMARY.md) - Bug 修复总结

### 技术参考 (references/)

- [references/CLI-REFERENCE.md](references/CLI-REFERENCE.md) - CLI 命令参考
- [references/CATEGORIES.md](references/CATEGORIES.md) - 分类规范
- [references/LIFECYCLE.md](references/LIFECYCLE.md) - 生命周期管理
- [references/TEMPLATES.md](references/TEMPLATES.md) - 模板规范

### 测试文档 (testing/)

- [testing/e2e/](testing/e2e/) - E2E 测试
- [testing/guides/](testing/guides/) - 测试指南
- [testing/screenshots/](testing/screenshots/) - 测试截图

### 归档文档 (archive/)

- [archive/phases/](archive/phases/) - 阶段报告
- [archive/reports/testing/](archive/reports/testing/) - 测试报告归档
- [archive/cli-testing/](archive/cli-testing/) - CLI 测试项目归档

---

## 按问题查找

### 如何快速开始？

👉 查看 [guides/quick-start.md](guides/quick-start.md)

### 如何使用 CLI？

👉 查看 [guides/cli-quick-start.md](guides/cli-quick-start.md)

### 如何查找特定命令？

👉 查看 [references/CLI-REFERENCE.md](references/CLI-REFERENCE.md)

### 如何运行测试？

👉 查看 [testing/guides/](testing/guides/) 或 [archive/cli-testing/README.md](archive/cli-testing/README.md)

### 如何了解系统架构？

👉 查看 [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)

### 如何查看项目历史？

👉 查看 [archive/phases/](archive/phases/) 阶段报告

### 如何参与开发？

👉 查看 [../CLAUDE.md](../CLAUDE.md) 和 [development/](development/)

### 如何部署系统？

👉 查看 [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)

---

## 文档统计概览

| 分类 | 数量 | 状态 | 位置 |
|------|------|------|------|
| 设计文档 | 2 | 活跃 | [design/](design/) |
| 用户指南 | 4 | 活跃 | [guides/](guides/) |
| 架构文档 | 1 | 活跃 | [architecture/](architecture/) |
| 开发文档 | 7 | 活跃 | [development/](development/) |
| 技术参考 | 10 | 活跃 | [references/](references/) |
| 测试文档 | 3 | 活跃 | [testing/](testing/) |
| 计划文档 | 3 | 活跃 | [plans/](plans/) |
| 归档文档 | 77+ | 归档 | [archive/](archive/) |
| 其他 | 44+ | 辅助 | 各目录 |

**总计**: 151+ 份文档

---

## 搜索技巧

### 按文件名搜索

```bash
# 查找所有测试报告
find docs/ -name "*TEST*REPORT*.md"

# 查找所有计划文档
find docs/ -name "*PLAN*.md"

# 查找所有总结文档
find docs/ -name "*SUMMARY*.md"
```

### 按内容搜索

```bash
# 搜索包含 "CLI" 的文档
grep -r "CLI" docs/ --include="*.md" -l

# 搜索包含 "测试" 的文档
grep -r "测试" docs/ --include="*.md" -l
```

### 按日期查找

```bash
# 查找最近修改的文档
find docs/ -name "*.md" -mtime -7

# 查找特定日期后修改的文档
find docs/ -name "*.md" -newermt "2026-02-01"
```

---

## 维护说明

### 文档更新频率

- **活跃文档**: 每周更新
- **归档文档**: 仅修正错误
- **设计文档**: 功能完成后归档

### 贡献指南

1. 遵循 [references/CATEGORIES.md](references/CATEGORIES.md) 分类规范
2. 使用 [references/TEMPLATES.md](references/TEMPLATES.md) 模板
3. 更新本索引文档
4. 保持链接有效

### 联系方式

**文档维护**: ContentHub 开发团队
**最后更新**: 2026-02-05
**版本**: 1.0.0

---

## 附录

### 文档状态符号

- ✅ **已实施**: 功能已实现并投入使用
- ❌ **待实施**: 设计完成，等待实现
- 🔄 **进行中**: 正在开发中

### 文档生命周期

```
设计阶段 → 实施阶段 → 完成归档
   ↓           ↓           ↓
design/  → 对应目录  → archive/
```

详见 [references/LIFECYCLE.md](references/LIFECYCLE.md)

---

**返回**: [README.md](README.md) | [项目根目录](../README.md)
