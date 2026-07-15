"""
wanderai/utils/pagination.py
Cursor-based and offset pagination helpers.
"""

from dataclasses import dataclass
from typing import TypeVar, Generic
from flask import request

T = TypeVar("T")


MAX_PER_PAGE: int = 100


@dataclass
class PaginationParams:
    page: int = 1
    per_page: int = 20
    MAX_PER_PAGE: int = 100

    @classmethod
    def from_request(cls) -> "PaginationParams":
        try:
            page = max(1, int(request.args.get("page", 1)))
            per_page = max(
                1,
                min(
                    int(request.args.get("per_page", 20)),
                    cls.MAX_PER_PAGE,
                ),
            )
        except (TypeError, ValueError):
            page, per_page = 1, 20
        return cls(page=page, per_page=per_page)


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.per_page - 1) // self.per_page)

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def to_meta(self) -> dict:
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total": self.total,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


def paginate_query(query, params: PaginationParams) -> PaginatedResult:
    """Apply pagination to a SQLAlchemy query."""
    total = query.count()
    items = (
        query.offset((params.page - 1) * params.per_page).limit(params.per_page).all()
    )
    return PaginatedResult(
        items=items, total=total, page=params.page, per_page=params.per_page
    )
