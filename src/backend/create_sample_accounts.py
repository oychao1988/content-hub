"""
创建示例账号数据
"""
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.platform import Platform
from app.models.account import Account

def create_sample_data():
    """创建示例数据"""
    db = SessionLocal()

    try:
        # 检查用户是否已存在
        print("正在检查用户...")
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("正在创建示例用户...")
            user = User(
                username="admin",
                email="admin@example.com",
                password_hash="placeholder_hash",  # 占位符，实际应用中应该使用哈希
                full_name="系统管理员",
                role="admin",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✓ 创建用户: {user.full_name} (ID: {user.id})")
        else:
            print(f"✓ 用户已存在: {user.full_name} (ID: {user.id})")

        # 创建示例客户
        print("\n正在创建示例客户...")
        customer = Customer(
            name="示例客户公司",
            contact_name="张经理",
            contact_email="contact@example.com",
            contact_phone="13800138000",
            description="示例客户公司",
            is_active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"✓ 创建客户: {customer.name} (ID: {customer.id})")

        # 创建示例平台
        print("\n正在创建示例平台...")
        platforms = [
            Platform(name="微信公众号", code="wechat", type="social", description="微信公众平台", api_url="https://mp.weixin.qq.com"),
            Platform(name="知乎", code="zhihu", type="community", description="知乎平台", api_url="https://www.zhihu.com"),
            Platform(name="CSDN", code="csdn", type="tech", description="CSDN技术社区", api_url="https://blog.csdn.net"),
        ]
        
        for platform in platforms:
            db.add(platform)
        db.commit()
        
        for platform in platforms:
            db.refresh(platform)
            print(f"✓ 创建平台: {platform.name} (ID: {platform.id})")

        # 创建示例账号
        print("\n正在创建示例账号...")
        accounts = [
            Account(
                name="技术博客公众号",
                directory_name="wechat_sample_customer_tech_blog",
                customer_id=customer.id,
                platform_id=platforms[0].id,  # 微信公众号
                owner_id=user.id,
                description="专注于技术分享的微信公众号",
                is_active=True
            ),
            Account(
                name="编程学习知乎专栏",
                directory_name="zhihu_sample_customer_programming",
                customer_id=customer.id,
                platform_id=platforms[1].id,  # 知乎
                owner_id=user.id,
                description="编程学习和技术讨论的知乎专栏",
                is_active=True
            ),
            Account(
                name="开发笔记CSDN博客",
                directory_name="csdn_sample_customer_dev_notes",
                customer_id=customer.id,
                platform_id=platforms[2].id,  # CSDN
                owner_id=user.id,
                description="开发经验和学习笔记的CSDN博客",
                is_active=True
            ),
        ]
        
        for account in accounts:
            db.add(account)
        db.commit()
        
        for account in accounts:
            db.refresh(account)
            print(f"✓ 创建账号: {account.name} (ID: {account.id}) - {account.directory_name}")

        print("\n" + "="*50)
        print("示例数据创建完成！")
        print("="*50)
        print(f"用户: {user.full_name} (ID: {user.id})")
        print(f"客户: {customer.name} (ID: {customer.id})")
        print(f"平台: {len(platforms)} 个")
        print(f"账号: {len(accounts)} 个")
        
        # 显示所有账号
        print("\n📋 账号列表:")
        all_accounts = db.query(Account).all()
        for acc in all_accounts:
            platform = db.query(Platform).filter(Platform.id == acc.platform_id).first()
            print(f"  • {acc.name} (ID: {acc.id}) - {platform.name if platform else '未知平台'} - {acc.directory_name}")

    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()