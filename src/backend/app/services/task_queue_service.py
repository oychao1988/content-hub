"""
任务队列服务
提供内存任务队列和多线程 Worker 处理机制
"""
import subprocess
import threading
import time
from datetime import datetime
from queue import Queue, Empty
from typing import Optional

from app.core.config import settings
from app.db.database import SessionLocal
from app.models import ContentGenerationTask
from app.utils.custom_logger import log


class MemoryTaskQueue:
    """内存任务队列（降级方案）"""

    def __init__(self, maxsize: int = 100):
        """
        初始化队列

        Args:
            maxsize: 队列最大容量
        """
        self.queue = Queue(maxsize=maxsize)
        self._lock = threading.Lock()

    def put(self, task: ContentGenerationTask, block: bool = False, timeout: Optional[float] = None) -> bool:
        """
        添加任务到队列

        Args:
            task: 任务对象
            block: 是否阻塞
            timeout: 超时时间

        Returns:
            是否成功添加
        """
        try:
            self.queue.put(task, block=block, timeout=timeout)
            return True
        except:
            return False  # 队列已满

    def get(self, block: bool = False, timeout: Optional[float] = None) -> Optional[ContentGenerationTask]:
        """
        从队列获取任务

        Args:
            block: 是否阻塞
            timeout: 超时时间

        Returns:
            任务对象，队列为空则返回 None
        """
        try:
            return self.queue.get(block=block, timeout=timeout)
        except Empty:
            return None

    def size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()

    def empty(self) -> bool:
        """队列是否为空"""
        return self.queue.empty()

    def task_done(self):
        """标记任务完成"""
        self.queue.task_done()

    def join(self):
        """等待所有任务完成"""
        self.queue.join()


class TaskQueueFactory:
    """任务队列工厂"""

    @staticmethod
    def create_queue(maxsize: int = 100) -> MemoryTaskQueue:
        """
        创建任务队列（当前只实现内存队列）

        Args:
            maxsize: 队列最大容量

        Returns:
            MemoryTaskQueue 实例

        Note:
            未来可以扩展 Redis 队列实现分布式任务队列
        """
        return MemoryTaskQueue(maxsize=maxsize)


