"""
账号管理服务
负责账号的创建、查询、更新、删除等操作
"""
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.db.database import get_db
from app.models.account import Account
from app.services.account_config_service import account_config_service
from app.core.cache import cache_query, invalidate_cache_pattern
from app.core.config import settings
from app.utils.custom_logger import log


class AccountService:
    """账号管理服务"""

    @staticmethod
    @cache_query(ttl=300, key_prefix="accounts")
    def get_account_list(db: Session) -> List[dict]:
        """获取账号列表（兼容前端字段，包含关联信息）"""
        accounts = db.query(Account).options(
            joinedload(Account.platform),
            joinedload(Account.customer),
            joinedload(Account.writing_style),
            joinedload(Account.publish_config).joinedload(Account.publish_config.property.mapper.class_.theme)
        ).order_by(Account.created_at.desc()).all()

        result = []
        for account in accounts:
            account_dict = {
                "id": account.id,
                "name": account.name,
                "directory_name": account.directory_name,
                "description": account.description,
                # 基础字段
                "customer_id": account.customer_id,
                "platform_id": account.platform_id,
                "owner_id": account.owner_id,
                "created_by": account.created_by,
                "updated_by": account.updated_by,
                # 兼容前端字段
                "platform_name": account.platform.name if account.platform else None,
                "account_id": account.directory_name,
                "status": "active" if account.is_active else "inactive",
                "created_at": account.created_at,
                "updated_at": account.updated_at,
                # 关联信息 - 写作风格
                "writing_style": {
                    "id": account.writing_style.id,
                    "name": account.writing_style.name,
                    "tone": account.writing_style.tone,
                    "min_words": account.writing_style.min_words,
                    "max_words": account.writing_style.max_words,
                    "persona": account.writing_style.persona,
                    "emoji_usage": account.writing_style.emoji_usage
                } if account.writing_style else None,
                # 关联信息 - 发布配置
                "publish_config": {
                    "id": account.publish_config.id,
                    "theme_id": account.publish_config.theme_id,
                    "auto_publish": account.publish_config.auto_publish,
                    "review_mode": account.publish_config.review_mode
                } if account.publish_config else None,
                # 关联信息 - 客户和所有者
                "customer": {
                    "id": account.customer.id,
                    "name": account.customer.name
                } if account.customer else None
            }
            result.append(account_dict)
        return result

    @staticmethod
    @cache_query(ttl=300, key_prefix="account_by_id")
    def get_account_detail(db: Session, account_id: int) -> Optional[Account]:
        """获取账号详情（含所有配置，使用 eager loading）"""
        return db.query(Account).options(
            joinedload(Account.platform),
            joinedload(Account.customer),
            joinedload(Account.writing_style),
            joinedload(Account.publish_config),
            joinedload(Account.configs),
            joinedload(Account.content_sections),
            joinedload(Account.data_sources)
        ).filter(Account.id == account_id).first()

    @staticmethod
    def create_account(db: Session, account_data: dict, current_user_id: int = None) -> Account:
        """创建账号（支持级联创建配置和关联预设风格）"""
        # 提取写作风格配置
        writing_style_id = account_data.pop('writing_style_id', None)
        writing_style_data = account_data.pop('writing_style', None)
        theme_id = account_data.pop('theme_id', None)

        # 参数互斥检查
        if writing_style_id and writing_style_data:
            log.warning(f"同时指定了 writing_style_id 和 writing_style 参数，将忽略 writing_style 并使用预设风格 ID {writing_style_id}")
            writing_style_data = None

        # 字段映射：display_name -> name
        if 'display_name' in account_data:
            account_data['name'] = account_data.pop('display_name')

        # 字段映射：status -> is_active
        if 'status' in account_data:
            is_active = account_data.pop('status') == 'active'
            account_data['is_active'] = is_active

        # 移除 Account 模型中不存在的字段
        account_data.pop('niche', None)

        # 设置创建人（方案 A: 审计追踪）
        if current_user_id:
            account_data['created_by'] = current_user_id
            account_data['updated_by'] = current_user_id

        # 创建账号
        account = Account(**account_data)
        db.add(account)
        db.flush()  # 获取 account.id，但不提交事务

        # 处理写作风格配置（优先级：writing_style_id > writing_style > 默认预设）
        if writing_style_id:
            # 复制预设风格配置创建新风格
            from app.models.account import WritingStyle
            preset_style = db.query(WritingStyle).filter(WritingStyle.id == writing_style_id).first()
            if not preset_style:
                raise ValueError(f"写作风格不存在: ID {writing_style_id}")

            # 复制预设风格的配置创建专属风格
            writing_style = WritingStyle(
                account_id=account.id,
                name=f"{preset_style.name} (副本)",
                code=f"account_{account.id}_style",
                tone=preset_style.tone,
                persona=preset_style.persona,
                min_words=preset_style.min_words,
                max_words=preset_style.max_words,
                emoji_usage=preset_style.emoji_usage,
                forbidden_words=preset_style.forbidden_words,
                is_system=False
            )
            db.add(writing_style)
            log.info(f"账号 {account.id} 复制预设写作风格: {preset_style.name} (ID {writing_style_id})")
        elif writing_style_data:
            # 创建自定义风格
            from app.models.account import WritingStyle
            writing_style_data['account_id'] = account.id
            writing_style_data.setdefault('name', f"账号{account.id}风格")
            writing_style_data.setdefault('code', f"account_{account.id}_style")
            writing_style = WritingStyle(**writing_style_data)
            db.add(writing_style)
            log.info(f"账号 {account.id} 创建自定义写作风格: {writing_style.name}")
        else:
            # 使用默认预设风格（复制）
            default_style_id = settings.DEFAULT_WRITING_STYLE_ID
            from app.models.account import WritingStyle
            preset_style = db.query(WritingStyle).filter(WritingStyle.id == default_style_id).first()
            if preset_style:
                # 复制默认风格配置
                writing_style = WritingStyle(
                    account_id=account.id,
                    name=f"{preset_style.name} (默认)",
                    code=f"account_{account.id}_style",
                    tone=preset_style.tone,
                    persona=preset_style.persona,
                    min_words=preset_style.min_words,
                    max_words=preset_style.max_words,
                    emoji_usage=preset_style.emoji_usage,
                    forbidden_words=preset_style.forbidden_words,
                    is_system=False
                )
                db.add(writing_style)
                log.info(f"账号 {account.id} 使用默认预设写作风格: {preset_style.name} (ID {default_style_id})")
            else:
                log.warning(f"默认写作风格 ID {default_style_id} 不存在，账号 {account.id} 未关联写作风格")

        # 级联创建发布配置
        if theme_id:
            from app.models.account import PublishConfig
            publish_config = PublishConfig(
                account_id=account.id,
                theme_id=theme_id
            )
            db.add(publish_config)

        db.commit()
        db.refresh(account)

        # 失效相关缓存
        invalidate_cache_pattern("account")

        return account

    @staticmethod
    def update_account(db: Session, account_id: int, account_data: dict, current_user_id: int = None) -> Optional[Account]:
        """更新账号（支持切换写作风格）"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None

        # 处理写作风格切换
        writing_style_id = account_data.pop('writing_style_id', None)
        if writing_style_id is not None:
            from app.models.account import WritingStyle

            # 验证新风格是否存在
            preset_style = db.query(WritingStyle).filter(WritingStyle.id == writing_style_id).first()
            if not preset_style:
                raise ValueError(f"写作风格不存在: ID {writing_style_id}")

            # 记录旧风格信息
            old_style_name = account.writing_style.name if account.writing_style else "无"

            # 删除旧的自定义风格
            if account.writing_style and account.writing_style.account_id == account_id:
                log.info(f"删除账号 {account_id} 的旧自定义风格: {account.writing_style.name}")
                db.delete(account.writing_style)

            # 复制新风格的配置创建专属风格
            new_style = WritingStyle(
                account_id=account.id,
                name=f"{preset_style.name} (副本)",
                code=f"account_{account.id}_style",
                tone=preset_style.tone,
                persona=preset_style.persona,
                min_words=preset_style.min_words,
                max_words=preset_style.max_words,
                emoji_usage=preset_style.emoji_usage,
                forbidden_words=preset_style.forbidden_words,
                is_system=False
            )
            db.add(new_style)
            log.info(f"账号 {account_id} 切换写作风格: {old_style_name} -> {preset_style.name} (ID {writing_style_id})")

        # 更新其他字段
        for key, value in account_data.items():
            setattr(account, key, value)

        # 更新修改人（方案 A: 审计追踪）
        if current_user_id:
            account.updated_by = current_user_id

        db.commit()
        db.refresh(account)

        # 失效相关缓存
        invalidate_cache_pattern("account")

        return account

    @staticmethod
    def delete_account(db: Session, account_id: int) -> bool:
        """删除账号"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            db.delete(account)
            db.commit()

            # 失效相关缓存
            invalidate_cache_pattern("account")

            return True
        return False

    @staticmethod
    def import_from_markdown(db: Session, account_id: int) -> dict:
        """从 Markdown 导入配置"""
        # 这里需要实现从 Markdown 导入配置的逻辑
        return {"success": False, "message": "未实现"}

    @staticmethod
    def export_to_markdown(db: Session, account_id: int) -> str:
        """导出配置到 Markdown"""
        return account_config_service.export_to_markdown(db, account_id)

    @staticmethod
    def switch_active_account(db: Session, account_id: int) -> dict:
        """切换活动账号"""
        # 这里需要实现切换活动账号的逻辑
        return {"success": True, "account_id": account_id}

    @staticmethod
    def get_writing_style(db: Session, account_id: int) -> Optional[dict]:
        """获取写作风格配置"""
        style = account_config_service.get_writing_style(db, account_id)
        if style:
            return {
                "id": style.id,
                "tone": style.tone,
                "persona": style.persona,
                "target_audience": None,  # 模型中不存在此字段，返回None
                "min_word_count": style.min_words,
                "max_word_count": style.max_words,
                "custom_instructions": None,  # 模型中不存在此字段，返回None
                "created_at": style.created_at,
                "updated_at": style.updated_at
            }
        return None

    @staticmethod
    def update_writing_style(db: Session, account_id: int, style_data: dict) -> dict:
        """更新写作风格配置"""
        style = account_config_service.update_writing_style(db, account_id, style_data)
        return {
            "id": style.id,
            "tone": style.tone,
            "persona": style.persona,
            "target_audience": None,  # 模型中不存在此字段，返回None
            "min_word_count": style.min_words,
            "max_word_count": style.max_words,
            "custom_instructions": None,  # 模型中不存在此字段，返回None
            "created_at": style.created_at,
            "updated_at": style.updated_at
        }

    @staticmethod
    def get_publish_config(db: Session, account_id: int) -> Optional[dict]:
        """获取发布配置"""
        config = account_config_service.get_publish_config(db, account_id)
        if config:
            return {
                "id": config.id,
                "wechat_app_id": None,  # 模型中不存在此字段，返回None
                "wechat_app_secret": None,  # 模型中不存在此字段，返回None
                "default_theme": None,  # 模型中不存在此字段，返回None
                "highlight_theme": None,  # 模型中不存在此字段，返回None
                "use_mac_style": None,  # 模型中不存在此字段，返回None
                "add_footnote": None,  # 模型中不存在此字段，返回None
                "auto_publish": config.auto_publish,
                "publish_to_draft": config.publish_mode == "draft",  # 转换publish_mode
                "review_mode": config.review_mode,
                "batch_publish_enabled": None,  # 模型中不存在此字段，返回None
                "batch_publish_interval": None,  # 模型中不存在此字段，返回None
                "batch_publish_size": None,  # 模型中不存在此字段，返回None
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
        return None

    @staticmethod
    def update_publish_config(db: Session, account_id: int, config_data: dict) -> dict:
        """更新发布配置"""
        config = account_config_service.update_publish_config(db, account_id, config_data)
        return {
            "id": config.id,
            "wechat_app_id": None,  # 模型中不存在此字段，返回None
            "wechat_app_secret": None,  # 模型中不存在此字段，返回None
            "default_theme": None,  # 模型中不存在此字段，返回None
            "highlight_theme": None,  # 模型中不存在此字段，返回None
            "use_mac_style": None,  # 模型中不存在此字段，返回None
            "add_footnote": None,  # 模型中不存在此字段，返回None
            "auto_publish": config.auto_publish,
            "publish_to_draft": config.publish_mode == "draft",  # 转换publish_mode
            "review_mode": config.review_mode,
            "batch_publish_enabled": None,  # 模型中不存在此字段，返回None
            "batch_publish_interval": None,  # 模型中不存在此字段，返回None
            "batch_publish_size": None,  # 模型中不存在此字段，返回None
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }


# 全局服务实例
account_service = AccountService()
