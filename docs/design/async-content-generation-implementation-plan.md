# 异步内容生成系统 - 执行计划

## 📋 项目概述

将 ContentHub 从同步内容生成改造为异步任务模式，实现：
- 定时任务非阻塞执行
- 批量并发生成内容
- 自动化业务流程（生成→审核→发布）
- 完善的任务监控和重试机制
- 队列降级机制（Redis 优先，内存降级）

**技术选型**：
- **任务队列**：Redis BullMQ（优先）或 内存队列（降级）
- **状态监控**：轮询机制（每30秒）
- **content-creator 集成**：CLI 调用（`--mode async`）
- **自动审核**：默认开启，支持任务级别配置

**预期收益**：
- 定时任务响应时间：从 **12分钟** → **3秒**
- 批量生成效率：从 **40分钟（10篇）** → **4分钟**
- 系统吞吐量提升 **10倍**

---

## 🎯 实施阶段

### 阶段 0：准备工作（1天）

#### 任务清单
- [x] 确认 content-creator 异步 API 规范
  - [x] CLI 异步命令：`content-creator create --mode async`
  - [x] 状态查询：`content-creator status --task-id <uuid>`
  - [x] 结果获取：`content-creator result --task-id <uuid>`
  - [x] BullMQ 队列（content-creator 内部使用）

- [ ] 搭建开发环境
  - [ ] 创建开发分支 `feature/async-content-generation`
  - [ ] 准备测试账号和数据
  - [ ] 配置开发环境变量

- [ ] 技术选型确认
  - [x] 队列方案：Redis BullMQ（优先）+ 内存队列（降级）
  - [x] Worker 实现：Python 线程池
  - [x] 状态监控：CLI 轮询机制
  - [x] 自动审核：默认开启，任务级别可配置

**输出物**：
- ✅ content-creator CLI 集成方案
- ✅ 队列降级机制设计
- 开发环境就绪

---

### 阶段 1：数据库模型改造（1天）

#### 1.1 创建 ContentGenerationTask 模型

**文件**：`src/backend/app/models/content_generation_task.py`

```python
class ContentGenerationTask(Base):
    __tablename__ = "content_generation_tasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # 任务参数
    topic = Column(String(500))
    keywords = Column(String(500))
    category = Column(String(100))
    requirements = Column(Text)
    tone = Column(String(50))

    # 任务状态
    status = Column(String(50), default="pending", index=True)
    priority = Column(Integer, default=5)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 时间戳
    submitted_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    timeout_at = Column(DateTime)

    # 结果
    result = Column(JSON)
    error_message = Column(Text)

    # 自动流程配置
    auto_approve = Column(Boolean, default=True)  # 默认自动审核

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**任务**：
- [ ] 创建模型文件
- [ ] 添加索引（task_id, status, account_id, submitted_at）
- [ ] 添加关联关系（Content, Account）
- [ ] 添加 auto_approve 字段
- [ ] 编写迁移脚本

#### 1.2 修改 Content 模型

**文件**：`src/backend/app/models/content.py`

```python
# 新增字段
generation_task_id = Column(String(100), index=True)
auto_publish = Column(Boolean, default=False)
scheduled_publish_at = Column(DateTime)
```

**任务**：
- [ ] 添加新字段
- [ ] 编写迁移脚本
- [ ] 更新 Schema

**输出物**：
- ✅ 数据库模型文件
- ✅ 迁移脚本
- ✅ 更新的 Schema 定义

---

### 阶段 2：核心服务开发（3-4天）

#### 2.1 异步任务服务

**文件**：`src/backend/app/services/async_content_generation_service.py`

**功能模块**：

**模块 A：任务管理**
```python
class AsyncContentGenerationService:
    # 任务提交
    def submit_task(account_id, topic, keywords, **options) -> str
    # 批量提交
    def submit_batch_tasks(tasks: List[Dict]) -> List[str]
    # 查询任务状态
    def get_task_status(task_id: str) -> Dict
    # 列出任务
    def list_tasks(filters: Dict) -> List[ContentGenerationTask]
    # 取消任务
    def cancel_task(task_id: str) -> bool
```

**模块 B：状态轮询**
```python
class TaskStatusPoller:
    # 轮询进行中的任务
    async def poll_running_tasks()
    # 查询外部API
    def check_task_status(task_id: str) -> Dict
    # 更新数据库状态
    def update_task_status(task_id: str, status: Dict)
