"""
平台管理服务
负责平台的创建、查询、更新、删除等操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.platform import Platform


class PlatformService:
    """平台管理服务"""

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None) -> tuple[List[Platform], int]:
        """
        获取平台列表

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            search: 搜索关键词（搜索平台名称、代码、类型）

        Returns:
            (平台列表, 总数)
        """
        query = db.query(Platform)

        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Platform.name.like(search_pattern)) |
                (Platform.code.like(search_pattern)) |
                (Platform.type.like(search_pattern))
            )

        # 获取总数
        total = query.count()

        # 分页查询
        platforms = query.order_by(Platform.created_at.desc()).offset(skip).limit(limit).all()

        return platforms, total

    @staticmethod
    def get_by_id(db: Session, platform_id: int) -> Optional[Platform]:
        """
        获取单个平台

        Args:
            db: 数据库会话
            platform_id: 平台ID

        Returns:
            平台对象或None
        """
        return db.query(Platform).filter(Platform.id == platform_id).first()

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Platform]:
        """
        根据代码获取平台

        Args:
            db: 数据库会话
            code: 平台代码

        Returns:
            平台对象或None
        """
        return db.query(Platform).filter(Platform.code == code).first()

    @staticmethod
    def create(db: Session, platform_data: dict) -> Platform:
        """
        创建平台

        Args:
            db: 数据库会话
            platform_data: 平台数据

        Returns:
            创建的平台对象
        """
        platform = Platform(**platform_data)
        db.add(platform)
        db.commit()
        db.refresh(platform)
        return platform

    @staticmethod
    def update(db: Session, platform_id: int, platform_data: dict) -> Optional[Platform]:
        """
        更新平台

        Args:
            db: 数据库会话
            platform_id: 平台ID
            platform_data: 更新的平台数据

        Returns:
            更新后的平台对象或None
        """
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
        if platform:
            for key, value in platform_data.items():
                setattr(platform, key, value)
            db.commit()
            db.refresh(platform)
        return platform

    @staticmethod
    def delete(db: Session, platform_id: int) -> bool:
        """
        删除平台

        Args:
            db: 数据库会话
            platform_id: 平台ID

        Returns:
            是否删除成功
        """
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
        if platform:
            db.delete(platform)
            db.commit()
            return True
        return False


# 全局服务实例
platform_service = PlatformService()
