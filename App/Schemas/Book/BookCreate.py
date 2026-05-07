from pydantic import Field

from App.Schemas.Author.AuthorBase import AuthorBase
from App.Schemas.Book.BookBase import BookBase


class BookCreate(BookBase):
    authors: list[AuthorBase] = Field(min_length=1)
