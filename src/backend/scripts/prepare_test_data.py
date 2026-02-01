#!/usr/bin/env python3
"""
准备测试数据的脚本
"""
import sys
import os
from pathlib import Path

# 添加后端路径
sys.path.insert(0, str(Path(__file__).parent / "src/backend"))

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import json

def prepare_test_data():
    """准备测试数据"""
    # 直接使用数据库文件的绝对路径
    db_path = "/Users/Oychao/Documents/Projects/content-hub/src/backend/data/contenthub.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        # 1. 创建测试平台
        print("创建测试平台...")
        platforms = [
            {
                "name": "微信公众号",
                "platform_type": "wechat",
                "description": "微信公众号平台",
                "status": "active",
                "config": json.dumps({"app_id": "test_app_id"}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "name": "今日头条",
                "platform_type": "toutiao",
                "description": "今日头条平台",
                "status": "active",
                "config": json.dumps({"app_id": "test_toutiao_id"}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]

        for platform in platforms:
            try:
                result = conn.execute(text("""
                    INSERT INTO platforms (name, platform_type, description, status, config, created_at, updated_at)
                    VALUES (:name, :platform_type, :description, :status, :config, :created_at, :updated_at)
                """), platform)
                print(f"✓ 创建平台: {platform['name']}")
            except Exception as e:
                print(f"✗ 平台可能已存在: {platform['name']}")

        # 获取平台ID
        platforms_result = conn.execute(text("SELECT id, name FROM platforms"))
        platforms_dict = {row[1]: row[0] for row in platforms_result}

        # 2. 创建测试账号
        print("\n创建测试账号...")
        accounts = [
            {
                "name": "测试微信公众号1",
                "platform_id": platforms_dict.get("微信公众号"),
                "account_id": "test_wechat_001",
                "status": "active",
                "config": json.dumps({"nickname": "测试公众号"}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "name": "测试头条号1",
                "platform_id": platforms_dict.get("今日头条"),
                "account_id": "test_toutiao_001",
                "status": "active",
                "config": json.dumps({"nickname": "测试头条号"}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]

        for account in accounts:
            try:
                conn.execute(text("""
                    INSERT INTO accounts (name, platform_id, account_id, status, config, created_at, updated_at)
                    VALUES (:name, :platform_id, :account_id, :status, :config, :created_at, :updated_at)
                """), account)
                print(f"✓ 创建账号: {account['name']}")
            except Exception as e:
                print(f"✗ 账号可能已存在: {account['name']}")

        # 3. 创建测试内容
        print("\n创建测试内容...")
        contents = [
            {
                "title": "如何使用 ContentHub 管理内容",
                "content_type": "article",
                "content": "# ContentHub 使用指南\n\nContentHub 是一个强大的内容运营管理系统...",
                "status": "published",
                "word_count": 1500,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "title": "2024年内容运营趋势分析",
                "content_type": "article",
                "content": "# 2024年内容运营趋势\n\n随着人工智能技术的发展...",
                "status": "draft",
                "word_count": 2300,
                "created_at": datetime.now() - timedelta(days=1),
                "updated_at": datetime.now() - timedelta(days=1)
            },
            {
                "title": "快速入门指南",
                "content_type": "tutorial",
                "content": "# 快速入门\n\n本文将帮助你快速上手...",
                "status": "published",
                "word_count": 800,
                "created_at": datetime.now() - timedelta(days=2),
                "updated_at": datetime.now() - timedelta(days=2)
            },
            {
                "title": "内容创作最佳实践",
                "content_type": "article",
                "content": "# 最佳实践\n\n在内容创作过程中...",
                "status": "draft",
                "word_count": 1200,
                "created_at": datetime.now() - timedelta(days=3),
                "updated_at": datetime.now() - timedelta(days=3)
            }
        ]

        for content in contents:
            try:
                conn.execute(text("""
                    INSERT INTO contents (title, content_type, content, status, word_count, created_at, updated_at)
                    VALUES (:title, :content_type, :content, :status, :word_count, :created_at, :updated_at)
                """), content)
                print(f"✓ 创建内容: {content['title']}")
            except Exception as e:
                print(f"✗ 内容可能已存在: {content['title']}")

        # 4. 创建测试定时任务
        print("\n创建测试定时任务...")
        tasks = [
            {
                "name": "每日内容推送",
                "task_type": "publish",
                "cron_expression": "0 9 * * *",
                "status": "active",
                "config": json.dumps({"publish_time": "09:00"}),
                "next_run_time": datetime.now() + timedelta(hours=1),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "name": "每周内容统计",
                "task_type": "statistics",
                "cron_expression": "0 18 * * 5",
                "status": "paused",
                "config": json.dumps({"report_type": "weekly"}),
                "next_run_time": datetime.now() + timedelta(days=7),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]

        for task in tasks:
            try:
                conn.execute(text("""
                    INSERT INTO scheduler_tasks (name, task_type, cron_expression, status, config, next_run_time, created_at, updated_at)
                    VALUES (:name, :task_type, :cron_expression, :status, :config, :next_run_time, :created_at, :updated_at)
                """), task)
                print(f"✓ 创建任务: {task['name']}")
            except Exception as e:
                print(f"✗ 任务可能已存在: {task['name']}")

        # 提交所有更改
        conn.commit()

        # 5. 统计创建的数据
        print("\n数据统计:")
        stats = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM platforms) as platforms,
                (SELECT COUNT(*) FROM accounts) as accounts,
                (SELECT COUNT(*) FROM contents) as contents,
                (SELECT COUNT(*) FROM scheduler_tasks) as tasks
        """))

        row = stats.fetchone()
        print(f"- 平台数: {row[0]}")
        print(f"- 账号数: {row[1]}")
        print(f"- 内容数: {row[2]}")
        print(f"- 定时任务数: {row[3]}")

        print("\n✅ 测试数据准备完成！")

if __name__ == "__main__":
    prepare_test_data()
