# CLI 测试文件快速索引

> **更新时间**: 2026-02-05
> **测试文件数**: 7 个
> **测试用例数**: 89 个
> **总代码行数**: 4,838 行

---

## 测试文件分类

### 按阶段分类

#### 阶段 1: 修复失败测试

**test_cli_simple.py** (193 行, 5.1K)
- 路径: `tests/test_cli_simple.py`
- 测试数: 10
- 用途: 基础功能验证
- 关键测试:
  - `test_version_command`
  - `test_db_stats_command`
  - `test_users_list_command`
  - `test_platform_list_command`
  - `test_customer_list_command`
  - `test_accounts_list_command`
  - `test_system_health_command`
  - `test_config_list_command` ⭐ 修复
  - `test_audit_list_command` ⭐ 修复
  - `test_dashboard_stats_command`

#### 阶段 2: 内容管理模块

**test_cli_content.py** (668 行, 20K)
- 路径: `tests/test_cli_content.py`
- 测试数: 15
- 用途: 内容管理核心功能测试
- 关键测试:
  - CRUD 操作: `test_content_create`, `test_content_info`, `test_content_update`, `test_content_delete`
  - 内容生成: `test_content_generate`, `test_content_batch_generate`
  - 审核流程: `test_content_approve`, `test_content_reject`, `test_content_submit_review`
  - 列表查询: `test_content_list`, `test_content_list_with_filters`
  - 统计搜索: `test_content_statistics`, `test_content_topic_search`
  - 完整流程: `test_content_full_lifecycle`

#### 阶段 3: 定时任务模块

**test_cli_scheduler.py** (853 行, 24K)
- 路径: `tests/test_cli_scheduler.py`
- 测试数: 22
- 用途: 定时任务核心功能测试
- 关键测试:
  - CRUD 操作: `test_scheduler_create`, `test_scheduler_info`, `test_scheduler_update`, `test_scheduler_delete`
  - 任务管理: `test_scheduler_list`, `test_scheduler_pause`, `test_scheduler_resume`
  - 执行控制: `test_scheduler_trigger`, `test_scheduler_history`
  - 调度器控制: `test_scheduler_start`, `test_scheduler_stop`, `test_scheduler_status`
  - 边界测试: `test_scheduler_pause_already_paused`, `test_scheduler_resume_already_active`
  - 完整流程: `test_scheduler_lifecycle`

#### 阶段 4: 发布管理模块

**test_cli_publisher.py** (686 行, 20K)
- 路径: `tests/test_cli_publisher.py`
- 测试数: 14
- 用途: 发布管理核心功能测试
- 关键测试:
  - 发布操作: `test_publisher_publish`, `test_publisher_batch_publish`
  - 历史记录: `test_publisher_history`, `test_publisher_records`
  - 重试机制: `test_publisher_retry`, `test_publisher_retry_successful_log`
  - 统计分析: `test_publisher_stats`, `test_publisher_stats_without_account`
  - 边界测试: `test_publisher_publish_with_invalid_account`
  - 完整流程: `test_publisher_full_lifecycle`

#### 阶段 5: 发布池管理模块

**test_cli_publish_pool.py** (813 行, 24K)
- 路径: `tests/test_cli_publish_pool.py`
- 测试数: 17
- 用途: 发布池管理核心功能测试
- 关键测试:
  - 队列管理: `test_publish_pool_list`, `test_publish_pool_add`, `test_publish_pool_remove`
  - 优先级设置: `test_publish_pool_set_priority`, `test_publish_pool_schedule`
  - 发布操作: `test_publish_pool_publish`, `test_publish_pool_clear`
  - 统计分析: `test_publish_pool_stats`, `test_publish_pool_stats_with_data`
  - 边界测试: `test_publish_pool_add_duplicate`, `test_publish_pool_set_priority_invalid`
  - 完整流程: `test_publish_pool_full_lifecycle`

#### 阶段 6: CRUD 操作测试

**test_cli_crud.py** (1,114 行, 31K)
- 路径: `tests/test_cli_crud.py`
- 测试数: 22
- 用途: 用户、账号、平台、客户 CRUD 测试
- 关键测试:
  - 用户管理: `test_users_create`, `test_users_update`, `test_users_delete`, `test_users_info`, `test_users_set_role`, `test_users_reset_password`
  - 账号管理: `test_accounts_create`, `test_accounts_update`, `test_accounts_delete`, `test_accounts_info`, `test_accounts_test_connection`
  - 平台管理: `test_platform_create`, `test_platform_update`, `test_platform_delete`, `test_platform_info`, `test_platform_test_api`
  - 客户管理: `test_customer_create`, `test_customer_update`, `test_customer_delete`, `test_customer_info`, `test_customer_stats`
  - 完整流程: `test_full_crud_workflow`

#### 端到端测试

**test_cli_e2e.py** (511 行, 14K)
- 路径: `tests/test_cli_e2e.py`
- 测试数: 7
- 用途: 完整业务流程测试
- 关键测试:
  - 系统初始化: `test_step_1_database_init`
  - 用户创建: `test_step_2_create_users`
  - 平台客户: `test_step_3_create_platforms_and_customers`
  - 账号创建: `test_step_4_create_accounts`
  - 内容生成: `test_step_5_generate_content`
  - 内容审核: `test_step_6_review_content`
  - 内容发布: `test_step_7_publish_content`

---

## 按模块分类

### 内容管理模块 (content)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_content.py | 15 | 100% |
| test_cli_e2e.py | 2 | - |
| **总计** | **17** | **100%** |

### 定时任务模块 (scheduler)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_scheduler.py | 22 | 100% |
| **总计** | **22** | **100%** |

### 发布管理模块 (publisher)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_publisher.py | 14 | 100% |
| test_cli_e2e.py | 1 | - |
| **总计** | **15** | **100%** |

