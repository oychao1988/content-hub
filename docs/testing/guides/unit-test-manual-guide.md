# ContentHub 单元测试手动执行指南

本文档提供详细的步骤说明，帮助您手动执行单元测试用例。

## 📋 测试概览

ContentHub 项目包含以下类型的测试：

| 测试类型 | 目录 | 测试数量 | 用途 |
|---------|------|---------|------|
| 单元测试 | `tests/unit/` | 20+ 文件 | 测试单个服务和功能模块 |
| 集成测试 | `tests/integration/` | 12+ 文件 | 测试API端点和模块集成 |
| E2E测试 | `tests/e2e/` | 2 文件 | 端到端业务流程测试 |
| 性能测试 | `tests/performance/` | 2 文件 | 性能和响应时间测试 |

---

## 🚀 快速开始

### 1. 安装测试依赖

```bash
cd src/backend

# 安装所有依赖（包括测试依赖）
pip install -r requirements.txt

# 或仅安装测试依赖
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### 2. 运行所有测试

```bash
cd src/backend

# 运行所有测试
pytest

# 运行所有测试并显示详细输出
pytest -v

# 运行所有测试并显示打印输出
pytest -v -s
```

### 3. 运行特定类型的测试

```bash
# 仅运行单元测试
pytest tests/unit/ -v

# 仅运行集成测试
pytest tests/integration/ -v

# 仅运行E2E测试
pytest tests/e2e/ -v

# 仅运行性能测试
pytest tests/performance/ -v
```

---

## 📊 单元测试详细指南

### 测试文件结构

```
tests/unit/
├── services/                    # 服务层单元测试
│   ├── test_account_service.py
│   ├── test_content_service.py
│   ├── test_scheduler_service.py
│   ├── test_publish_pool_service.py
│   ├── test_user_service.py
│   ├── test_customer_service.py
│   ├── test_platform_service.py
│   ├── test_publisher_service.py
│   ├── test_account_config_service.py
│   ├── test_batch_publish_service.py
│   ├── test_content_creator_service.py
│   ├── test_content_review_service.py
│   ├── test_dashboard_service.py
│   └── test_image_manager.py
├── test_audit_service.py
├── test_permissions.py
├── test_rate_limiter.py
├── test_roles.py
├── test_security.py
└── test_system_service.py
```

---

## 🧪 核心服务测试用例

### 1. 内容管理服务测试

**文件**: `tests/unit/services/test_content_service.py`

**测试用例**:
- ✅ `test_create_content` - 测试创建内容
- ✅ `test_get_content_detail` - 测试获取内容详情
- ✅ `test_get_content_list` - 测试获取内容列表（分页）
- ✅ `test_update_content` - 测试更新内容
- ✅ `test_delete_content` - 测试删除内容
- ✅ `test_review_operations` - 测试审核操作
- ✅ `test_content_service_operations` - 综合测试

**运行方式**:
```bash
# 运行内容服务所有测试
pytest tests/unit/services/test_content_service.py -v

# 运行单个测试用例
pytest tests/unit/services/test_content_service.py::test_create_content -v

# 运行包含特定关键字的测试
pytest tests/unit/services/test_content_service.py -k "create" -v
```

**预期输出**:
```
tests/unit/services/test_content_service.py::test_create_content PASSED
tests/unit/services/test_content_service.py::test_get_content_detail PASSED
tests/unit/services/test_content_service.py::test_get_content_list PASSED
tests/unit/services/test_content_service.py::test_update_content PASSED
tests/unit/services/test_content_service.py::test_delete_content PASSED
tests/unit/services/test_content_service.py::test_review_operations PASSED
tests/unit/services/test_content_service.py::test_content_service_operations PASSED

