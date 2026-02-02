"""
账号管理模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AccountCreate(BaseModel):
    """创建账号请求模型"""
    customer_id: int = Field(..., description="客户 ID")
    platform_id: int = Field(..., description="平台 ID")
    directory_name: str = Field(..., min_length=1, max_length=100, description="目录名称（唯一）")
    display_name: str = Field(..., min_length=1, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=500, description="账号描述")
    niche: Optional[str] = Field(None, max_length=100, description="垂直领域")

    class Config:
        schema_extra = {
            "example": {
                "customer_id": 1,
                "platform_id": 1,
                "directory_name": "tech_blog",
                "display_name": "技术博客",
                "description": "分享技术文章和教程",
                "niche": "technology"
            }
        }


class AccountUpdate(BaseModel):
    """更新账号请求模型"""
    directory_name: Optional[str] = Field(None, min_length=1, max_length=100, description="目录名称（唯一）")
    display_name: Optional[str] = Field(None, min_length=1, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=500, description="账号描述")
    niche: Optional[str] = Field(None, max_length=100, description="垂直领域")

    class Config:
        schema_extra = {
            "example": {
                "display_name": "技术博客（更新）",
                "description": "分享最新技术文章和教程"
            }
        }


class AccountRead(BaseModel):
    """账号响应模型"""
    id: int
    name: str
    directory_name: str
    description: Optional[str] = None
    # 兼容前端字段
    platform_name: Optional[str] = None  # 平台名称
    account_id: Optional[str] = None  # 账号ID（使用directory_name）
    status: Optional[str] = None  # 状态（从is_active转换）
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class WritingStyleUpdate(BaseModel):
    """写作风格更新请求模型"""
    tone: Optional[str] = Field(None, max_length=100, description="语气：专业/轻松/幽默/严肃")
    persona: Optional[str] = Field(None, max_length=200, description="人设：行业专家/科技爱好者/资深编辑")
    target_audience: Optional[str] = Field(None, max_length=200, description="目标受众")
    min_word_count: Optional[int] = Field(None, ge=100, le=10000, description="最小字数")
    max_word_count: Optional[int] = Field(None, ge=100, le=10000, description="最大字数")
    custom_instructions: Optional[str] = Field(None, description="自定义指令")

    class Config:
        schema_extra = {
            "example": {
                "tone": "专业",
                "persona": "技术专家",
                "target_audience": "开发者",
                "min_word_count": 800,
                "max_word_count": 2000,
                "custom_instructions": "文章需要包含代码示例"
            }
        }


class WritingStyleRead(BaseModel):
    """写作风格响应模型"""
    id: int
    tone: Optional[str]
    persona: Optional[str]
    target_audience: Optional[str]
    min_word_count: Optional[int]
    max_word_count: Optional[int]
    custom_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class PublishConfigUpdate(BaseModel):
    """发布配置更新请求模型"""
    wechat_app_id: Optional[str] = Field(None, max_length=100, description="微信公众号 AppID")
    wechat_app_secret: Optional[str] = Field(None, max_length=200, description="微信公众号 AppSecret")
    default_theme: Optional[str] = Field(None, max_length=50, description="默认主题")
    highlight_theme: Optional[str] = Field(None, max_length=50, description="代码高亮主题")
    use_mac_style: Optional[bool] = Field(None, description="是否使用 Mac 风格")
    add_footnote: Optional[bool] = Field(None, description="是否添加脚注")
    auto_publish: Optional[bool] = Field(None, description="是否自动发布")
    publish_to_draft: Optional[bool] = Field(None, description="是否发布到草稿箱")
    review_mode: Optional[str] = Field(None, max_length=20, description="审核模式：auto/manual")
    batch_publish_enabled: Optional[bool] = Field(None, description="是否启用批量发布")
    batch_publish_interval: Optional[int] = Field(None, ge=1, le=60, description="批量发布间隔（分钟）")
    batch_publish_size: Optional[int] = Field(None, ge=1, le=100, description="单次批量发布数量")

    class Config:
        schema_extra = {
            "example": {
                "default_theme": "dark",
                "highlight_theme": "monokai",
                "use_mac_style": True,
                "add_footnote": True,
                "auto_publish": False,
                "publish_to_draft": True,
                "review_mode": "auto",
                "batch_publish_enabled": True,
                "batch_publish_interval": 5,
                "batch_publish_size": 5
            }
        }


class PublishConfigRead(BaseModel):
    """发布配置响应模型"""
    id: int
    wechat_app_id: Optional[str]
    wechat_app_secret: Optional[str]
    default_theme: Optional[str]
    highlight_theme: Optional[str]
    use_mac_style: Optional[bool]
    add_footnote: Optional[bool]
    auto_publish: Optional[bool]
    publish_to_draft: Optional[bool]
    review_mode: Optional[str]
    batch_publish_enabled: Optional[bool]
    batch_publish_interval: Optional[int]
    batch_publish_size: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AccountDetailRead(AccountRead):
    """账号详情响应模型（含配置）"""
    writing_style: Optional[WritingStyleRead]
    publish_config: Optional[PublishConfigRead]

    class Config:
        orm_mode = True
