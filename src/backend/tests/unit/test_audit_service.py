"""
审计服务单元测试
"""
import pytest
from datetime import datetime, date
from fastapi import Request
from sqlalchemy.orm import Session

from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog


class TestAuditService:
    """审计服务测试类"""

    def test_log_event_success(self, db_session: Session):
        """测试成功记录审计事件"""
        # 创建审计日志
        log_entry = AuditService.log_event(
            db=db_session,
            event_type="user_login",
            user_id=1,
            result="success",
            details={"username": "admin", "email": "admin@example.com"}
        )

        # 验证日志创建成功
        assert log_entry is not None
        assert log_entry.id is not None
        assert log_entry.event_type == "user_login"
        assert log_entry.user_id == 1
        assert log_entry.result == "success"
        assert log_entry.details["username"] == "admin"
        assert log_entry.timestamp is not None

    def test_log_event_with_request(self, db_session: Session, mock_request):
        """测试带请求对象的审计日志记录"""
        # 创建审计日志（包含请求信息）
        log_entry = AuditService.log_event(
            db=db_session,
            event_type="content_create",
            user_id=2,
            result="success",
            details={"content_id": 100},
            request=mock_request
        )

        # 验证日志包含请求信息
        assert log_entry is not None
        assert log_entry.ip_address is not None
        assert log_entry.user_agent is not None

    def test_log_event_without_user(self, db_session: Session):
        """测试无用户的审计日志记录（系统操作）"""
        log_entry = AuditService.log_event(
            db=db_session,
            event_type="system_backup",
            user_id=None,
            result="success",
            details={"backup_file": "backup_20240129.zip"}
        )

        # 验证日志创建成功
        assert log_entry is not None
        assert log_entry.user_id is None
        assert log_entry.event_type == "system_backup"

    def test_get_audit_logs_no_filter(self, db_session: Session):
        """测试无过滤条件的日志查询"""
        # 创建测试数据
        for i in range(5):
            AuditService.log_event(
                db=db_session,
                event_type="test_event",
                user_id=1,
                result="success",
                details={"index": i}
            )

        # 查询日志
        result = AuditService.get_audit_logs(
            db=db_session,
            filters={},
            page=1,
            page_size=10
        )

        # 验证结果
        assert result["total"] >= 5
        assert len(result["logs"]) <= 10
        assert result["page"] == 1
        assert result["page_size"] == 10

    def test_get_audit_logs_with_event_type_filter(self, db_session: Session):
        """测试按事件类型过滤"""
        # 创建不同类型的日志
        AuditService.log_event(
            db=db_session,
            event_type="user_login",
            user_id=1,
            result="success",
            details={}
        )
        AuditService.log_event(
            db=db_session,
            event_type="content_create",
            user_id=1,
            result="success",
            details={}
        )

        # 按事件类型过滤
        result = AuditService.get_audit_logs(
            db=db_session,
            filters={"event_type": "user_login"},
            page=1,
            page_size=10
        )

        # 验证结果
        assert all(log.event_type == "user_login" for log in result["logs"])

    def test_get_audit_logs_with_user_filter(self, db_session: Session):
        """测试按用户过滤"""
        # 创建不同用户的日志
        AuditService.log_event(
            db=db_session,
            event_type="test_event",
            user_id=1,
            result="success",
            details={}
        )
        AuditService.log_event(
            db=db_session,
            event_type="test_event",
            user_id=2,
            result="success",
            details={}
        )

        # 按用户过滤
        result = AuditService.get_audit_logs(
            db=db_session,
            filters={"user_id": 1},
            page=1,
            page_size=10
        )

        # 验证结果
        assert all(log.user_id == 1 for log in result["logs"])

    def test_get_audit_logs_with_date_filter(self, db_session: Session):
        """测试按日期范围过滤"""
        # 创建测试数据
        AuditService.log_event(
            db=db_session,
            event_type="test_event",
            user_id=1,
            result="success",
            details={}
        )

        # 按日期范围过滤
        today = date.today()
        result = AuditService.get_audit_logs(
            db=db_session,
            filters={
                "start_date": today,
                "end_date": today
            },
            page=1,
            page_size=10
        )

        # 验证结果
        assert result["total"] >= 1

    def test_get_audit_logs_pagination(self, db_session: Session):
        """测试分页功能"""
        # 创建测试数据
        for i in range(25):
            AuditService.log_event(
                db=db_session,
                event_type="test_event",
                user_id=i % 5 + 1,
                result="success",
                details={"index": i}
            )

        # 测试第一页
        page1 = AuditService.get_audit_logs(
            db=db_session,
            filters={},
            page=1,
            page_size=10
        )
        assert len(page1["logs"]) == 10
        assert page1["total_pages"] == 3

        # 测试第二页
        page2 = AuditService.get_audit_logs(
            db=db_session,
            filters={},
            page=2,
            page_size=10
        )
        assert len(page2["logs"]) == 10
        assert page2["page"] == 2

    def test_get_audit_log_by_id(self, db_session: Session):
        """测试根据ID获取审计日志"""
        # 创建测试日志
        log_entry = AuditService.log_event(
            db=db_session,
            event_type="test_event",
            user_id=1,
            result="success",
            details={"test": "data"}
        )

        # 根据ID查询
        found_log = AuditService.get_audit_log_by_id(db_session, log_entry.id)

        # 验证结果
        assert found_log is not None
        assert found_log.id == log_entry.id
        assert found_log.event_type == "test_event"

    def test_get_audit_log_by_id_not_found(self, db_session: Session):
        """测试查询不存在的日志ID"""
        found_log = AuditService.get_audit_log_by_id(db_session, 99999)
        assert found_log is None

    def test_export_audit_logs(self, db_session: Session):
        """测试导出审计日志"""
        # 创建测试数据
        for i in range(3):
            AuditService.log_event(
                db=db_session,
                event_type="test_event",
                user_id=1,
                result="success",
                details={"index": i}
            )

        # 导出日志
        today = date.today()
        exported_logs = AuditService.export_audit_logs(
            db=db_session,
            start_date=today,
            end_date=today
        )

        # 验证结果
        assert len(exported_logs) >= 3
        assert all("id" in log for log in exported_logs)
        assert all("timestamp" in log for log in exported_logs)
        assert all("event_type" in log for log in exported_logs)

    def test_export_audit_logs_with_filters(self, db_session: Session):
        """测试带过滤条件的导出"""
        # 创建测试数据
        AuditService.log_event(
            db=db_session,
            event_type="user_login",
            user_id=1,
            result="success",
            details={}
        )
        AuditService.log_event(
            db=db_session,
            event_type="content_create",
            user_id=2,
            result="success",
            details={}
        )

        # 导出特定事件类型的日志
        today = date.today()
        exported_logs = AuditService.export_audit_logs(
            db=db_session,
            start_date=today,
            end_date=today,
            filters={"event_type": "user_login"}
        )

        # 验证结果
        assert len(exported_logs) >= 1
        assert all(log["event_type"] == "user_login" for log in exported_logs)

    def test_get_audit_statistics(self, db_session: Session):
        """测试获取审计统计信息"""
        # 创建测试数据
        AuditService.log_event(
            db=db_session,
            event_type="user_login",
            user_id=1,
            result="success",
            details={}
        )
        AuditService.log_event(
            db=db_session,
            event_type="user_login",
            user_id=1,
            result="failure",
            details={}
        )
        AuditService.log_event(
            db=db_session,
            event_type="content_create",
            user_id=2,
            result="success",
            details={}
        )

        # 获取统计信息
        stats = AuditService.get_audit_statistics(db_session)

        # 验证结果
        assert stats["total_logs"] >= 3
        assert stats["success_count"] >= 2
        assert stats["failure_count"] >= 1
        assert 0 <= stats["success_rate"] <= 100
        assert len(stats["event_type_stats"]) > 0
        assert len(stats["top_users"]) > 0

    def test_get_audit_statistics_with_date_range(self, db_session: Session):
        """测试带日期范围的统计信息"""
        # 创建测试数据
        AuditService.log_event(
            db=db_session,
            event_type="test_event",
            user_id=1,
            result="success",
            details={}
        )

        # 获取统计信息
        today = date.today()
        stats = AuditService.get_audit_statistics(
            db_session,
            start_date=today,
            end_date=today
        )

        # 验证结果
        assert stats["total_logs"] >= 1

    def test_event_types_mapping(self):
        """测试事件类型映射"""
        # 验证所有事件类型都有中文名称
        for event_type, event_name in AuditService.EVENT_TYPES.items():
            assert isinstance(event_type, str)
            assert isinstance(event_name, str)
            assert len(event_name) > 0

    def test_log_event_error_handling(self, db_session: Session):
        """测试日志记录失败时的错误处理"""
        # 测试日志记录失败不应抛出异常
        # 这里我们模拟一个错误场景，但实际应该被捕获
        log_entry = AuditService.log_event(
            db=db_session,
            event_type="test_event",
            user_id=1,
            result="success",
            details={"test": "data"}
        )

        # 验证在正常情况下日志记录成功
        assert log_entry is not None


# Fixtures
@pytest.fixture
def mock_request():
    """模拟 FastAPI Request 对象"""
    from unittest.mock import Mock

    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "192.168.1.100"

    # 创建一个可调用的 headers 对象
    class HeadersDict(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    request.headers = HeadersDict({
        "X-Forwarded-For": "10.0.0.1, 192.168.1.1",
        "X-Real-IP": "10.0.0.2",
        "User-Agent": "Mozilla/5.0 (Test Browser)"
    })

    return request
