# Content-Creator 快速参考

> **最后更新**: 2026-02-05
> **版本**: 1.0.0

## 一分钟快速开始

### 最简单的用法

```bash
contenthub content generate \
  --account-id 49 \
  --topic "你想要的文章主题"
```

### 带参数的用法

```bash
contenthub content generate \
  --account-id 49 \
  --topic "人工智能在汽车行业的应用" \
  --category "科技" \
  --tone "科技感" \
  --requirements "写一篇1500字的深度文章，包含3个应用场景"
```

### 查看生成的内容

```bash
# 查看内容详情
contenthub content info <内容ID>

# 查看某个账号的所有内容
contenthub content list --account-id 49
```

## 常用参数说明

| 参数 | 说明 | 示例 | 默认值 |
|------|------|------|--------|
| `--account-id` | 账号ID（必需） | `--account-id 49` | - |
| `--topic` | 文章主题（必需） | `--topic "新能源汽车"` | - |
| `--category` | 内容分类 | `--category "科技"` | "默认" |
| `--tone` | 语气风格 | `--tone "友好专业"` | "友好专业" |
| `--requirements` | 创作要求 | `--requirements "800字"` | 自动生成 |
| `--keywords` | 关键词 | `--keywords "AI,汽车"` | 无 |

## 语气风格建议

| 场景 | 推荐tone | 示例 |
|------|----------|------|
| 科普文章 | "友好专业" | 技术博客、知识分享 |
| 科技新闻 | "科技感" | 行业动态、产品发布 |
| 产品评测 | "客观中立" | 对比评测、购买建议 |
| 教程指南 | "实用详细" | 操作手册、入门教程 |
| 专题分析 | "深度分析" | 行业报告、趋势分析 |

## 创作要求模板

### 按字数
```
"写一篇800字的文章"
"生成一篇1500字的深度分析"
"写一篇5000字的白皮书"
```

### 按结构
```
"包含引言、3个主要章节、结论"
"使用列表和子标题组织内容"
"分段落详细阐述每个要点"
```

### 按内容
```
"包含3个实际应用场景"
"提供具体的操作建议"
"对比分析不同方案的优缺点"
```

### 组合使用
```
"写一篇1500字的文章，包含引言、4个主要章节和结论，
每个章节包含具体案例和数据支持"
```

## 输出说明

### 自动生成的内容

- ✅ **文章正文**: Markdown格式，结构清晰
- ✅ **配图**: 2-3张（本地路径）
- ✅ **质量评分**: 0-10分
- ✅ **元数据**: 字数、分类、标签

### 质量评分参考

| 分数范围 | 质量等级 | 说明 |
|---------|---------|------|
| 8.0-10.0 | 优秀 | 可直接发布 |
| 6.0-7.9 | 良好 | 轻微修改即可 |
| 4.0-5.9 | 一般 | 需要较大修改 |
| 0.0-3.9 | 较差 | 建议重新生成 |

### 图片信息

生成的图片存储在content-creator项目中：
```
/Users/Oychao/Documents/Projects/content-creator/data/images/
```

图片命名格式：`task-{任务ID}_{序号}_{时间戳}.png`

## 性能参考

| 内容类型 | 平均字数 | 图片数 | 平均耗时 |
|---------|---------|--------|----------|
| 快速生成 | 500-800字 | 0-1张 | ~2分钟 |
| 标准生成 | 1000-1500字 | 2-3张 | ~3分钟 |
| 深度文章 | 2000-3000字 | 3-5张 | ~5分钟 |

## 常见问题

### Q1: 生成失败怎么办？

**A**: 检查以下几点：
1. content-creator CLI是否正确配置
2. Claude CLI是否正常工作
3. 网络连接是否正常（搜索需要）
4. 重新尝试或简化要求

### Q2: 如何提高内容质量？

**A**: 尝试以下方法：
1. 明确指定目标受众
2. 提供详细的创作要求
3. 指定具体的语气风格
4. 给出具体的结构要求

### Q3: 生成时间过长？

**A**: 正常情况下：
- 简单内容：2-3分钟
- 复杂内容：3-5分钟
- 如果超过5分钟，可能是网络问题

### Q4: 图片路径不正确？

**A**: 图片存储在content-creator项目，确保：
1. content-creator项目路径正确
2. 有写入权限
3. 磁盘空间充足

### Q5: 如何修改生成的内容？

**A**: 使用update命令：
```bash
contenthub content update <内容ID> --content "新内容"
```

或使用文本编辑器手动修改数据库中的内容。

## 实用技巧

### 1. 批量生成类似内容

```bash
# 创建简单的shell脚本
for topic in "主题1" "主题2" "主题3"; do
  contenthub content generate \
    --account-id 49 \
    --topic "$topic" \
    --category "科技" \
    --tone "科技感"
done
```

### 2. 使用定时任务自动生成

```bash
# 创建定时任务
contenthub scheduler create \
  --name "每日科技新闻" \
  --type content_generation \
  --cron "0 9 * * *" \
  --account-id 49 \
  --topic "今日AI科技新闻" \
  --category "科技"
```

### 3. 生成后直接发布到发布池

```bash
# 1. 生成内容
contenthub content generate \
  --account-id 49 \
  --topic "新文章"

# 2. 添加到发布池
contenthub publish-pool add <内容ID> \
  --priority 5

# 3. 设置发布时间
contenthub publish-pool schedule <内容ID> \
  --time "2026-02-06 22:00:00"
```

## 相关文档

- [Content-Creator集成指南](../references/content-creator-integration.md) - 详细技术文档
- [ContentHub CLI参考](../references/CLI-REFERENCE.md) - 完整命令参考
- [集成完成报告](../development/2026-02-05-content-creator-integration.md) - 实施细节

## 反馈和改进

如有问题或建议，请：
1. 查看完整文档
2. 检查日志文件
3. 联系开发团队
