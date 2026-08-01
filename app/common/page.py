from math import ceil
from typing import Generic, TypeVar
from pydantic import BaseModel, Field



T = TypeVar("T")


class PageRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PageResponse(BaseModel, Generic[T]):
    content: list[T]

    page: int
    size: int

    total_elements: int
    total_pages: int

from math import ceil


def create_page_response(
    content: list[T],
    page: int,
    size: int,
    total_elements: int,
) -> PageResponse[T]:
    return PageResponse(
        content=content,
        page=page,
        size=size,
        total_elements=total_elements,
        total_pages=ceil(total_elements / size),
    )