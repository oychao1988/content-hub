# ContentHub Skill - 模块文档

[根目录](../../../CLAUDE.md) > [.claude](../../) > **[skills](../)** > **ContentHub**

---

## 变更记录 (Changelog)

### 2026-01-15 - 初始文档生成
- 基于 ContentHub v2.0 生成模块文档
- 记录核心工作流、配置模板、MCP工具使用

---

## 模块职责

**ContentHub** 是一个**通用内容运营管理系统** Skill 框架，用于管理多个内容运营账号。

### 核心功能
1. **多账号管理**：支持同时管理多个垂直领域的内容账号
2. **模块化工作流**：选题→生成→配图→质检→发布，可按需启用
3. **自动化配置**：创建新账号时自动生成配置文件
4. **质量保证**：内置质量门禁机制
5. **MCP 工具集成**：豆包AI文生图、微信发布、网络搜索

### 适用场景
- 管理多个内容运营账号（如：汽车、美食、科技）
- 标准化内容生产流程
- 自动化文章生成和发布
- 多平台内容分发

---

## 入口与启动

### Skill 入口文件
- **主文档**：`SKILL.md` - Skill 定义和工作流说明
- **用户指南**：`USER-GUIDE.md` - 使用说明和常见问题
- **版本历史**：`CHANGELOG.md` - 版本更新记录

### 核心工作流文件
- **工作流定义**：`resources/core-workflow.md` - 详细执行步骤
- **质量门禁**：`resources/quality-gates.md` - 质量检查标准
- **MCP 工具指南**：`resources/mcp-tools-guide.md` - MCP 工具使用说明

---

## 对外接口

### 工作流0：创建新账号

**输入**：用户说"创建一个XX账号"或"我要运营一个XX账号"

**执行步骤**：
1. 检查账号文件夹是否存在
2. 引导用户定义账号（名称、类型、定位、模块）
3. 自动生成账号文件夹和配置文件
4. 引导用户完善配置

**输出**：
- 创建 `{账号名称}/` 文件夹
- 生成配置文件：account-config.md, writing-style.md, content-structure.md
- 可选生成：data-sources.md, publish-config.md, .env.{账号名称}

---

### 工作流1：基于现有账号生成内容

**Step 0：加载账号配置**
- 读取 account-config.md
- 读取 writing-style.md
- 读取 content-structure.md
- 初始化执行状态记录

**Step 1：选题模块（可选）**
- 从 data-sources.md 读取信息源
- 从 topic-history.md 读取历史选题
- 按照信息源逐个检索最新内容
- 根据评分标准筛选选题
- 记录到 topic-history.md

**Step 2：内容生成模块（核心）**
- 从 content-structure.md 读取板块定义
- 确定本次生成的板块和选题
- 基于 writing-style.md 的风格要求生成内容
- 遵循必选/可选模块规则
- 输出到 `{账号}/output/{日期}/` 目录

**Step 3：配图模块（可选）**
- 根据文章内容分析配图需求
- 使用 doubao-mcp 生成配图
- 下载到 `{账号}/output/{日期}/images/`
- 更新文章中的图片引用

**Step 4：质量检查模块（可选）**
- 执行质量门禁检查
- 检查结构、字数、风格、事实准确性、时效性
- 不通过则调整内容
- 检查配图是否符合要求

**Step 5：内容发布（可选）**
- 执行质量门禁4（发布合规性检查）
- 使用 wenyan-mcp 发布到目标平台
- 发布成功后更新 content-plan.md

**Step 6：更新执行状态**
- 更新 current-run-status.md
- 标记完成的任务和通过的质量门禁

---

## 关键依赖与配置

### MCP 工具依赖

**1. doubao-mcp（豆包AI文生图）**
- 用途：为文章生成配图
- 配置：
  ```json
  {
    "mcpServers": {
      "doubao-mcp": {
        "command": "npx",
        "args": ["-y", "@tonychaos/mcp-server-doubao"],
        "env": {
          "ARK_API_KEY": "your-api-key"
        }
      }
    }
  }
  ```

**2. wenyan-mcp（微信公众号发布）**
- 用途：发布内容到微信公众号
- 配置：
  ```json
  {
    "mcpServers": {
      "wenyan-mcp": {
        "command": "npx",
        "args": ["-y", "@wenyan-md/mcp"]
      }
    }
  }
  ```