```

**模块 C：结果处理**
```python
class TaskResultHandler:
    # 处理成功结果
    def handle_success(task: ContentGenerationTask, result: Dict)
    # 处理失败结果
    def handle_failure(task: ContentGenerationTask, error: str)
    # 创建Content记录
    def create_content_from_result(result: Dict) -> Content
    # 自动审核
    def auto_approve_content(content_id: int) -> bool
    # 添加到发布池
    def add_to_publish_pool(content_id: int, priority: int) -> bool
```

**任务**：
- [ ] 实现 AsyncContentGenerationService
- [ ] 实现 TaskStatusPoller
- [ ] 实现 TaskResultHandler
- [ ] 编写单元测试

#### 2.2 任务队列和 Worker（降级机制）

**文件**：`src/backend/app/services/task_queue_service.py`

**实现方案**：Redis + 内存双队列

```python
class TaskQueueFactory:
    """任务队列工厂，支持降级"""

    @staticmethod
    def create_queue():
        # 优先使用 Redis 队列
        if config.REDIS_ENABLED:
            try:
                redis_queue = RedisTaskQueue(config.REDIS_URL)
                # 测试连接
                redis_queue.ping()
                logger.info("✅ 使用 Redis 任务队列")
                return redis_queue
            except Exception as e:
                logger.warning(f"⚠️ Redis 连接失败，降级到内存队列: {e}")

        # 降级到内存队列
        logger.info("✅ 使用内存任务队列")
        return MemoryTaskQueue(maxsize=100)

class RedisTaskQueue:
    """Redis 队列（使用 Redis 或 BullMQ）"""

    def __init__(self, redis_url):
        import redis
        self.redis = redis.from_url(redis_url)
        self.queue_key = "content_generation_tasks"

    def enqueue(self, task_id: str, priority: int = 5):
        """添加任务到队列（支持优先级）"""
        score = priority  # 优先级作为分数
        self.redis.zadd(self.queue_key, {task_id: score})

    def dequeue(self) -> str:
        """从队列取出任务（FIFO + 优先级）"""
        # ZRANGEBYSCORE ... LIMIT 0 1
        result = self.redis.zrange(self.queue_key, 0, 0, withscores=False)
        if result:
            task_id = result[0]
            self.redis.zrem(self.queue_key, task_id)
            return task_id
        return None

class MemoryTaskQueue:
    """内存队列（降级方案）"""

    def __init__(self, maxsize=100):
        from queue import PriorityQueue
        self.queue = PriorityQueue(maxsize=maxsize)

    def enqueue(self, task_id: str, priority: int = 5):
        """添加任务到队列"""
        self.queue.put((priority, task_id), block=False)

    def dequeue(self) -> str:
        """从队列取出任务"""
        priority, task_id = self.queue.get(block=False)
        return task_id
```

**Worker 实现**：

```python
class TaskWorker:
    """任务执行器（线程池）"""

    def __init__(self, queue, num_workers=5):
        from concurrent.futures import ThreadPoolExecutor
        self.queue = queue
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

    def start(self):
        """启动 Worker"""
        while True:
            try:
                task_id = self.queue.dequeue()
                if task_id:
                    # 提交到线程池执行
                    self.executor.submit(self._process_task, task_id)
            except Exception as e:
                logger.error(f"Worker 错误: {e}")

    def _process_task(self, task_id: str):
        """处理单个任务"""
        # 1. 调用 content-creator CLI
        # 2. 更新任务状态
        # 3. 处理结果
        pass
```

**任务**：
- [x] 选择技术方案（Redis + 内存双队列）
- [ ] 实现 TaskQueueFactory
- [ ] 实现 RedisTaskQueue
- [ ] 实现 MemoryTaskQueue
- [ ] 实现 TaskWorker
- [ ] 实现任务提交接口
- [ ] 编写单元测试

**输出物**：
- ✅ 异步任务服务（3个模块）
- ✅ 任务队列和 Worker（Redis + 内存双队列）
- ✅ 单元测试和集成测试

---

### 阶段 3：CLI 命令改造（2天）

#### 3.1 改造 generate 命令

**文件**：`src/backend/cli/modules/content.py`

**修改前**：
```python
def generate(...):
    # 同步调用，阻塞等待
    result = content_creator_service.create_content(...)
