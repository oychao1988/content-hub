"""定时任务 API 集成测试"""

import pytest
from fastapi.testclient import TestClient


class TestSchedulerEndpoints:
    """定时任务 API 端点测试类"""

    def test_create_scheduled_task(self, client: TestClient, auth_headers):
        """测试创建定时任务"""
        task_data = {
            "name": "每日内容生成",
            "description": "每天早上8点自动生成内容",
            "task_type": "content_generation",
            "cron_expression": "0 8 * * *",
            "task_config": {
                "account_id": 1,
                "content_count": 5
            },
            "is_active": True
        }

        response = client.post(
            "/api/v1/scheduler/tasks",
            json=task_data,
            headers=auth_headers
        )

        # 验证结果
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "每日内容生成"
        assert data["task_type"] == "content_generation"
        assert data["cron_expression"] == "0 8 * * *"
        assert data["is_active"] is True

    def test_get_scheduled_task_list(self, client: TestClient, auth_headers):
        """测试获取定时任务列表"""
        # 创建测试任务
        for i in range(3):
            client.post(
                "/api/v1/scheduler/tasks",
                json={
                    "name": f"定时任务{i+1}",
                    "description": f"这是第{i+1}个定时任务",
                    "task_type": "content_generation" if i % 2 == 0 else "publishing",
                    "cron_expression": f"0 {i*8} * * *",
                    "is_active": True
                },
                headers=auth_headers
            )

        # 获取任务列表
        response = client.get("/api/v1/scheduler/tasks", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_get_scheduled_task_detail(self, client: TestClient, auth_headers):
        """测试获取定时任务详情"""
        # 创建测试任务
        create_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "详情测试任务",
                "description": "用于详情测试的定时任务",
                "task_type": "publishing",
                "cron_expression": "0 12 * * *",
                "is_active": True
            },
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # 获取任务详情
        response = client.get(f"/api/v1/scheduler/tasks/{task_id}", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["name"] == "详情测试任务"

    def test_update_scheduled_task(self, client: TestClient, auth_headers):
        """测试更新定时任务"""
        # 创建测试任务
        create_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "原任务名称",
                "description": "原始任务描述",
                "task_type": "content_generation",
                "cron_expression": "0 8 * * *",
                "is_active": True
            },
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # 更新任务
        update_data = {
            "name": "更新后的任务名称",
            "description": "更新后的任务描述",
            "cron_expression": "0 10 * * *",
            "is_active": False
        }
        response = client.put(
            f"/api/v1/scheduler/tasks/{task_id}",
            json=update_data,
            headers=auth_headers
        )

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的任务名称"
        assert data["cron_expression"] == "0 10 * * *"
        assert data["is_active"] is False

    def test_delete_scheduled_task(self, client: TestClient, auth_headers):
        """测试删除定时任务"""
        # 创建测试任务
        create_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "待删除任务",
                "description": "这个任务将被删除",
                "task_type": "content_generation",
                "cron_expression": "0 8 * * *",
                "is_active": True
            },
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # 删除任务
        response = client.delete(f"/api/v1/scheduler/tasks/{task_id}", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200

        # 验证任务已删除
        get_response = client.get(f"/api/v1/scheduler/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_execute_scheduled_task(self, client: TestClient, auth_headers):
        """测试执行定时任务"""
        # 创建测试任务
        create_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "立即执行任务",
                "description": "用于测试立即执行的任务",
                "task_type": "content_generation",
                "cron_expression": "0 8 * * *",
                "is_active": True
            },
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # 手动执行任务
        response = client.post(f"/api/v1/scheduler/tasks/{task_id}/execute", headers=auth_headers)

        # 验证结果（可能返回200或202）
        assert response.status_code in [200, 202]

    def test_get_task_execution_history(self, client: TestClient, auth_headers):
        """测试获取任务执行历史"""
        # 创建测试任务
        create_response = client.post(
            "/api/v1/scheduler/tasks",
            json={
                "name": "历史记录任务",
                "description": "用于测试执行历史的任务",
                "task_type": "content_generation",
                "cron_expression": "0 8 * * *",
                "is_active": True
            },
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        # 获取执行历史
        response = client.get(f"/api/v1/scheduler/tasks/{task_id}/history", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_task_pagination(self, client: TestClient, auth_headers):
        """测试任务分页"""
        # 创建多个任务
        for i in range(5):
            client.post(
                "/api/v1/scheduler/tasks",
                json={
                    "name": f"分页测试任务{i+1}",
                    "description": f"用于分页测试的任务{i+1}",
                    "task_type": "content_generation",
                    "cron_expression": f"0 {i*2} * * *",
                    "is_active": True
                },
                headers=auth_headers
            )

        # 测试分页
        response = client.get("/api/v1/scheduler/tasks?page=1&page_size=3", headers=auth_headers)

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3
        assert data["page"] == 1
        assert data["page_size"] == 3

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/v1/scheduler/tasks")
        assert response.status_code == 401
