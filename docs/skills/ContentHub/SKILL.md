---
name: content-hub
description: 管理多个内容运营账号，每个账号有独立的内容板块和写作风格。支持自动创建账号配置、模块化工作流（选题/生成/配图/质检）。
---

## 适用场景

当你需要管理多个内容运营账号时，使用本 Skill。每个账号可以有独特的内容定位、板块规划和写作风格。

**典型场景**：
- 创建新的运营账号（自动生成账号配置）
- 基于现有账号生成内容
- 管理多个运营账号（如：美食评论、新闻媒体、技术博客）
- 需要灵活的工作流配置（选题/生成/配图/质检）

**核心理念**：这不是简单的写作工具，而是**内容运营管理系统**，帮助内容创作者管理多个账号，每个账号有独特的内容定位、板块规划和写作风格。

## 目标产出

- **账号配置**：每个账号有独立的4个配置文件（account-config.md, writing-style.md, content-structure.md, data-sources.md）
- **文章输出**：按账号和日期组织，输出到 `{账号名称}/output/{日期}/` 目录
- **本地图片**：统一存放到 `{账号名称}/output/{日期}/images/` 目录
- **选题历史**：更新 `{账号名称}/output/topic-history.md`
- **执行状态**：更新 `{账号名称}/output/current-run-status.md`

## 账号文件夹结构

每个运营账号文件夹包含4个核心配置文件：

```
{账号名称}/
├── account-config.md         # 账号配置总览（工作流、输出配置、板块列表）
├── writing-style.md          # 写作风格定义（语气、人设、字数标准）
├── content-structure.md      # 内容板块定义（各板块的定位、结构、更新频率）
├── data-sources.md           # 数据源定义（监控站点、选题策略、评分标准）
├── output/                   # 输出目录
│   ├── {日期}/               # 按日期组织
│   │   ├── {日期}-{板块}-{主题}.md
│   │   └── images/
│   ├── topic-history.md      # 选题历史记录
│   └── current-run-status.md   # 本次执行状态
└── assets/                   # 静态资源
    └── brand-assets/         # 品牌素材
```

## 核心工作流

### 工作流0：创建新账号

当用户说"创建一个XX账号"或"我要运营一个XX账号"时：

1. **检查账号是否存在**
   - 查找项目根目录下是否有对应的账号文件夹
   - 如果不存在，进入创建流程

2. **引导用户定义账号**
   - 询问账号名称（如"吃货一本经"）
   - 询问账号类型（基于默认风格库或自定义）
   - 询问账号定位和目标受众
   - 询问需要启用哪些模块（选题/配图/质检）

3. **自动生成账号文件夹和配置文件**
   - 创建目录：`{账号名称}/output/`, `{账号名称}/assets/brand-assets/`
   - **核心文件（必选）**：
     - `account-config.md`, `writing-style.md`, `content-structure.md`, `content-plan.md`
     - `{账号名称}/output/current-run-status.md`
   - **模块文件（根据选配模块生成）**：
     - **选题模块**：生成 `data-sources.md` 和 `output/topic-history.md`
     - **发布模块**：生成 `publish-config.md` 和 `.env.{账号名称}`

4. **引导用户完善配置**
   - 提示用户编辑生成的配置文件
   - 特别提示用户规划内容板块

### 工作流1：基于现有账号生成内容

**Step 0：加载账号配置（必须）**
1. 读取用户指定的账号文件夹
2. 加载 `account-config.md`（获取工作流配置和板块列表）
3. 加载 `writing-style.md`（获取写作风格）
4. 加载 `content-structure.md`（获取内容板块定义）
5. 初始化执行状态记录

**Step 1：选题模块（可选）**
如果启用了选题模块：
- 从 `data-sources.md` 读取信息源列表
- 从 `topic-history.md` 读取历史选题
- 从 `content-plan.md` 读取内容计划
- 按照信息源逐个检索最新内容
- 根据评分标准筛选选题
- 记录到 `{账号}/output/topic-history.md`

