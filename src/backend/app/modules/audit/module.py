from __future__ import annotations

from fastapi import APIRouter

from app.modules.audit import endpoints
from app.core.module_system.module import Module

router = APIRouter()
router.include_router(endpoints.router, prefix="/audit", tags=["审计"])

MODULE = Module(name="audit", router=router)
