# ContentHub 性能测试

本目录包含 ContentHub 系统的性能测试套件。

## 测试目标

根据设计文档（docs/DESIGN.md 第 14 章），系统需要满足以下性能指标：

- **GET 请求**: P95 响应时间 < 200ms
- **POST 请求**: P95 响应时间 < 500ms
- **并发测试**: 100 并发用户，持续 5 分钟，成功率 > 99%

## 测试工具

### 1. Locust（负载测试）

Locust 是一个开源的负载测试工具，可以模拟大量用户并发访问系统。

**安装**：
```bash
pip install locust==2.29.0
```

**使用方法**：

1. **Web UI 模式**（推荐用于交互式测试）：
```bash
# 确保后端服务正在运行
cd src/backend
python main.py

# 在另一个终端启动 Locust
locust -f locustfile.py --host http://localhost:8000

# 访问 Web UI
open http://localhost:8089
```

2. **命令行模式**（推荐用于自动化测试）：
```bash
# 100 用户，每秒启动 10 个用户，持续 5 分钟
locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000

# 生成 HTML 报告
locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000 --html performance_report.html
```

**测试场景**：

- **ContentHubUser**: 标准用户行为
  - 登录系统
  - 查看仪表板（权重 3）
  - 查看账号列表（权重 5）
  - 查看内容列表（权重 4）
  - 查看平台列表（权重 2）
  - 查看配置（权重 2）

- **QuickTestUser**: 快速测试用户
  - 等待时间更短（0.5-1秒）
  - 用于快速验证

- **StressTestUser**: 压力测试用户
  - 等待时间最短（0.1-0.5秒）
  - 用于压力测试

### 2. pytest-benchmark（基准测试）

pytest-benchmark 是一个 pytest 插件，用于测量代码执行时间。

**安装**：
```bash
pip install pytest-benchmark==4.0.0
```

**使用方法**：

```bash
# 运行所有性能测试
pytest tests/performance/ -v --benchmark-only

# 运行 API 响应时间测试
pytest tests/performance/test_api_response_time.py -v --benchmark-only

# 运行数据库查询性能测试
pytest tests/performance/test_db_query_performance.py -v --benchmark-only

# 生成 JSON 报告
pytest tests/performance/ -v --benchmark-only --benchmark-json=benchmark_results.json

# 生成比较报告（需要之前的基准数据）
pytest tests/performance/ -v --benchmark-only --benchmark-compare=benchmark_results.json

# 生成 HTML 报告
pytest tests/performance/ -v --benchmark-only --benchmark-html=benchmark_report.html
```

## 测试文件

### 1. locustfile.py

Locust 配置文件，定义用户行为和测试场景。

**关键配置**：
- `wait_time`: 用户请求之间的等待时间
- `@task`: 定义用户行为，数字表示权重
- `on_start`: 用户启动时的操作（登录）

### 2. test_api_response_time.py

API 响应时间测试，测试关键 API 端点的性能。

**测试接口**：
- 登录接口（POST）
- 账号列表查询（GET）
- 内容列表查询（GET）
- 写作风格查询（GET）
- 仪表板统计（GET）
- 平台列表查询（GET）

**性能目标**：
- GET P95 < 200ms
- POST P95 < 500ms

### 3. test_db_query_performance.py

数据库查询性能测试，识别慢查询并提供优化建议。

**测试内容**：
- 简单查询 vs 关联查询
- 单表查询 vs 连接查询
- 分页查询性能
- 聚合查询性能
- 写入性能

## 性能优化建议

### 数据库优化

1. **索引优化**
```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_content_status ON contents(status);
CREATE INDEX idx_content_created_at ON contents(created_at DESC);
CREATE INDEX idx_account_customer_id ON accounts(customer_id);
```

2. **避免 N+1 查询**
```python
# 使用 selectinload 或 joinedload
from sqlalchemy.orm import selectinload

result = db.execute(
    select(Content)
    .options(selectinload(Content.account))
    .limit(20)
)
```

3. **查询优化**
```python
# 只查询需要的字段
result = db.execute(
    select(Content.id, Content.title, Content.status)
    .limit(20)
)
```

### API 优化

1. **启用压缩**
```python
# 在 main.py 中启用 gzip 压缩
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

2. **响应优化**
```python
# 排除不必要的字段
response = AccountRead.from_orm(account).exclude({"credentials"})
```

3. **使用缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_platforms_cached():
    return platform_service.get_all_platforms(db)
```

### 配置优化

1. **连接池配置**
```python
# 在 database.py 中配置
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}
```

2. **限流配置**
```python
# 根据性能测试结果调整限流参数
RATE_LIMIT_CONFIG = {
    "default": {"capacity": 1000, "refill_rate": 0.28},
}
```

## 性能监控

### 生产环境监控

建议在生产环境中部署以下监控工具：

1. **APM 工具**
   - Sentry（错误追踪）
   - New Relic（性能监控）
   - Datadog（综合监控）

2. **日志分析**
   - ELK Stack（Elasticsearch, Logstash, Kibana）
   - Grafana Loki

3. **指标收集**
   - Prometheus（指标收集）
   - Grafana（可视化）

### 关键指标

- **响应时间**: P50, P95, P99
- **吞吐量**: RPS（Requests Per Second）
- **错误率**: 4xx, 5xx 错误比例
- **资源使用**: CPU, 内存, 磁盘 I/O
- **数据库性能**: 查询时间, 连接数

## 性能测试最佳实践

1. **在独立环境中测试**
   - 使用独立的测试数据库
   - 避免影响生产数据
   - 确保测试环境与生产环境配置一致

2. **模拟真实场景**
   - 使用真实的用户行为模式
   - 包含读写混合操作
   - 测试峰值负载

3. **持续监控**
   - 定期运行性能测试
   - 跟踪性能趋势
   - 在代码变更后进行回归测试

4. **基准对比**
   - 保存历史测试结果
   - 比较不同版本的性能
   - 识别性能退化

5. **迭代优化**
   - 先测量，后优化
   - 一次优化一个瓶颈
   - 验证优化效果

## 故障排查

### 问题：响应时间过长

**可能原因**：
- 数据库查询慢
- N+1 查询问题
- 缺少索引
- 网络延迟

**排查步骤**：
1. 查看数据库查询日志
2. 使用 EXPLAIN 分析查询计划
3. 检查索引使用情况
4. 使用 profiling 工具分析代码

### 问题：并发性能差

**可能原因**：
- 数据库连接池太小
- 锁竞争
- 资源泄露
- 单点瓶颈

**排查步骤**：
1. 检查连接池配置
2. 监控数据库锁等待
3. 检查内存和 CPU 使用
4. 使用性能分析工具

### 问题：内存占用过高

**可能原因**：
- 查询返回过多数据
- 缓存未设置过期时间
- 对象未释放
- 内存泄露

**排查步骤**：
1. 分析内存使用情况
2. 检查查询结果集大小
3. 审查缓存策略
4. 使用内存分析工具

## 参考资料

- [Locust 官方文档](https://docs.locust.io/)
- [pytest-benchmark 文档](https://pytest-benchmark.readthedocs.io/)
- [FastAPI 性能优化](https://fastapi.tiangolo.com/tutorial/additional-performances/)
- [SQLAlchemy 性能优化](https://docs.sqlalchemy.org/en/20/core/performance.html)
- ContentHub 设计文档第 14 章：性能优化策略
