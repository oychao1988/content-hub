from __future__ import annotations

from fastapi import APIRouter

from app.modules.system import endpoints
from app.core.module_system.module import Module

router = APIRouter()
router.include_router(endpoints.router, prefix="/system", tags=["系统"])

MODULE = Module(name="system", router=router)