- **注意**：wenyan-mcp 会从运行时环境变量读取 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`

**3. tavily-mcp（网络搜索，可选）**
- 用途：检索最新新闻和资讯
- 配置：
  ```json
  {
    "mcpServers": {
      "tavily-mcp": {
        "command": "npx",
        "args": ["-y", "tavily-mcp@0.1.4"],
        "env": {
          "TAVILY_API_KEY": "your-api-key"
        }
      }
    }
  }
  ```

### 配置模板

**账号配置模板**：
- `resources/config-templates/account-config-template.md` - 账号配置模板
- `resources/config-templates/writing-style-template.md` - 写作风格模板
- `resources/config-templates/content-structure-template.md` - 内容板块模板
- `resources/config-templates/data-sources-template.md` - 数据源模板
- `resources/config-templates/publish-config-template.md` - 发布配置模板
- `resources/config-templates/content-plan-template.md` - 内容规划模板
- `resources/config-templates/topic-history-template.md` - 选题历史模板
- `resources/config-templates/current-run-status-template.md` - 执行状态模板

**默认风格库**：
- `resources/default-styles/tech-blog-style.md` - 技术博客风格
- `resources/default-styles/marketing-copy-style.md` - 营销文案风格
- `resources/default-styles/food-review-style.md` - 美食评论风格
- `resources/default-styles/news-media-style.md` - 新闻媒体风格

---

## 数据模型

### 账号文件夹结构

```
{账号名称}/
├── account-config.md         # 账号配置总览
├── writing-style.md          # 写作风格定义
├── content-structure.md      # 内容板块定义
├── data-sources.md           # 数据源定义（可选）
├── publish-config.md         # 发布配置（可选）
├── .env.{账号名称}           # 微信凭证（可选）
├── output/
│   ├── topic-history.md      # 选题历史记录
│   ├── content-plan.md       # 内容规划
│   ├── current-run-status.md # 执行状态
│   └── {日期}/
│       ├── {日期}-{板块}-{主题}.md
│       └── images/
│           ├── manifest.txt  # 图片清单
│           └── *.jpg
└── assets/
    └── brand-assets/         # 品牌素材
```

### 文章元数据模型（YAML Front Matter）

```yaml
---
title: "文章标题"
cover: 图片完整路径
date: YYYY-MM-DD
category: 板块名称
tags:
  - 标签1
  - 标签2
---
```

### 选题历史记录模型

```markdown
## 每日选题记录表

| 日期 | 板块 | 选题 | 评分 | 状态 | 文章路径 | 备注 |
|------|------|------|------|------|---------|------|
| 2026-01-13 | 显眼快讯 | 车圈热点一览 | 28 | 已完成 | 2026-01-13/2026-01-13-显眼快讯-车圈热点一览.md | - |
```

---

## 测试与质量

### 质量门禁机制

**质量门禁0：历史检查**
- 已读取最近15天选题历史
- 已检查连载系列状态
- 已清理超过7天的快讯新闻
- 今日选题无高度重复

**质量门禁1：选题质量**
- 每个板块都有1个选题
- 选题符合板块定位
- 优先级评分≥25分
- 有明确的新闻来源URL

**质量门禁2：事实准确性**
- 所有数据都有来源标注
- 关键数据已交叉验证
- 没有未经证实的断言
- 无法验证的数据使用了限定词

**质量门禁3：配图完整性**
- 每篇文章至少1张图片
- 所有图片已下载到本地
- 图片文件正常（>100KB且<2MB）
- 图片引用使用本地路径
- manifest.txt 记录完整

**质量门禁4：发布合规性**
- 文章格式符合发布工具要求
- 图片已上传到素材库
- 预览链接可访问

---

## 常见问题 (FAQ)

### Q1: 如何创建新账号？
**A**: 说"创建一个XX账号"或"我要运营一个XX账号"，Skill 会引导你完成账号创建。

### Q2: 如何切换账号？
**A**: 使用账号管理脚本：
```bash
.claude/skills/ContentHub/scripts/manage-accounts.sh switch <账号名>
```
切换后需要重启 Claude Code。

### Q3: 如何规划内容板块？
**A**: 编辑账号的 `content-structure.md` 文件，定义每个板块的定位、字数范围、更新频率和结构要求。

### Q4: 如何修改写作风格？
**A**: 编辑账号的 `writing-style.md` 文件，调整语气、人设、字数标准等。

### Q5: 可以不使用默认风格吗？
**A**: 可以，创建账号时选择"自定义"，或编辑生成的配置文件。

### Q6: 如何禁用某个模块？
**A**: 编辑 `account-config.md`，取消勾选对应的模块（选题/配图/质检）。

---

## 相关文件清单

### 核心文档
- `SKILL.md` - 主技能文档
- `USER-GUIDE.md` - 用户指南
- `CHANGELOG.md` - 版本历史

### 资源文件
- `resources/core-workflow.md` - 核心工作流
- `resources/quality-gates.md` - 质量门禁
- `resources/mcp-tools-guide.md` - MCP工具指南

### 配置模板
- `resources/config-templates/account-config-template.md`
- `resources/config-templates/writing-style-template.md`
- `resources/config-templates/content-structure-template.md`
- `resources/config-templates/data-sources-template.md`
- `resources/config-templates/publish-config-template.md`
- `resources/config-templates/content-plan-template.md`
- `resources/config-templates/topic-history-template.md`
- `resources/config-templates/current-run-status-template.md`

### 默认风格库
- `resources/default-styles/tech-blog-style.md`
- `resources/default-styles/marketing-copy-style.md`
- `resources/default-styles/food-review-style.md`
- `resources/default-styles/news-media-style.md`

### 执行脚本
- `scripts/manage-accounts.sh` - 账号管理脚本
- `scripts/contenthub_publish_prep.py` - 发布前准备脚本
- `scripts/contenthub_preflight.py` - 预检查脚本

---

**文档版本**：v1.0
**生成时间**：2026-01-15
**Skill 版本**：v2.0
**维护者**：ContentHub 团队
