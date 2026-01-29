"""
数据库查询性能测试

使用 pytest-benchmark 测试关键数据库查询的性能
识别慢查询并提供优化建议
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.account import Account
from app.models.content import Content
from app.models.platform import Platform
from app.models.user import User
from app.models.customer import Customer


@pytest.fixture(scope="module")
def db_session():
    """获取数据库会话"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@pytest.mark.benchmark(group="db_query_performance")
class TestDatabaseQueryPerformance:
    """数据库查询性能测试"""

    def test_simple_user_query(self, benchmark, db_session: Session):
        """测试简单用户查询性能"""

        def query_users():
            result = db_session.execute(select(User).limit(10))
            return result.scalars().all()

        result = benchmark(query_users)
        assert len(result) <= 10

    def test_user_with_relations_query(self, benchmark, db_session: Session):
        """测试带关联的用户查询（可能存在 N+1 问题）"""

        def query_users_with_relations():
            result = db_session.execute(
                select(User)
                .options(selectinload(User.customer))
                .limit(10)
            )
            return result.scalars().all()

        from sqlalchemy.orm import selectinload
        result = benchmark(query_users_with_relations)
        assert len(result) <= 10

    def test_account_list_query(self, benchmark, db_session: Session):
        """测试账号列表查询性能"""

        def query_accounts():
            result = db_session.execute(
                select(Account)
                .order_by(Account.created_at.desc())
                .limit(20)
            )
            return result.scalars().all()

        result = benchmark(query_accounts)
        assert len(result) <= 20

    def test_account_with_platform_query(self, benchmark, db_session: Session):
        """测试账号关联平台查询"""

        def query_accounts_with_platform():
            from sqlalchemy.orm import selectinload

            result = db_session.execute(
                select(Account)
                .options(selectinload(Account.platform))
                .limit(20)
            )
            return result.scalars().all()

        result = benchmark(query_accounts_with_platform)
        assert len(result) <= 20

    def test_content_list_query(self, benchmark, db_session: Session):
        """测试内容列表查询性能"""

        def query_contents():
            result = db_session.execute(
                select(Content)
                .order_by(Content.created_at.desc())
                .limit(20)
            )
            return result.scalars().all()

        result = benchmark(query_contents)
        assert len(result) <= 20

    def test_content_with_relations_query(self, benchmark, db_session: Session):
        """测试内容关联查询（账号、平台）"""

        def query_contents_with_relations():
            from sqlalchemy.orm import selectinload, joinedload

            result = db_session.execute(
                select(Content)
                .options(
                    joinedload(Content.account),
                    joinedload(Content.platform)
                )
                .limit(20)
            )
            return result.scalars().all()

        result = benchmark(query_contents_with_relations)
        assert len(result) <= 20

    def test_content_filter_by_status_query(self, benchmark, db_session: Session):
        """测试按状态筛选内容查询"""

        def query_contents_by_status():
            result = db_session.execute(
                select(Content)
                .filter(Content.status == "pending")
                .limit(20)
            )
            return result.scalars().all()

        result = benchmark(query_contents_by_status)
        # 不断言结果数量，因为可能没有数据

    def test_platform_list_query(self, benchmark, db_session: Session):
        """测试平台列表查询性能"""

        def query_platforms():
            result = db_session.execute(select(Platform))
            return result.scalars().all()

        result = benchmark(query_platforms)
        assert isinstance(result, list) or hasattr(result, '__iter__')

    def test_aggregation_query(self, benchmark, db_session: Session):
        """测试聚合查询（统计）"""

        def aggregate_stats():
            result = db_session.execute(
                select(
                    func.count(Content.id).label('total_contents'),
                    func.count(Account.id).label('total_accounts')
                )
            )
            return result.one()

        result = benchmark(aggregate_stats)
        assert result.total_contents >= 0
        assert result.total_accounts >= 0

    def test_complex_join_query(self, benchmark, db_session: Session):
        """测试复杂连接查询性能"""

        def complex_join():
            from sqlalchemy import and_

            result = db_session.execute(
                select(Content, Account, Platform)
                .join(Account, Content.account_id == Account.id)
                .join(Platform, Content.platform_id == Platform.id)
                .filter(Content.status == "published")
                .limit(20)
            )
            return result.all()

        result = benchmark(complex_join)
        assert len(result) <= 20

    def test_pagination_query(self, benchmark, db_session: Session):
        """测试分页查询性能（模拟第 10 页）"""

        def paginate():
            page = 10
            page_size = 20
            offset = (page - 1) * page_size

            result = db_session.execute(
                select(Content)
                .order_by(Content.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            return result.scalars().all()

        result = benchmark(paginate)
        assert len(result) <= 20

    def test_count_query(self, benchmark, db_session: Session):
        """测试 COUNT 查询性能"""

        def count_contents():
            result = db_session.execute(
                select(func.count(Content.id))
            )
            return result.scalar()

        result = benchmark(count_contents)
        assert result >= 0


@pytest.mark.benchmark(group="db_write_performance")
class TestDatabaseWritePerformance:
    """数据库写入性能测试"""

    def test_simple_insert(self, benchmark, db_session: Session):
        """测试简单插入性能"""

        def insert_and_rollback():
            # 创建但不提交，测试会自动回滚
            test_content = Content(
                title="Test Content",
                content="Test content body",
                status="draft",
                account_id=1,
                platform_id=1
            )
            db_session.add(test_content)
            db_session.flush()  # 执行但不提交
            db_session.rollback()  # 回滚

        benchmark(insert_and_rollback)

    def test_batch_insert(self, benchmark, db_session: Session):
        """测试批量插入性能"""

        def batch_insert_and_rollback():
            contents = [
                Content(
                    title=f"Test Content {i}",
                    content=f"Test content body {i}",
                    status="draft",
                    account_id=1,
                    platform_id=1
                )
                for i in range(10)
            ]
            db_session.add_all(contents)
            db_session.flush()
            db_session.rollback()

        benchmark(batch_insert_and_rollback)


# 性能优化建议
"""
性能优化建议：

1. 索引优化：
   - 为经常用于查询的字段添加索引（status, created_at 等）
   - 为外键字段添加索引
   - 考虑使用复合索引优化多条件查询

2. 查询优化：
   - 使用 selectinload 或 joinedload 避免 N+1 查询
   - 只查询需要的字段（使用 .with_entities()）
   - 使用 exists() 代替 count() 当只需要判断是否存在

3. 连接池配置：
   - 增加 pool_size 和 max_overflow
   - 启用 pool_pre_ping 避免连接过期

4. 缓存策略：
   - 对不常变化的数据（如平台列表）使用缓存
   - 实现查询结果缓存（Redis）

5. 分页优化：
   - 使用 cursor-based 分页代替 offset-based 分页
   - 避免过大的 offset 值

6. 数据库优化：
   - 定期执行 VACUUM（SQLite）
   - 分析查询计划（EXPLAIN QUERY PLAN）
   - 考虑迁移到 PostgreSQL 用于生产环境
"""

# 运行说明
"""
运行这些测试：
1. 确保数据库有足够的测试数据
2. 运行测试：pytest tests/performance/test_db_query_performance.py -v --benchmark-only

生成性能报告：
pytest tests/performance/test_db_query_performance.py -v --benchmark-only --benchmark-json=db_benchmark.json

识别慢查询：
pytest tests/performance/test_db_query_performance.py -v --benchmark-only --benchmark-sort=name
"""
