"""
测试配置模块
验证写作风格和内容主题的 CRUD 操作
"""
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.account import WritingStyle
from app.models.theme import ContentTheme

def test_writing_style_model():
    """测试写作风格模型"""
    db = SessionLocal()
    try:
        # 查询所有写作风格
        styles = db.query(WritingStyle).all()
        print(f"✓ 找到 {len(styles)} 个写作风格")

        # 显示系统级和自定义风格数量
        system_count = db.query(WritingStyle).filter(WritingStyle.is_system == True).count()
        custom_count = db.query(WritingStyle).filter(WritingStyle.is_system == False).count()
        print(f"  - 系统级: {system_count}")
        print(f"  - 自定义: {custom_count}")

        # 显示前3个风格
        for style in styles[:3]:
            print(f"  • {style.name} ({style.code}) - {'系统级' if style.is_system else '自定义'}")

        return True
    except Exception as e:
        print(f"✗ 写作风格模型测试失败: {e}")
        return False
    finally:
        db.close()

def test_content_theme_model():
    """测试内容主题模型"""
    db = SessionLocal()
    try:
        # 查询所有内容主题
        themes = db.query(ContentTheme).all()
        print(f"\n✓ 找到 {len(themes)} 个内容主题")

        # 显示系统级和自定义主题数量
        system_count = db.query(ContentTheme).filter(ContentTheme.is_system == True).count()
        custom_count = db.query(ContentTheme).filter(ContentTheme.is_system == False).count()
        print(f"  - 系统级: {system_count}")
        print(f"  - 自定义: {custom_count}")

        # 显示前3个主题
        for theme in themes[:3]:
            print(f"  • {theme.name} ({theme.code}) - {'系统级' if theme.is_system else '自定义'}")

        return True
    except Exception as e:
        print(f"✗ 内容主题模型测试失败: {e}")
        return False
    finally:
        db.close()

def test_api_endpoints():
    """测试 API 端点"""
    try:
        from app.modules.config.endpoints import router
        print("\n✓ API 端点加载成功")

        # 显示所有路由
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':
                        routes.append(f"{method} {route.path}")

        print("可用的 API 端点:")
        for route in sorted(routes):
            print(f"  • {route}")

        return True
    except Exception as e:
        print(f"✗ API 端点测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("配置模块测试")
    print("=" * 60)

    results = []

    # 测试写作风格模型
    results.append(test_writing_style_model())

    # 测试内容主题模型
    results.append(test_content_theme_model())

    # 测试 API 端点
    results.append(test_api_endpoints())

    print("\n" + "=" * 60)
    if all(results):
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
