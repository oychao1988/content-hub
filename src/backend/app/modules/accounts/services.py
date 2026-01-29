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
    def get_account_list(db: Session) -> List[Account]:
        """获取账号列表"""
        return db.query(Account).order_by(Account.created_at.desc()).all()

    @staticmethod
    @cache_query(ttl=300, key_prefix="account_by_id")
    def get_account_detail(db: Session, account_id: int) -> Optional[Account]:
        """获取账号详情（含所有配置）"""
        return db.query(Account).filter(Account.id == account_id).first()

    @staticmethod
    def create_account(db: Session, account_data: dict) -> Account:
        """创建账号"""
        account = Account(**account_data)
        db.add(account)
        db.commit()
        db.refresh(account)

        # 失效相关缓存
        invalidate_cache_pattern("account")

        return account

    @staticmethod
    def update_account(db: Session, account_id: int, account_data: dict) -> Optional[Account]:
        """更新账号"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            for key, value in account_data.items():
                setattr(account, key, value)
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
                "target_audience": style.target_audience,
                "min_word_count": style.min_word_count,
                "max_word_count": style.max_word_count,
                "custom_instructions": style.custom_instructions
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
            "target_audience": style.target_audience,
            "min_word_count": style.min_word_count,
            "max_word_count": style.max_word_count,
            "custom_instructions": style.custom_instructions
        }

    @staticmethod
    def get_publish_config(db: Session, account_id: int) -> Optional[dict]:
        """获取发布配置"""
        config = account_config_service.get_publish_config(db, account_id)
        if config:
            return {
                "id": config.id,
                "wechat_app_id": config.wechat_app_id,
                "wechat_app_secret": config.wechat_app_secret,
                "default_theme": config.default_theme,
                "highlight_theme": config.highlight_theme,
                "use_mac_style": config.use_mac_style,
                "add_footnote": config.add_footnote,
                "auto_publish": config.auto_publish,
                "publish_to_draft": config.publish_to_draft,
                "review_mode": config.review_mode,
                "batch_publish_enabled": config.batch_publish_enabled,
                "batch_publish_interval": config.batch_publish_interval,
                "batch_publish_size": config.batch_publish_size
            }
        return None

    @staticmethod
    def update_publish_config(db: Session, account_id: int, config_data: dict) -> dict:
        """更新发布配置"""
        config = account_config_service.update_publish_config(db, account_id, config_data)
        return {
            "id": config.id,
            "wechat_app_id": config.wechat_app_id,
            "wechat_app_secret": config.wechat_app_secret,
            "default_theme": config.default_theme,
            "highlight_theme": config.highlight_theme,
            "use_mac_style": config.use_mac_style,
            "add_footnote": config.add_footnote,
            "auto_publish": config.auto_publish,
            "publish_to_draft": config.publish_to_draft,
            "review_mode": config.review_mode,
            "batch_publish_enabled": config.batch_publish_enabled,
            "batch_publish_interval": config.batch_publish_interval,
            "batch_publish_size": config.batch_publish_size
        }


# 全局服务实例
account_service = AccountService()
