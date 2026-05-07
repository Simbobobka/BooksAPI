from pydantic import BaseModel

from App.Schemas.Book.BookResponse import BookResponse


class BookListResponse(BaseModel):
    items: list[BookResponse]
    total: int
    limit: int
    offset: int