**Step 2：内容生成模块（核心）**
1. 从 `content-structure.md` 读取板块定义
2. 确定本次生成的板块和选题
3. 基于 `writing-style.md` 的风格要求生成内容
4. 遵循必选/可选模块规则
5. 输出到 `{账号}/output/{日期}/` 目录

**Step 3：配图模块（可选）**
如果启用了配图模块：
- 根据文章内容分析配图需求
- 可以网络搜索图片或者通过AI生成
- 图片需要下载到 `{账号}/output/{日期}/images/`
- 更新文章中的图片引用

**Step 4：质量检查模块（可选）**
如果启用了质量检查模块：
- 执行质量门禁检查
- 检查结构、字数、风格、事实准确性、时效性
- 不通过则调整内容
- 检查配图是否符合要求，图片是否下载成功

**Step 5：内容发布（可选）**
如果启用了发布模块：
- 执行质量门禁4（发布合规性检查）
- 检查发布内容的格式是否符合发布工具的要求
- 发布到目标平台
- 发布成功后更新内容计划 (content-plan.md)

**Step 6：更新执行状态**
- 更新 `{账号}/output/current-run-status.md`
- 标记完成的任务和通过的质量门禁
- 统计输出资产清单

## MCP工具
### 网络搜索工具
- 默认MCP服务 `fetch`
   ```json
   {
      "mcpServers": {
         "fetch": {
            "args": [
               "-y",
               "mcp-server-fetch"
            ],
            "command": "uvx"
         }
      }
   }
   ```
- 可选MCP服务 `tavily`
   ```json
   {
      "mcpServers": {
         "tavily-mcp": {
            "args": [
               "-y",
               "tavily-mcp@0.1.4"
            ],
            "autoApprove": [],
            "command": "npx",
            "disabled": false,
            "env": {
               "TAVILY_API_KEY": "your-api-key-here"
            }
         }
      }
   }
   ```


### 图片生成工具
- 默认MCP服务 `mcp-server-doubao`
  ```json
   {
      "mcpServers": {
         "doubao": {
            "args": [
               "-y",
               "@tonychaos/mcp-server-doubao"
            ],
            "command": "npx",
            "disabledTools": [],
            "env": {
               "ARK_API_KEY": "your-api-key-here"
            }
         },
      }
   }
  ```

### 文章发布工具
- 微信公众号发布MCP服务 `wenyan-mcp`
  ```json
  {
     "mcpServers": {
          "wenyan-mcp": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@wenyan-md/mcp"]
            // 注意：不在启动配置中添加 env 信息
            // wenyan-mcp 会从运行时环境变量读取 WECHAT_APP_ID 和 WECHAT_APP_SECRET
         }
     }
  }
  ```

  **账号管理机制**：
  - 每个账号的微信凭证存储在 `{账号}/.env.{账号名}` 文件中
  - 项目根目录的 `.env` 文件指向当前激活的账号
  - 使用 `manage-accounts.sh switch <账号名>` 切换账号（更新 .env 文件）
  - wenyan-mcp 启动后自动从环境变量读取微信配置，无需重启


## Skill 框架关键文件

### 主文档
- **SKILL.md**：本文件，主技能文档
- **USER-GUIDE.md**：用户使用指南（如何创建账号、编辑配置、生成内容）

### 核心资源
- **resources/core-workflow.md**：核心工作流定义（详细执行步骤）
- **resources/quality-gates.md**：质量门禁规范
- **resources/mcp-tools-guide.md**：MCP工具使用指南

### 配置模板
- **resources/config-templates/account-config-template.md**：账号配置模板
- **resources/config-templates/writing-style-template.md**：写作风格模板
- **resources/config-templates/content-structure-template.md**：内容板块模板
- **resources/config-templates/data-sources-template.md**：数据源模板
- **resources/config-templates/current-run-status-template.md**：执行状态模板
- **resources/config-templates/topic-history-template.md**：选题历史记录模板

