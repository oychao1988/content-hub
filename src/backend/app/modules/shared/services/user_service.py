from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_salt, get_password_hash, verify_password
from app.models.user import User
from app.modules.shared.schemas.user import UserCreate


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, payload: UserCreate) -> User:
    salt = create_salt()
    password_hash = get_password_hash(payload.password, salt)
    username = payload.username or payload.email
    user = User(
        username=username,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=password_hash,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str, use_email=True) -> Optional[User]:
    print(f"=== authenticate_user 调试信息 ===")
    print(f"标识符: {identifier}")
    print(f"使用邮箱: {use_email}")
    print(f"密码: {password}")

    user: Optional[User] = None
    if use_email:
        user = get_user_by_email(db, identifier)
        print(f"通过邮箱查找用户: {user}")
    if not user:
        user = get_user_by_username(db, identifier)
        print(f"通过用户名查找用户: {user}")
    if not user:
        print("未找到用户")
        return None

    print(f"找到用户: {user.username}")
    print(f"密码哈希: {user.password_hash}")

    from app.core.security import verify_password
    verify_result = verify_password(password, user.password_hash)
    print(f"密码验证结果: {verify_result}")

    if not verify_result:
        return None
    return user


def update_password(db: Session, user: User, new_password: str) -> User:
    salt = create_salt()
    user.password_hash = get_password_hash(new_password, salt)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
