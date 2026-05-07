from pydantic import Field

from App.Schemas.User.UserBase import UserBase


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
