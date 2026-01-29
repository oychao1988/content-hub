"""
API 响应时间性能测试

测试目标：
- GET 请求：P95 < 200ms
- POST 请求：P95 < 500ms

测试接口：
- 登录接口
- 账号列表查询
- 内容列表查询
- 写作风格查询
- 仪表板统计
"""

import pytest
from httpx import Client
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import create_password_hash
from app.models.user import User


# 测试基准
GET_P95_TARGET = 200  # ms
POST_P95_TARGET = 500  # ms


@pytest.fixture(scope="module")
def test_client():
    """创建测试客户端"""
    base_url = "http://localhost:8000"
    return Client(base_url=base_url, timeout=10.0)


@pytest.fixture(scope="module")
def auth_token(test_client, db_session):
    """获取认证 token"""
    # 确保测试用户存在
    user = db_session.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin",
            email="admin@test.com",
            password_hash=create_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

    # 登录获取 token
    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture(scope="module")
def db_session():
    """获取数据库会话"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@pytest.mark.benchmark(group="api_response_time")
class TestAPIResponseTime:
    """API 响应时间测试"""

    def test_login_response_time(self, benchmark, test_client):
        """测试登录接口响应时间"""

        def login():
            response = test_client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            assert response.status_code == 200
            return response

        result = benchmark.pedantic(login, iterations=10, rounds=5)
        response_time = result.elapsed.total_seconds() * 1000  # 转换为毫秒

        # 验证 POST 请求 P95 < 500ms
        assert response_time < POST_P95_TARGET, \
            f"Login API response time {response_time}ms exceeds target {POST_P95_TARGET}ms"

    def test_accounts_list_response_time(self, benchmark, test_client, auth_token):
        """测试账号列表查询响应时间"""

        def get_accounts():
            response = test_client.get(
                "/api/v1/accounts/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            return response

        result = benchmark.pedantic(get_accounts, iterations=20, rounds=5)
        response_time = result.elapsed.total_seconds() * 1000

        # 验证 GET 请求 P95 < 200ms
        assert response_time < GET_P95_TARGET, \
            f"Accounts List API response time {response_time}ms exceeds target {GET_P95_TARGET}ms"

    def test_contents_list_response_time(self, benchmark, test_client, auth_token):
        """测试内容列表查询响应时间"""

        def get_contents():
            response = test_client.get(
                "/api/v1/contents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            return response

        result = benchmark.pedantic(get_contents, iterations=20, rounds=5)
        response_time = result.elapsed.total_seconds() * 1000

        # 验证 GET 请求 P95 < 200ms
        assert response_time < GET_P95_TARGET, \
            f"Contents List API response time {response_time}ms exceeds target {GET_P95_TARGET}ms"

    def test_writing_styles_response_time(self, benchmark, test_client, auth_token):
        """测试写作风格查询响应时间"""

        def get_writing_styles():
            response = test_client.get(
                "/api/v1/config/writing-styles",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            return response

        result = benchmark.pedantic(get_writing_styles, iterations=20, rounds=5)
        response_time = result.elapsed.total_seconds() * 1000

        # 验证 GET 请求 P95 < 200ms
        assert response_time < GET_P95_TARGET, \
            f"Writing Styles API response time {response_time}ms exceeds target {GET_P95_TARGET}ms"

    def test_dashboard_stats_response_time(self, benchmark, test_client, auth_token):
        """测试仪表板统计响应时间"""

        def get_dashboard():
            response = test_client.get(
                "/api/v1/dashboard/stats",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            return response

        result = benchmark.pedantic(get_dashboard, iterations=20, rounds=5)
        response_time = result.elapsed.total_seconds() * 1000

        # 验证 GET 请求 P95 < 200ms
        assert response_time < GET_P95_TARGET, \
            f"Dashboard Stats API response time {response_time}ms exceeds target {GET_P95_TARGET}ms"

    def test_platforms_list_response_time(self, benchmark, test_client, auth_token):
        """测试平台列表查询响应时间"""

        def get_platforms():
            response = test_client.get(
                "/api/v1/platforms/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            return response

        result = benchmark.pedantic(get_platforms, iterations=20, rounds=5)
        response_time = result.elapsed.total_seconds() * 1000

        # 验证 GET 请求 P95 < 200ms
        assert response_time < GET_P95_TARGET, \
            f"Platforms List API response time {response_time}ms exceeds target {GET_P95_TARGET}ms"


# 运行说明
"""
运行这些测试需要：
1. 后端服务正在运行（python main.py）
2. 数据库中有测试数据
3. 已安装 pytest-benchmark

运行命令：
pytest tests/performance/test_api_response_time.py -v --benchmark-only

生成基准测试报告：
pytest tests/performance/test_api_response_time.py -v --benchmark-only --benchmark-json=benchmark_results.json

比较历史数据：
pytest tests/performance/test_api_response_time.py -v --benchmark-only --benchmark-compare=[benchmark_file.json]
"""