======== 7 passed in 2.34s ========
```

### 2. 账号管理服务测试

**文件**: `tests/unit/services/test_account_service.py`

**测试用例**:
- ✅ `test_create_account` - 测试创建账号
- ✅ `test_get_account_detail` - 测试获取账号详情
- ✅ `test_get_account_list` - 测试获取账号列表
- ✅ `test_update_account` - 测试更新账号
- ✅ `test_delete_account` - 测试删除账号
- ✅ `test_account_service_operations` - 综合测试

**运行方式**:
```bash
pytest tests/unit/services/test_account_service.py -v
```

### 3. 定时任务服务测试

**文件**: `tests/unit/services/test_scheduler_service.py`

**测试用例**:
- ✅ `test_create_task` - 测试创建定时任务
- ✅ `test_create_task_with_interval` - 测试创建基于间隔的任务
- ✅ `test_create_task_duplicate_name` - 测试重名任务处理
- ✅ `test_get_task_detail` - 测试获取任务详情
- ✅ `test_get_task_list` - 测试获取任务列表
- ✅ `test_update_task` - 测试更新任务
- ✅ `test_delete_task` - 测试删除任务
- ✅ `test_trigger_task_success` - 测试手动触发任务
- ✅ `test_trigger_task_not_found` - 测试触发不存在的任务
- ✅ `test_get_execution_history` - 测试获取执行历史
- ✅ `test_toggle_task_enable` - 测试启用/禁用切换
- ✅ `test_concurrent_task_handling` - 测试并发任务处理
- ✅ `test_task_with_cron_expressions` - 测试不同Cron表达式
- ✅ `test_task_with_different_intervals` - 测试不同间隔配置

**运行方式**:
```bash
# 运行所有定时任务测试
pytest tests/unit/services/test_scheduler_service.py -v

# 运行包含"cron"的测试
pytest tests/unit/services/test_scheduler_service.py -k "cron" -v
```

### 4. 发布池服务测试

**文件**: `tests/unit/services/test_publish_pool_service.py`

**测试用例**:
- ✅ 添加到发布池
- ✅ 从发布池移除
- ✅ 更新发布池条目
- ✅ 批量发布
- ✅ 清空已发布项

**运行方式**:
```bash
pytest tests/unit/services/test_publish_pool_service.py -v
```

### 5. 用户服务测试

**文件**: `tests/unit/services/test_user_service.py`

**测试用例**:
- ✅ 用户创建
- ✅ 用户查询
- ✅ 用户更新
- ✅ 用户删除
- ✅ 密码哈希验证

**运行方式**:
```bash
pytest tests/unit/services/test_user_service.py -v
```

---

## 🔧 核心功能测试

### 1. 权限控制测试

**文件**: `tests/unit/test_permissions.py`

**运行方式**:
```bash
pytest tests/unit/test_permissions.py -v
```

### 2. 限流测试

**文件**: `tests/unit/test_rate_limiter.py`

**运行方式**:
```bash
pytest tests/unit/test_rate_limiter.py -v
```

### 3. 安全功能测试

**文件**: `tests/unit/test_security.py`

**运行方式**:
```bash
pytest tests/unit/test_security.py -v
```

### 4. 审计日志测试

**文件**: `tests/unit/test_audit_service.py`

**运行方式**:
```bash
pytest tests/unit/test_audit_service.py -v
```

---

## 📈 测试覆盖率

### 生成覆盖率报告

```bash
# 生成覆盖率报告（终端）
pytest --cov=app --cov-report=term

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html

# 生成XML覆盖率报告（用于CI/CD）
pytest --cov=app --cov-report=xml

# 组合使用
pytest --cov=app --cov-report=term-missing --cov-report=html
```

**查看HTML报告**:
```bash
# 报告生成在 htmlcov/index.html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| services/ | 80%+ | ✅ |
| models/ | 90%+ | ✅ |
| core/ | 85%+ | ✅ |
| modules/ | 75%+ | ⚠️ |

---

## 🎯 按标记运行测试

### 使用 pytest markers

测试文件使用了 `@pytest.mark.unit` 等标记：

```bash
# 运行所有单元测试
pytest -m unit -v

# 运行所有集成测试
pytest -m integration -v

# 运行所有慢速测试
pytest -m slow -v
```

### 自定义标记组合

```bash
# 运行单元测试，但排除慢速测试
pytest -m "unit and not slow" -v

# 运行集成测试或慢速测试
pytest -m "integration or slow" -v
```

---

## 🐛 调试测试

### 1. 查看详细输出

```bash
# 显示详细输出（包括print语句）
pytest -v -s

# 显示更详细的错误信息
pytest -vv

# 在第一个失败时停止
pytest -x

# 在第N个失败时停止
pytest --maxfail=3
```

### 2. 进入调试器

```bash
# 在失败时进入pdb调试器
pytest --pdb

# 在测试开始时进入pdb调试器
pytest --trace
```

### 3. 只运行失败的测试

```bash
# 只运行上次失败的测试
pytest --lf

# 先运行失败的测试，然后运行其他测试
pytest --ff
```

