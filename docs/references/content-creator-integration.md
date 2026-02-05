# Content-Creator CLI 集成指南

> **版本**: 1.0.0
> **创建日期**: 2026-02-05
> **状态**: ✅ 已实施
> **实施时间**: 2026-02-05

## 概述

ContentHub通过调用content-creator CLI实现AI驱动的内容生成功能。本文档详细说明集成方案、配置方法和技术细节。

## 架构设计

### 系统架构

```
ContentHub (Python)
    ↓
ContentCreatorService
    ↓
content-creator-cli.sh (包装脚本)
    ↓
content-creator (TypeScript/Node.js)
    ↓
Claude CLI / DeepSeek API
```

### 核心组件

1. **ContentCreatorService** (`app/services/content_creator_service.py`)
   - 负责调用content-creator CLI
   - 处理参数转换和结果解析
   - 错误处理和重试机制

2. **CLI包装脚本** (`content-creator-cli.sh`)
   - 环境变量转换（LOG_LEVEL大小写兼容）
   - 工作目录切换
   - 调用pnpm执行CLI

3. **Content-Creator CLI**
   - LangGraph工作流引擎
   - 支持多种LLM后端
   - 内容生成和图片生成

## 配置说明

### 环境变量配置

**ContentHub (.env)**

```bash
# Content-Creator CLI 配置
CREATOR_CLI_PATH=./content-creator-cli.sh
CREATOR_WORK_DIR=./data/creator-work

# 日志级别
LOG_LEVEL=ERROR  # 大写，会被包装脚本转换为小写
```

**Content-Creator (.env)**

```bash
# LLM 服务类型
LLM_SERVICE_TYPE=cli  # 使用Claude CLI（推荐）
# LLM_SERVICE_TYPE=api  # 使用DeepSeek API

# Claude CLI 配置
CLAUDE_CLI_ENABLED=true
CLAUDE_CLI_DEFAULT_MODEL=sonnet
CLAUDE_CLI_DEFAULT_TIMEOUT=180000

# DeepSeek API 配置（当使用api模式时）
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://xiaoai.plus/v1
LLM_MODEL_NAME=deepseek-chat

# 数据库
DATABASE_TYPE=sqlite

# 日志
LOG_LEVEL=debug  # 小写
```

### CLI包装脚本

**位置**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/content-creator-cli.sh`

```bash
#!/bin/bash
# Content-Creator CLI 包装脚本

cd /Users/Oychao/Documents/Projects/content-creator

# 设置兼容的环境变量（转换为大写->小写）
case "${LOG_LEVEL:-ERROR}" in
  ERROR|error) export LOG_LEVEL_CREATOR=error ;;
  WARN|warn) export LOG_LEVEL_CREATOR=warn ;;
  INFO|info) export LOG_LEVEL_CREATOR=info ;;
  DEBUG|debug) export LOG_LEVEL_CREATOR=debug ;;
  *) export LOG_LEVEL_CREATOR=info ;;
esac

export NODE_ENV=${NODE_ENV:-development}
export LOG_LEVEL=$LOG_LEVEL_CREATOR

# 执行 pnpm run cli，并将所有参数传递
exec pnpm run cli "$@"
```

## 工作流类型

### Content-Creator (标准工作流) ✅ 推荐

**特点**：
- 明确的步骤控制
- 不会陷入无限循环
- 完整的质检流程

**工作流程**：
1. 搜索阶段（可选）
2. 内容写作
3. 文本质检（可重试）
4. 图片生成
5. 图片质检（可重试）
6. 后处理（占位符替换）

**调用参数**：
```bash
create \
  --type content-creator \
  --mode sync \
  --topic "主题" \
  --requirements "创作要求" \
  --target-audience "目标受众" \
  --tone "语气风格" \
  --priority normal
```

### Content-Creator-Agent (Agent工作流) ⚠️ 不推荐

**问题**：
- 容易陷入无限搜索循环
- 达到25步递归限制后失败
- 缺少明确的停止条件

**现状**：暂不使用，等待上游修复

## API接口说明

### ContentCreatorService.create_content()

**方法签名**：
```python
@staticmethod
def create_content(
    topic: str,
    requirements: Optional[str] = None,
    target_audience: str = "普通读者",
    tone: str = "友好专业",
    account_id: Optional[int] = None,
    category: Optional[str] = None
) -> dict
```

**参数说明**：
- `topic`: 文章主题（必需）
- `requirements`: 创作要求（可选，如字数、结构等）
- `target_audience`: 目标受众（默认"普通读者"）
- `tone`: 语气风格（默认"友好专业"）
- `account_id`: 已废弃，保留兼容性
- `category`: 已废弃，保留兼容性

**返回值**：
```python
{
    "success": True,
    "task_id": "task-1770304545665",
    "status": "已完成",
    "duration": 203,  # 秒
    "content": "# 文章标题\n\n文章内容...",
    "images": [
        "data/images/task-1770304545665_0_1770304667229.png",
        "data/images/task-1770304545665_1_1770304668425.png",
        "data/images/task-1770304545665_2_1770304669543.png"
    ],
    "quality_score": 8.3,  # 0-10分
    "quality_passed": True
}
```

**异常处理**：
- `CreatorCLINotFoundException`: CLI路径未配置或不存在
- `CreatorTimeoutException`: 执行超时（默认300秒）
- `CreatorInvalidResponseException`: 无法解析CLI输出
- `CreatorException`: 其他错误

## CLI使用示例

### 基本用法

```bash
contenthub content generate \
  --account-id 49 \
  --topic "新能源汽车选购指南"
