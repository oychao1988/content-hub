"""客户管理服务单元测试"""

import pytest
from sqlalchemy.orm import Session
from app.modules.customer.services import CustomerService
from app.models.customer import Customer


class TestCustomerService:
    """客户管理服务测试类"""

    def test_create_customer(self, db_session: Session):
        """测试创建客户"""
        # 准备测试数据
        customer_data = {
            "name": "测试客户1",
            "contact_name": "张三",
            "contact_email": "zhangsan@example.com",
            "contact_phone": "13800138001",
            "description": "这是一个测试客户",
            "is_active": True
        }

        # 执行测试
        customer = CustomerService.create(db_session, customer_data)

        # 断言结果
        assert customer is not None
        assert customer.name == "测试客户1"
        assert customer.contact_name == "张三"
        assert customer.contact_email == "zhangsan@example.com"
        assert customer.contact_phone == "13800138001"
        assert customer.description == "这是一个测试客户"
        assert customer.is_active is True

    def test_get_customer_by_id(self, db_session: Session):
        """测试通过ID获取客户"""
        # 创建测试数据
        customer_data = {
            "name": "测试客户2",
            "contact_name": "李四",
            "contact_email": "lisi@example.com",
            "contact_phone": "13800138002",
            "is_active": True
        }
        customer = CustomerService.create(db_session, customer_data)

        # 执行测试
        retrieved = CustomerService.get_by_id(db_session, customer.id)

        # 断言结果
        assert retrieved is not None
        assert retrieved.id == customer.id
        assert retrieved.name == customer.name

    def test_get_all_customers(self, db_session: Session):
        """测试获取客户列表"""
        # 创建多个测试客户
        for i in range(3):
            CustomerService.create(db_session, {
                "name": f"客户{i+1}",
                "contact_name": f"联系人{i+1}",
                "contact_email": f"contact{i+1}@example.com",
                "contact_phone": f"1380013800{i+1}",
                "is_active": True
            })

        # 执行测试
        customers, total = CustomerService.get_all(db_session)

        # 断言结果
        assert total >= 3
        assert len(customers) >= 3

    def test_search_customers(self, db_session: Session):
        """测试搜索客户"""
        # 创建测试数据
        CustomerService.create(db_session, {
            "name": "腾讯科技",
            "contact_name": "马化腾",
            "contact_email": "mahuateng@qq.com",
            "contact_phone": "13800138888",
            "is_active": True
        })

        # 执行测试
        customers, total = CustomerService.get_all(db_session, search="腾讯")

        # 断言结果
        assert total >= 1
        assert any("腾讯" in customer.name for customer in customers)

    def test_update_customer(self, db_session: Session):
        """测试更新客户"""
        # 创建测试数据
        customer_data = {
            "name": "原始客户",
            "contact_name": "王五",
            "contact_email": "wangwu@example.com",
            "contact_phone": "13800138003",
            "is_active": True
        }
        customer = CustomerService.create(db_session, customer_data)

        # 执行测试
        update_data = {
            "name": "更新后的客户",
            "contact_name": "赵六",
            "contact_email": "zhaoliu@example.com",
            "contact_phone": "13800138004",
            "is_active": False
        }
        updated = CustomerService.update(db_session, customer.id, update_data)

        # 断言结果
        assert updated is not None
        assert updated.name == "更新后的客户"
        assert updated.contact_name == "赵六"
        assert updated.contact_email == "zhaoliu@example.com"
        assert updated.contact_phone == "13800138004"
        assert updated.is_active is False

    def test_delete_customer(self, db_session: Session):
        """测试删除客户"""
        # 创建测试数据
        customer_data = {
            "name": "待删除客户",
            "contact_name": "孙七",
            "contact_email": "sunqi@example.com",
            "contact_phone": "13800138005",
            "is_active": True
        }
        customer = CustomerService.create(db_session, customer_data)

        # 执行测试
        deleted = CustomerService.delete(db_session, customer.id)

        # 断言结果
        assert deleted is True

        # 验证客户已删除
        retrieved = CustomerService.get_by_id(db_session, customer.id)
        assert retrieved is None

    def test_get_nonexistent_customer(self, db_session: Session):
        """测试获取不存在的客户"""
        # 执行测试
        customer = CustomerService.get_by_id(db_session, 9999)

        # 断言结果
        assert customer is None

    def test_update_nonexistent_customer(self, db_session: Session):
        """测试更新不存在的客户"""
        # 执行测试
        updated = CustomerService.update(db_session, 9999, {"name": "不存在的客户"})

        # 断言结果
        assert updated is None

    def test_delete_nonexistent_customer(self, db_session: Session):
        """测试删除不存在的客户"""
        # 执行测试
        deleted = CustomerService.delete(db_session, 9999)

        # 断言结果
        assert deleted is False

    def test_pagination(self, db_session: Session):
        """测试分页功能"""
        # 创建多个客户
        for i in range(5):
            CustomerService.create(db_session, {
                "name": f"分页客户{i+1}",
                "contact_name": f"联系人{i+1}",
                "contact_email": f"page{i+1}@example.com",
                "contact_phone": f"13800138{i+10}",
                "is_active": True
            })

        # 测试第一页
        customers1, total1 = CustomerService.get_all(db_session, skip=0, limit=2)
        assert len(customers1) == 2

        # 测试第二页
        customers2, total2 = CustomerService.get_all(db_session, skip=2, limit=2)
        assert len(customers2) == 2

        # 总数量应该一致
        assert total1 == total2