### 4. 打印本地变量

```bash
# 显示失败测试的本地变量
pytest -l
```

---

## 📝 测试用例编写模板

### 单元测试模板

```python
"""
模块名称单元测试
"""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.modules.your_module.services import your_service
from app.models.your_model import YourModel


@pytest.mark.unit
def test_create_something(db_session: Session):
    """测试创建功能"""
    # 准备测试数据
    test_data = {
        "name": "测试名称",
        "value": "测试值"
    }

    # 执行测试
    result = your_service.create(db_session, test_data)

    # 验证结果
    assert result is not None
    assert result.name == "测试名称"
    assert result.value == "测试值"

    print(f"✓ 测试通过 (ID: {result.id})")


@pytest.mark.unit
def test_get_something(db_session: Session):
    """测试查询功能"""
    # 创建测试数据
    item = YourModel(name="测试项")
    db_session.add(item)
    db_session.commit()

    # 执行查询
    result = your_service.get_detail(db_session, item.id)

    # 验证结果
    assert result is not None
    assert result.id == item.id
    assert result.name == "测试项"

    print(f"✓ 查询测试通过 (ID: {item.id})")


@pytest.mark.unit
def test_update_something(db_session: Session):
    """测试更新功能"""
    # 创建测试数据
    item = YourModel(name="初始名称")
    db_session.add(item)
    db_session.commit()

    # 执行更新
    update_data = {"name": "更新后名称"}
    result = your_service.update(db_session, item.id, update_data)

    # 验证结果
    assert result.name == "更新后名称"

    print(f"✓ 更新测试通过 (ID: {item.id})")


@pytest.mark.unit
def test_delete_something(db_session: Session):
    """测试删除功能"""
    # 创建测试数据
    item = YourModel(name="待删除项")
    db_session.add(item)
    db_session.commit()

    item_id = item.id

    # 执行删除
    result = your_service.delete(db_session, item_id)

    # 验证结果
    assert result is True

    # 验证已删除
    deleted = your_service.get_detail(db_session, item_id)
    assert deleted is None

    print("✓ 删除测试通过")
```

### Mock 测试模板

```python
@pytest.mark.unit
@patch('app.modules.your_module.external_service')
def test_with_mock_service(mock_external, db_session: Session):
    """测试使用Mock的服务"""
    # 配置Mock返回值
    mock_external.some_method.return_value = {
        "status": "success",
        "data": "mocked data"
    }

    # 执行测试
    result = your_service.do_something(db_session, 1)

    # 验证Mock被调用
    mock_external.some_method.assert_called_once()

    # 验证结果
    assert result is not None

    print("✓ Mock测试通过")
```

---

## 🔍 常见问题排查

### 问题1: 导入错误 `ModuleNotFoundError`

**错误信息**:
```
ModuleNotFoundError: No module named 'app'
```

**解决方案**:
```bash
# 确保在项目根目录执行
cd src/backend

# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 或使用 pytest 的配置文件
# pytest.ini 中已配置 pythonpath
```

### 问题2: 数据库错误

**错误信息**:
```
sqlalchemy.exc.OperationalError: no such table
```

**解决方案**:
```bash
# 测试使用内存数据库，会自动创建
# 如果遇到问题，检查 conftest.py 中的 fixture

# 手动初始化测试数据库
python -c "
from app.db.database import init_db
init_db()
"
```

### 问题3: Fixture 未找到

**错误信息**:
```
fixture 'db_session' not found
```

**解决方案**:
```bash
# 确保 conftest.py 在正确位置
ls tests/conftest.py

# 检查 fixture 作用域
pytest --fixtures
```

### 问题4: 异步测试失败

**错误信息**:
```
RuntimeError: Event loop is closed
```

**解决方案**:
```bash
# 安装 pytest-asyncio
pip install pytest-asyncio

# 在测试文件中添加标记
@pytest.mark.asyncio
async def test_async_function():
    ...
```

### 问题5: 时间相关的测试不稳定

**解决方案**:
```python
# 使用 freezegun 冻结时间
pip install freezegun

import freezegun

@freezegun.freeze_time("2026-02-01")
def test_time_dependent():
    # 时间将被冻结在 2026-02-01
    assert datetime.now().year == 2026
```

---

## 📊 测试报告

### 生成测试报告

