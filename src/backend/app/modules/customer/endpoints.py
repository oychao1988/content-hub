"""
客户管理 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.modules.customer.services import customer_service
from app.modules.customer.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse
)
from app.db.database import get_db
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user

router = APIRouter(tags=["customers"])


@router.get("/", response_model=CustomerListResponse)
@require_permission(Permission.CUSTOMER_READ)
async def get_customers(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取客户列表

    支持分页和搜索功能：
    - skip: 跳过的记录数（默认0）
    - limit: 返回的记录数（默认20，最大100）
    - search: 搜索关键词，会搜索客户名称、联系人姓名、邮箱、电话
    """
    customers, total = customer_service.get_all(db, skip=skip, limit=limit, search=search)
    return CustomerListResponse(items=customers, total=total)


@router.get("/{customer_id}", response_model=CustomerResponse)
@require_permission(Permission.CUSTOMER_READ)
async def get_customer(customer_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    获取客户详情

    Args:
        customer_id: 客户ID

    Returns:
        客户详情
    """
    customer = customer_service.get_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer


@router.post("/", response_model=CustomerResponse, status_code=201)
@require_permission(Permission.CUSTOMER_CREATE)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    创建客户

    Args:
        customer: 客户创建数据

    Returns:
        创建的客户
    """
    # 检查客户名称是否已存在
    from app.models.customer import Customer
    existing = db.query(Customer).filter(Customer.name == customer.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="客户名称已存在")

    return customer_service.create(db, customer.dict())


@router.put("/{customer_id}", response_model=CustomerResponse)
@require_permission(Permission.CUSTOMER_UPDATE)
async def update_customer(
    customer_id: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新客户

    Args:
        customer_id: 客户ID
        customer: 客户更新数据

    Returns:
        更新后的客户
    """
    # 如果要更新名称，检查是否与其他客户冲突
    if customer.name is not None:
        from app.models.customer import Customer
        existing = db.query(Customer).filter(
            Customer.name == customer.name,
            Customer.id != customer_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="客户名称已被其他客户使用")

    updated_customer = customer_service.update(
        db, customer_id, customer.dict(exclude_unset=True)
    )
    if not updated_customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return updated_customer


@router.delete("/{customer_id}")
@require_permission(Permission.CUSTOMER_DELETE)
async def delete_customer(customer_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    删除客户

    Args:
        customer_id: 客户ID

    Returns:
        删除结果
    """
    success = customer_service.delete(db, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"message": "客户已删除"}
