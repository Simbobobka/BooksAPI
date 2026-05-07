from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    published_year: int = Field(ge=1800)
    genre_name: str = Field(min_length=1)

    @field_validator("published_year")
    @classmethod
    def validate_year_upper_bound(cls, v: int) -> int:
        max_year = datetime.now(UTC).year + 1
        if v > max_year or v < 1800:
            raise ValueError(f"published_year must be between 1800 and {max_year}")
        return v
