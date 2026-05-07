import hashlib
import secrets

import bcrypt
from fastapi import HTTPException, status

from App.Repositories.RefreshTokensRepository import RefreshTokensRepository
from App.Repositories.UsersRepository import UsersRepository
from App.Schemas.Auth.TokenResponse import TokenResponse
from App.Schemas.User.UserCreate import UserCreate
from App.Services.Auth.JwtService import JwtService


class AuthService:
    def __init__(
        self,
        users_repository: UsersRepository,
        refresh_tokens_repository: RefreshTokensRepository,
        jwt_service: JwtService,
        refresh_token_expire_days: int,
    ) -> None:
        self._users = users_repository
        self._refresh_tokens = refresh_tokens_repository
        self._jwt = jwt_service
        self._refresh_expire_days = refresh_token_expire_days

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def _build_token_response(self, user_id: int) -> TokenResponse:
        access_token = self._jwt.encode(str(user_id))
        refresh_token = secrets.token_urlsafe(32)
        await self._refresh_tokens.create(
            user_id, self._hash_token(refresh_token), self._refresh_expire_days
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def register(self, payload: UserCreate) -> TokenResponse:
        if await self._users.get_by_email(payload.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        record = await self._users.create(payload.email, self._hash_password(payload.password))
        return await self._build_token_response(record["id"])

    async def login(self, email: str, password: str) -> TokenResponse:
        record = await self._users.get_by_email(email)
        if record is None or not self._verify_password(password, record["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return await self._build_token_response(record["id"])

    async def refresh(self, refresh_token: str) -> TokenResponse:
        token_hash = self._hash_token(refresh_token)
        record = await self._refresh_tokens.get_by_hash(token_hash)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        await self._refresh_tokens.delete(token_hash)
        return await self._build_token_response(record["user_id"])

    async def logout(self, refresh_token: str) -> None:
        await self._refresh_tokens.delete(self._hash_token(refresh_token))
