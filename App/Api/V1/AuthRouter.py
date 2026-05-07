import asyncpg
from fastapi import APIRouter, Request, status

from App.Api.Limiter import limiter
from App.Api.V1.Dependencies.GetDbConnection import DbConnection
from App.Config.Settings import get_settings
from App.Repositories.UsersRepository import UsersRepository
from App.Schemas.Auth.LoginRequest import LoginRequest
from App.Schemas.Auth.TokenResponse import TokenResponse
from App.Schemas.User.UserCreate import UserCreate
from App.Services.Auth.AuthService import AuthService
from App.Services.Auth.JwtService import JwtService

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(connection: asyncpg.Connection) -> AuthService:
    settings = get_settings()
    return AuthService(
        users_repository=UsersRepository(connection),
        jwt_service=JwtService(
            settings.jwt_secret,
            settings.jwt_algorithm,
            settings.access_token_expire_minutes,
        ),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request, payload: UserCreate, connection: DbConnection
) -> TokenResponse:
    return await _build_service(connection).register(payload)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest, connection: DbConnection) -> TokenResponse:
    return await _build_service(connection).login(payload.email, payload.password)
