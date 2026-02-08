"""
简化的 Content-Hub CLI
绕过复杂的依赖，直接提供核心功能
"""
import sys
import argparse
from app.db.database import SessionLocal
from app.models.account import Account
from app.models.platform import Platform
from app.models.customer import Customer
from app.models.user import User

def format_datetime(dt):
    """格式化日期时间"""
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def list_accounts(args):
    """列出账号"""
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
            
            print(f"{account.id:<4} {account.name:<20} {platform_name:<10} {customer_name:<15} {owner_name:<10} {status:<6} {format_datetime(account.created_at)}")
        
        print("=" * 80)
        print(f"总计: {len(accounts)} 个账号")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()

def show_account_info(args):
    """显示账号详情"""
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
        print(f"创建时间: {format_datetime(account.created_at)}")
        print(f"更新时间: {format_datetime(account.updated_at)}")
        
        # 显示配置信息
        if account.wechat_app_id:
            print(f"微信AppID: {account.wechat_app_id}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()

def list_platforms(args):
    """列出平台"""
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

def list_customers(args):
    """列出客户"""
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

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Content-Hub 简化 CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # accounts list 命令
    list_parser = subparsers.add_parser("accounts", help="账号管理")
    list_subparsers = list_parser.add_subparsers(dest="subcommand", help="账号子命令")
    
    # accounts list
    list_accounts_parser = list_subparsers.add_parser("list", help="列出账号")
    list_accounts_parser.add_argument("--customer-id", type=int, help="按客户ID筛选")
    list_accounts_parser.add_argument("--platform-id", type=int, help="按平台ID筛选")
    list_accounts_parser.add_argument("--status", choices=["active", "inactive"], help="按状态筛选")
    list_accounts_parser.add_argument("--limit", type=int, help="限制返回数量")
    list_accounts_parser.add_argument("--offset", type=int, help="偏移量")
    
    # accounts info
    info_parser = list_subparsers.add_parser("info", help="查看账号详情")
    info_parser.add_argument("account_id", type=int, help="账号ID")
    
    # platforms list 命令
    platforms_parser = subparsers.add_parser("platforms", help="平台管理")
    platforms_subparsers = platforms_parser.add_subparsers(dest="subcommand", help="平台子命令")
    platforms_subparsers.add_parser("list", help="列出平台")
    
    # customers list 命令
    customers_parser = subparsers.add_parser("customers", help="客户管理")
    customers_subparsers = customers_parser.add_subparsers(dest="subcommand", help="客户子命令")
    customers_subparsers.add_parser("list", help="列出客户")
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == "accounts":
        if args.subcommand == "list":
            list_accounts(args)
        elif args.subcommand == "info":
            show_account_info(args)
        else:
            list_accounts_parser.print_help()
    elif args.command == "platforms":
        if args.subcommand == "list":
            list_platforms(args)
        else:
            platforms_parser.print_help()
    elif args.command == "customers":
        if args.subcommand == "list":
            list_customers(args)
        else:
            customers_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()