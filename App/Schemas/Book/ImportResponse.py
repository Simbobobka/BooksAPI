from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int
    detail: str


class ImportResponse(BaseModel):
    imported: int
    failed: int
    errors: list[ImportRowError]
