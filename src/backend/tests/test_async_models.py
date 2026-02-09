"""
异步内容生成系统 - 数据库模型测试脚本

测试 ContentGenerationTask 模型及其与 Content 和 Account 的关系
"""
import sys
import uuid
from datetime import datetime
from sqlalchemy import func

# 添加项目根目录到 Python 路径
sys.path.insert(0, '/Users/Oychao/Documents/Projects/content-hub/src/backend')

from app.db.database import SessionLocal
from app.models import ContentGenerationTask, Content, Account


def test_task_creation():
    """测试任务创建"""
    print("\n=== Test 1: Task Creation ===")
    db = SessionLocal()

    try:
        # 获取第一个账号
        account = db.query(Account).first()
        if not account:
            print("✗ No account found in database")
            return False

        # 创建任务
        task = ContentGenerationTask(
            task_id=f"test-{uuid.uuid4().hex[:8]}",
            account_id=account.id,
            topic="测试选题：AI 技术发展趋势",
            keywords="AI,人工智能,技术趋势",
            category="技术",
            requirements="要求内容专业，包含最新发展",
            tone="专业",
            status="pending",
            priority=8,
            auto_approve=True
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"✓ Task created: {task.task_id}")
        print(f"  - Account: {account.name}")
        print(f"  - Topic: {task.topic}")
        print(f"  - Status: {task.status}")
        print(f"  - Priority: {task.priority}")

        return task.id

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_task_with_content():
    """测试任务与内容的关联"""
    print("\n=== Test 2: Task with Content ===")
    db = SessionLocal()

    try:
        # 获取账号和内容
        account = db.query(Account).first()
        content = db.query(Content).first()

        if not account or not content:
            print("✗ No account or content found")
            return False

        # 创建关联内容的任务
        task = ContentGenerationTask(
            task_id=f"test-{uuid.uuid4().hex[:8]}",
            content_id=content.id,
            account_id=account.id,
            topic=content.topic or "内容生成任务",
            status="processing",
            started_at=datetime.utcnow()
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"✓ Task created with content: {task.task_id}")
        print(f"  - Content ID: {content.id}")
        print(f"  - Content Title: {content.title}")
        print(f"  - Task Status: {task.status}")

        # 验证关系
        db.refresh(content)
        assert content.generation_task_id == task.task_id
        print(f"✓ Content.generation_task_id updated: {content.generation_task_id}")

        return task.id

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_relationships():
    """测试模型关系"""
    print("\n=== Test 3: Model Relationships ===")
    db = SessionLocal()

    try:
        # 获取账号
        account = db.query(Account).first()
        if not account:
            print("✗ No account found")
            return False

        # 创建多个任务
        task1 = ContentGenerationTask(
            task_id=f"test-{uuid.uuid4().hex[:8]}",
            account_id=account.id,
            topic="关系测试 1",
            status="pending"
        )

        task2 = ContentGenerationTask(
            task_id=f"test-{uuid.uuid4().hex[:8]}",
            account_id=account.id,
            topic="关系测试 2",
            status="completed",
            completed_at=datetime.utcnow()
        )

        db.add_all([task1, task2])
        db.commit()

        # 测试从 Account 访问 generation_tasks
        db.refresh(account)
        task_count = len(account.generation_tasks)
        print(f"✓ Account has {task_count} generation tasks")

        # 测试从 ContentGenerationTask 访问 account
        db.refresh(task1)
        print(f"✓ Task belongs to account: {task1.account.name}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_task_status_update():
    """测试任务状态更新"""
    print("\n=== Test 4: Task Status Update ===")
    db = SessionLocal()

    try:
        # 创建任务
        account = db.query(Account).first()
        if not account:
            return False

        task = ContentGenerationTask(
            task_id=f"test-{uuid.uuid4().hex[:8]}",
            account_id=account.id,
            topic="状态更新测试",
            status="pending"
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 更新状态
        task.status = "processing"
        task.started_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        print(f"✓ Task status updated: {task.status}")
        print(f"  - Started at: {task.started_at}")

        # 完成任务
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.result = {
            "success": True,
            "content_id": 123,
            "word_count": 1500
        }
        db.commit()
        db.refresh(task)

        print(f"✓ Task completed: {task.status}")
        print(f"  - Result: {task.result}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_query_tasks():
    """测试任务查询"""
    print("\n=== Test 5: Query Tasks ===")
    db = SessionLocal()

    try:
        # 统计任务
        total_tasks = db.query(func.count(ContentGenerationTask.id)).scalar()
        print(f"✓ Total tasks: {total_tasks}")

        # 按状态统计
        pending_tasks = db.query(func.count(ContentGenerationTask.id)).filter(
            ContentGenerationTask.status == "pending"
        ).scalar()
        print(f"  - Pending: {pending_tasks}")

        completed_tasks = db.query(func.count(ContentGenerationTask.id)).filter(
            ContentGenerationTask.status == "completed"
        ).scalar()
        print(f"  - Completed: {completed_tasks}")

        # 查询特定账号的任务
        account = db.query(Account).first()
        if account:
            account_tasks = db.query(func.count(ContentGenerationTask.id)).filter(
                ContentGenerationTask.account_id == account.id
            ).scalar()
            print(f"  - Account '{account.name}' tasks: {account_tasks}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def cleanup_test_data():
    """清理测试数据"""
    print("\n=== Cleanup Test Data ===")
    db = SessionLocal()

    try:
        # 删除测试任务（task_id 以 'test-' 开头的）
        test_tasks = db.query(ContentGenerationTask).filter(
            ContentGenerationTask.task_id.like("test-%")
        ).all()

        count = len(test_tasks)
        for task in test_tasks:
            db.delete(task)

        db.commit()
        print(f"✓ Cleaned up {count} test tasks")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("=" * 60)
    print("ContentHub Async Content Generation - Model Tests")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("Task Creation", test_task_creation()))
    results.append(("Task with Content", test_task_with_content()))
    results.append(("Relationships", test_relationships()))
    results.append(("Status Update", test_task_status_update()))
    results.append(("Query Tasks", test_query_tasks()))

    # 清理
    cleanup_test_data()

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
