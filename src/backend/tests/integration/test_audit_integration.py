"""
审计日志集成测试
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.audit_log import AuditLog
from app.models.user import User
from app.core.security import create_access_token, hash_password


class TestAuditIntegration:
    """审计日志集成测试"""

    def test_audit_log_on_login_success(self, client: TestClient, db_session: Session, test_user: User):
        """测试登录成功时记录审计日志"""
        # 登录
        response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpass123"
        })

        # 验证登录成功
        assert response.status_code == 200

        # 验证审计日志已创建
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == "user_login",
            AuditLog.user_id == test_user.id
        ).all()

        assert len(audit_logs) > 0
        assert audit_logs[0].result == "success"
        assert audit_logs[0].details["username"] == test_user.username

    def test_audit_log_on_login_failure(self, client: TestClient, db_session: Session, test_user: User):
        """测试登录失败时记录审计日志"""
        # 使用错误密码登录
        response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword"
        })

        # 验证登录失败
        assert response.status_code == 401

        # 验证审计日志已创建
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == "user_login_failed"
        ).all()

        assert len(audit_logs) > 0
        assert audit_logs[0].result == "failure"

    def test_get_audit_logs_as_admin(self, client: TestClient, db_session: Session, admin_user: User):
        """测试管理员获取审计日志"""
        # 创建管理员 token
        token = create_access_token(str(admin_user.id))

        # 创建一些审计日志
        for i in range(5):
            log = AuditLog(
                event_type="test_event",
                user_id=admin_user.id,
                result="success",
                details={"index": i}
            )
            db_session.add(log)
        db_session.commit()

        # 获取审计日志
        response = client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert data["total"] >= 5

    def test_get_audit_logs_as_operator_forbidden(self, client: TestClient, operator_user: User):
        """测试非管理员访问审计日志被拒绝"""
        # 创建操作员 token
        token = create_access_token(str(operator_user.id))

        # 尝试获取审计日志
        response = client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 验证被拒绝
        assert response.status_code == 403

    def test_get_audit_logs_with_filters(self, client: TestClient, db_session: Session, admin_user: User):
        """测试带过滤条件的审计日志查询"""
        # 创建管理员 token
        token = create_access_token(str(admin_user.id))

        # 创建不同类型的审计日志
        log1 = AuditLog(event_type="user_login", user_id=1, result="success", details={})
        log2 = AuditLog(event_type="content_create", user_id=1, result="success", details={})
        log3 = AuditLog(event_type="user_login", user_id=2, result="failure", details={})
        db_session.add_all([log1, log2, log3])
        db_session.commit()

        # 按事件类型过滤
        response = client.get(
            "/api/v1/audit/logs?event_type=user_login",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 验证结果
        assert response.status_code == 200
        data = response.json()
        assert all(log["event_type"] == "user_login" for log in data["logs"])

    def test_get_audit_log_detail(self, client: TestClient, db_session: Session, admin_user: User):
        """测试获取审计日志详情"""
        # 创建管理员 token
        token = create_access_token(str(admin_user.id))

        # 创建审计日志
        log = AuditLog(
            event_type="test_event",
            user_id=admin_user.id,
            result="success",
            details={"test": "data"},
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        # 获取日志详情
        response = client.get(
            f"/api/v1/audit/logs/{log.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log.id
        assert data["event_type"] == "test_event"
        assert data["ip_address"] == "192.168.1.100"
        assert data["user_agent"] == "Test Browser"

    def test_export_audit_logs(self, client: TestClient, db_session: Session, admin_user: User):
        """测试导出审计日志"""
        # 创建管理员 token
        token = create_access_token(str(admin_user.id))

        # 创建测试数据
        for i in range(3):
            log = AuditLog(
                event_type="test_event",
                user_id=admin_user.id,
                result="success",
                details={"index": i}
            )
            db_session.add(log)
        db_session.commit()

        # 导出日志
        today = date.today()
        response = client.post(
            "/api/v1/audit/logs/export",
            json={
                "start_date": today.isoformat(),
                "end_date": today.isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logs" in data["data"]
        assert len(data["data"]["logs"]) >= 3

    def test_get_audit_statistics(self, client: TestClient, db_session: Session, admin_user: User):
        """测试获取审计统计信息"""
        # 创建管理员 token
        token = create_access_token(str(admin_user.id))

        # 创建测试数据
        log1 = AuditLog(event_type="user_login", user_id=1, result="success", details={})
        log2 = AuditLog(event_type="user_login", user_id=1, result="failure", details={})
        log3 = AuditLog(event_type="content_create", user_id=2, result="success", details={})
        db_session.add_all([log1, log2, log3])
        db_session.commit()

        # 获取统计信息
        response = client.get(
            "/api/v1/audit/statistics",
            headers={"Authorization": f"Bearer {token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data
        assert "success_count" in data
        assert "failure_count" in data
        assert "success_rate" in data
        assert "event_type_stats" in data
        assert "top_users" in data
        assert data["total_logs"] >= 3


# Fixtures
@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        full_name="Test User",
        role="operator",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """创建管理员用户"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        full_name="Admin User",
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def operator_user(db_session: Session):
    """创建操作员用户"""
    user = User(
        username="operator",
        email="operator@example.com",
        password_hash=hash_password("operatorpass123"),
        full_name="Operator User",
        role="operator",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session: Session):
    """创建测试客户端"""
    from app.db.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