```

**修改后**：
```python
def generate(
    ...,
    async_mode: bool = typer.Option(False, "--async", help="异步模式"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="等待完成")
):
    if async_mode:
        task_id = async_service.submit_task(...)
        if wait:
            # 等待完成（带进度条）
            await_task_completion(task_id)
        else:
            print(f"✅ 任务已提交 (task_id: {task_id})")
            return task_id
    else:
        # 保留同步模式（兼容）
        result = content_creator_service.create_content(...)
```

**任务**：
- [ ] 添加 --async 参数
- [ ] 添加 --wait/--no-wait 参数
- [ ] 实现异步提交逻辑
- [ ] 实现等待逻辑（带进度显示）

#### 3.2 新增任务管理命令

**文件**：`src/backend/cli/modules/tasks.py`（新建）

```python
# 查询任务状态
@app.command()
def task_status(task_id: str):
    """查询任务状态"""

# 列出任务
@app.command()
def task_list(
    --status: str = None,
    --account-id: int = None,
    --limit: int = 20
):
    """列出任务"""

# 取消任务
@app.command()
def task_cancel(task_id: str):
    """取消任务"""

# 重试任务
@app.command()
def task_retry(task_id: str):
    """重试失败的任务"""

# 任务统计
@app.command()
def task_stats():
    """任务统计信息"""
```

**任务**：
- [ ] 创建 tasks.py 模块
- [ ] 实现所有命令
- [ ] 集成到主 CLI
- [ ] 编写帮助文档

#### 3.3 改造 batch-generate 命令

**文件**：`src/backend/cli/modules/content.py`

**修改前**：
```python
def batch_generate(...):
    for i in range(count):
        generate_sync(...)  # 串行执行
```

**修改后**：
```python
def batch_generate(..., async_mode: bool = True):
    if async_mode:
        # 并发提交所有任务
        task_ids = []
        for i in range(count):
            task_id = async_service.submit_task(...)
            task_ids.append(task_id)
        print(f"✅ 已提交 {count} 个任务")
        return task_ids
    else:
        # 保留串行模式
        for i in range(count):
            generate_sync(...)
```

**任务**：
- [ ] 添加 --async 参数
- [ ] 实现并发提交逻辑
- [ ] 添加进度显示
- [ ] 测试批量功能

**输出物**：
- ✅ 改造后的 generate 命令
- ✅ 新增 tasks 模块和命令
- ✅ 改造后的 batch-generate 命令
- ✅ CLI 更新文档

---

### 阶段 4：定时任务改造（2天）

#### 4.1 新增异步生成任务类型

**文件**：`src/backend/app/modules/scheduler/services.py`

**新增任务类型**：
```python
# 在 TaskType 枚举中添加
class TaskType(str, Enum):
    CONTENT_GENERATION = "content_generation"  # 原有（同步）
    ASYNC_CONTENT_GENERATION = "async_content_generation"  # 新增（异步）
    PUBLISHING = "publishing"
    # ...
```

#### 4.2 实现异步生成任务执行器

**文件**：`src/backend/app/services/executors/async_content_generation_executor.py`（新建）

```python
class AsyncContentGenerationExecutor:
    def execute(self, job_config: Dict) -> Dict:
        """执行异步生成任务"""
        account_id = job_config['account_id']
        count = job_config.get('count', 1)

        # 批量提交任务
        task_ids = []
        for i in range(count):
            topic = self._generate_topic(account_id)
            task_id = async_service.submit_task(
                account_id=account_id,
                topic=topic,
                **job_config
            )
            task_ids.append(task_id)

        return {
            "success": True,
            "submitted_tasks": len(task_ids),
            "task_ids": task_ids
        }
```

**任务**：
- [ ] 创建执行器文件
- [ ] 实现任务执行逻辑
- [ ] 集成到调度器
- [ ] 测试定时触发

#### 4.3 改造发布池任务

**文件**：`src/backend/app/services/executors/publishing_executor.py`

**优化**：
- 支持批量发布
- 失败自动重试
- 状态更新

**任务**：
- [ ] 优化发布逻辑
- [ ] 添加批量发布支持
- [ ] 测试自动发布

**输出物**：
- ✅ 新增异步任务类型
- ✅ 异步生成任务执行器
- ✅ 优化的发布池任务
- ✅ 定时任务测试用例

---

### 阶段 5：配置和监控（1天）

#### 5.1 配置文件

**文件**：`src/backend/.env`

**新增配置**：
```bash
# 异步任务配置
ASYNC_MAX_CONCURRENT_TASKS=5
ASYNC_TASK_TIMEOUT=1800
ASYNC_POLL_INTERVAL=30
ASYNC_AUTO_APPROVE=true  # 默认开启自动审核
ASYNC_AUTO_ADD_TO_POOL=true

