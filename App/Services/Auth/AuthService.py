import bcrypt
from fastapi import HTTPException, status

from App.Repositories.UsersRepository import UsersRepository
from App.Schemas.Auth.TokenResponse import TokenResponse
from App.Schemas.User.UserCreate import UserCreate
from App.Services.Auth.JwtService import JwtService


class AuthService:
    def __init__(self, users_repository: UsersRepository, jwt_service: JwtService) -> None:
        self._users_repository = users_repository
        self._jwt_service = jwt_service

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    async def register(self, payload: UserCreate) -> TokenResponse:
        if await self._users_repository.get_by_email(payload.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        record = await self._users_repository.create(
            payload.email, self._hash_password(payload.password)
        )
        return TokenResponse(access_token=self._jwt_service.encode(str(record["id"])))

    async def login(self, email: str, password: str) -> TokenResponse:
        record = await self._users_repository.get_by_email(email)
        if record is None or not self._verify_password(password, record["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return TokenResponse(access_token=self._jwt_service.encode(str(record["id"])))
