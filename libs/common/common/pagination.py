"""Phan trang dung chung: ?page=1&size=20, size toi da 100."""

from __future__ import annotations

from fastapi import Query
from pydantic import BaseModel

MAX_PAGE_SIZE = 100


class PageParams:
    """Dependency doc ?page & ?size. Vuot gioi han thi FastAPI tra 422."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Trang, bat dau tu 1"),
        size: int = Query(20, ge=1, le=MAX_PAGE_SIZE, description="So dong moi trang"),
    ) -> None:
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> Page[T]:
        return cls(items=items, total=total, page=params.page, size=params.size)
