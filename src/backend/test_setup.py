"""
基础架构验证脚本
验证数据库、模型和配置是否正确加载
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试导入"""
    print("🔍 测试模块导入...")

    try:
        from app.core.config import settings
        print("✅ 配置模块导入成功")
        print(f"   应用名称: {settings.APP_NAME}")
        print(f"   版本: {settings.APP_VERSION}")
        print(f"   数据库: {settings.DATABASE_URL}")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False

    try:
        from app.db.database import Base, engine, SessionLocal
        print("✅ 数据库模块导入成功")
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False

    try:
        from app.models import (
            Account,
            WritingStyle,
            ContentSection,
            DataSource,
            PublishConfig,
            Content,
            TopicHistory,
            ScheduledTask,
            PublishLog,
            PublishPool,
        )
        print("✅ 数据模型导入成功")
        print(f"   已加载 {len(Account.__subclasses__())} 个账号相关模型")
    except Exception as e:
        print(f"❌ 数据模型导入失败: {e}")
        return False

    try:
        from app.services.scheduler_service import scheduler_service
        print("✅ 调度器服务导入成功")
    except Exception as e:
        print(f"❌ 调度器服务导入失败: {e}")
        return False

    return True


def test_database():
    """测试数据库连接和表创建"""
    print("\n🔍 测试数据库连接...")

    try:
        from app.db.database import init_db, engine, Base

        # 初始化数据库
        init_db()
        print("✅ 数据库初始化成功")

        # 检查表是否创建
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "accounts",
            "writing_styles",
            "content_sections",
            "data_sources",
            "publish_configs",
            "account_configs",
            "contents",
            "topic_history",
            "scheduled_tasks",
            "publish_logs",
            "publish_pool",
        ]

        print(f"   已创建 {len(tables)} 个表:")
        for table in tables:
            status = "✅" if table in expected_tables else "⚠️ "
            print(f"   {status} {table}")

        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"⚠️  缺少表: {missing_tables}")
            return False

        return True

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_factory():
    """测试应用工厂"""
    print("\n🔍 测试应用工厂...")

    try:
        from app.factory import create_app

        app = create_app()
        print("✅ 应用创建成功")
        print(f"   应用标题: {app.title}")
        print(f"   版本: {app.version}")
        print(f"   API 前缀: {app.routes[0].path if app.routes else 'N/A'}")

        return True

    except Exception as e:
        print(f"❌ 应用工厂测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("ContentHub 基础架构验证")
    print("=" * 60)

    results = []

    # 测试导入
    results.append(("模块导入", test_imports()))

    # 测试数据库
    results.append(("数据库", test_database()))

    # 测试应用工厂
    results.append(("应用工厂", test_factory()))

    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:.<30} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有测试通过！基础架构搭建完成。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
