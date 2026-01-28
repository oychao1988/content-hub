from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import HTTPException, Query, status
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T")


class PaginationParams:
    """
    分页参数基类
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(
            None, ge=1, le=settings.MAX_PAGE_SIZE, description="每页项目数"
        ),
    ):
        self.page = page
        self.page_size = page_size or settings.DEFAULT_PAGE_SIZE
        self.skip = (page - 1) * self.page_size

        # 验证参数
        if self.page_size > settings.MAX_PAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"每页项目数不能超过{settings.MAX_PAGE_SIZE}",
            )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应
    """

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls, items: List[T], total: int, params: PaginationParams
    ) -> "PaginatedResponse[T]":
        """
        创建分页响应
        """
        pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )
