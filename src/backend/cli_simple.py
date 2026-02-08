"""
简化的 Content-Hub CLI 入口点
绕过复杂的依赖问题
"""
import sys
import os
import argparse
from pathlib import Path

# 设置环境变量，禁用日志
os.environ['LOG_LEVEL'] = 'ERROR'
os.environ['LOG_FILE'] = 'false'

# 添加项目路径
sys.path.insert(0, '.')

def run_accounts_list(args):
    """列出账号"""
    from app.db.database import SessionLocal
    from app.models.account import Account
    from app.models.platform import Platform
    from app.models.customer import Customer
    from app.models.user import User
    
    db = SessionLocal()
    
    try:
        print("📋 Content-Hub 账号列表")
        print("=" * 80)
        
        # 构建查询
        query = db.query(Account)
        
        # 应用筛选条件
        if args.customer_id:
            query = query.filter(Account.customer_id == args.customer_id)
        if args.platform_id:
            query = query.filter(Account.platform_id == args.platform_id)
        if args.status:
            is_active = args.status.lower() == "active"
            query = query.filter(Account.is_active == is_active)
        
        # 排序和分页
        query = query.order_by(Account.id)
        if args.limit:
            query = query.limit(args.limit)
        if args.offset:
            query = query.offset(args.offset)
        
        accounts = query.all()
        
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
            
            # 格式化时间
            from datetime import datetime
            created_at = account.created_at.strftime("%Y-%m-%d %H:%M:%S") if account.created_at else "-"
            
            print(f"{account.id:<4} {account.name:<20} {platform_name:<10} {customer_name:<15} {owner_name:<10} {status:<6} {created_at}")
        
        print("=" * 80)
        print(f"总计: {len(accounts)} 个账号")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def run_accounts_info(args):
    """查看账号详情"""
    from app.db.database import SessionLocal
    from app.models.account import Account
    from app.models.platform import Platform
    from app.models.customer import Customer
    from app.models.user import User
    
    db = SessionLocal()
    
    try:
        account = db.query(Account).filter(Account.id == args.account_id).first()
        if not account:
            print(f"❌ 账号不存在: ID {args.account_id}")
            return
        
        # 获取关联信息
        platform = db.query(Platform).filter(Platform.id == account.platform_id).first()
        customer = db.query(Customer).filter(Customer.id == account.customer_id).first()
        owner = db.query(User).filter(User.id == account.owner_id).first() if account.owner_id else None
        
        print(f"📄 账号详情 (ID: {account.id})")
        print("=" * 50)
        print(f"名称: {account.name}")
        print(f"目录名: {account.directory_name}")
        print(f"描述: {account.description or '无'}")
        print(f"平台: {platform.name if platform else '未知'} (ID: {account.platform_id})")
        print(f"客户: {customer.name if customer else '未知'} (ID: {account.customer_id})")
        print(f"运营者: {owner.full_name if owner else '未知'} (ID: {account.owner_id})")
        print(f"状态: {'✅ 激活' if account.is_active else '❌ 停用'}")
        
        # 格式化时间
        from datetime import datetime
        created_at = account.created_at.strftime("%Y-%m-%d %H:%M:%S") if account.created_at else "-"
        updated_at = account.updated_at.strftime("%Y-%m-%d %H:%M:%S") if account.updated_at else "-"
        
        print(f"创建时间: {created_at}")
        print(f"更新时间: {updated_at}")
        
        # 显示配置信息
        if account.wechat_app_id:
            print(f"微信AppID: {account.wechat_app_id}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()

def run_platforms_list(args):
    """列出平台"""
    from app.db.database import SessionLocal
    from app.models.platform import Platform
    
    db = SessionLocal()
    
    try:
        platforms = db.query(Platform).order_by(Platform.id).all()
        
        if not platforms:
            print("❌ 没有找到任何平台")
            return
        
        print("📱 平台列表")
        print("=" * 50)
        print(f"{'ID':<4} {'名称':<15} {'代码':<10} {'类型':<10} {'状态':<6}")
        print("-" * 50)
        
        for platform in platforms:
            status = "✅激活" if platform.is_active else "❌停用"
            print(f"{platform.id:<4} {platform.name:<15} {platform.code:<10} {platform.type or '-':<10} {status:<6}")
        
        print("=" * 50)
        print(f"总计: {len(platforms)} 个平台")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()

def run_customers_list(args):
    """列出客户"""
    from app.db.database import SessionLocal
    from app.models.customer import Customer
    
    db = SessionLocal()
    
    try:
        customers = db.query(Customer).order_by(Customer.id).all()
        
        if not customers:
            print("❌ 没有找到任何客户")
            return
        
        print("👥 客户列表")
        print("=" * 60)
        print(f"{'ID':<4} {'名称':<20} {'联系人':<10} {'邮箱':<20} {'状态':<6}")
        print("-" * 60)
        
        for customer in customers:
            status = "✅激活" if customer.is_active else "❌停用"
            print(f"{customer.id:<4} {customer.name:<20} {customer.contact_name or '-':<10} {customer.contact_email or '-':<20} {status:<6}")
        
        print("=" * 60)
        print(f"总计: {len(customers)} 个客户")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()

def run_db_status(args):
    """查看数据库状态"""
    from app.db.database import SessionLocal, engine
    from sqlalchemy import text
    import os
    
    db = SessionLocal()
    
    try:
        print("🗄️  数据库状态")
        print("=" * 50)
        
        # 检查数据库文件
        db_path = "data/contenthub.db"
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            print(f"数据库文件: {db_path}")
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print(f"数据库文件: {db_path} (不存在)")
        
        # 测试连接
        try:
            result = db.execute(text("SELECT 1"))
            print("连接状态: ✅ 正常")
        except Exception as e:
            print(f"连接状态: ❌ 失败 ({e})")
        
        # 获取表数量
        try:
            result = db.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"表数量: {table_count}")
        except Exception as e:
            print(f"表数量: 查询失败 ({e})")
        
        # 获取账号数量
        try:
            from app.models.account import Account
            account_count = db.query(Account).count()
            print(f"账号数量: {account_count}")
        except Exception as e:
            print(f"账号数量: 查询失败 ({e})")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Content-Hub 简化 CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # accounts 命令
    accounts_parser = subparsers.add_parser("accounts", help="账号管理")
    accounts_subparsers = accounts_parser.add_subparsers(dest="subcommand", help="账号子命令")
    
    # accounts list
    list_parser = accounts_subparsers.add_parser("list", help="列出账号")
    list_parser.add_argument("--customer-id", type=int, help="按客户ID筛选")
    list_parser.add_argument("--platform-id", type=int, help="按平台ID筛选")
    list_parser.add_argument("--status", choices=["active", "inactive"], help="按状态筛选")
    list_parser.add_argument("--limit", type=int, help="限制返回数量")
    list_parser.add_argument("--offset", type=int, help="偏移量")
    list_parser.set_defaults(func=run_accounts_list)
    
    # accounts info
    info_parser = accounts_subparsers.add_parser("info", help="查看账号详情")
    info_parser.add_argument("account_id", type=int, help="账号ID")
    info_parser.set_defaults(func=run_accounts_info)
    
    # platforms 命令
    platforms_parser = subparsers.add_parser("platforms", help="平台管理")
    platforms_subparsers = platforms_parser.add_subparsers(dest="subcommand", help="平台子命令")
    
    # platforms list
    platforms_list_parser = platforms_subparsers.add_parser("list", help="列出平台")
    platforms_list_parser.set_defaults(func=run_platforms_list)
    
    # customers 命令
    customers_parser = subparsers.add_parser("customers", help="客户管理")
    customers_subparsers = customers_parser.add_subparsers(dest="subcommand", help="客户子命令")
    
    # customers list
    customers_list_parser = customers_subparsers.add_parser("list", help="列出客户")
    customers_list_parser.set_defaults(func=run_customers_list)
    
    # db 命令
    db_parser = subparsers.add_parser("db", help="数据库管理")
    db_subparsers = db_parser.add_subparsers(dest="subcommand", help="数据库子命令")
    
    # db status
    db_status_parser = db_subparsers.add_parser("status", help="查看数据库状态")
    db_status_parser.set_defaults(func=run_db_status)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()