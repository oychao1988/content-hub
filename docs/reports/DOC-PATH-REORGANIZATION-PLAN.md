# ContentHub 文档路径整理计划

**创建时间**: 2026-02-08
**执行状态**: 待执行

---

## 📊 当前问题分析

### 根目录散落的文档（需要整理）

| 文件 | 类型 | 目标位置 |
|------|------|---------|
| ASYNC-CONTENT-EXECUTION.md | 执行跟踪 | docs/reports/async-content-generation/ |
| ASYNC-CONTENT-GENERATION-FINAL-REPORT.md | 最终报告 | docs/reports/async-content-generation/ |
| CLI-CHANGES-SUMMARY.md | 变化总结 | docs/reports/cli-updates/ |
| CLI-UPDATE-REPORT.md | 更新报告 | docs/reports/cli-updates/ |
| DEPLOYMENT-VERIFICATION-REPORT.md | 部署验证 | docs/reports/deployment/ |

### src/backend/docs 重复文档（需要移动）

| 文件 | 类型 | 目标位置 |
|------|------|---------|
| docs/api/async-content-api.md | API 文档 | docs/api/ |
| docs/guides/async-content-cli-quick-reference.md | CLI 参考 | docs/guides/ |
| docs/guides/async-content-user-guide.md | 用户指南 | docs/guides/ |
| docs/guides/publishing-executor-quickstart.md | 执行器指南 | docs/guides/ |
| docs/guides/scheduler-quick-reference.md | 调度器参考 | docs/guides/ |
| docs/guides/workflow-executor-guide.md | 工作流指南 | docs/guides/ |
| docs/references/ContentGenerationTask-QUICK-REFERENCE.md | 模型参考 | docs/references/ |
| docs/reports/*.md | 各种报告 | docs/reports/ 或 docs/archive/ |

### archive 目录重复文档（需要清理）

- archive/phases/ 有重复的阶段报告
- archive/sessions/ 有重复的会话记录
- archive/reports/ 有重复的测试报告

---

## 🎯 整理目标

1. ✅ 清空根目录的报告文件
2. ✅ 统一 API 文档到 docs/api/
3. ✅ 统一用户指南到 docs/guides/
4. ✅ 清理 src/backend/docs 目录
5. ✅ 归档历史报告到 docs/archive/
6. ✅ 更新所有引用路径

---

## 📋 整理步骤

### Step 1: 移动根目录报告文件

```bash
# 移动异步内容生成相关报告
mv ASYNC-CONTENT-EXECUTION.md docs/reports/async-content-generation/
mv ASYNC-CONTENT-GENERATION-FINAL-REPORT.md docs/reports/async-content-generation/

# 移动 CLI 更新相关报告
mkdir -p docs/reports/cli-updates
mv CLI-CHANGES-SUMMARY.md docs/reports/cli-updates/
mv CLI-UPDATE-REPORT.md docs/reports/cli-updates/

# 移动部署相关报告
mkdir -p docs/reports/deployment
mv DEPLOYMENT-VERIFICATION-REPORT.md docs/reports/deployment/
```

### Step 2: 移动 src/backend/docs/guides

```bash
# 移动用户指南到主 docs/guides/
mv src/backend/docs/guides/async-content-cli-quick-reference.md docs/guides/
mv src/backend/docs/guides/async-content-user-guide.md docs/guides/
mv src/backend/docs/guides/publishing-executor-quickstart.md docs/guides/
mv src/backend/docs/guides/scheduler-quick-reference.md docs/guides/
mv src/backend/docs/guides/workflow-executor-guide.md docs/guides/
```

### Step 3: 移动 src/backend/docs/api

```bash
# 移动 API 文档
mkdir -p docs/api
mv src/backend/docs/api/async-content-api.md docs/api/
```

### Step 4: 移动 src/backend/docs/references

```bash
# 移动参考文档
mv src/backend/docs/references/ContentGenerationTask-QUICK-REFERENCE.md docs/references/
```

### Step 5: 归档 src/backend/docs/reports

```bash
# 归档历史报告
mv src/backend/docs/reports/*.md docs/archive/reports/backend/
```

### Step 6: 清理空目录

```bash
# 清理空目录
rm -rf src/backend/docs/
```

### Step 7: 更新引用

```bash
# 更新所有文档中的引用路径
# (需要手动检查和更新)
```

---

## ✅ 预期结果

### 根目录（保持简洁）

```
content-hub/
├── README.md           # 项目说明
├── CLAUDE.md           # Claude 配置
├── CHANGELOG.md        # 变更日志
└── src/               # 源代码
```

### docs 目录（结构清晰）

```
docs/
├── api/                           # API 文档
│   └── async-content-api.md
├── design/                        # 设计文档
├── guides/                        # 用户指南
│   ├── async-content-cli-quick-reference.md
│   ├── async-content-user-guide.md
│   ├── publishing-executor-quickstart.md
│   ├── scheduler-quick-reference.md
│   └── workflow-executor-guide.md
├── references/                    # 技术参考
│   └── ContentGenerationTask-QUICK-REFERENCE.md
├── reports/                       # 项目报告
│   ├── async-content-generation/
│   ├── cli-updates/
│   └── deployment/
└── archive/                       # 历史归档
    ├── phases/
    ├── sessions/
    └── reports/
```

---

## ⚠️ 注意事项

1. **备份优先**: 执行前先备份
2. **引用更新**: 移动文件后需更新引用
3. **Git 追踪**: 使用 git mv 而不是 mv
4. **逐步执行**: 分步骤执行，每步验证

---

## 📝 执行清单

- [ ] Step 1: 移动根目录报告文件
- [ ] Step 2: 移动用户指南
- [ ] Step 3: 移动 API 文档
- [ ] Step 4: 移动参考文档
- [ ] Step 5: 归档历史报告
- [ ] Step 6: 清理空目录
- [ ] Step 7: 更新引用路径
- [ ] Step 8: 验证文档完整性
- [ ] Step 9: 更新 README.md
- [ ] Step 10: 提交 Git

---

**执行人**: Claude Code
**计划版本**: 1.0
