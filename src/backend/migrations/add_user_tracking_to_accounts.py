"""
数据库迁移脚本：为 accounts 表添加用户追踪字段

方案 A: 审计追踪
- created_by: 创建人 ID
- updated_by: 最后修改人 ID

方案 B: 账号所有者
- owner_id: 账号所有者 ID

执行方式：
    python migrations/add_user_tracking_to_accounts.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import get_db


def migrate():
    """执行数据库迁移"""
    print("开始迁移：为 accounts 表添加用户追踪字段...")

    try:
        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)

        # 检查字段是否已存在
        check_sql = text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('accounts')
            WHERE name IN ('created_by', 'updated_by', 'owner_id')
        """)
        result = db.execute(check_sql).fetchone()
        existing_count = result[0] if result else 0

        if existing_count >= 3:
            print("✓ 字段已存在，跳过迁移")
            return

        # 添加 created_by 字段
        if existing_count == 0:
            print("添加 created_by 字段...")
            db.execute(text("""
                ALTER TABLE accounts
                ADD COLUMN created_by INTEGER
                REFERENCES users(id)
            """))
            print("✓ created_by 字段添加成功")

        # 添加 updated_by 字段
        db.execute(text("""
            ALTER TABLE accounts
            ADD COLUMN updated_by INTEGER
            REFERENCES users(id)
        """))
        print("✓ updated_by 字段添加成功")

        # 添加 owner_id 字段
        db.execute(text("""
            ALTER TABLE accounts
            ADD COLUMN owner_id INTEGER
            REFERENCES users(id)
        """))
        print("✓ owner_id 字段添加成功")

        # 创建索引
        print("创建索引...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_accounts_owner
            ON accounts(owner_id)
        """))
        print("✓ owner_id 索引创建成功")

        # 提交事务
        db.commit()
        print("\n✓ 迁移成功完成！")

    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        if 'db' in locals():
            db.rollback()
        sys.exit(1)
    finally:
        if 'db_gen' in locals():
            db_gen.close()


def rollback():
    """回滚迁移"""
    print("开始回滚：删除用户追踪字段...")

    try:
        db_gen = get_db()
        db = next(db_gen)

        # SQLite 不支持 DROP COLUMN，需要重建表
        print("⚠ 警告：SQLite 不支持直接删除列")
        print("如需回滚，请手动重建 accounts 表")

        db.commit()

    except Exception as e:
        print(f"\n✗ 回滚失败: {e}")
        if 'db' in locals():
            db.rollback()
        sys.exit(1)
    finally:
        if 'db_gen' in locals():
            db_gen.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移：添加用户追踪字段")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
