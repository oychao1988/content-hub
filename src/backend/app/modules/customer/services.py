"""
客户管理服务
负责客户的创建、查询、更新、删除等操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.customer import Customer


class CustomerService:
    """客户管理服务"""

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None) -> tuple[List[Customer], int]:
        """
        获取客户列表

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            search: 搜索关键词（搜索客户名称、联系人姓名、邮箱、电话）

        Returns:
            (客户列表, 总数)
        """
        query = db.query(Customer)

        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Customer.name.like(search_pattern)) |
                (Customer.contact_name.like(search_pattern)) |
                (Customer.contact_email.like(search_pattern)) |
                (Customer.contact_phone.like(search_pattern))
            )

        # 获取总数
        total = query.count()

        # 分页查询
        customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()

        return customers, total

    @staticmethod
    def get_by_id(db: Session, customer_id: int) -> Optional[Customer]:
        """
        获取单个客户

        Args:
            db: 数据库会话
            customer_id: 客户ID

        Returns:
            客户对象或None
        """
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def create(db: Session, customer_data: dict) -> Customer:
        """
        创建客户

        Args:
            db: 数据库会话
            customer_data: 客户数据

        Returns:
            创建的客户对象
        """
        customer = Customer(**customer_data)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def update(db: Session, customer_id: int, customer_data: dict) -> Optional[Customer]:
        """
        更新客户

        Args:
            db: 数据库会话
            customer_id: 客户ID
            customer_data: 更新的客户数据

        Returns:
            更新后的客户对象或None
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            for key, value in customer_data.items():
                setattr(customer, key, value)
            db.commit()
            db.refresh(customer)
        return customer

    @staticmethod
    def delete(db: Session, customer_id: int) -> bool:
        """
        删除客户

        Args:
            db: 数据库会话
            customer_id: 客户ID

        Returns:
            是否删除成功
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            db.delete(customer)
            db.commit()
            return True
        return False


# 全局服务实例
customer_service = CustomerService()
