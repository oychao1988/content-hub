"""
账号管理服务
负责账号的创建、查询、更新、删除等操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.account import Account
from app.services.account_config_service import account_config_service
from app.core.cache import cache_query, invalidate_cache_pattern


class AccountService:
    """账号管理服务"""

    @staticmethod
    @cache_query(ttl=300, key_prefix="accounts")
    def get_account_list(db: Session) -> List[dict]:
        """获取账号列表（兼容前端字段）"""
        accounts = db.query(Account).order_by(Account.created_at.desc()).all()
        result = []
        for account in accounts:
            account_dict = {
                "id": account.id,
                "name": account.name,
                "directory_name": account.directory_name,
                "description": account.description,
                # 兼容前端字段
                "platform_name": account.platform.name if account.platform else None,
                "account_id": account.directory_name,
                "status": "active" if account.is_active else "inactive",
                "created_at": account.created_at,
                "updated_at": account.updated_at
            }
            result.append(account_dict)
        return result

    @staticmethod
    @cache_query(ttl=300, key_prefix="account_by_id")
    def get_account_detail(db: Session, account_id: int) -> Optional[Account]:
        """获取账号详情（含所有配置）"""
        return db.query(Account).filter(Account.id == account_id).first()

    @staticmethod
    def create_account(db: Session, account_data: dict, current_user_id: int = None) -> Account:
        """创建账号"""
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

        account = Account(**account_data)
        db.add(account)
        db.commit()
        db.refresh(account)

        # 失效相关缓存
        invalidate_cache_pattern("account")

        return account

    @staticmethod
    def update_account(db: Session, account_id: int, account_data: dict, current_user_id: int = None) -> Optional[Account]:
        """更新账号"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
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
