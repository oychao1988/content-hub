"""
只创建示例账号（假设用户、客户、平台已存在）
"""
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.account import Account

def create_sample_accounts():
    """创建示例账号"""
    db = SessionLocal()

    try:
        # 检查现有数据
        from app.models.user import User
        from app.models.customer import Customer
        from app.models.platform import Platform
        
        user = db.query(User).first()
        if not user:
            print("❌ 没有用户，请先创建用户")
            return
        
        customer = db.query(Customer).first()
        if not customer:
            print("❌ 没有客户，请先创建客户")
            return
        
        platforms = db.query(Platform).all()
        if not platforms:
            print("❌ 没有平台，请先创建平台")
            return
        
        print(f"使用用户: {user.full_name} (ID: {user.id})")
        print(f"使用客户: {customer.name} (ID: {customer.id})")
        print(f"可用平台: {len(platforms)} 个")
        
        # 创建示例账号
        print("\n正在创建示例账号...")
        accounts = [
            Account(
                name="技术博客公众号",
                directory_name="wechat_sample_customer_tech_blog",
                customer_id=customer.id,
                platform_id=platforms[0].id,  # 第一个平台
                owner_id=user.id,
                description="专注于技术分享的微信公众号",
                is_active=True
            ),
            Account(
                name="编程学习知乎专栏",
                directory_name="zhihu_sample_customer_programming",
                customer_id=customer.id,
                platform_id=platforms[1].id if len(platforms) > 1 else platforms[0].id,  # 第二个平台
                owner_id=user.id,
                description="编程学习和技术讨论的知乎专栏",
                is_active=True
            ),
            Account(
                name="开发笔记CSDN博客",
                directory_name="csdn_sample_customer_dev_notes",
                customer_id=customer.id,
                platform_id=platforms[2].id if len(platforms) > 2 else platforms[0].id,  # 第三个平台
                owner_id=user.id,
                description="开发经验和学习笔记的CSDN博客",
                is_active=True
            ),
        ]
        
        created_count = 0
        for account in accounts:
            # 检查是否已存在
            existing = db.query(Account).filter(Account.directory_name == account.directory_name).first()
            if existing:
                print(f"✓ 账号已存在: {account.name} (ID: {existing.id})")
                continue
                
            db.add(account)
            created_count += 1
        
        if created_count > 0:
            db.commit()
            print(f"✓ 创建了 {created_count} 个新账号")
        else:
            print("✓ 所有账号已存在")
        
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
    create_sample_accounts()