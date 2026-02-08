#!/usr/bin/env python
"""
测试异步内容生成 CLI 命令
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models import ContentGenerationTask, Account
from app.services.async_content_generation_service import AsyncContentGenerationService


def test_list_empty():
    """测试列出任务（空列表）"""
    print("\n" + "="*60)
    print("测试 1: 列出任务（空列表）")
    print("="*60)

    db = SessionLocal()
    try:
        service = AsyncContentGenerationService(db)
        tasks = service.list_tasks(limit=5)
        print(f"✅ 找到 {len(tasks)} 个任务")
        for task in tasks:
            print(f"   - {task.task_id}: {task.status} - {task.topic}")
    finally:
        db.close()


def test_task_status():
    """测试查询任务状态"""
    print("\n" + "="*60)
    print("测试 2: 查询任务状态")
    print("="*60)

    db = SessionLocal()
    try:
        service = AsyncContentGenerationService(db)
        tasks = service.list_tasks(limit=1)

        if not tasks:
            print("⚠️  没有任务可测试")
            return

        task = tasks[0]
        status = service.get_task_status(task.task_id)
        print(f"✅ 任务ID: {status['task_id']}")
        print(f"   状态: {status['status']}")
        print(f"   选题: {status.get('topic', 'N/A')}")
        print(f"   创建时间: {status.get('created_at', 'N/A')}")
    finally:
        db.close()


def test_submit_async_task():
    """测试提交异步任务"""
    print("\n" + "="*60)
    print("测试 3: 提交异步任务")
    print("="*60)

    db = SessionLocal()
    try:
        # 查找一个测试账号
        account = db.query(Account).first()
        if not account:
            print("❌ 没有找到账号，请先创建账号")
            return None

        service = AsyncContentGenerationService(db)
        task_id = service.submit_task(
            account_id=account.id,
            topic="CLI异步测试-" + str(hash(os.urandom(8)))[:8],
            keywords="测试,CLI",
            category="测试",
            requirements="这是一个CLI异步测试任务",
            tone="友好",
            priority=5,
            auto_approve=False
        )

        print(f"✅ 异步任务已提交")
        print(f"   任务ID: {task_id}")
        print(f"   状态: pending")

        return task_id
    finally:
        db.close()


def test_task_cancel():
    """测试取消任务"""
    print("\n" + "="*60)
    print("测试 4: 取消任务")
    print("="*60)

    db = SessionLocal()
    try:
        service = AsyncContentGenerationService(db)

        # 创建一个待取消的任务
        task_id = test_submit_async_task()
        if not task_id:
            return

        # 尝试取消
        success = service.cancel_task(task_id)
        if success:
            print(f"✅ 任务已取消: {task_id}")
        else:
            print(f"❌ 取消失败: {task_id}")
    finally:
        db.close()


def test_task_stats():
    """测试任务统计"""
    print("\n" + "="*60)
    print("测试 5: 任务统计")
    print("="*60)

    db = SessionLocal()
    try:
        from sqlalchemy import func

        stats = db.query(
            ContentGenerationTask.status,
            func.count(ContentGenerationTask.id).label('count')
        ).group_by(ContentGenerationTask.status).all()

        print("✅ 任务统计:")
        total = 0
        for status, count in stats:
            print(f"   {status}: {count}")
            total += count
        print(f"   总计: {total}")
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("ContentHub 异步内容生成 CLI 测试")
    print("="*60)

    try:
        test_list_empty()
        test_task_status()
        test_submit_async_task()
        test_task_cancel()
        test_task_stats()

        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)

        print("\n📝 CLI 命令示例:")
        print("   contenthub content generate -a 49 -t '测试选题' --async")
        print("   contenthub task list")
        print("   contenthub task status <task-id>")
        print("   contenthub task cancel <task-id>")
        print("   contenthub task retry <task-id>")
        print("   contenthub task stats")
        print("   contenthub task cleanup --days 7")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
