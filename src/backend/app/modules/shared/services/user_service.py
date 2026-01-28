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
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str, use_email=True) -> Optional[User]:
    user: Optional[User] = None
    if use_email:
        user = get_user_by_email(db, identifier)
    if not user:
        user = get_user_by_username(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_password(db: Session, user: User, new_password: str) -> User:
    salt = create_salt()
    user.password_hash = get_password_hash(new_password, salt)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
