"""
性能测试数据准备脚本

为性能测试准备足够的测试数据，包括：
- 测试用户
- 测试账号
- 测试内容
- 测试平台
- 测试配置

使用方法：
python init_performance_test_data.py [--count 100]
"""

import sys
import argparse
from sqlalchemy.orm import Session
from faker import Faker

from app.db.database import get_db
from app.core.security import create_password_hash
from app.models.user import User
from app.models.customer import Customer
from app.models.platform import Platform
from app.models.account import Account
from app.models.content import Content
from app.models.config import WritingStyle, ContentTheme

fake = Faker('zh_CN')


def create_test_users(db: Session, count: int = 10):
    """创建测试用户"""
    print(f"创建 {count} 个测试用户...")

    users = []
    # 创建管理员
    admin = User(
        username="admin",
        email="admin@test.com",
        password_hash=create_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    users.append(admin)

    # 创建操作员
    for i in range(3):
        operator = User(
            username=f"operator{i+1}",
            email=f"operator{i+1}@test.com",
            password_hash=create_password_hash("operator123"),
            role="operator",
            is_active=True
        )
        users.append(operator)

    # 创建客户
    for i in range(count - 4):
        customer = User(
            username=f"customer{i+1}",
            email=f"customer{i+1}@test.com",
            password_hash=create_password_hash("customer123"),
            role="customer",
            is_active=True
        )
        users.append(customer)

    try:
        db.add_all(users)
        db.commit()
        print(f"✓ 创建了 {len(users)} 个用户")
        return users
    except Exception as e:
        db.rollback()
        print(f"✗ 创建用户失败: {e}")
        return []


def create_test_customers(db: Session, count: int = 10):
    """创建测试客户"""
    print(f"创建 {count} 个测试客户...")

    customers = []
    for i in range(count):
        customer = Customer(
            name=fake.company(),
            contact_name=fake.name(),
            contact_email=fake.email(),
            contact_phone=fake.phone_number(),
            status="active"
        )
        customers.append(customer)

    try:
        db.add_all(customers)
        db.commit()
        print(f"✓ 创建了 {len(customers)} 个客户")
        return customers
    except Exception as e:
        db.rollback()
        print(f"✗ 创建客户失败: {e}")
        return []


def create_test_platforms(db: Session):
    """创建测试平台"""
    print("创建测试平台...")

    platforms = [
        Platform(name="微信公众号", code="wechat_mp", status="active", description="微信公众号平台"),
        Platform(name="今日头条", code="toutiao", status="active", description="今日头条平台"),
        Platform(name="知乎", code="zhihu", status="active", description="知乎平台"),
        Platform(name="小红书", code="xiaohongshu", status="active", description="小红书平台"),
        Platform(name="抖音", code="douyin", status="active", description="抖音平台"),
    ]

    try:
        # 检查是否已存在
        existing = db.query(Platform).count()
        if existing > 0:
            print(f"✓ 平台已存在 ({existing} 个)")
            return db.query(Platform).all()

        db.add_all(platforms)
        db.commit()
        print(f"✓ 创建了 {len(platforms)} 个平台")
        return platforms
    except Exception as e:
        db.rollback()
        print(f"✗ 创建平台失败: {e}")
        return []


def create_test_accounts(db: Session, count: int = 50):
    """创建测试账号"""
    print(f"创建 {count} 个测试账号...")

    customers = db.query(Customer).all()
    platforms = db.query(Platform).all()

    if not customers or not platforms:
        print("✗ 需要先创建客户和平台")
        return []

    accounts = []
    for i in range(count):
        customer = fake.random_element(customers)
        platform = fake.random_element(platforms)

        account = Account(
            name=fake.user_name(),
            platform_id=platform.id,
            customer_id=customer.id,
            account_id=fake.uuid4(),
            status="active",
            credentials={"test": "data"}
        )
        accounts.append(account)

    try:
        db.add_all(accounts)
        db.commit()
        print(f"✓ 创建了 {len(accounts)} 个账号")
        return accounts
    except Exception as e:
        db.rollback()
        print(f"✗ 创建账号失败: {e}")
        return []


def create_test_writing_styles(db: Session):
    """创建测试写作风格"""
    print("创建测试写作风格...")

    styles = [
        WritingStyle(name="正式商务", description="正式商务风格", is_active=True),
        WritingStyle(name="轻松活泼", description="轻松活泼风格", is_active=True),
        WritingStyle(name="专业严谨", description="专业严谨风格", is_active=True),
        WritingStyle(name="亲切友好", description="亲切友好风格", is_active=True),
    ]

    try:
        # 检查是否已存在
        existing = db.query(WritingStyle).count()
        if existing > 0:
            print(f"✓ 写作风格已存在 ({existing} 个)")
            return db.query(WritingStyle).all()

        db.add_all(styles)
        db.commit()
        print(f"✓ 创建了 {len(styles)} 个写作风格")
        return styles
    except Exception as e:
        db.rollback()
        print(f"✗ 创建写作风格失败: {e}")
        return []


def create_test_content_themes(db: Session):
    """创建测试内容主题"""
    print("创建测试内容主题...")

    themes = [
        ContentTheme(name="科技前沿", description="科技前沿话题", is_active=True),
        ContentTheme(name="商业管理", description="商业管理话题", is_active=True),
        ContentTheme(name="生活方式", description="生活方式话题", is_active=True),
        ContentTheme(name="健康养生", description="健康养生话题", is_active=True),
        ContentTheme(name="教育培训", description="教育培训话题", is_active=True),
    ]

    try:
        # 检查是否已存在
        existing = db.query(ContentTheme).count()
        if existing > 0:
            print(f"✓ 内容主题已存在 ({existing} 个)")
            return db.query(ContentTheme).all()

        db.add_all(themes)
        db.commit()
        print(f"✓ 创建了 {len(themes)} 个内容主题")
        return themes
    except Exception as e:
        db.rollback()
        print(f"✗ 创建内容主题失败: {e}")
        return []


def create_test_contents(db: Session, count: int = 200):
    """创建测试内容"""
    print(f"创建 {count} 个测试内容...")

    accounts = db.query(Account).all()
    platforms = db.query(Platform).all()

    if not accounts or not platforms:
        print("✗ 需要先创建账号和平台")
        return []

    statuses = ["draft", "pending", "approved", "published", "rejected"]
    contents = []

    for i in range(count):
        account = fake.random_element(accounts)
        platform = fake.random_element(platforms)

        content = Content(
            title=fake.sentence(nb_words=8),
            content=fake.paragraph(nb_sentences=10),
            status=fake.random_element(statuses),
            account_id=account.id,
            platform_id=platform.id,
            word_count=fake.random_int(min=500, max=3000),
        )
        contents.append(content)

    try:
        db.add_all(contents)
        db.commit()
        print(f"✓ 创建了 {len(contents)} 个内容")
        return contents
    except Exception as e:
        db.rollback()
        print(f"✗ 创建内容失败: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="创建性能测试数据")
    parser.add_argument("--count", type=int, default=100, help="数据数量（默认 100）")
    parser.add_argument("--users", type=int, default=10, help="用户数量（默认 10）")
    parser.add_argument("--customers", type=int, default=10, help="客户数量（默认 10）")
    parser.add_argument("--accounts", type=int, default=50, help="账号数量（默认 50）")
    parser.add_argument("--contents", type=int, default=200, help="内容数量（默认 200）")
    args = parser.parse_args()

    db = next(get_db())

    try:
        print("=" * 50)
        print("开始创建性能测试数据")
        print("=" * 50)
        print()

        # 创建基础数据
        create_test_users(db, args.users)
        create_test_customers(db, args.customers)
        create_test_platforms(db)
        create_test_writing_styles(db)
        create_test_content_themes(db)

        # 创建关联数据
        create_test_accounts(db, args.accounts)
        create_test_contents(db, args.contents)

        print()
        print("=" * 50)
        print("性能测试数据创建完成！")
        print("=" * 50)
        print()
        print("可以运行以下命令开始性能测试：")
        print("  ./run_benchmark_test.sh     # 运行基准测试")
        print("  ./run_concurrent_test.sh    # 运行并发测试")
        print()

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
