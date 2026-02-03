"""
用户管理 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["users"])


@router.get("/", response_model=dict)
async def get_users(
    username: Optional[str] = Query(None, description="用户名筛选"),
    role: Optional[str] = Query(None, description="角色筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取用户列表

    支持分页和筛选功能
    """
    # 构建查询
    query = db.query(User)

    # 筛选条件
    if username:
        query = query.filter(User.username.contains(username))
    if role:
        query = query.filter(User.role == role)
    if status:
        is_active = status.lower() == "active"
        query = query.filter(User.is_active == is_active)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()

    # 转换为响应格式
    items = []
    for user in users:
        items.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }


@router.post("/", response_model=dict)
async def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建新用户"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.get("username")).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    if user_data.get("email"):
        existing_email = db.query(User).filter(User.email == user_data.get("email")).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="邮箱已存在")

    # 创建新用户
    from app.core.security import get_password_hash, create_salt

    # 生成盐值和哈希密码
    salt = create_salt()
    password_hash = get_password_hash(user_data.get("password", "123456"), salt)

    new_user = User(
        username=user_data.get("username"),
        email=user_data.get("email"),
        password_hash=password_hash,
        role=user_data.get("role", "viewer"),
        is_active=user_data.get("is_active", True)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if "email" in user_data:
        user.email = user_data["email"]
    if "role" in user_data:
        user.role = user_data["role"]
    if "is_active" in user_data:
        user.is_active = user_data["is_active"]

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")

    db.delete(user)
    db.commit()

    return {"message": "用户已删除"}
