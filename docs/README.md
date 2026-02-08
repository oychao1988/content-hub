# ContentHub 文档中心

欢迎来到 ContentHub 项目文档中心。本文档采用标准化的分类管理体系，按文档用途和生命周期组织。

> **最后更新**: 2026-02-08
> **文档版本**: 2.6.0

---

## 快速导航

### 按角色查找

- **新成员入门**: 阅读 [guides/quick-start.md](guides/quick-start.md)
- **CLI 使用者**: 查看 [guides/cli-quick-start.md](guides/cli-quick-start.md)
- **开发人员**: 查看 [architecture/](architecture/) 和 [references/](references/)
- **测试人员**: 查看 [testing/](testing/) 和 [archive/reports/testing/](archive/reports/testing/)
- **项目经理**: 查看 [archive/phases/](archive/phases/) 阶段报告
- **系统管理员**: 查看 [guides/cli-quick-start.md](guides/cli-quick-start.md) 和 [development/CLI-IMPLEMENTATION-SUMMARY.md](development/CLI-IMPLEMENTATION-SUMMARY.md)

### 按需求查找

| 我想... | 推荐文档 |
|---------|---------|
| 快速了解项目 | [guides/quick-start.md](guides/quick-start.md) |
| 学习 CLI 使用 | [guides/cli-quick-start.md](guides/cli-quick-start.md) |
| 了解系统架构 | [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) |
| 使用 CLI 命令 | [references/CLI-REFERENCE.md](references/CLI-REFERENCE.md) |
| **配置 Webhook 功能** | **[guides/webhook-configuration.md](guides/webhook-configuration.md)** ✨ |
| 查找技术参考 | [references/](references/) |
| 查看测试报告 | [archive/reports/testing/](archive/reports/testing/) |
| 查看开发历史 | [archive/phases/](archive/phases/) |
| 了解功能设计 | [design/](design/) |
| **查看 Webhook 实施报告** | **[reports/webhook-implementation/](reports/webhook-implementation/)** ✨ |
| 查看 CLI 实施总结 | [development/CLI-IMPLEMENTATION-SUMMARY.md](development/CLI-IMPLEMENTATION-SUMMARY.md) |
| 查看 CLI 测试报告 | [development/CLI-TEST-REPORT.md](development/CLI-TEST-REPORT.md) |
| 查看 CLI 测试项目 | [archive/cli-testing/](archive/cli-testing/) |

---

## 文档分类

### 1. 设计文档 (design/)

功能设计和系统设计文档。

| 文档 | 状态 | 描述 |
|------|------|------|
| system-design.md | ✅ 已实施 | ContentHub 系统设计文档 |
| cli-system-design.md | ✅ 已实施 | CLI 系统设计文档（13个模块，123个命令） |
| scheduler-system-design.md | ✅ 已实施 | 定时任务系统设计文档 |

### 2. 用户指南 (guides/)

面向用户的操作和使用指南。

| 文档 | 描述 |
|------|------|
| quick-start.md | 快速开始指南 |
| cli-quick-start.md | CLI 快速入门指南 |
| quick-reference.md | 快速参考手册 |
| **webhook-configuration.md** | **Webhook 配置完整指南（826行）** ✨ |
| **scheduler-quick-reference.md** | **定时任务快速参考指南** ✨ |
| **publishing-executor-quickstart.md** | **发布执行器快速入门** ✨ |

### 3. 架构文档 (architecture/)

系统架构和技术架构文档。

| 文档 | 描述 |
|------|------|
| ARCHITECTURE.md | ContentHub 系统架构说明 |

### 4. 开发文档 (development/)

当前活跃的开发相关文档。

| 文档 | 描述 |
|------|------|
| **webhook/** | **Webhook 开发文档目录** ✨ |
| **SCHEDULER-TASK-IMPLEMENTATION-SUMMARY.md** | **定时任务功能实现总结（6个阶段完成）** ✨ |
| CLI-IMPLEMENTATION-SUMMARY.md | CLI 系统实施总结（13个模块完成） |
| CLI-TESTREPORT.md | CLI 系统测试报告（覆盖率72.36%） |
| CLI-TEST-FIX-SUMMARY.md | CLI 测试 Bug 修复总结 |
| DOCKER_STRUCTURE.md | Docker 结构说明 |
| FINAL-GAP-FILLING-COMPLETION-REPORT.md | 差距填补完成报告 |
| FRONTEND_VALIDATION_SUMMARY.md | 前端验证总结 |

### 5. 技术参考 (references/)

技术工具使用参考和开发规范。

| 文档 | 描述 |
|------|------|
| CATEGORIES.md | 文档分类规范 |
| LIFECYCLE.md | 文档生命周期管理 |
| TEMPLATES.md | 文档模板规范 |
| CLI-REFERENCE.md | CLI 命令参考手册（123个命令） |
| error-handling-quick-reference.md | 错误处理快速参考 |
| error-handling-summary.md | 错误处理总结 |
| error-handling-test.md | 错误处理测试 |
| AUDIT_LOG_USAGE_GUIDE.md | 审计日志使用指南 |
| RATE_LIMITER_GUIDE.md | 速率限制器指南 |

### 6. 测试文档 (testing/)

当前活跃的测试文档。

| 子目录 | 描述 |
|--------|------|
| e2e/ | E2E 测试文档 |
| guides/ | 测试指南（E2E、单元测试） |
| screenshots/ | 测试截图 |

### 7. 归档文档 (archive/)

历史文档和已完成项目的记录。

| 子目录 | 描述 |
|--------|------|
| phases/ | 各阶段完成报告（PHASE 1-7）|
| sessions/ | 开发会话记录和临时总结 |
| reports/ | 各类历史报告 |
| reports/testing/ | 测试报告归档（37+ 份）|
| cli-testing/ | CLI 测试项目归档（7份）|

### 8. 其他文档

| 子目录 | 描述 |
|--------|------|
| agents/ | Claude Code Agent 配置 |
| skills/ | ContentHub 技能配置 |
| plans/ | 项目实施计划（3份）|
| backup/ | 备份相关文档 |
| deployment/ | 部署指南 |
| **reports/** | **项目报告目录** ✨ |
| **examples/** | **示例代码目录** ✨ |

---

## 📁 新增文档结构

### Webhook 功能文档（2026-02-08 新增）

**项目报告**:
- 📘 [reports/webhook-implementation/](reports/webhook-implementation/) - 完整实施文档
  - 实施计划和总结
  - 阶段完成报告
  - 最终完成报告（项目根目录）

**开发文档**:
- 📗 [development/webhook/](development/webhook/) - 开发阶段文档
  - 阶段 3 总结
  - 端点实现文档
  - 快速配置指南

**用户指南**:
- 📙 [guides/webhook-configuration.md](guides/webhook-configuration.md) - 完整配置指南（826 行）

**示例代码**:
- 💡 [examples/webhook/](examples/webhook/) - 使用示例
  - 签名验证示例
  - 集成代码示例

---

## 文档状态符号

- ✅ **已实施**: 功能已实现并投入使用
- ❌ **待实施**: 设计完成，等待实现
- 🔄 **进行中**: 正在开发中

---

## 文档生命周期

ContentHub 文档遵循完整的生命周期管理：

```
设计阶段 → 实施阶段 → 完成归档
   ↓           ↓           ↓
design/  → 对应目录  → archive/
(❌待实施)  (✅已实施)   (历史记录)
```

详见 [references/CATEGORIES.md](references/CATEGORIES.md) 和 [references/LIFECYCLE.md](references/LIFECYCLE.md)

---

## 文档统计

| 分类 | 文档数量 | 状态 |
|------|---------|------|
| 设计文档 | 3 | 活跃 |
| 用户指南 | 6 | 活跃 |
| 架构文档 | 1 | 活跃 |
| 开发文档 | 8 | 活跃 |
| 技术参考 | 10 | 活跃 |
| 测试文档 | 3 | 活跃 |
| 计划文档 | 3 | 活跃 |
| 归档文档 | 86+ | 归档 |
| 其他 | 44+ | 辅助 |

**总计**: 164+ 份文档

---

## 维护指南

### 添加新文档

1. **设计阶段**: 在 `design/` 创建 `<功能名>-design.md`，标记为 ❌
2. **实施完成**: 更新状态为 ✅，添加实施时间
3. **可选转移**: 移到对应目录或保留在 `design/`
4. **历史归档**: 过期文档移到 `archive/` 对应子目录

### 文档命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 设计文档 | `<功能名>-design.md` | `workflow-scaffolding-design.md` |
| 使用指南 | `<功能名>-guide.md` | `translation-workflow-guide.md` |
| 快速开始 | `quick-start.md` | 固定命名 |
| 计划文档 | `<功能名>-PLAN.md` | `database-refactoring-PLAN.md` |
| 总结文档 | `<功能名>-SUMMARY.md` | `database-refactoring-SUMMARY.md` |
| 完成报告 | `<阶段>-COMPLETION-REPORT.md` | `STAGE-4-COMPLETION-REPORT.md` |

### 搜索文档

```bash
# 查找测试文档
ls docs/testing/

# 查找阶段报告
ls docs/archive/phases/

# 查找归档报告
ls docs/archive/reports/
```

---

## 相关链接

- **项目主 README**: [../README.md](../README.md)
- **Claude 开发指南**: [../CLAUDE.md](../CLAUDE.md)
- **GitHub 仓库**: [ContentHub](https://github.com/your-org/content-hub)

---

**维护者**: ContentHub 开发团队
**文档框架**: project-documentation-management v2.0

---

## 快速查找索引

需要快速找到文档？请查看 [INDEX.md](INDEX.md) 获取完整的文档查找指南。