### 发布池管理模块 (publish-pool)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_publish_pool.py | 17 | 100% |
| test_cli_e2e.py | 1 | - |
| **总计** | **18** | **100%** |

### 用户管理模块 (users)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_crud.py | 6 | 75% |
| test_cli_simple.py | 1 | - |
| test_cli_e2e.py | 1 | - |
| **总计** | **8** | **87.5%** |

### 账号管理模块 (accounts)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_crud.py | 5 | 38% |
| test_cli_simple.py | 1 | - |
| test_cli_e2e.py | 1 | - |
| **总计** | **7** | **46.2%** |

### 平台管理模块 (platform)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_crud.py | 5 | 63% |
| test_cli_simple.py | 1 | - |
| test_cli_e2e.py | 1 | - |
| **总计** | **7** | **75.0%** |

### 客户管理模块 (customer)

| 测试文件 | 测试用例数 | 覆盖率 |
|----------|-----------|--------|
| test_cli_crud.py | 5 | 50% |
| test_cli_simple.py | 1 | - |
| test_cli_e2e.py | 1 | - |
| **总计** | **7** | **60.0%** |

---

## 按测试类型分类

### 单元测试 (67 个)

- test_cli_content.py: 15
- test_cli_scheduler.py: 22
- test_cli_publisher.py: 14
- test_cli_publish_pool.py: 17
- test_cli_crud.py: 22 (部分)

### 集成测试 (13 个)

- test_cli_crud.py: 1 (test_full_crud_workflow)
- test_cli_content.py: 1 (test_content_full_lifecycle)
- test_cli_scheduler.py: 1 (test_scheduler_lifecycle)
- test_cli_publisher.py: 1 (test_publisher_full_lifecycle)
- test_cli_publish_pool.py: 1 (test_publish_pool_full_lifecycle)
- 其他: 8

### 端到端测试 (9 个)

- test_cli_e2e.py: 7
- test_cli_simple.py: 10 (部分)

---

## 快速查找

### 查找特定模块的测试

```bash
# 内容管理
tests/test_cli_content.py

# 定时任务
tests/test_cli_scheduler.py

# 发布管理
tests/test_cli_publisher.py

# 发布池
tests/test_cli_publish_pool.py

# 用户/账号/平台/客户
tests/test_cli_crud.py
```

### 查找特定类型的测试

```bash
# 单元测试
tests/test_cli_content.py
tests/test_cli_scheduler.py
tests/test_cli_publisher.py
tests/test_cli_publish_pool.py

# 集成测试
tests/test_cli_crud.py

# 端到端测试
tests/test_cli_e2e.py
tests/test_cli_simple.py
```

### 查找特定功能的测试

```bash
# CRUD 操作
tests/test_cli_crud.py
tests/test_cli_content.py

# 生命周期测试
tests/test_cli_content.py::test_content_full_lifecycle
tests/test_cli_scheduler.py::test_scheduler_lifecycle
tests/test_cli_publisher.py::test_publisher_full_lifecycle
tests/test_cli_publish_pool.py::test_publish_pool_full_lifecycle

# 边界测试
tests/test_cli_scheduler.py (多个边界测试)
tests/test_cli_publish_pool.py (多个边界测试)
```

---

## 运行特定测试

### 运行单个测试文件

```bash
python -m pytest tests/test_cli_content.py -v
python -m pytest tests/test_cli_scheduler.py -v
python -m pytest tests/test_cli_publisher.py -v
python -m pytest tests/test_cli_publish_pool.py -v
python -m pytest tests/test_cli_crud.py -v
```

### 运行单个测试用例

```bash
python -m pytest tests/test_cli_content.py::test_content_create -v
python -m pytest tests/test_cli_scheduler.py::test_scheduler_create -v
```

### 运行匹配模式的测试

```bash
# 所有 create 测试
python -m pytest tests/test_cli_*.py -k "create" -v

# 所有 lifecycle 测试
python -m pytest tests/test_cli_*.py -k "lifecycle" -v

# 所有 scheduler 测试
python -m pytest tests/test_cli_scheduler.py -v
```

---

## 测试文件统计

### 文件大小排名

1. test_cli_crud.py - 1,114 行 (31K)
2. test_cli_scheduler.py - 853 行 (24K)
3. test_cli_publish_pool.py - 813 行 (24K)
4. test_cli_content.py - 668 行 (20K)
5. test_cli_publisher.py - 686 行 (20K)
6. test_cli_e2e.py - 511 行 (14K)
7. test_cli_simple.py - 193 行 (5.1K)

### 测试用例数排名

1. test_cli_scheduler.py - 22 个
2. test_cli_crud.py - 22 个
3. test_cli_publish_pool.py - 17 个
4. test_cli_content.py - 15 个
5. test_cli_publisher.py - 14 个
6. test_cli_simple.py - 10 个
7. test_cli_e2e.py - 7 个

### 代码密度排名 (用例/行)

1. test_cli_simple.py - 0.052
2. test_cli_scheduler.py - 0.026
3. test_cli_publish_pool.py - 0.021
4. test_cli_publisher.py - 0.020
5. test_cli_crud.py - 0.020
6. test_cli_content.py - 0.022
7. test_cli_e2e.py - 0.014

---

## 相关文档

- **测试报告**: `docs/development/CLI-TEST-REPORT.md`
- **最终总结**: `CLI-TEST-FINAL-SUMMARY.md`
- **执行摘要**: `CLI-TEST-EXECUTIVE-SUMMARY.md`
- **可视化**: `CLI-TEST-COVERAGE-VISUALIZATION.md`

---

**更新时间**: 2026-02-05
**维护者**: Claude Code AI
**版本**: 1.0.0