```bash
# 生成 JUnit XML 报告（用于CI/CD）
pytest --junitxml=test-report.xml

# 生成 HTML 测试报告
pytest-html pytest --html=test-report.html --self-contained-html

# 生成详细报告
pytest -v --tb=long > test-output.txt
```

### 查看测试统计

```bash
# 显示最慢的10个测试
pytest --durations=10

# 显示所有测试的持续时间
pytest --durations=all
```

---

## 🎪 完整测试流程示例

### 1. 开发新功能前的测试

```bash
# 1. 确保所有测试通过
pytest -v

# 2. 检查覆盖率
pytest --cov=app --cov-report=term-missing

# 3. 记录当前测试数量
pytest --collect-only -q
```

### 2. 开发过程中的测试

```bash
# 1. 只运行相关模块的测试
pytest tests/unit/services/test_your_service.py -v

# 2. 运行到第一个失败
pytest tests/unit/services/test_your_service.py -x

# 3. 在失败时进入调试
pytest tests/unit/services/test_your_service.py --pdb
```

### 3. 提交代码前的测试

```bash
# 1. 运行完整测试套件
pytest -v

# 2. 生成覆盖率报告
pytest --cov=app --cov-report=html

# 3. 检查代码质量
pytest -v --flakes  # 需要安装 pytest-flakes

# 4. 运行linting
pytest -v --pylint  # 需要安装 pytest-pylint
```

---

## 📋 测试检查清单

使用以下清单确保测试完整性：

### 功能覆盖
- [ ] 所有公共方法都有测试
- [ ] 所有错误路径都有测试
- [ ] 边界条件都有测试
- [ ] 异常情况都有处理

### 测试质量
- [ ] 测试可以独立运行
- [ ] 测试可以重复运行
- [ ] 测试运行速度快
- [ ] 测试有清晰的描述

### 测试文档
- [ ] 测试文件有文档字符串
- [ ] 复杂逻辑有注释
- [ ] 测试数据有说明

---

## 🚀 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        cd src/backend
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd src/backend
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./src/backend/coverage.xml
```

---

## 📚 相关文档

- [E2E测试手动执行指南](E2E_TEST_MANUAL_GUIDE.md) - 端到端测试指南
- [E2E测试最终报告](E2E_TEST_FINAL_REPORT.md) - E2E测试结果报告
- [pytest 官方文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)

---

## 💡 最佳实践

### 1. 测试命名规范
```python
# ✅ 好的命名
def test_create_user_with_valid_data():
def test_create_user_with_duplicate_email_raises_error():

# ❌ 不好的命名
def test_1():
def test_user():
```

### 2. 测试结构（AAA模式）
```python
def test_something():
    # Arrange - 准备测试数据
    data = {"name": "test"}

    # Act - 执行测试操作
    result = service.create(data)

    # Assert - 验证结果
    assert result.name == "test"
```

### 3. 使用 Fixture
```python
# ✅ 使用 fixture 复用代码
@pytest.fixture
def test_data():
    return {"name": "test", "value": 123}

def test_with_fixture(test_data):
    result = service.create(test_data)
    assert result is not None

# ❌ 重复创建测试数据
def test_without_fixture():
    data = {"name": "test", "value": 123}
    result = service.create(data)
    assert result is not None
```

### 4. 保持测试独立
```python
# ✅ 每个测试独立
def test_create(db_session):
    item = Item(name="test1")
    db_session.add(item)
    db_session.commit()
    assert item.id is not None

def test_update(db_session):
    item = Item(name="test2")  # 新的数据
    db_session.add(item)
    db_session.commit()
    updated = service.update(item.id, {"name": "updated"})
    assert updated.name == "updated"

# ❌ 测试间有依赖
def test_create(db_session):
    global item_id
    item = Item(name="test")
    db_session.add(item)
    db_session.commit()
    item_id = item.id

def test_update(db_session):
    # 依赖上面的 item_id
    updated = service.update(item_id, {"name": "updated"})
```

---

**提示**: 定期运行测试并保持高覆盖率是保证代码质量的关键。建议在每次提交代码前运行相关测试。

**测试命令速查**:
```bash
pytest                           # 运行所有测试
pytest -v                        # 显示详细输出
pytest -s                        # 显示print输出
pytest -x                        # 第一个失败时停止
pytest -k "keyword"              # 运行匹配关键字的测试
pytest --cov                     # 生成覆盖率报告
pytest --lf                      # 只运行上次失败的测试
```
