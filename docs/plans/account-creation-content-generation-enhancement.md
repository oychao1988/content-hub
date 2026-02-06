# ContentHub 账号创建与内容生成增强计划

**创建日期**: 2026-02-06
**状态**: 待实施

---

## 需求概述

1. **在创建账号时就应该指定主题和写作风格**
2. **在生成内容时，内容主题和写作风格也要加入到系统提示词中**

---

## 当前实现问题

### 账号创建
- CLI 创建账号时不支持写作风格和主题参数
- Service 层只创建 Account 对象，不级联创建 WritingStyle 和 PublishConfig
- 需要后续单独调用配置接口

### 内容生成
- ContentCreatorService 未读取账号的写作风格和内容主题配置
- requirements 参数构建简单，未整合账号配置
- CLI 参数未与账号配置结合

---

## 实现方案

### 一、账号创建增强

#### 1.1 Schema 层扩展

**文件**: `app/modules/accounts/schemas.py`

**修改内容**:

```python
class WritingStyleCreate(BaseModel):
    """写作风格创建模型"""
    tone: str = Field("专业", max_length=100, description="语气：专业/轻松/幽默/严肃")
    persona: Optional[str] = Field(None, max_length=200, description="人设")
    min_words: int = Field(800, ge=100, le=10000, description="最小字数")
    max_words: int = Field(1500, ge=100, le=10000, description="最大字数")
    emoji_usage: str = Field("适度", description="表情使用：不使用/适度/频繁")
    forbidden_words: Optional[List[str]] = Field(None, description="禁用词列表")

class AccountCreate(BaseModel):
    # ... 现有字段 ...
    # 新增：
    writing_style: Optional[WritingStyleCreate] = Field(None, description="写作风格配置")
    theme_id: Optional[int] = Field(None, description="内容主题 ID")
```

#### 1.2 Service 层增强

**文件**: `app/modules/accounts/services.py`

**修改 `create_account` 方法（第44-72行）**:

```python
@staticmethod
def create_account(db: Session, account_data: dict, current_user_id: int = None) -> Account:
    """创建账号（支持级联创建配置）"""
    # 提取嵌套配置
    writing_style_data = account_data.pop('writing_style', None)
    theme_id = account_data.pop('theme_id', None)

    # ... 现有字段映射逻辑 ...

    # 创建账号
    account = Account(**account_data)
    db.add(account)
    db.flush()  # 获取 account.id，但不提交事务

    # 级联创建写作风格
    if writing_style_data:
        writing_style_data['account_id'] = account.id
        writing_style_data.setdefault('name', f"账号{account.id}风格")
        writing_style_data.setdefault('code', f"account_{account.id}_style")
        writing_style = WritingStyle(**writing_style_data)
        db.add(writing_style)

    # 级联创建发布配置
    if theme_id:
        publish_config = PublishConfig(
            account_id=account.id,
            theme_id=theme_id
        )
        db.add(publish_config)

    db.commit()
    db.refresh(account)

    invalidate_cache_pattern("account")
    return account
```

#### 1.3 CLI 层增强

**文件**: `cli/modules/accounts.py`

**修改 `create` 命令（第195-261行）**:

```python
@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="账号名称"),
    customer_id: int = typer.Option(..., "--customer-id", "-c", help="客户 ID（必填）"),
    platform_id: int = typer.Option(..., "--platform-id", "-p", help="平台 ID（必填）"),
    owner_id: int = typer.Option(..., "--owner-id", "-o", help="账号所有者 ID（必填）"),
    description: str = typer.Option(None, "--description", "-d", help="账号描述"),
    status: str = typer.Option("active", "--status", "-s", help="账号状态 (active/inactive)"),

    # 新增：写作风格参数
    tone: str = typer.Option(None, "--tone", help="写作语气（专业/轻松/幽默/严肃）"),
    persona: str = typer.Option(None, "--persona", help="人设描述"),
    min_words: int = typer.Option(None, "--min-words", help="最小字数"),
    max_words: int = typer.Option(None, "--max-words", help="最大字数"),

    # 新增：内容主题参数
    theme_id: int = typer.Option(None, "--theme-id", help="内容主题 ID")
):
    """创建账号（支持指定写作风格和内容主题）"""
    # ... 验证逻辑 ...

    # 准备写作风格配置
    writing_style_data = None
    if any([tone, persona, min_words, max_words]):
        writing_style_data = {
            "tone": tone or "专业",
            "persona": persona,
            "min_words": min_words or 800,
            "max_words": max_words or 1500
        }

    # 准备账号数据
    account_data = {
        "name": name,
        "customer_id": customer_id,
        "platform_id": platform_id,
        "owner_id": owner_id,
        "directory_name": f"{platform.code}_{customer.id}_{name}".lower().replace(" ", "_"),
        "description": description,
        "is_active": status.lower() == "active",
        "writing_style": writing_style_data,
        "theme_id": theme_id
    }

    account = account_service.create_account(db, account_data)

    # ... 显示结果 ...
```

