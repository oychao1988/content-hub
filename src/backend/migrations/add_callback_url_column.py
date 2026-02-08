"""
数据库迁移脚本：添加 callback_url 字段到 content_generation_tasks 表

运行方式：
    python -m migrations.add_callback_url_column
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import SessionLocal, engine


def migrate():
    """执行迁移"""
    session = SessionLocal()

    try:
        # 检查列是否已存在
        check_column_sql = text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('content_generation_tasks')
            WHERE name = 'callback_url'
        """)

        result = session.execute(check_column_sql).fetchone()

        if result[0] > 0:
            print("✓ callback_url 列已存在，无需迁移")
            return True

        # 添加 callback_url 列
        add_column_sql = text("""
            ALTER TABLE content_generation_tasks
            ADD COLUMN callback_url VARCHAR(500)
        """)

        print("正在添加 callback_url 列...")
        session.execute(add_column_sql)
        session.commit()

        print("✓ 成功添加 callback_url 列")

        # 验证列是否添加成功
        verify_result = session.execute(check_column_sql).fetchone()
        if verify_result[0] > 0:
            print("✓ 验证成功：callback_url 列已存在")
            return True
        else:
            print("✗ 验证失败：callback_url 列未找到")
            return False

    except Exception as e:
        session.rollback()
        print(f"✗ 迁移失败: {str(e)}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移：添加 callback_url 字段")
    print("=" * 60)
    print()

    success = migrate()

    print()
    print("=" * 60)
    if success:
        print("迁移完成！")
        sys.exit(0)
    else:
        print("迁移失败！")
        sys.exit(1)