# 任务队列配置（降级机制）
TASK_QUEUE_TYPE=auto  # auto | redis | memory
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true  # 自动检测 Redis 可用性

# content-creator 配置
CREATOR_CLI_PATH=/path/to/content-creator
CREATOR_MODE=async
```

**任务**：
- [ ] 添加配置项
- [ ] 更新 config.py
- [ ] 实现 Redis 自动检测
- [ ] 编写配置文档

#### 5.2 监控和告警

**文件**：`src/backend/app/services/monitoring_service.py`（新建）

**功能**：
```python
class MonitoringService:
    def get_task_statistics(self) -> Dict:
        """获取任务统计"""

    def get_queue_status(self) -> Dict:
        """获取队列状态"""

    def check_health(self) -> Dict:
        """健康检查"""

    def send_alert(self, alert: Dict):
        """发送告警"""
```

**任务**：
- [ ] 实现监控服务
- [ ] 添加监控端点
- [ ] 实现告警规则
- [ ] 集成通知渠道

#### 5.3 Dashboard

**新增 CLI 命令**：
```bash
# 任务监控面板
contenthub tasks monitor

# 实时统计
contenthub tasks stats --realtime
```

**任务**：
- [ ] 实现监控命令
- [ ] 添加实时统计
- [ ] 美化输出格式

**输出物**：
- ✅ 配置文件和文档
- ✅ 监控服务
- ✅ Dashboard 命令

---

### 阶段 6：测试和文档（2-3天）

#### 6.1 单元测试

**测试覆盖**：
- [ ] AsyncContentGenerationService 测试
- [ ] TaskStatusPoller 测试
- [ ] TaskResultHandler 测试
- [ ] TaskQueueService 测试
- [ ] Webhook 端点测试
- [ ] Executor 测试

**目标覆盖率**：> 80%

#### 6.2 集成测试

**测试场景**：
- [ ] 完整流程测试（提交→生成→审核→发布）
- [ ] 批量任务测试
- [ ] 失败重试测试
- [ ] 超时处理测试
- [ ] 并发测试
- [ ] Webhook 回调测试

**测试文件**：
```
tests/integration/test_async_content_flow.py
tests/integration/test_batch_generation.py
tests/integration/test_error_handling.py
```

#### 6.3 性能测试

**测试指标**：
- [ ] 定时任务响应时间（目标：< 5秒）
- [ ] 并发任务处理能力（目标：5个并发）
- [ ] 任务队列吞吐量（目标：> 100任务/小时）
- [ ] 内存占用（目标：< 500MB）

#### 6.4 文档更新

**文档列表**：
- [ ] 更新 CLAUDE.md（新增异步命令）
- [ ] 更新 API 文档（新增 Webhook 端点）
- [ ] 创建用户指南（异步任务使用）
- [ ] 创建运维手册（监控和告警）
- [ ] 更新 CLI 参考文档
- [ ] 创建迁移指南（从同步到异步）

**输出物**：
- ✅ 单元测试套件
- ✅ 集成测试套件
- ✅ 性能测试报告
- ✅ 完整文档

---

### 阶段 7：部署和上线（2天）

#### 7.1 数据库迁移

**步骤**：
```bash
# 1. 备份数据库
python -m cli.main db backup

# 2. 执行迁移
alembic upgrade head

# 3. 验证表结构
python -m cli.main db validate
```

**任务**：
- [ ] 编写迁移脚本
- [ ] 测试迁移（开发环境）
- [ ] 测试迁移（测试环境）
- [ ] 执行迁移（生产环境）

#### 7.2 灰度发布

**阶段 1：内部测试**（1天）
- [ ] 部署到开发环境
- [ ] 运行集成测试
- [ ] 手动测试核心流程
- [ ] 修复发现的问题

**阶段 2：小范围试用**（2-3天）
- [ ] 部署到测试环境
- [ ] 选择1-2个账号启用异步模式
- [ ] 监控任务执行情况
- [ ] 收集反馈和优化

**阶段 3：全量上线**（1周后）
- [ ] 所有账号切换到异步模式
- [ ] 保留同步模式作为降级方案
- [ ] 持续监控和优化

#### 7.3 回滚方案

**触发条件**：
- 任务失败率 > 30%
- 系统崩溃或严重性能问题
- 数据不一致

**回滚步骤**：
```bash
# 1. 停止异步 Worker
python -m cli.main scheduler stop

