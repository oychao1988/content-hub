# 异步内容生成系统 - 部署检查清单

## 准备阶段

### 代码审查

- [ ] 代码已经过 Code Review
- [ ] 所有测试通过（单元测试 + 集成测试）
- [ ] 测试覆盖率达到 80% 以上
- [ ] 文档完整且最新
- [ ] 变更日志已更新

### 配置检查

- [ ] `.env` 文件已配置
- [ ] 环境变量已验证
- [ ] 数据库连接正常
- [ ] 外部服务可用（content-creator CLI）
- [ ] 日志目录可写

### 数据库准备

- [ ] 数据库备份完成
- [ ] 迁移脚本准备就绪
- [ ] 表结构已验证
- [ ] 索引已创建
- [ ] 数据模型已测试

## 系统检查

### 依赖服务

- [ ] content-creator CLI 可用
- [ ] CLI 路径配置正确
- [ ] 环境变量 `CREATOR_CLI_PATH` 已设置
- [ ] 网络连接正常
- [ ] 端口未被占用（18010, 18030）

### 功能验证

#### 核心功能

- [ ] 异步任务提交成功
- [ ] 任务状态正确更新
- [ ] 结果处理正常工作
- [ ] Content 记录正确创建
- [ ] 发布池集成正常

#### CLI 命令

- [ ] `content generate --async` 可用
- [ ] `task status` 可用
- [ ] `task list` 可用
- [ ] `task cancel` 可用
- [ ] `task retry` 可用
- [ ] `task cleanup` 可用

#### 监控功能

- [ ] `monitor metrics` 可用
- [ ] `monitor pending` 可用
- [ ] `monitor failed` 可用
- [ ] `monitor health` 可用
- [ ] `monitor stats` 可用

#### 调度器集成

- [ ] `scheduler create` 可用
- [ ] 定时任务正确触发
- [ ] 执行历史正常记录
- [ ] 暂停/恢复功能正常

### 性能验证

- [ ] 并发任务测试通过
- [ ] 超时处理正常
- [ ] 错误恢复正常
- [ ] 资源使用合理
- [ ] 响应时间符合预期

## 部署步骤

### 1. 备份

```bash
# 备份数据库
cp data/contenthub.db data/contenthub_backup_$(date +%Y%m%d_%H%M%S).db

# 备份配置
cp .env .env.backup
```

- [ ] 数据库已备份
- [ ] 配置文件已备份
- [ ] 备份文件已验证

### 2. 代码部署

```bash
# 拉取最新代码
git pull origin main

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "from app.services.async_content_generation_service import AsyncContentGenerationService; print('OK')"
```

- [ ] 代码已更新
- [ ] 依赖已安装
- [ ] 导入测试通过

### 3. 数据库迁移

```bash
# 验证表结构
python -c "
from app.db.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
assert 'content_generation_tasks' in inspector.get_table_names()
"
```

- [ ] 表结构正确
- [ ] 索引存在
- [ ] 数据完整性 OK

### 4. 服务启动

```bash
# 启动后端
python main.py

# 验证 API
curl http://localhost:18010/docs
```

- [ ] 后端启动成功
- [ ] API 文档可访问
- [ ] 健康检查通过

### 5. 功能测试

```bash
# 提交测试任务
contenthub content generate -a 49 -t "部署测试" --async

# 查询状态
contenthub task status <task_id>

# 查看监控
contenthub monitor metrics
```

- [ ] 测试任务提交成功
- [ ] 状态查询正常
- [ ] 监控指标正常

### 6. 性能测试

```bash
# 并发测试
for i in {1..10}; do
  contenthub content generate -a 49 -t "并发测试 $i" --async
done

# 检查处理速度
contenthub monitor stats --days 1
```

- [ ] 并发任务处理正常
- [ ] 性能指标达标
- [ ] 无内存泄漏

## 上线后验证

### 监控检查

- [ ] 任务提交正常
- [ ] 成功率 > 95%
- [ ] 平均完成时间 < 60s
- [ ] 错误率 < 5%
- [ ] 资源使用正常

### 日志检查

```bash
# 查看错误日志
grep "ERROR" logs/app.log | tail -20

# 查看任务日志
grep "task-" logs/app.log | tail -50
```

- [ ] 无严重错误
- [ ] 任务流程正常
- [ ] 性能日志正常

### 用户反馈

- [ ] 收集用户反馈
- [ ] 监控问题报告
- [ ] 记录优化建议

## 回滚计划

### 回滚触发条件

- 成功率 < 80%
- 平均完成时间 > 120s
- 严重错误持续发生
- 用户无法正常使用

### 回滚步骤

```bash
# 1. 停止服务
pkill -f "python main.py"

# 2. 恢复数据库
cp data/contenthub_backup_YYYYMMDD_HHMMSS.db data/contenthub.db

# 3. 恢复代码
git checkout <previous_commit>

# 4. 重启服务
python main.py
```

- [ ] 回滚脚本准备
- [ ] 回滚时间 < 5 分钟
- [ ] 数据无丢失

## 应急预案

### 问题 1: 任务卡住

**症状**: 任务长时间处于 processing 状态

**处理**:
```bash
# 1. 检查任务状态
contenthub task status <task_id>

# 2. 检查 content-creator
./content-creator-cli.sh health

# 3. 重启服务
pkill -f "python main.py" && python main.py
```

### 问题 2: 大量失败

**症状**: 成功率突然下降

**处理**:
```bash
# 1. 查看失败任务
contenthub monitor failed

# 2. 查看错误日志
tail -f logs/app.log | grep ERROR

# 3. 暂停新任务
# 修改 .env: ASYNC_CONTENT_GENERATION_ENABLED=false

# 4. 分析原因并修复
```

### 问题 3: 性能下降

**症状**: 响应时间明显增加

**处理**:
```bash
# 1. 检查资源使用
top

# 2. 减少并发数
# 修改 .env: ASYNC_MAX_CONCURRENT_TASKS=2

# 3. 清理旧数据
contenthub task cleanup --days 30
```

## 完成标准

- [ ] 所有检查项通过
- [ ] 测试任务成功完成
- [ ] 性能指标达标
- [ ] 监控正常工作
- [ ] 用户反馈良好
- [ ] 文档已归档

---

**准备人员**: ___________
**执行人员**: ___________
**验证人员**: ___________
**完成时间**: ___________

**签名**: ___________
**日期**: ___________
