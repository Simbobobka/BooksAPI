from datetime import datetime

from pydantic import BaseModel

from App.Schemas.Author.AuthorResponse import AuthorResponse
from App.Schemas.Genre.GenreResponse import GenreResponse


class BookResponse(BaseModel):
    id: int
    title: str
    published_year: int
    genre: GenreResponse
    authors: list[AuthorResponse]
    created_at: datetime
    updated_at: datetime
