#!/usr/bin/env python
"""
异步内容生成核心服务简单验证脚本

验证以下内容：
1. 所有服务可以正常导入
2. 服务实例化正常
3. 基本方法可以调用

运行方式：
    python verify_async_services_simple.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_imports():
    """测试所有服务导入"""
    print_section("1. 测试服务导入")

    try:
        from app.services.async_content_generation_service import AsyncContentGenerationService
        from app.services.task_status_poller import TaskStatusPoller
        from app.services.task_result_handler import TaskResultHandler
        from app.services.task_queue_service import (
            MemoryTaskQueue,
            TaskQueueFactory,
            TaskWorker,
            TaskWorkerPool,
            get_task_worker_pool
        )

        print("✓ 所有服务导入成功\n")

        print("导入的服务类：")
        print(f"  - AsyncContentGenerationService")
        print(f"  - TaskStatusPoller")
        print(f"  - TaskResultHandler")
        print(f"  - MemoryTaskQueue")
        print(f"  - TaskQueueFactory")
        print(f"  - TaskWorker")
        print(f"  - TaskWorkerPool")
        print(f"  - get_task_worker_pool")

        return True

    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_instantiation():
    """测试服务实例化"""
    print_section("2. 测试服务实例化")

    try:
        from app.services.async_content_generation_service import AsyncContentGenerationService
        from app.services.task_status_poller import TaskStatusPoller
        from app.services.task_result_handler import TaskResultHandler
        from app.services.task_queue_service import (
            MemoryTaskQueue,
            TaskQueueFactory,
            TaskWorker,
            TaskWorkerPool
        )
        from app.db.database import SessionLocal

        # 测试 AsyncContentGenerationService
        db = SessionLocal()
        try:
            async_service = AsyncContentGenerationService(db)
            print(f"✓ AsyncContentGenerationService 实例化成功")
            print(f"  - 默认超时时间: {async_service.DEFAULT_TIMEOUT_MINUTES} 分钟")
        finally:
            db.close()

        # 测试 TaskStatusPoller
        poller = TaskStatusPoller(poll_interval=30)
        print(f"✓ TaskStatusPoller 实例化成功")
        print(f"  - 轮询间隔: {poller.poll_interval} 秒")

        # 测试 TaskResultHandler
        handler = TaskResultHandler()
        print(f"✓ TaskResultHandler 实例化成功")

        # 测试 MemoryTaskQueue
        queue = MemoryTaskQueue(maxsize=100)
        print(f"✓ MemoryTaskQueue 实例化成功")
        print(f"  - 最大容量: {queue.queue.maxsize}")

        # 测试 TaskQueueFactory
        queue2 = TaskQueueFactory.create_queue(maxsize=50)
        print(f"✓ TaskQueueFactory 创建队列成功")
        print(f"  - 队列容量: {queue2.queue.maxsize}")

        # 测试 TaskWorker（不启动）
        worker = TaskWorker(worker_id=0, num_workers=3)
        print(f"✓ TaskWorker 实例化成功")
        print(f"  - Worker ID: {worker.worker_id}")
        print(f"  - Worker 总数: {worker.num_workers}")

        # 测试 TaskWorkerPool（不启动）
        pool = TaskWorkerPool(num_workers=3)
        print(f"✓ TaskWorkerPool 实例化成功")
        print(f"  - Worker 数量: {pool.num_workers}")

        return True

    except Exception as e:
        print(f"✗ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_queue_operations():
    """测试队列基本操作"""
    print_section("3. 测试队列操作")

    try:
        from app.services.task_queue_service import MemoryTaskQueue
        from app.models import ContentGenerationTask
        from app.db.database import SessionLocal
        from app.models import Account, Customer, Platform

        db = SessionLocal()
        try:
            # 创建测试数据（使用唯一名称避免冲突）
            import time
            unique_id = int(time.time() * 1000)

            customer = Customer(
                name=f"测试客户_{unique_id}",
                contact_name="测试联系人",
                contact_email="test@example.com"
            )
            db.add(customer)
            db.flush()

            platform = Platform(
                name=f"测试平台_{unique_id}",
                code=f"test_platform_{unique_id}",
                description="测试平台"
            )
            db.add(platform)
            db.flush()

            account = Account(
                name=f"测试账号_{unique_id}",
                customer_id=customer.id,
                platform_id=platform.id,
                directory_name=f"test_account_{unique_id}"
            )
            db.add(account)
            db.commit()
            db.refresh(account)

            # 创建任务对象
            task = ContentGenerationTask(
                task_id=f"test-task-{unique_id}",
                account_id=account.id,
                topic="队列测试任务",
                status="pending"
            )

            # 测试队列
            queue = MemoryTaskQueue(maxsize=10)

            # 测试放入
            result = queue.put(task, block=False)
            assert result is True, "放入队列失败"
            print(f"✓ 任务放入队列成功: {task.task_id}")

            # 测试大小
            size = queue.size()
            assert size == 1, f"队列大小应为1，实际为{size}"
            print(f"✓ 队列大小正确: {size}")

            # 测试是否为空
            assert not queue.empty(), "队列不应为空"
            print(f"✓ 队列非空检查通过")

            # 测试获取
            retrieved_task = queue.get(block=False)
            assert retrieved_task is not None, "获取任务失败"
            assert retrieved_task.task_id == task.task_id, "获取的任务不匹配"
            print(f"✓ 从队列获取任务成功: {retrieved_task.task_id}")

            # 测试空队列
            assert queue.empty(), "队列应为空"
            print(f"✓ 队列为空检查通过")

            # 清理测试数据（只清理已持久化的对象）
            db.delete(account)
            db.delete(platform)
            db.delete(customer)
            db.commit()

            print(f"✓ 测试数据清理完成")

            return True

        finally:
            db.close()

    except Exception as e:
        print(f"✗ 队列操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_worker_pool():
    """测试 Worker 池基本操作"""
    print_section("4. 测试 Worker 池")

    try:
        from app.services.task_queue_service import TaskWorkerPool

        # 创建 Worker 池
        pool = TaskWorkerPool(num_workers=2)
        print(f"✓ 创建 Worker 池（2个Worker）")

        # 启动
        pool.start()
        print(f"✓ 启动 Worker 池")

        # 等待一小段时间确保线程启动
        import time
        time.sleep(0.5)

        # 获取状态
        status = pool.get_status()
        print(f"✓ 获取 Worker 池状态:")
        print(f"  - Worker 总数: {status['num_workers']}")
        print(f"  - 活跃 Worker: {status['active_workers']}")
        print(f"  - 队列总大小: {status['total_queue_size']}")

        # 验证状态
        assert status['num_workers'] == 2, "Worker 数量不正确"
        assert status['active_workers'] == 2, "活跃 Worker 数量不正确"
        print(f"✓ Worker 池状态验证通过")

        # 打印每个 Worker 的状态
        for worker_status in status['worker_statuses']:
            print(f"  - Worker {worker_status['worker_id']}: running={worker_status['running']}, queue_size={worker_status['queue_size']}")

        # 停止
        pool.stop()
        print(f"✓ 停止 Worker 池")

        # 验证停止
        status = pool.get_status()
        assert status['active_workers'] == 0, "Worker 未完全停止"
        print(f"✓ Worker 池已完全停止")

        return True

    except Exception as e:
        print(f"✗ Worker 池测试失败: {e}")
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
    results["服务导入"] = test_imports()
    results["服务实例化"] = test_service_instantiation()
    results["队列操作"] = test_queue_operations()
    results["Worker 池"] = test_worker_pool()

    # 打印总结
    print_section("测试总结")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n核心服务功能验证完成：")
        print("  ✓ AsyncContentGenerationService - 任务管理服务")
        print("  ✓ TaskStatusPoller - 状态轮询器")
        print("  ✓ TaskResultHandler - 结果处理器")
        print("  ✓ MemoryTaskQueue - 内存任务队列")
        print("  ✓ TaskWorkerPool - 任务 Worker 池")
        print("\n所有核心组件已就绪，可以进入下一阶段开发。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
