"""
初始化测试用户脚本
创建不同角色的测试用户用于权限系统测试

运行方式:
  python init_test_users.py

测试用户:
  - admin@example.com / admin123 (管理员)
  - operator@example.com / operator123 (运营人员)
  - customer@example.com / customer123 (客户)
"""
import sys
import os

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import create_salt, get_password_hash


def create_test_users():
    """创建测试用户"""
    db: Session = next(get_db())

    try:
        # 检查用户是否已存在
        from app.models.user import User

        existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_admin:
            print("测试用户已存在，跳过创建")
            return

        # 创建管理员用户
        salt = create_salt()
        admin_password_hash = get_password_hash("admin123", salt)
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=admin_password_hash,
            full_name="系统管理员",
            role="admin",
            is_active=True
        )
        db.add(admin)

        # 创建运营人员用户
        salt = create_salt()
        operator_password_hash = get_password_hash("operator123", salt)
        operator = User(
            username="operator",
            email="operator@example.com",
            password_hash=operator_password_hash,
            full_name="运营人员",
            role="operator",
            is_active=True
        )
        db.add(operator)

        # 创建客户用户
        salt = create_salt()
        customer_password_hash = get_password_hash("customer123", salt)
        customer = User(
            username="customer",
            email="customer@example.com",
            password_hash=customer_password_hash,
            full_name="客户用户",
            role="customer",
            is_active=True
        )
        db.add(customer)

        db.commit()
        print("=" * 60)
        print("测试用户创建成功！")
        print("=" * 60)
        print("\n管理员账户:")
        print("  邮箱: admin@example.com")
        print("  密码: admin123")
        print("  权限: 全部权限")
        print("\n运营人员账户:")
        print("  邮箱: operator@example.com")
        print("  密码: operator123")
        print("  权限: 内容管理、发布管理、定时任务")
        print("\n客户账户:")
        print("  邮箱: customer@example.com")
        print("  密码: customer123")
        print("  权限: 只读权限")
        print("=" * 60)

    except Exception as e:
        print(f"创建测试用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
