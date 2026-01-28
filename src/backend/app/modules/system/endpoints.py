from typing import Any, Dict

from fastapi import APIRouter

from app.modules.shared.schemas.api import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def health() -> ApiResponse[Dict[str, Any]]:
    return ApiResponse(success=True, data={"status": "ok"})