---

### 二、内容生成增强

#### 2.1 ContentCreatorService 增强

**文件**: `app/services/content_creator_service.py`

**修改 `create_content` 方法（第215-262行）**:

```python
@staticmethod
def create_content(
    topic: str,
    requirements: Optional[str] = None,
    target_audience: str = "普通读者",
    tone: str = "友好专业",
    account_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Optional[Session] = None  # 新增数据库会话参数
) -> dict:
    """调用 content-creator CLI 生成内容（支持读取账号配置）"""
    if not settings.CREATOR_CLI_PATH:
        raise CreatorCLINotFoundException("CREATOR_CLI_PATH 未配置")

    # 读取账号配置
    account_config = {}
    if account_id and db:
        from app.models.account import Account
        from app.models.theme import ContentTheme

        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            # 读取写作风格配置
            if account.writing_style:
                ws = account.writing_style
                if tone == "友好专业":  # 使用默认值表示未指定
                    tone = ws.tone or tone

                style_prompt = f"\n## 写作风格要求\n"
                style_prompt += f"- 语气：{ws.tone}\n"
                if ws.persona:
                    style_prompt += f"- 人设：{ws.persona}\n"
                style_prompt += f"- 字数：{ws.min_words}-{ws.max_words}字\n"
                if ws.emoji_usage:
                    style_prompt += f"- 表情使用：{ws.emoji_usage}\n"
                if ws.forbidden_words:
                    style_prompt += f"- 禁用词：{', '.join(ws.forbidden_words)}\n"

                account_config['style_prompt'] = style_prompt

            # 读取内容主题配置
            if account.publish_config and account.publish_config.theme_id:
                theme = db.query(ContentTheme).filter(
                    ContentTheme.id == account.publish_config.theme_id
                ).first()

                if theme:
                    theme_prompt = f"\n## 内容主题\n"
                    theme_prompt += f"- 主题：{theme.name}\n"
                    if theme.description:
                        theme_prompt += f"- 描述：{theme.description}\n"
                    if theme.type:
                        theme_prompt += f"- 类型：{theme.type}\n"

                    account_config['theme_prompt'] = theme_prompt

    # 构建默认创作要求
    if not requirements:
        requirements = f"写一篇关于'{topic}'的文章，要求内容详实、结构清晰"

    # 整合账号配置到 requirements
    if account_config:
        enhanced_requirements = requirements
        if 'style_prompt' in account_config:
            enhanced_requirements += account_config['style_prompt']
        if 'theme_prompt' in account_config:
            enhanced_requirements += account_config['theme_prompt']
        requirements = enhanced_requirements

    # 构建命令参数（保持现有逻辑）
    command = [
        settings.CREATOR_CLI_PATH,
        "create",
        "--type", "content-creator",
        "--mode", "sync",
        "--topic", topic,
        "--requirements", requirements,
        "--target-audience", target_audience,
        "--tone", tone,
        "--priority", "normal"
    ]

    log.info(f"Generating content with account config: topic='{topic}', tone='{tone}'")

    # 执行命令并解析输出
    result = ContentCreatorService._run_cli_command(
        command,
        timeout=ContentCreatorService.DEFAULT_TIMEOUT
    )

    return result
```

#### 2.2 CLI 内容生成命令更新

**文件**: `cli/modules/content.py`

**修改 `generate` 命令（第224-366行）**:

```python
@app.command()
def generate(
    account_id: int = typer.Option(..., "--account-id", "-a", help="账号 ID"),
    topic: str = typer.Option(..., "--topic", "-t", help="选题"),
    keywords: str = typer.Option(None, "--keywords", "-k", help="关键词（逗号分隔）"),
    category: str = typer.Option("默认", "--category", "-c", help="内容板块"),
    requirements: str = typer.Option(None, "--requirements", "-r", help="创作要求"),
    tone: str = typer.Option("友好专业", "--tone", help="语气风格")
):
    """生成内容（自动应用账号配置的写作风格和主题）"""
    try:
        with get_session_local()() as db:
            # ... 验证逻辑 ...

            # 显示账号配置
            if account.writing_style:
                print_info(f"写作风格: {account.writing_style.tone}")
            if account.publish_config and account.publish_config.theme_id:
                theme = db.query(ContentTheme).filter(
                    ContentTheme.id == account.publish_config.theme_id
                ).first()
                if theme:
                    print_info(f"内容主题: {theme.name}")

            # 调用生成服务（传递 db 会话）
            result = content_creator_service.create_content(
                topic=topic,
                requirements=requirements,
                target_audience=category if category != "默认" else "普通读者",
                tone=tone,
                account_id=account_id,  # 新增
                db=db  # 新增
            )

            # ... 后续逻辑保持不变 ...
```

#### 2.3 API 内容生成端点更新

**文件**: `app/modules/content/endpoints.py`

**修改 `generate_content` 端点**:

```python
@router.post("/generate")
@require_permission(Permission.CONTENT_CREATE)
async def generate_content(
    request: ContentGenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """生成内容（支持账号配置）"""
    # ... 验证逻辑 ...

    # 调用生成服务（传递 db 会话）
    result = content_creator_service.create_content(
        topic=request.topic,
        requirements=request.requirements,
        target_audience=request.target_audience or "普通读者",
        tone=request.tone or "友好专业",
        account_id=request.account_id,
        db=db  # 传递数据库会话
    )

    # ... 后续逻辑 ...
```

---

## 关键文件清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `app/modules/accounts/schemas.py` | 添加 WritingStyleCreate、扩展 AccountCreate | 高 |
| `app/modules/accounts/services.py` | create_account 支持级联创建配置 | 高 |
| `app/services/content_creator_service.py` | 读取账号配置并构建提示词 | 高 |
| `cli/modules/accounts.py` | 添加写作风格和主题参数 | 中 |
| `cli/modules/content.py` | 传递 db 会话 | 中 |
| `app/modules/content/endpoints.py` | 传递 db 会话 | 中 |

---

## 实现优先级

### 阶段一：基础架构（高优先级）
1. Schema 扩展（1小时）
2. Service 层增强（2小时）

### 阶段二：服务层核心（高优先级）
3. ContentCreatorService 增强（3小时）

### 阶段三：CLI/API 层（中优先级）
4. CLI 账号创建命令（2小时）
5. CLI 内容生成命令（1.5小时）
6. API 内容生成端点（1小时）

### 阶段四：测试验证（中优先级）
7. 单元测试（2小时）
8. 集成测试（2小时）

---

## 向后兼容性

- 所有新参数均为可选（`Optional`）
- CLI 参数优先级高于账号配置
- 不传新参数时行为与原来一致
- 存量账号保持当前行为

---

## 测试验证

### 验证步骤

```bash
# 1. 创建账号（指定配置）
contenthub accounts create \
  --name "测试账号" \
  --customer-id 1 \
  --platform-id 1 \
  --owner-id 1 \
  --tone "轻松" \
  --persona "科技博主" \
  --min-words 1000 \
  --max-words 2000 \
  --theme-id 1

# 2. 验证配置已关联
contenthub accounts info <ID>

# 3. 生成内容（自动应用配置）
contenthub content generate \
  --account-id <ID> \
  --topic "AI技术发展"

# 4. 检查生成的提示词是否包含配置信息
```

### 预期结果

1. 账号创建成功，WritingStyle 和 PublishConfig 同时创建
2. `accounts info` 显示写作风格和内容主题
3. 内容生成时提示词包含：
   - 写作风格要求（语气、人设、字数、表情使用、禁用词）
   - 内容主题（主题名称、描述、类型）

---

## 预计工作量

- **Schema 扩展**: 1小时
- **Service 层增强**: 2小时
- **ContentCreatorService**: 3小时
- **CLI 命令**: 2小时
- **API 端点**: 1小时
- **测试验证**: 4小时

**总计**: 约 **13 小时**（~2 人天）

---

## 相关文件

### 数据模型
- `app/models/account.py` - Account, WritingStyle, PublishConfig
- `app/models/theme.py` - ContentTheme

### 配置服务
- `app/services/account_config_service.py` - 配置管理参考

### 测试文件
- `tests/unit/services/test_content_creator_service.py`
- `tests/e2e/test_content_generation_flow.py`
