"""
用户管理服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user import User


class UserService:
    """用户管理服务"""

    @staticmethod
    def get_users(
        db: Session,
        username: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """获取用户列表"""
        query = db.query(User)

        if username:
            query = query.filter(User.username.contains(username))
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_data: dict) -> User:
        """创建用户"""
        from app.core.security import get_password_hash

        user = User(
            username=user_data.get("username"),
            email=user_data.get("email"),
            hashed_password=get_password_hash(user_data.get("password", "123456")),
            role=user_data.get("role", "viewer"),
            is_active=user_data.get("is_active", True)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user: User, user_data: dict) -> User:
        """更新用户"""
        if "email" in user_data:
            user.email = user_data["email"]
        if "role" in user_data:
            user.role = user_data["role"]
        if "is_active" in user_data:
            user.is_active = user_data["is_active"]

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user: User) -> bool:
        """删除用户"""
        db.delete(user)
        db.commit()
        return True


# 全局服务实例
user_service = UserService()