class TaskWorker:
    """任务执行器（Worker）"""

    def __init__(self, worker_id: int, num_workers: int = 3, poll_interval: int = 5):
        """
        初始化 Worker

        Args:
            worker_id: Worker ID
            num_workers: Worker 总数
            poll_interval: 轮询间隔（秒）
        """
        self.worker_id = worker_id
        self.num_workers = num_workers
        self.poll_interval = poll_interval
        self.queue = TaskQueueFactory.create_queue()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.db_session = None

    def start(self):
        """启动 Worker"""
        if self.running:
            log.warning(f"Worker {self.worker_id} is already running")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._worker_loop,
            name=f"TaskWorker-{self.worker_id}",
            daemon=True
        )
        self.thread.start()

        log.info(f"Started TaskWorker-{self.worker_id}")

    def stop(self):
        """停止 Worker"""
        if not self.running:
            return

        self.running = False

        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                log.warning(f"TaskWorker-{self.worker_id} did not stop gracefully")

        log.info(f"Stopped TaskWorker-{self.worker_id}")

    def _worker_loop(self):
        """Worker 循环"""
        log.info(f"TaskWorker-{self.worker_id} started loop")

        while self.running:
            try:
                # 1. 从队列获取任务
                task = self.queue.get(block=False)

                if task:
                    # 2. 处理任务
                    self._process_task(task)
                    self.queue.task_done()
                else:
                    # 3. 队列为空，从数据库拉取待处理任务
                    self._fetch_pending_tasks()

                    # 4. 休眠一段时间
                    time.sleep(self.poll_interval)

            except Exception as e:
                log.error(f"Error in TaskWorker-{self.worker_id} loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)

        log.info(f"TaskWorker-{self.worker_id} exited loop")

    def _process_task(self, task: ContentGenerationTask):
        """
        处理单个任务

        Args:
            task: 任务对象
        """
        db = SessionLocal()
        try:
            log.info(f"TaskWorker-{self.worker_id} processing task {task.task_id}")

            # 重新查询任务（确保是最新的）
            task = db.query(ContentGenerationTask).filter_by(task_id=task.task_id).first()
            if not task:
                log.warning(f"Task {task.task_id} not found in database")
                return

            # 检查任务状态
            if task.status != "pending":
                log.warning(f"Task {task.task_id} is not in pending status: {task.status}")
                return

            # 提交到 content-creator CLI
            self._submit_to_creator(task)

            log.info(f"TaskWorker-{self.worker_id} submitted task {task.task_id}")

        except Exception as e:
            log.error(f"Error processing task {task.task_id}: {e}", exc_info=True)

            # 更新任务状态为失败
            task.status = "failed"
            task.error_message = str(e)
            db.commit()

        finally:
            db.close()

    def _submit_to_creator(self, task: ContentGenerationTask):
        """
        将任务提交到 content-creator CLI

        Args:
            task: 任务对象
        """
        if not settings.CREATOR_CLI_PATH:
            raise Exception("CREATOR_CLI_PATH not configured")

        # 构建命令参数
        command = [
            settings.CREATOR_CLI_PATH,
            "create",
            "--type", "content-creator",
            "--mode", "async",
            "--topic", task.topic,
            "--task-id", task.task_id
        ]

        # 可选参数
        if task.requirements:
            command.extend(["--requirements", task.requirements])
        if task.tone:
            command.extend(["--tone", task.tone])
        if task.keywords:
            command.extend(["--keywords", task.keywords])

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            # 更新任务状态
            task.status = "submitted"
            task.submitted_at = datetime.utcnow()

            log.info(f"Task {task.task_id} submitted to CLI successfully")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            log.error(f"Failed to submit task {task.task_id}: {error_msg}")
            raise Exception(f"CLI submission failed: {error_msg}")
        except subprocess.TimeoutExpired:
            log.error(f"Timeout submitting task {task.task_id}")
            raise Exception("CLI submission timeout")

    def _fetch_pending_tasks(self):
        """从数据库拉取待处理任务"""
        db = SessionLocal()
        try:
            # 查询待处理任务
            pending_tasks = db.query(ContentGenerationTask).filter(
                ContentGenerationTask.status == "pending"
            ).order_by(
                ContentGenerationTask.priority.desc(),
                ContentGenerationTask.created_at.asc()
            ).limit(10).all()

            # 添加到队列
            for task in pending_tasks:
                if not self.queue.full():
                    self.queue.put(task, block=False)
                else:
                    break  # 队列已满

            if pending_tasks:
                log.info(f"TaskWorker-{self.worker_id} fetched {len(pending_tasks)} pending tasks")

        finally:
            db.close()

    def add_task(self, task: ContentGenerationTask) -> bool:
        """
        添加任务到队列

        Args:
            task: 任务对象

        Returns:
            是否成功添加
        """
        return self.queue.put(task, block=False)

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.queue.size()


class TaskWorkerPool:
    """任务 Worker 池"""

    def __init__(self, num_workers: int = 3):
        """
        初始化 Worker 池

        Args:
            num_workers: Worker 数量
        """
        self.num_workers = num_workers
        self.workers: list[TaskWorker] = []

    def start(self):
        """启动所有 Worker"""
        for i in range(self.num_workers):
            worker = TaskWorker(worker_id=i, num_workers=self.num_workers)
            worker.start()
            self.workers.append(worker)

        log.info(f"Started TaskWorkerPool with {self.num_workers} workers")

    def stop(self):
        """停止所有 Worker"""
        for worker in self.workers:
            worker.stop()

        self.workers.clear()
        log.info("Stopped TaskWorkerPool")

    def add_task(self, task: ContentGenerationTask) -> bool:
        """
        添加任务到任意 Worker 队列

        Args:
            task: 任务对象

        Returns:
            是否成功添加
        """
        # 轮询选择 Worker
        for worker in self.workers:
            if worker.add_task(task):
                return True

        return False  # 所有队列都已满

    def get_total_queue_size(self) -> int:
        """获取所有 Worker 队列总大小"""
        return sum(worker.get_queue_size() for worker in self.workers)

    def get_status(self) -> dict:
        """
        获取 Worker 池状态

        Returns:
            状态字典
        """
        return {
            "num_workers": self.num_workers,
            "active_workers": sum(1 for w in self.workers if w.running),
            "total_queue_size": self.get_total_queue_size(),
            "worker_statuses": [
                {
                    "worker_id": w.worker_id,
                    "running": w.running,
                    "queue_size": w.get_queue_size()
                }
                for w in self.workers
            ]
        }


# 全局 Worker 池实例（单例）
_global_worker_pool: Optional[TaskWorkerPool] = None
_pool_lock = threading.Lock()


def get_task_worker_pool(num_workers: int = 3) -> TaskWorkerPool:
    """
    获取任务 Worker 池实例（单例模式）

    Args:
        num_workers: Worker 数量（仅首次创建时有效）

    Returns:
        TaskWorkerPool 实例
    """
    global _global_worker_pool

    with _pool_lock:
        if _global_worker_pool is None:
            _global_worker_pool = TaskWorkerPool(num_workers=num_workers)
            log.info(f"Created global TaskWorkerPool with {num_workers} workers")

        return _global_worker_pool


def start_worker_pool(num_workers: int = 3):
    """
    启动 Worker 池

    Args:
        num_workers: Worker 数量
    """
    pool = get_task_worker_pool(num_workers)
    pool.start()


def stop_worker_pool():
    """停止 Worker 池"""
    global _global_worker_pool

    with _pool_lock:
        if _global_worker_pool:
            _global_worker_pool.stop()
            _global_worker_pool = None
