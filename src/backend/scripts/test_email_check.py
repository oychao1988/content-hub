#!/usr/bin/env python3
"""直接测试邮箱存在性检查的脚本"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models.user import User
from app.modules.shared.services.user_service import get_user_by_email, get_user_by_username, create_user
from app.modules.shared.schemas.user import UserCreate

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

db_session = TestingSessionLocal()

print("=== 直接测试邮箱存在性检查 ===")

# 1. 检查数据库是否为空
all_users = db_session.query(User).all()
print(f"数据库中的用户数量: {len(all_users)}")

# 2. 直接使用 user_service.get_user_by_email 查询
email_to_check = "admin@example.com"
user_by_email = get_user_by_email(db_session, email_to_check)
print(f"通过 get_user_by_email 查询 '{email_to_check}': {'存在' if user_by_email else '不存在'}")

# 3. 直接使用 SQL 查询
direct_sql = db_session.execute(f"SELECT * FROM users WHERE email = '{email_to_check}'")
direct_result = direct_sql.fetchall()
print(f"直接 SQL 查询结果数量: {len(direct_result)}")

# 4. 尝试创建用户
user_data = UserCreate(
    username="adminuser",
    email="admin@example.com",
    password="testpassword123",
    role="admin"
)

print("\n尝试创建用户:")
try:
    new_user = create_user(db_session, user_data)
    print(f"成功创建用户: {new_user.username} ({new_user.email})")

    # 验证用户是否已创建
    all_users = db_session.query(User).all()
    print(f"创建后用户数量: {len(all_users)}")

    # 再次查询
    user_by_email_after = get_user_by_email(db_session, email_to_check)
    print(f"查询创建后的用户: {'存在' if user_by_email_after else '不存在'}")

except Exception as e:
    print(f"创建用户失败: {e}")

db_session.close()
Base.metadata.drop_all(bind=engine)