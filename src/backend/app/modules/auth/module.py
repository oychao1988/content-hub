from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth import endpoints
from app.core.module_system.module import Module

router = APIRouter()
router.include_router(endpoints.router, tags=["认证"])

MODULE = Module(name="auth", router=router)
