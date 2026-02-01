"""
账号配置服务
负责管理账号的各项配置
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.account import (
    Account, AccountConfig, WritingStyle, ContentSection,
    DataSource, PublishConfig
)


class AccountConfigService:
    """账号配置服务"""

    @staticmethod
    def get_account_configs(db: Session, account_id: int) -> List[AccountConfig]:
        """获取账号配置"""
        return db.query(AccountConfig).filter(
            AccountConfig.account_id == account_id
        ).all()

    @staticmethod
    def get_config_by_type(db: Session, account_id: int, config_type: str) -> Optional[AccountConfig]:
        """按类型获取配置"""
        return db.query(AccountConfig).filter(
            AccountConfig.account_id == account_id,
            AccountConfig.config_type == config_type
        ).first()

    @staticmethod
    def create_config(db: Session, account_id: int, config_type: str, config_name: str,
                      config_data: dict, markdown_content: str = None) -> AccountConfig:
        """创建配置"""
        config = AccountConfig(
            account_id=account_id,
            config_type=config_type,
            config_name=config_name,
            config_data=config_data,
            markdown_content=markdown_content
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def update_config(db: Session, config_id: int, config_data: dict,
                      markdown_content: str = None) -> Optional[AccountConfig]:
        """更新配置"""
        config = db.query(AccountConfig).filter(AccountConfig.id == config_id).first()
        if config:
            config.config_data = config_data
            if markdown_content:
                config.markdown_content = markdown_content
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def delete_config(db: Session, config_id: int) -> bool:
        """删除配置"""
        config = db.query(AccountConfig).filter(AccountConfig.id == config_id).first()
        if config:
            db.delete(config)
            db.commit()
            return True
        return False

    @staticmethod
    def get_writing_style(db: Session, account_id: int) -> Optional[WritingStyle]:
        """获取写作风格配置"""
        return db.query(WritingStyle).filter(WritingStyle.account_id == account_id).first()

    @staticmethod
    def update_writing_style(db: Session, account_id: int, style_data: dict) -> WritingStyle:
        """更新写作风格配置"""
        style = db.query(WritingStyle).filter(WritingStyle.account_id == account_id).first()
        if not style:
            # 创建新的写作风格时，自动设置必需字段
            # 如果 style_data 中没有 name 和 code，生成默认值
            if "name" not in style_data:
                style_data = dict(style_data)  # 复制字典避免修改原数据
                style_data["name"] = f"账号{account_id}风格"
            if "code" not in style_data:
                style_data = dict(style_data) if "name" in style_data else dict(style_data)
                style_data["code"] = f"account_{account_id}_style"

            # 映射字段名：API使用min_word_count/max_word_count，模型使用min_words/max_words
            if "min_word_count" in style_data and "min_words" not in style_data:
                style_data["min_words"] = style_data.pop("min_word_count")
            if "max_word_count" in style_data and "max_words" not in style_data:
                style_data["max_words"] = style_data.pop("max_word_count")

            style = WritingStyle(account_id=account_id, **style_data)
            db.add(style)
        else:
            # 更新现有写作风格
            # 映射字段名
            update_data = dict(style_data)
            if "min_word_count" in update_data:
                update_data["min_words"] = update_data.pop("min_word_count")
            if "max_word_count" in update_data:
                update_data["max_words"] = update_data.pop("max_word_count")

            for key, value in update_data.items():
                setattr(style, key, value)
        db.commit()
        db.refresh(style)
        return style

    @staticmethod
    def get_content_sections(db: Session, account_id: int) -> List[ContentSection]:
        """获取内容板块配置"""
        return db.query(ContentSection).filter(ContentSection.account_id == account_id).all()

    @staticmethod
    def create_content_section(db: Session, account_id: int, section_data: dict) -> ContentSection:
        """创建内容板块配置"""
        section = ContentSection(account_id=account_id, **section_data)
        db.add(section)
        db.commit()
        db.refresh(section)
        return section

    @staticmethod
    def update_content_section(db: Session, section_id: int, section_data: dict) -> Optional[ContentSection]:
        """更新内容板块配置"""
        section = db.query(ContentSection).filter(ContentSection.id == section_id).first()
        if section:
            for key, value in section_data.items():
                setattr(section, key, value)
            db.commit()
            db.refresh(section)
        return section

    @staticmethod
    def delete_content_section(db: Session, section_id: int) -> bool:
        """删除内容板块配置"""
        section = db.query(ContentSection).filter(ContentSection.id == section_id).first()
        if section:
            db.delete(section)
            db.commit()
            return True
        return False

    @staticmethod
    def get_data_sources(db: Session, account_id: int) -> List[DataSource]:
        """获取数据源配置"""
        return db.query(DataSource).filter(DataSource.account_id == account_id).all()

    @staticmethod
    def create_data_source(db: Session, account_id: int, source_data: dict) -> DataSource:
        """创建数据源配置"""
        source = DataSource(account_id=account_id, **source_data)
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @staticmethod
    def get_publish_config(db: Session, account_id: int) -> Optional[PublishConfig]:
        """获取发布配置"""
        return db.query(PublishConfig).filter(PublishConfig.account_id == account_id).first()

    @staticmethod
    def update_publish_config(db: Session, account_id: int, config_data: dict) -> PublishConfig:
        """更新发布配置"""
        config = db.query(PublishConfig).filter(PublishConfig.account_id == account_id).first()
        if not config:
            config = PublishConfig(account_id=account_id, **config_data)
            db.add(config)
        else:
            for key, value in config_data.items():
                setattr(config, key, value)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def import_from_markdown(db: Session, account_id: int, markdown_path: str) -> dict:
        """从 Markdown 导入配置"""
        try:
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()
            # 解析 Markdown 配置的逻辑
            # 这里只是占位实现，实际项目中需要根据 Markdown 格式进行解析
            config_data = {"content": content}
            config = AccountConfig(
                account_id=account_id,
                config_type="markdown_import",
                config_name="markdown_config",
                config_data=config_data,
                markdown_content=content
            )
            db.add(config)
            db.commit()
            return {"success": True, "imported": 1}
        except Exception as e:
            raise Exception(f"导入失败: {str(e)}")

    @staticmethod
    def export_to_markdown(db: Session, account_id: int) -> str:
        """导出配置到 Markdown"""
        configs = db.query(AccountConfig).filter(AccountConfig.account_id == account_id).all()
        content = "# 账号配置\n\n"
        for config in configs:
            content += f"## {config.config_name}\n"
            content += config.markdown_content + "\n\n"
        return content


# 全局服务实例
account_config_service = AccountConfigService()
