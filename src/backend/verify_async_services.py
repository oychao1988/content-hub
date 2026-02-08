#!/usr/bin/env python
"""
验证异步内容生成核心服务的基本功能

运行方式：
    python verify_async_services.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models import Account, Customer, Platform, ContentGenerationTask
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.services.task_status_poller import TaskStatusPoller
from app.services.task_result_handler import TaskResultHandler
from app.services.task_queue_service import MemoryTaskQueue, TaskQueueFactory, TaskWorkerPool


def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_service_imports():
    """测试服务导入"""
    print_section("1. 测试服务导入")

    try:
        from app.services.async_content_generation_service import AsyncContentGenerationService
        from app.services.task_status_poller import TaskStatusPoller
        from app.services.task_result_handler import TaskResultHandler
        from app.services.task_queue_service import MemoryTaskQueue, TaskQueueFactory, TaskWorkerPool

        print("✓ 所有服务导入成功")
        print(f"  - AsyncContentGenerationService: {AsyncContentGenerationService}")
        print(f"  - TaskStatusPoller: {TaskStatusPoller}")
        print(f"  - TaskResultHandler: {TaskResultHandler}")
        print(f"  - MemoryTaskQueue: {MemoryTaskQueue}")
        print(f"  - TaskWorkerPool: {TaskWorkerPool}")
        return True
    except Exception as e:
        print(f"✗ 服务导入失败: {e}")
        return False


def test_async_service_basic():
    """测试 AsyncContentGenerationService 基本功能"""
    print_section("2. 测试 AsyncContentGenerationService")

    db = SessionLocal()
    try:
        # 创建测试数据
        customer = Customer(
            name="测试客户",
            contact_name="测试联系人",
            contact_email="test@example.com",
            contact_phone="13800138000"
        )
        db.add(customer)
        db.flush()

        platform = Platform(
            name="微信公众号",
            code="wechat_mp",
            description="测试平台"
        )
        db.add(platform)
        db.flush()

        account = Account(
            name="测试公众号",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name="test_verify_account"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        print(f"✓ 创建测试账号: {account.name} (ID: {account.id})")

        # 测试服务
        service = AsyncContentGenerationService(db)

        # 创建任务（不提交到 CLI，只创建数据库记录）
        task = ContentGenerationTask(
            task_id="verify-test-task-001",
            account_id=account.id,
            topic="验证测试选题",
            category="测试",
            priority=5,
            auto_approve=True,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"✓ 创建测试任务: {task.task_id}")

        # 查询任务状态
        status = service.get_task_status(task.task_id)
        assert status is not None, "任务状态查询失败"
        assert status["task_id"] == task.task_id, "任务ID不匹配"
        assert status["status"] == "pending", "任务状态不正确"

        print(f"✓ 查询任务状态: {status['status']}")

        # 列出任务
        tasks = service.list_tasks(account_id=account.id)
        assert len(tasks) >= 1, "任务列表为空"

        print(f"✓ 列出任务: 找到 {len(tasks)} 个任务")

        # 取消任务
        result = service.cancel_task(task.task_id)
        assert result is True, "取消任务失败"

        print(f"✓ 取消任务成功")

        # 验证取消后的状态
        task = db.query(ContentGenerationTask).filter_by(task_id=task.task_id).first()
        assert task.status == "cancelled", "任务状态未更新为 cancelled"

        print(f"✓ 任务状态已更新为: {task.status}")

        # 清理测试数据
        db.delete(task)
        db.delete(account)
        db.delete(platform)
        db.delete(customer)
        db.commit()

        print(f"✓ 清理测试数据完成")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_result_handler():
    """测试 TaskResultHandler"""
    print_section("3. 测试 TaskResultHandler")

    db = SessionLocal()
    try:
        # 创建测试数据
        customer = Customer(
            name="测试客户2",
            contact_name="测试联系人2",
            contact_email="test2@example.com",
            contact_phone="13800138001"
        )
        db.add(customer)
        db.flush()

        platform = Platform(
            name="微信公众号2",
            code="wechat_mp2",
            description="测试平台2"
        )
        db.add(platform)
        db.flush()

        account = Account(
            name="测试公众号2",
            customer_id=customer.id,
            platform_id=platform.id,
            directory_name="test_verify_account2"
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        print(f"✓ 创建测试账号: {account.name} (ID: {account.id})")

        # 创建任务
        task = ContentGenerationTask(
            task_id="verify-result-test-001",
            account_id=account.id,
            topic="结果处理器测试",
            category="测试",
            priority=5,
            auto_approve=False,  # 不自动审核
            status="processing"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"✓ 创建测试任务: {task.task_id}")

        # 测试结果处理器
        handler = TaskResultHandler()

        # 模拟成功结果
        result = {
            "content": "这是测试生成的内容",
            "htmlContent": "<p>这是测试生成的内容</p>",
            "images": ["test1.jpg", "test2.jpg"],
            "qualityScore": 0.85
        }

        # 处理成功
        content = handler.handle_success(db, task, result)
        assert content is not None, "内容创建失败"

        print(f"✓ 处理成功任务，创建内容: {content.id}")
        print(f"  - 标题: {content.title}")
        print(f"  - 字数: {content.word_count}")
        print(f"  - 审核状态: {content.review_status}")

        # 验证任务状态
        db.refresh(task)
        assert task.status == "completed", "任务状态未更新"
        assert task.content_id == content.id, "内容关联失败"

        print(f"✓ 任务状态已更新: {task.status}")

        # 清理测试数据
        db.delete(content)
        db.delete(task)
        db.delete(account)
        db.delete(platform)
        db.delete(customer)
        db.commit()

        print(f"✓ 清理测试数据完成")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_task_queue():
    """测试 MemoryTaskQueue"""
    print_section("4. 测试 MemoryTaskQueue")

    try:
        # 创建队列
        queue = MemoryTaskQueue(maxsize=10)
        print(f"✓ 创建队列 (maxsize=10)")

        # 创建测试任务
        db = SessionLocal()
        try:
            customer = Customer(
                name="测试客户3",
                contact_name="测试联系人3",
                contact_email="test3@example.com"
            )
            db.add(customer)
            db.flush()

            platform = Platform(name="平台3", code="platform3", description="测试")
            db.add(platform)
            db.flush()

            account = Account(
                name="账号3",
                customer_id=customer.id,
                platform_id=platform.id,
                directory_name="account3"
            )
            db.add(account)
            db.commit()
            db.refresh(account)

            # 创建任务对象
            task = ContentGenerationTask(
                task_id="queue-test-001",
                account_id=account.id,
                topic="队列测试",
                status="pending"
            )

            # 测试放入
            result = queue.put(task)
            assert result is True, "放入队列失败"
            print(f"✓ 放入任务到队列: {task.task_id}")

            # 测试大小
            size = queue.size()
            assert size == 1, f"队列大小不正确: {size}"
            print(f"✓ 队列大小: {size}")

            # 测试获取
            retrieved_task = queue.get()
            assert retrieved_task is not None, "从队列获取任务失败"
            assert retrieved_task.task_id == task.task_id, "获取的任务不匹配"
            print(f"✓ 从队列获取任务: {retrieved_task.task_id}")

            # 测试空队列
            assert queue.empty(), "队列应该为空"
            print(f"✓ 队列为空")

            # 清理
            db.delete(task)
            db.delete(account)
            db.delete(platform)
            db.delete(customer)
            db.commit()

        finally:
            db.close()

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_worker_pool():
    """测试 TaskWorkerPool 基本功能"""
    print_section("5. 测试 TaskWorkerPool")

    try:
        # 创建 Worker 池
        pool = TaskWorkerPool(num_workers=2)
        print(f"✓ 创建 Worker 池 (num_workers=2)")

        # 启动
        pool.start()
        print(f"✓ 启动 Worker 池")

        # 获取状态
        status = pool.get_status()
        assert status["num_workers"] == 2, "Worker 数量不正确"
        assert status["active_workers"] == 2, "活跃 Worker 数量不正确"
        print(f"✓ Worker 池状态:")
        print(f"  - 总数: {status['num_workers']}")
        print(f"  - 活跃: {status['active_workers']}")
        print(f"  - 队列大小: {status['total_queue_size']}")

        # 停止
        pool.stop()
        print(f"✓ 停止 Worker 池")

        # 验证停止
        status = pool.get_status()
        assert status["active_workers"] == 0, "Worker 未停止"
        print(f"✓ Worker 已全部停止")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  异步内容生成核心服务验证")
    print("="*60)

    results = {}

    # 运行所有测试
    results["服务导入"] = test_service_imports()
    results["AsyncContentGenerationService"] = test_async_service_basic()
    results["TaskResultHandler"] = test_result_handler()
    results["MemoryTaskQueue"] = test_task_queue()
    results["TaskWorkerPool"] = test_worker_pool()

    # 打印总结
    print_section("测试总结")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！核心服务功能正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