# 2. 切换回同步模式
# 修改配置：ASYNC_ENABLED=false

# 3. 重启服务
make restart

# 4. 验证同步模式正常
python -m cli.main content generate --sync ...
```

**任务**：
- [ ] 编写回滚脚本
- [ ] 测试回滚流程
- [ ] 准备应急联系人

**输出物**：
- ✅ 数据库迁移完成
- ✅ 生产环境部署
- ✅ 监控和告警就绪
- ✅ 回滚方案就绪

---

## 📊 进度管理

### 时间估算

| 阶段 | 预估时间 | 依赖 |
|------|----------|------|
| 阶段 0：准备工作 | 1天 | - |
| 阶段 1：数据库模型 | 1天 | 阶段 0 |
| 阶段 2：核心服务 | 3-4天 | 阶段 1 |
| 阶段 3：CLI 改造 | 2天 | 阶段 2 |
| 阶段 4：定时任务 | 2天 | 阶段 2 |
| 阶段 5：配置监控 | 1天 | 阶段 4 |
| 阶段 6：测试文档 | 2-3天 | 阶段 2-5 |
| 阶段 7：部署上线 | 2天 | 阶段 6 |
| **总计** | **14-18天** | - |

### 里程碑

- **M1**（第 2天）：数据库模型完成
- **M2**（第 6天）：核心服务开发完成
- **M3**（第 10天）：CLI 和定时任务改造完成
- **M4**（第 13天）：测试通过，文档完成
- **M5**（第 15天）：生产环境上线

---

## 🎯 成功标准

### 功能指标
- ✅ 定时任务非阻塞执行
- ✅ 支持异步任务提交和状态查询
- ✅ 支持批量并发生成（> 3个并发）
- ✅ 自动化业务流程（生成→审核→发布）
- ✅ Webhook + 轮询双重保障
- ✅ 完善的错误处理和重试

### 性能指标
- ✅ 定时任务响应时间 < 5秒
- ✅ 任务队列吞吐量 > 100任务/小时
- ✅ 并发处理能力 ≥ 5个任务
- ✅ 任务成功率 > 95%

### 质量指标
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试通过率 100%
- ✅ 无严重 Bug
- ✅ 文档完整

---

## 📝 待确认事项

在开始实施前，需要确认：

1. **content-creator 异步 API 规范**
   - [x] CLI 命令：`content-creator create --mode async`
   - [x] 状态查询：`content-creator status --task-id <uuid>`
   - [x] 结果获取：`content-creator result --task-id <uuid>`
   - [x] BullMQ 队列（content-creator 内部使用）

2. **技术选型**
   - [x] 任务队列方案：Redis BullMQ（优先）+ 内存队列（降级）
   - [x] Worker 实现方式：Python 线程池
   - [x] 状态监控：CLI 轮询机制（每30秒）
   - [x] 自动审核：默认开启（可配置）
   - [ ] 是否需要分布式部署？

3. **业务规则**
   - [x] 自动审核：默认开启（`AUTO_APPROVE=true`）
   - [x] 任务级别配置：`auto_approve` 参数覆盖全局配置
   - [x] 重试策略：3次，指数退避（30s/60s/120s）
   - [ ] 是否启用自动发布？

4. **监控要求**
   - [ ] 监控指标定义
   - [ ] 告警规则和阈值
   - [ ] 通知渠道（邮件/消息/钉钉）

5. **兼容性**
   - [ ] 是否保留同步模式？
   - [ ] 如何处理历史数据？
   - [ ] 如何平滑迁移？

---

## 📅 下一步行动

请审核此执行计划，确认：
1. ✅ 技术方案已确认（content-creator CLI、队列降级、轮询机制）
2. ✅ 自动审核已确认（默认开启，任务级别可配置）
3. 是否有时间要求？
4. 是否需要调整优先级？
5. 其他疑问或建议？

**确认后即可开始实施！**

---

## 📄 相关文档

- **设计方案**：`docs/design/async-content-generation.md`
- **content-creator 项目**：`../content-creator/`
- **content-creator CLI 参考文档**：`../content-creator/docs/references/`
