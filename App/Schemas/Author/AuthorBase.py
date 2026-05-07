from pydantic import BaseModel, Field


class AuthorBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    pen_name: str | None = Field(default=None, min_length=1, max_length=255)
