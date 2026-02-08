"""
创建示例平台
"""
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.platform import Platform

def create_platforms():
    """创建示例平台"""
    db = SessionLocal()

    try:
        print("正在创建示例平台...")
        
        platforms_data = [
            {"name": "微信公众号", "code": "wechat", "type": "social", "description": "微信公众平台"},
            {"name": "知乎", "code": "zhihu", "type": "community", "description": "知乎平台"},
            {"name": "CSDN", "code": "csdn", "type": "tech", "description": "CSDN技术社区"},
        ]
        
        created_count = 0
        for data in platforms_data:
            # 检查是否已存在
            existing = db.query(Platform).filter(Platform.code == data["code"]).first()
            if existing:
                print(f"✓ 平台已存在: {data['name']} (ID: {existing.id})")
                continue
                
            platform = Platform(**data)
            db.add(platform)
            created_count += 1
        
        if created_count > 0:
            db.commit()
            print(f"✓ 创建了 {created_count} 个新平台")
        else:
            print("✓ 所有平台已存在")
        
        # 显示所有平台
        print("\n📋 平台列表:")
        all_platforms = db.query(Platform).all()
        for platform in all_platforms:
            print(f"  • {platform.name} (ID: {platform.id}) - {platform.code} - {platform.type}")

    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_platforms()