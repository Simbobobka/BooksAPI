from datetime import datetime

from App.Schemas.User.UserBase import UserBase


class UserResponse(UserBase):
    id: int
    created_at: datetime