### 默认风格库
- **resources/default-styles/tech-blog-style.md**：技术博客默认风格
- **resources/default-styles/marketing-copy-style.md**：营销文案默认风格
- **resources/default-styles/food-review-style.md**：美食评论默认风格
- **resources/default-styles/news-media-style.md**：新闻媒体默认风格

### 执行脚本
- **scripts/manage-accounts.sh**：账号管理脚本

### 其他
- **CHANGELOG.md**：版本历史记录

## 账号文件夹关键文件

**必选配置文件**：
- `{账号}/account-config.md`：账号配置总览
- `{账号}/writing-style.md`：写作风格定义
- `{账号}/content-structure.md`：内容板块定义
- `{账号}/data-sources.md`：数据源定义

**输出文件**：
- `{账号}/output/{日期}/{日期}-{板块}-{主题}.md`：生成的文章
- `{账号}/output/{日期}/images/*.jpg`：配图
- `{账号}/output/topic-history.md`：选题历史记录
- `{账号}/output/current-run-status.md`：本次执行状态

## 示例输入/输出

### 示例输入1：创建新账号
```
"创建一个美食评论账号，名称叫吃货一本经，启用所有模块"
```

### 示例输出1
- 创建 `吃货一本经/` 文件夹
- 生成4个配置文件（基于美食评论默认风格）
- 引导用户规划内容板块（如：美食快讯、美食教程、美食探店等）

### 示例输入2：基于现有账号生成内容
```
"用吃货一本经账号，生成今天的美食快讯"
```

### 示例输出2
- 加载 `吃货一本经/account-config.md` 等配置
- 按该账号的写作风格和板块定义生成文章
- 输出到 `吃货一本经/output/2026-01-13/2026-01-13-美食快讯-xxx.md`
- 如果启用配图，生成并下载图片到 `吃货一本经/output/2026-01-13/images/`

## 常见问题处理

### Q1: 如何创建新账号？
**A**: 说"创建一个XX账号"或"我要运营一个XX账号"，Skill 会引导你完成账号创建。

### Q2: 如何切换账号？
**A**: 使用账号管理脚本切换默认发布账号：

**步骤1: 执行切换命令**
```bash
.claude/skills/ContentHub/scripts/manage-accounts.sh switch <账号名>
```
例如：切换到"吃货一本经"账号
```bash
.claude/skills/ContentHub/scripts/manage-accounts.sh switch 吃货一本经
```

**步骤2: 脚本自动执行以下操作**
- ✅ 更新项目根目录的 `.env` 文件
- ✅ 更新 `~/.claude.json` 中 wenyan-mcp 的环境变量配置
- ✅ 创建备份文件（`.env.backup` 和 `~/.claude.json.backup`）

**步骤3: 重启 Claude Code**
- ⚠️ **必须重启 Claude Code 才能使配置生效**
- wenyan-mcp 在启动时读取环境变量
- 重启后 wenyan-mcp 会自动使用新账号的微信凭证

**账号切换机制说明**：
- 脚本会自动在 `~/.claude.json` 的 `projects['{项目路径}'].mcpServers['wenyan-mcp'].env` 中设置：
  - `WECHAT_APP_ID`
  - `WECHAT_APP_SECRET`
- 无需手动编辑配置文件
- 切换后需要重启 Claude Code

也可以在生成内容时指定账号名称，如"用吃货一本经账号生成文章"。

### Q3: 如何规划内容板块？
**A**: 编辑账号的 `content-structure.md` 文件，定义每个板块的定位、字数范围、更新频率和结构要求。

### Q4: 如何修改写作风格？
**A**: 编辑账号的 `writing-style.md` 文件，调整语气、人设、字数标准等。

### Q5: 可以不使用默认风格吗？
**A**: 可以，创建账号时选择"自定义"，或编辑生成的配置文件。

### Q6: 如何禁用某个模块？
**A**: 编辑 `account-config.md`，取消勾选对应的模块（选题/配图/质检）。

---

**版本历史**：详见 [CHANGELOG.md](./CHANGELOG.md)

**用户指南**：详见 [USER-GUIDE.md](./USER-GUIDE.md)