```

### 高级用法

```bash
contenthub content generate \
  --account-id 49 \
  --topic "人工智能在汽车行业的应用" \
  --category "科技" \
  --tone "科技感" \
  --requirements "写一篇1500字的深度文章，包含3个应用场景"
```

### 查看生成内容

```bash
# 查看内容详情
contenthub content info 7

# 列出所有内容
contenthub content list --account-id 49
```

## 输出解析

Content-Creator CLI输出纯文本（非JSON），需要通过正则表达式提取关键信息：

### 提取规则

```python
# 任务ID
task_id_match = re.search(r'任务ID:\s*(\S+)', stdout)

# 状态
status_match = re.search(r'状态:\s*(\S+)', stdout)

# 耗时（3分23秒 或 23秒）
duration_match = re.search(r'耗时:\s*((\d+)分)?(\d+)秒', stdout)

# 生成的内容（在分隔符之间）
content_match = re.search(
    r'📝 生成的内容:.*?─────────────\n(.*?)\n─────────────',
    stdout,
    re.DOTALL
)

# 图片路径
image_paths = re.findall(r'(data/images/[^\s]+)', images_text)

# 质量评分
quality_match = re.search(
    r'🔍 文本质检:.*?状态:\s*(\S+).*?评分:\s*([\d.]+)',
    stdout,
    re.DOTALL
)
```

## 性能指标

### 典型执行时间

| 内容类型 | 字数 | 图片数 | 平均耗时 |
|---------|-----|--------|----------|
| 汽车科普 | 1500字 | 3张 | ~3分30秒 |
| 科技文章 | 1000字 | 2张 | ~3分20秒 |
| 快速生成 | 800字 | 0张 | ~2分30秒 |

### 资源消耗

- **内存**: Claude CLI约200-400MB
- **CPU**: 中等（Claude CLI进行推理）
- **网络**: 低（仅在搜索时使用）

## 故障排查

### 常见问题

**1. CLI路径未找到**

```
错误: Creator CLI not found at: ./content-creator-cli.sh
解决: 检查.env中CREATOR_CLI_PATH配置，确保路径正确
```

**2. 执行超时**

```
错误: Creator CLI timeout after 300s
解决: 增加DEFAULT_TIMEOUT或减少内容要求（字数）
```

**3. 无法解析输出**

```
错误: 无法从CLI输出中提取内容
解决: 检查content-creator CLI是否正常运行，查看日志
```

**4. Agent模式无限循环**

```
错误: Recursion limit of 25 reached
解决: 使用--type content-creator而不是content-creator-agent
```

### 调试技巧

1. **启用debug日志**：
   ```bash
   LOG_LEVEL=debug contenthub content generate --topic "测试"
   ```

2. **直接测试CLI**：
   ```bash
   ./content-creator-cli.sh create --type content-creator --topic "测试"
   ```

3. **查看日志文件**：
   - ContentHub: `logs/app.log`
   - Content-Creator: `/path/to/content-creator/logs/app.log`

## 技术决策记录

### 为什么使用CLI包装脚本？

**问题**：ContentHub使用大写LOG_LEVEL，content-creator使用小写log_level

**解决方案**：
1. 创建包装脚本转换环境变量
2. 自动切换到content-creator工作目录
3. 避免修改content-creator代码

**优点**：
- 解耦两个系统
- 维护简单
- 版本升级兼容

### 为什么使用CLI模式而非API模式？

**对比**：

| 特性 | CLI模式 | API模式 |
|------|---------|---------|
| Token统计 | ❌ 不准确 | ✅ 准确 |
| 成本控制 | ⚠️ 估算 | ✅ 精确 |
| 配置复杂度 | ✅ 简单 | ⚠️ 需要API密钥 |
| 本地执行 | ✅ 完全本地 | ⚠️ 依赖外部服务 |
| 质量 | ✅ Claude Sonnet | ⚠️ DeepSeek |

**决策**：使用Claude CLI（质量优先）

### 为什么废弃account_id和category参数？

**原因**：
- Content-Creator不需要这些参数
- 造成参数冗余
- 与账号管理耦合过紧

**处理**：
- 保留参数签名（向后兼容）
- 内部不再使用
- 记录为"已废弃"

## 未来改进方向

1. **支持异步模式**：
   - 当前仅支持sync模式
   - 可添加async模式支持后台生成

2. **批量生成优化**：
   - 当前batch-generate逐个执行
   - 可改为并发执行

3. **进度回调**：
   - 长时间生成时显示进度
   - 实时反馈当前步骤

4. **内容模板系统**：
   - 预定义常用模板
   - 减少参数输入

5. **重新生成功能**：
   - 基于已有内容修订
   - 改进不满意的部分

## 相关文档

- [Content-Creator README](https://github.com/your-org/content-creator)
- [ContentHub CLI使用指南](../guides/cli-usage.md)
- [ContentHub架构设计](../architecture/system-design.md)

## 更新日志

### v1.0.0 (2026-02-05)

- ✅ 初始版本
- ✅ 支持content-creator工作流
- ✅ CLI包装脚本
- ✅ 环境变量转换
- ✅ 输出解析
- ✅ 错误处理和重试
- ✅ CLI命令集成
