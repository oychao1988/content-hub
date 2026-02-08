"""
模拟 CLI 功能列出账号
"""
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.account import Account
from app.models.platform import Platform
from app.models.customer import Customer
from app.models.user import User
from datetime import datetime

def format_datetime(dt):
    """格式化日期时间"""
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def list_accounts():
    """列出所有账号"""
    db = SessionLocal()
    
    try:
        print("📋 Content-Hub 账号列表")
        print("=" * 80)
        
        # 查询所有账号
        accounts = db.query(Account).order_by(Account.id).all()
        
        if not accounts:
            print("❌ 没有找到任何账号")
            return
        
        # 显示表头
        print(f"{'ID':<4} {'名称':<20} {'平台':<10} {'客户':<15} {'运营者':<10} {'状态':<6} {'创建时间':<19}")
        print("-" * 80)
        
        for account in accounts:
            # 获取关联信息
            platform = db.query(Platform).filter(Platform.id == account.platform_id).first()
            customer = db.query(Customer).filter(Customer.id == account.customer_id).first()
            owner = db.query(User).filter(User.id == account.owner_id).first() if account.owner_id else None
            
            platform_name = platform.name if platform else "未知"
            customer_name = customer.name if customer else "未知"
            owner_name = owner.full_name if owner else "未知"
            status = "✅激活" if account.is_active else "❌停用"
            
            print(f"{account.id:<4} {account.name:<20} {platform_name:<10} {customer_name:<15} {owner_name:<10} {status:<6} {format_datetime(account.created_at)}")
        
        print("=" * 80)
        print(f"总计: {len(accounts)} 个账号")
        
        # 显示统计信息
        active_count = sum(1 for a in accounts if a.is_active)
        print(f"激活账号: {active_count} 个")
        print(f"停用账号: {len(accounts) - active_count} 个")
        
        # 按平台统计
        print("\n📊 按平台统计:")
        platform_stats = {}
        for account in accounts:
            platform = db.query(Platform).filter(Platform.id == account.platform_id).first()
            platform_name = platform.name if platform else "未知"
            platform_stats[platform_name] = platform_stats.get(platform_name, 0) + 1
        
        for platform_name, count in platform_stats.items():
            print(f"  • {platform_name}: {count} 个账号")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    list_accounts()