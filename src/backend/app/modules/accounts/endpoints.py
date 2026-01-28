from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.modules.accounts.services import account_service
from app.modules.accounts.schemas import (
    AccountCreate, AccountUpdate, AccountRead, AccountDetailRead,
    WritingStyleUpdate, WritingStyleRead,
    PublishConfigUpdate, PublishConfigRead
)
from app.db.database import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/", response_model=list[AccountRead])
async def get_account_list(db: Session = Depends(get_db)):
    """获取账号列表"""
    return account_service.get_account_list(db)

@router.get("/{id}", response_model=AccountDetailRead)
async def get_account_detail(id: int, db: Session = Depends(get_db)):
    """获取账号详情（含所有配置）"""
    account = account_service.get_account_detail(db, id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account

@router.post("/", response_model=AccountRead)
async def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """创建账号"""
    return account_service.create_account(db, account.dict())

@router.put("/{id}", response_model=AccountRead)
async def update_account(id: int, account: AccountUpdate, db: Session = Depends(get_db)):
    """更新账号"""
    updated_account = account_service.update_account(db, id, account.dict(exclude_unset=True))
    if not updated_account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return updated_account

@router.delete("/{id}")
async def delete_account(id: int, db: Session = Depends(get_db)):
    """删除账号"""
    success = account_service.delete_account(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"message": "账号已删除"}

@router.post("/{id}/import-md")
async def import_from_markdown(id: int, db: Session = Depends(get_db)):
    """从 Markdown 导入配置"""
    result = account_service.import_from_markdown(db, id)
    return result

@router.post("/{id}/export-md")
async def export_to_markdown(id: int, db: Session = Depends(get_db)):
    """导出配置到 Markdown"""
    content = account_service.export_to_markdown(db, id)
    return {"content": content}

@router.post("/{id}/switch")
async def switch_active_account(id: int, db: Session = Depends(get_db)):
    """切换活动账号"""
    result = account_service.switch_active_account(db, id)
    return result

@router.get("/{id}/writing-style", response_model=WritingStyleRead)
async def get_writing_style(id: int, db: Session = Depends(get_db)):
    """获取写作风格配置"""
    style = account_service.get_writing_style(db, id)
    if not style:
        raise HTTPException(status_code=404, detail="写作风格配置不存在")
    return style

@router.put("/{id}/writing-style", response_model=WritingStyleRead)
async def update_writing_style(id: int, style: WritingStyleUpdate, db: Session = Depends(get_db)):
    """更新写作风格配置"""
    updated_style = account_service.update_writing_style(db, id, style.dict(exclude_unset=True))
    return updated_style

@router.get("/{id}/publish-config", response_model=PublishConfigRead)
async def get_publish_config(id: int, db: Session = Depends(get_db)):
    """获取发布配置"""
    config = account_service.get_publish_config(db, id)
    if not config:
        raise HTTPException(status_code=404, detail="发布配置不存在")
    return config

@router.put("/{id}/publish-config", response_model=PublishConfigRead)
async def update_publish_config(id: int, config: PublishConfigUpdate, db: Session = Depends(get_db)):
    """更新发布配置"""
    updated_config = account_service.update_publish_config(db, id, config.dict(exclude_unset=True))
    return updated_config
