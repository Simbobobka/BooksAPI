from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from App.Api.V1.Dependencies.GetDbConnection import DbConnection
from App.Config.Settings import get_settings
from App.Repositories.UsersRepository import UsersRepository
from App.Schemas.User.UserResponse import UserResponse
from App.Services.Auth.JwtService import JwtService

_bearer = HTTPBearer(auto_error=False)

BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


async def get_current_user(
    credentials: BearerCredentials,
    connection: DbConnection,
) -> UserResponse:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    settings = get_settings()
    jwt_service = JwtService(
        settings.jwt_secret,
        settings.jwt_algorithm,
        settings.access_token_expire_minutes,
    )

    try:
        payload = jwt_service.decode(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    record = await UsersRepository(connection).get_by_id(int(subject))
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return UserResponse(
        id=record["id"],
        email=record["email"],
        created_at=record["created_at"],
    )
