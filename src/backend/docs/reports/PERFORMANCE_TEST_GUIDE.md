# ContentHub 性能测试执行指南

本文档详细说明了如何执行 ContentHub 的性能测试，包括环境准备、测试执行、结果分析和报告生成。

---

## 目录

1. [测试概述](#测试概述)
2. [环境准备](#环境准备)
3. [测试数据准备](#测试数据准备)
4. [执行测试](#执行测试)
5. [结果分析](#结果分析)
6. [优化建议](#优化建议)
7. [报告模板](#报告模板)

---

## 测试概述

### 测试目标

根据 ContentHub 设计文档（`docs/DESIGN.md` 第 14 章），系统需要满足以下性能指标：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| GET 请求 P95 | < 200ms | 95% 的 GET 请求响应时间小于 200ms |
| POST 请求 P95 | < 500ms | 95% 的 POST 请求响应时间小于 500ms |
| 并发用户 | 100 | 同时支持 100 个并发用户 |
| 成功率 | > 99% | 99% 以上的请求成功 |
| P50 响应时间 | < 100ms | 50% 的请求响应时间小于 100ms |
| P99 响应时间 | < 1000ms | 99% 的请求响应时间小于 1秒 |

### 测试类型

1. **API 响应时间测试**: 使用 pytest-benchmark 测试各个 API 端点的响应时间
2. **数据库查询性能测试**: 测试关键数据库查询的性能
3. **并发压力测试**: 使用 Locust 进行高并发负载测试

---

## 环境准备

### 1. 系统要求

- Python 3.12+
- SQLite 数据库
- 至少 4GB 内存
- 稳定的网络环境

### 2. 安装依赖

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 安装性能测试工具
pip install locust==2.29.0
pip install pytest-benchmark==4.0.0

# 或从 requirements.txt 安装
pip install -r requirements.txt
```

### 3. 启动后端服务

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 启动服务
python main.py

# 服务应该运行在 http://localhost:8000
```

验证服务运行：
```bash
curl http://localhost:8000/api/v1/system/health
```

---

## 测试数据准备

### 创建测试数据

在运行性能测试之前，需要准备足够的测试数据：

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 创建默认数量的测试数据
python init_performance_test_data.py

# 创建自定义数量的测试数据
python init_performance_test_data.py --users 20 --accounts 100 --contents 500
```

默认数据量：
- 10 个用户
- 10 个客户
- 5 个平台
- 50 个账号
- 200 个内容

---

## 执行测试

### 1. API 响应时间测试

#### 方式一：使用脚本

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 运行基准测试脚本
./run_benchmark_test.sh
```

#### 方式二：手动执行

```bash
# 运行所有基准测试
pytest tests/performance/test_api_response_time.py \
    -v \
    --benchmark-only \
    --benchmark-json=benchmark_results.json \
    --benchmark-html=benchmark_report.html

# 只运行 GET 请求测试
pytest tests/performance/test_api_response_time.py::TestAPIResponseTime::test_accounts_list_response_time \
    -v \
    --benchmark-only

# 生成比较报告（需要历史数据）
pytest tests/performance/test_api_response_time.py \
    -v \
    --benchmark-only \
    --benchmark-compare=benchmark_results_old.json
```

### 2. 数据库查询性能测试

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 运行数据库性能测试
pytest tests/performance/test_db_query_performance.py \
    -v \
    --benchmark-only \
    --benchmark-json=db_benchmark_results.json \
    --benchmark-sort=name

# 查看测试结果摘要
pytest tests/performance/test_db_query_performance.py \
    -v \
    --benchmark-only \
    --benchmark-sort=mean
```

### 3. 并发压力测试

#### 方式一：使用脚本

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 运行默认配置（100 用户，5 分钟）
./run_concurrent_test.sh

# 自定义配置
LOCUST_USERS=200 LOCUST_RUN_TIME=10m ./run_concurrent_test.sh
```

#### 方式二：使用 Locust Web UI

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 启动 Locust Web UI
locust -f locustfile.py --host http://localhost:8000

# 访问 Web UI
open http://localhost:8089
```

在 Web UI 中：
1. 设置用户数量（如 100）
2. 设置启动速率（如 10 用户/秒）
3. 点击 "Start swarming" 开始测试
4. 观察实时性能数据
5. 测试结束后下载报告

#### 方式三：命令行模式

```bash
# 100 用户，每秒启动 10 个，持续 5 分钟
locust -f locustfile.py \
    --headless \
    --host http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --html performance_report.html

# 查看结果
cat performance_report.html
```

---

## 结果分析

### 1. API 响应时间分析

查看生成的 JSON 或 HTML 报告：

```bash
# 查看 JSON 报告
cat benchmark_results.json | jq '.benchmarks'

# 关键指标
# - mean: 平均响应时间
# - min: 最小响应时间
# - max: 最大响应时间
# - stddev: 标准差
# - rounds: 测试轮数
```

**判断标准**：
- ✅ GET 请求 P95 < 200ms
- ✅ POST 请求 P95 < 500ms
- ❌ 如果超过目标，需要优化

### 2. 数据库查询分析

```bash
# 查看数据库性能测试结果
cat db_benchmark_results.json | jq '.benchmarks[] | select(.name | contains("query"))'
```

**需要关注的查询**：
- 平均时间 > 100ms 的查询
- 最大时间 > 500ms 的查询
- 存在 N+1 问题的查询

### 3. 并发测试分析

查看 Locust 生成的 HTML 报告，关注：

**关键指标**：
- **Requests/s**: 每秒请求数（越高越好）
- **Failures**: 失败请求数（应为 0 或极低）
- **Median**: 中位数响应时间
- **95%**: P95 响应时间
- **99%**: P99 响应时间

**性能分布图**：
- Response Times: 响应时间分布
- Total Requests per Second: 每秒请求数趋势
- Response Time Percentiles: 百分位数趋势

**判断标准**：
- ✅ 成功率 > 99%
- ✅ P95 响应时间符合目标
- ✅ 无明显性能退化

---

## 优化建议

### 数据库优化

#### 1. 添加索引

```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_content_status ON contents(status);
CREATE INDEX idx_content_created_at ON contents(created_at DESC);
CREATE INDEX idx_account_customer_id ON accounts(customer_id);
CREATE INDEX idx_account_platform_id ON accounts(platform_id);
CREATE INDEX idx_content_account_id ON contents(account_id);
```

#### 2. 优化查询

**问题：N+1 查询**
```python
# 不好的方式
accounts = db.query(Account).all()
for account in accounts:
    print(account.platform.name)  # 每次循环都查询数据库
```

**优化方案**：
```python
# 使用 joinedload 或 selectinload
from sqlalchemy.orm import selectinload

accounts = db.query(Account).options(
    selectinload(Account.platform)
).all()

for account in accounts:
    print(account.platform.name)  # 不会产生额外查询
```

#### 3. 只查询需要的字段

```python
# 不要
result = db.query(Content).all()

# 优先
result = db.query(Content.id, Content.title, Content.status).all()
```

### API 优化

#### 1. 启用响应压缩

在 `main.py` 中添加：

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 2. 优化响应数据

```python
# 排除不必要的字段
from pydantic import BaseModel

class AccountRead(BaseModel):
    id: int
    name: str
    platform_id: int

    class Config:
        from_attributes = True
        exclude = {'credentials', 'internal_notes'}  # 排除敏感字段
```

#### 3. 实现缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_platforms_cached(db_session_id: int):
    return db.query(Platform).all()
```

### 架构优化

#### 1. 数据库连接池

在 `database.py` 中配置：

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": False  # 生产环境关闭 SQL 日志
}
```

#### 2. 异步处理

```python
from fastapi import BackgroundTasks

@router.post("/contents/generate")
async def generate_content(
    content: ContentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 立即返回
    content_obj = create_content(db, content)

    # 后台处理
    background_tasks.add_task(
        process_content_generation,
        content_obj.id
    )

    return content_obj
```

#### 3. 分页优化

对于大结果集，使用游标分页代替偏移分页：

```python
# 传统偏移分页（慢）
# SELECT * FROM contents OFFSET 1000 LIMIT 20

# 游标分页（快）
def get_contents_cursor(cursor: int = None, limit: int = 20):
    query = db.query(Content)
    if cursor:
        query = query.filter(Content.id > cursor)
    return query.order_by(Content.id).limit(limit).all()
```

---

## 报告模板

性能测试完成后，使用以下模板生成报告：

### 1. 自动生成报告模板

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

python tests/performance/test_template.py
```

这将生成：
- `benchmark_reports/performance_report.json`
- `PERFORMANCE_TEST_REPORT.md`

### 2. 填充实际数据

打开 `PERFORMANCE_TEST_REPORT.md`，根据测试结果填充数据。

### 3. 报告内容

报告应包含以下部分：

1. **测试概述**: 测试目标、范围、环境
2. **API 响应时间测试**: 各端点的 P50、P95、P99 值
3. **数据库查询性能**: 关键查询的执行时间
4. **并发压力测试**: 负载测试结果和成功率
5. **性能瓶颈分析**: 识别的问题
6. **优化建议**: 具体的改进措施

---

## 持续监控

### 生产环境监控

部署后，持续监控以下指标：

1. **APM 工具**
   - Sentry（错误追踪）
   - New Relic（性能监控）
   - Datadog（综合监控）

2. **日志分析**
   - ELK Stack
   - Grafana Loki

3. **指标收集**
   - Prometheus + Grafana

### 定期回归测试

建议：
- 每周运行一次完整性能测试
- 代码变更后运行关键测试
- 性能退化超过 20% 时触发警报

---

## 故障排查

### 问题：响应时间过长

**检查清单**：
1. 查看数据库查询日志
2. 使用 `EXPLAIN` 分析查询计划
3. 检查索引使用情况
4. 检查网络延迟

### 问题：并发性能差

**检查清单**：
1. 检查数据库连接池配置
2. 监控数据库锁等待
3. 检查内存和 CPU 使用
4. 检查是否有阻塞操作

### 问题：内存占用过高

**检查清单**：
1. 分析查询结果集大小
2. 检查缓存策略
3. 查找内存泄露
4. 使用内存分析工具

---

## 参考资料

- [Locust 官方文档](https://docs.locust.io/)
- [pytest-benchmark 文档](https://pytest-benchmark.readthedocs.io/)
- [FastAPI 性能优化](https://fastapi.tiangolo.com/tutorial/additional-performances/)
- [SQLAlchemy 性能优化](https://docs.sqlalchemy.org/en/20/core/performance.html)
- ContentHub 设计文档第 14 章

---

## 联系方式

如有问题，请联系开发团队。

**最后更新**: 2026-01-29
