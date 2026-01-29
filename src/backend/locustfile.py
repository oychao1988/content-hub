"""
ContentHub 性能测试脚本 - Locust 配置

使用方法:
1. 启动后端服务器: python main.py
2. 运行 Locust: locust -f locustfile.py
3. 访问 Web UI: http://localhost:8089
4. 配置测试参数并开始测试

或使用命令行模式:
locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000
"""

import os
import random
import time
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# 测试配置
BASE_URL = os.getenv("LOCUST_HOST", "http://localhost:8000")

# 测试用户凭据（这些用户应该已经存在于测试数据库中）
TEST_USERS = [
    {"username": "admin", "password": "admin123"},
    {"username": "operator1", "password": "operator123"},
    {"username": "customer1", "password": "customer123"},
]


class ContentHubUser(HttpUser):
    """
    ContentHub 用户行为模拟

    模拟真实用户的使用场景：
    1. 登录系统
    2. 查看仪表板
    3. 查询账号列表
    4. 查询内容列表
    5. 查询平台列表
    6. 查询配置（写作风格、主题）
    """

    # 等待时间：1-3秒之间随机，模拟真实用户思考时间
    wait_time = between(1, 3)

    def on_start(self):
        """用户启动时登录"""
        self.login()

    def on_stop(self):
        """用户停止时可执行清理操作"""
        pass

    def login(self):
        """登录并保存 token"""
        # 随机选择一个测试用户
        user = random.choice(TEST_USERS)

        # 尝试登录
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": user["username"], "password": user["password"]},
            catch_response=True,
            name="[Auth] Login"
        ) as response:

            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success") and data.get("data", {}).get("access_token"):
                        # 保存 token 用于后续请求
                        self.token = data["data"]["access_token"]
                        self.headers = {
                            "Authorization": f"Bearer {self.token}",
                            "Content-Type": "application/json"
                        }
                        response.success()
                    else:
                        response.failure("Login failed: No token in response")
                except Exception as e:
                    response.failure(f"Login failed: {str(e)}")
            else:
                response.failure(f"Login failed with status {response.status_code}")

    @task(3)
    def view_dashboard(self):
        """查看仪表板（权重 3）"""
        if not hasattr(self, 'token'):
            self.login()

        with self.client.get(
            "/api/v1/dashboard/stats",
            headers=self.headers,
            catch_response=True,
            name="[Dashboard] View Stats"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token 过期，重新登录
                self.login()
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(5)
    def view_accounts(self):
        """查看账号列表（权重 5）"""
        if not hasattr(self, 'token'):
            self.login()

        with self.client.get(
            "/api/v1/accounts/",
            headers=self.headers,
            catch_response=True,
            name="[Accounts] List"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.login()
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(4)
    def view_contents(self):
        """查看内容列表（权重 4）"""
        if not hasattr(self, 'token'):
            self.login()

        with self.client.get(
            "/api/v1/contents/",
            headers=self.headers,
            catch_response=True,
            name="[Contents] List"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.login()
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def view_platforms(self):
        """查看平台列表（权重 2）"""
        if not hasattr(self, 'token'):
            self.login()

        with self.client.get(
            "/api/v1/platforms/",
            headers=self.headers,
            catch_response=True,
            name="[Platforms] List"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.login()
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def view_writing_styles(self):
        """查看写作风格列表（权重 2）"""
        if not hasattr(self, 'token'):
            self.login()

        with self.client.get(
            "/api/v1/config/writing-styles",
            headers=self.headers,
            catch_response=True,
            name="[Config] Writing Styles"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.login()
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def view_content_themes(self):
        """查看内容主题列表（权重 1）"""
        if not hasattr(self, 'token'):
            self.login()

        with self.client.get(
            "/api/v1/config/content-themes",
            headers=self.headers,
            catch_response=True,
            name="[Config] Content Themes"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.login()
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


# Locust 事件处理器（可选）
@events.request.add_hook
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    请求事件钩子
    可以在这里添加自定义的日志记录或监控逻辑
    """
    if exception:
        print(f"Request to {name} failed with exception {exception}")
    elif response_time > 1000:  # 响应时间超过 1 秒
        print(f"Request to {name} took {response_time}ms (slow!)")


@events.test_stop.add_hook
def on_test_stop(environment, **kwargs):
    """测试停止时的钩子"""
    if isinstance(environment.runner, MasterRunner):
        print("Test stopped on master node")
    else:
        print("Test stopped on worker/standalone node")


# 性能测试场景预设
class QuickTestUser(ContentHubUser):
    """
    快速测试用户 - 用于快速验证
    减少等待时间，增加请求频率
    """
    wait_time = between(0.5, 1)  # 0.5-1秒


class StressTestUser(ContentHubUser):
    """
    压力测试用户 - 用于压力测试
    最小等待时间，最大化请求频率
    """
    wait_time = between(0.1, 0.5)  # 0.1-0.5秒
