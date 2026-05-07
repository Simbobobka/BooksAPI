from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

from App.Schemas.Author.AuthorBase import AuthorBase


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    published_year: int | None = Field(default=None, ge=1800)
    genre_name: str | None = None
    authors: list[AuthorBase] | None = Field(default=None, min_length=1)

    @field_validator("published_year")
    @classmethod
    def validate_year_upper_bound(cls, v: int | None) -> int | None:
        if v is None:
            return v
        max_year = datetime.now(UTC).year + 1
        if v > max_year or v < 1800:
            raise ValueError(f"published_year must be between 1800 and {max_year}")
        return v
