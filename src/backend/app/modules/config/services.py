"""
系统配置模块服务
负责写作风格和内容主题的 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.account import WritingStyle
from app.models.theme import ContentTheme
from app.core.cache import cache_config, invalidate_cache_pattern


class WritingStyleService:
    """写作风格管理服务"""

    @staticmethod
    @cache_config(ttl=3600, key_prefix="writing_styles")
    def get_writing_styles(db: Session, skip: int = 0, limit: int = 100) -> List[WritingStyle]:
        """获取写作风格列表"""
        return db.query(WritingStyle).order_by(WritingStyle.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    @cache_config(ttl=3600, key_prefix="writing_style_by_id")
    def get_writing_style_by_id(db: Session, style_id: int) -> Optional[WritingStyle]:
        """根据 ID 获取写作风格"""
        return db.query(WritingStyle).filter(WritingStyle.id == style_id).first()

    @staticmethod
    @cache_config(ttl=3600, key_prefix="writing_style_by_code")
    def get_writing_style_by_code(db: Session, code: str) -> Optional[WritingStyle]:
        """根据代码获取写作风格"""
        return db.query(WritingStyle).filter(WritingStyle.code == code).first()

    @staticmethod
    def create_writing_style(db: Session, style_data: dict) -> WritingStyle:
        """创建写作风格"""
        # 检查代码是否已存在
        existing = WritingStyleService.get_writing_style_by_code(db, style_data.get("code"))
        if existing:
            raise ValueError(f"写作风格代码 '{style_data.get('code')}' 已存在")

        writing_style = WritingStyle(**style_data)
        db.add(writing_style)
        db.commit()
        db.refresh(writing_style)

        # 失效相关缓存
        invalidate_cache_pattern("writing_style")
        invalidate_cache_pattern("writing_styles")

        return writing_style

    @staticmethod
    def update_writing_style(db: Session, style_id: int, style_data: dict) -> Optional[WritingStyle]:
        """更新写作风格"""
        writing_style = WritingStyleService.get_writing_style_by_id(db, style_id)
        if not writing_style:
            return None

        # 如果要更新代码，检查新代码是否已存在
        if "code" in style_data and style_data["code"] != writing_style.code:
            existing = WritingStyleService.get_writing_style_by_code(db, style_data["code"])
            if existing:
                raise ValueError(f"写作风格代码 '{style_data['code']}' 已存在")

        for key, value in style_data.items():
            setattr(writing_style, key, value)

        db.commit()
        db.refresh(writing_style)

        # 失效相关缓存
        invalidate_cache_pattern("writing_style")
        invalidate_cache_pattern("writing_styles")

        return writing_style

    @staticmethod
    def delete_writing_style(db: Session, style_id: int) -> bool:
        """删除写作风格"""
        writing_style = WritingStyleService.get_writing_style_by_id(db, style_id)
        if not writing_style:
            return False

        # 系统级风格不允许删除
        if writing_style.is_system:
            raise ValueError("系统级写作风格不允许删除")

        db.delete(writing_style)
        db.commit()

        # 失效相关缓存
        invalidate_cache_pattern("writing_style")
        invalidate_cache_pattern("writing_styles")

        return True

    @staticmethod
    def get_system_writing_styles(db: Session) -> List[WritingStyle]:
        """获取系统级写作风格列表"""
        return db.query(WritingStyle).filter(WritingStyle.is_system == True).all()

    @staticmethod
    def get_custom_writing_styles(db: Session) -> List[WritingStyle]:
        """获取自定义写作风格列表"""
        return db.query(WritingStyle).filter(WritingStyle.is_system == False).all()


class ContentThemeService:
    """内容主题管理服务"""

    @staticmethod
    @cache_config(ttl=3600, key_prefix="content_themes")
    def get_content_themes(db: Session, skip: int = 0, limit: int = 100) -> List[ContentTheme]:
        """获取内容主题列表"""
        return db.query(ContentTheme).order_by(ContentTheme.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    @cache_config(ttl=3600, key_prefix="content_theme_by_id")
    def get_content_theme_by_id(db: Session, theme_id: int) -> Optional[ContentTheme]:
        """根据 ID 获取内容主题"""
        return db.query(ContentTheme).filter(ContentTheme.id == theme_id).first()

    @staticmethod
    @cache_config(ttl=3600, key_prefix="content_theme_by_code")
    def get_content_theme_by_code(db: Session, code: str) -> Optional[ContentTheme]:
        """根据代码获取内容主题"""
        return db.query(ContentTheme).filter(ContentTheme.code == code).first()

    @staticmethod
    def create_content_theme(db: Session, theme_data: dict) -> ContentTheme:
        """创建内容主题"""
        # 检查代码是否已存在
        existing = ContentThemeService.get_content_theme_by_code(db, theme_data.get("code"))
        if existing:
            raise ValueError(f"内容主题代码 '{theme_data.get('code')}' 已存在")

        content_theme = ContentTheme(**theme_data)
        db.add(content_theme)
        db.commit()
        db.refresh(content_theme)

        # 失效相关缓存
        invalidate_cache_pattern("content_theme")
        invalidate_cache_pattern("content_themes")

        return content_theme

    @staticmethod
    def update_content_theme(db: Session, theme_id: int, theme_data: dict) -> Optional[ContentTheme]:
        """更新内容主题"""
        content_theme = ContentThemeService.get_content_theme_by_id(db, theme_id)
        if not content_theme:
            return None

        # 如果要更新代码，检查新代码是否已存在
        if "code" in theme_data and theme_data["code"] != content_theme.code:
            existing = ContentThemeService.get_content_theme_by_code(db, theme_data["code"])
            if existing:
                raise ValueError(f"内容主题代码 '{theme_data['code']}' 已存在")

        for key, value in theme_data.items():
            setattr(content_theme, key, value)

        db.commit()
        db.refresh(content_theme)

        # 失效相关缓存
        invalidate_cache_pattern("content_theme")
        invalidate_cache_pattern("content_themes")

        return content_theme

    @staticmethod
    def delete_content_theme(db: Session, theme_id: int) -> bool:
        """删除内容主题"""
        content_theme = ContentThemeService.get_content_theme_by_id(db, theme_id)
        if not content_theme:
            return False

        # 系统级主题不允许删除
        if content_theme.is_system:
            raise ValueError("系统级内容主题不允许删除")

        db.delete(content_theme)
        db.commit()

        # 失效相关缓存
        invalidate_cache_pattern("content_theme")
        invalidate_cache_pattern("content_themes")

        return True

    @staticmethod
    def get_system_content_themes(db: Session) -> List[ContentTheme]:
        """获取系统级内容主题列表"""
        return db.query(ContentTheme).filter(ContentTheme.is_system == True).all()

    @staticmethod
    def get_custom_content_themes(db: Session) -> List[ContentTheme]:
        """获取自定义内容主题列表"""
        return db.query(ContentTheme).filter(ContentTheme.is_system == False).all()


# 全局服务实例
writing_style_service = WritingStyleService()
content_theme_service = ContentThemeService()
