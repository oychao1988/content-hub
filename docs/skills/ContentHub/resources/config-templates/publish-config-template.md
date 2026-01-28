# 微信公众号发布配置

## 账号信息
- 账号名称: {账号名称}
- 公众号名称: {公众号名称}
- 创建时间: {YYYY-MM-DD}
- 最后更新: {YYYY-MM-DD}

## 发布状态
- [ ] 启用微信公众号发布
- [ ] 已配置 AppID 和 AppSecret
- [ ] 已测试发布流程

## 公众号配置

### 账号环境变量配置

ContentHub Skill 会自动通过账号管理脚本管理微信凭证，无需在配置文件中手动填写。

凭证存储位置: `{账号目录}/.env.{账号名称}`

## 发布配置

### 发布模式
- **草稿模式**（推荐）: 发布到草稿箱，人工审核后发布
- **直接发布**: 自动直接发布到公众号

### 默认主题
- 快讯类: `orangeheart`（温暖活力）
- 深度文章: `default`（经典长文）
- 测评类: `lapis`（清新简约）

### 发布时间
- 快讯: 09:00 / 12:00 / 18:00
- 深度文章: 15:00
- 测评文章: 20:00

## 使用流程

### 1. 配置账号（首次）

1. 使用管理工具添加账号：`.claude/skills/ContentHub/scripts/manage-accounts.sh add {账号名称}`
2. 按提示输入 AppID 和 AppSecret
3. 重启 Claude Code 加载新配置

### 2. 发布文章

**步骤**:
1. 确认文章已生成并通过质量检查
2. 准备 frontmatter（标题和封面）
3. 调用 wenyan-mcp 发布工具
4. 选择合适的主题
5. 发布到草稿箱
6. 登录微信公众平台确认

**示例**:
```markdown
---
title: 【文章标题】
---

![图片](本地路径或网络URL)

文章正文...
```

### 3. 切换账号（多账号场景）

使用 ContentHub Skill 提供的账号管理工具：

```bash
# 列出所有账号
.claude/skills/ContentHub/scripts/manage-accounts.sh list

# 切换账号
.claude/skills/ContentHub/scripts/manage-accounts.sh switch {账号名称}
```

## 多账号管理

### 当前账号配置

本账号的微信公众号配置存储在：

```
{账号目录}/.env.{账号名称}
```

### 账号管理工具

ContentHub Skill 提供了账号管理脚本：

```bash
# 列出所有账号
.claude/skills/ContentHub/scripts/manage-accounts.sh list

# 切换账号
.claude/skills/ContentHub/scripts/manage-accounts.sh switch {账号名称}

# 添加新账号
.claude/skills/ContentHub/scripts/manage-accounts.sh add 新账号名

# 验证配置
.claude/skills/ContentHub/scripts/manage-accounts.sh validate
```

### 切换账号

切换账号时，管理脚本会：
1. 读取目标账号的 `.env.{账号名}` 文件
2. 更新全局 MCP 配置中的环境变量
3. 提示重启 Claude Code 使配置生效

## 故障排除

### 问题1: 发布失败 - AppID 或 AppSecret 错误

**解决方案**:
1. 检查 `.env.{账号名称}` 文件中的配置是否正确
2. 确认文件名称与账号名称匹配
3. 重启 Claude Code 重新加载配置
4. 在微信公众平台后台验证凭证

### 问题2: 图片上传失败

**解决方案**:
1. 检查图片文件大小（≤ 2MB）
2. 确认图片格式（JPG/PNG）
3. 使用绝对路径而非相对路径
4. 检查文件读取权限

### 问题3: 账号切换无效

**解决方案**:
1. 确认 `.env.{账号名称}` 文件已保存
2. 完全退出并重启 Claude Code
3. 检查文件名称拼写
4. 使用 `manage-accounts.sh validate` 验证配置

## 测试发布

### 测试流程

1. 创建测试文章：
   ```bash
   cat > test-article.md << 'EOF'
   ---
   title: 测试文章
   ---

   这是一篇测试文章。
   EOF
   ```

2. 使用草稿模式发布
3. 在微信公众平台后台查看草稿
4. 确认无误后删除测试文章

## 相关文档
- [微信公众平台开发文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html)
- [wenyan-mcp GitHub仓库](https://github.com/wenyan-md/mcp)
- [项目 MCP 工具指南](../mcp-tools-guide.md)

---
**版本**: v2.0
**最后更新**: {YYYY-MM-DD}
