"""
数据库迁移脚本：添加异步内容生成任务系统

此迁移脚本执行以下操作：
1. 创建 content_generation_tasks 表
2. 为 contents 表添加异步生成相关字段：
   - generation_task_id (VARCHAR(100))
   - auto_publish (BOOLEAN)
   - scheduled_publish_at (DATETIME)

执行方式：
    python migrations/add_content_generation_task.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.sql_db import get_db


def migrate():
    """执行数据库迁移"""
    print("=" * 60)
    print("开始迁移：添加异步内容生成任务系统...")
    print("=" * 60)

    try:
        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)

        # ========== 1. 创建 content_generation_tasks 表 ==========
        print("\n[1/3] 检查 content_generation_tasks 表...")

        check_table_sql = text("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='content_generation_tasks'
        """)
        table_exists = db.execute(check_table_sql).fetchone()

        if table_exists:
            print("✓ content_generation_tasks 表已存在，跳过创建")
        else:
            print("创建 content_generation_tasks 表...")
            create_table_sql = text("""
                CREATE TABLE content_generation_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    content_id INTEGER,
                    account_id INTEGER NOT NULL,
                    topic TEXT,
                    keywords TEXT,
                    category TEXT,
                    requirements TEXT,
                    tone TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_at DATETIME,
                    completed_at DATETIME,
                    timeout_at DATETIME,
                    result TEXT,
                    error_message TEXT,
                    auto_approve INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (content_id) REFERENCES contents (id),
                    FOREIGN KEY (account_id) REFERENCES accounts (id))
            """)
            db.execute(create_table_sql)

            # 创建索引
            print("创建 content_generation_tasks 表索引...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_content_generation_tasks_task_id ON content_generation_tasks(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_content_generation_tasks_content_id ON content_generation_tasks(content_id)",
                "CREATE INDEX IF NOT EXISTS idx_content_generation_tasks_account_id ON content_generation_tasks(account_id)",
                "CREATE INDEX IF NOT EXISTS idx_content_generation_tasks_status ON content_generation_tasks(status)",
                "CREATE INDEX IF NOT EXISTS idx_content_generation_tasks_submitted_at ON content_generation_tasks(submitted_at)",
            ]
            for idx_sql in indexes:
                db.execute(text(idx_sql))

            print("✓ content_generation_tasks 表创建成功")

        # ========== 2. 为 contents 表添加字段 ==========
        print("\n[2/3] 检查 contents 表字段...")

        check_columns_sql = text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('contents')
            WHERE name IN ('generation_task_id', 'auto_publish', 'scheduled_publish_at')
        """)
        result = db.execute(check_columns_sql).fetchone()
        existing_count = result[0] if result else 0

        if existing_count >= 3:
            print("✓ contents 表字段已存在，跳过添加")
        else:
            # 添加 generation_task_id 字段
            if existing_count == 0:
                print("添加 generation_task_id 字段...")
                db.execute(text("""
                    ALTER TABLE contents
                    ADD COLUMN generation_task_id TEXT
                """))
                print("✓ generation_task_id 字段添加成功")

            # 添加 auto_publish 字段
            print("添加 auto_publish 字段...")
            db.execute(text("""
                ALTER TABLE contents
                ADD COLUMN auto_publish INTEGER DEFAULT 0
            """))
            print("✓ auto_publish 字段添加成功")

            # 添加 scheduled_publish_at 字段
            print("添加 scheduled_publish_at 字段...")
            db.execute(text("""
                ALTER TABLE contents
                ADD COLUMN scheduled_publish_at DATETIME
            """))
            print("✓ scheduled_publish_at 字段添加成功")

            # 创建索引
            print("创建 contents 表索引...")
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_contents_generation_task_id
                ON contents(generation_task_id)
            """))
            print("✓ contents 表索引创建成功")

        # ========== 3. 创建触发器（自动更新 updated_at） ==========
        print("\n[3/3] 创建触发器...")

        check_trigger_sql = text("""
            SELECT name
            FROM sqlite_master
            WHERE type='trigger' AND name='update_content_generation_tasks_timestamp'
        """)
        trigger_exists = db.execute(check_trigger_sql).fetchone()

        if not trigger_exists:
            print("创建 updated_at 自动更新触发器...")
            create_trigger_sql = text("""
                CREATE TRIGGER IF NOT EXISTS update_content_generation_tasks_timestamp
                AFTER UPDATE ON content_generation_tasks
                FOR EACH ROW
                BEGIN
                    UPDATE content_generation_tasks
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END
            """)
            db.execute(create_trigger_sql)
            print("✓ 触发器创建成功")
        else:
            print("✓ 触发器已存在，跳过创建")

        # 提交事务
        db.commit()
        print("\n" + "=" * 60)
        print("✓ 迁移成功完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        sys.exit(1)
    finally:
        if 'db_gen' in locals():
            db_gen.close()


def rollback():
    """回滚迁移"""
    print("=" * 60)
    print("开始回滚：删除异步内容生成任务系统...")
    print("=" * 60)

    try:
        db_gen = get_db()
        db = next(db_gen)

        # 删除 content_generation_tasks 表
        print("\n删除 content_generation_tasks 表...")
        db.execute(text("DROP TABLE IF EXISTS content_generation_tasks"))
        print("✓ content_generation_tasks 表删除成功")

        # 删除触发器
        print("删除触发器...")
        db.execute(text("DROP TRIGGER IF EXISTS update_content_generation_tasks_timestamp"))
        print("✓ 触发器删除成功")

        # 注意：SQLite 不支持直接删除列，contents 表新增的字段无法删除
        print("\n⚠ 警告：SQLite 不支持直接删除列")
        print("contents 表中的新增字段（generation_task_id, auto_publish, scheduled_publish_at）将保留")
        print("如需删除这些字段，请手动重建 contents 表")

        db.commit()
        print("\n" + "=" * 60)
        print("✓ 回滚完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 回滚失败: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        sys.exit(1)
    finally:
        if 'db_gen' in locals():
            db_gen.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="数据库迁移：添加异步内容生成任务系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python migrations/add_content_generation_task.py           # 执行迁移
  python migrations/add_content_generation_task.py --rollback # 回滚迁移
        """
    )
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
