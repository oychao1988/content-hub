from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[Dict[str, Any]] = None


class PaginatedResponse(ApiResponse[T], Generic[T]):
    data: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
