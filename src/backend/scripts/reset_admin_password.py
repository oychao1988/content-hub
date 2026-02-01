#!/usr/bin/env python3
"""重置admin用户密码"""
from app.db.database import get_db
from app.models.user import User
from app.core.security import get_password_hash

db = next(get_db())
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    # 重置密码为 123456
    admin.password_hash = get_password_hash('123456')
    db.commit()
    print(f'Admin password reset successfully')
    print(f'New password hash: {admin.password_hash[:50]}...')
else:
    print('Admin user not found')
