from typing import Optional
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from api.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from api.database.redis import token_is_in_blocklist
from api.core.config import Config
from datetime import datetime, timedelta
from uuid import uuid4
import jwt
import logging
from api.services import AuthService


def create_token(
    user_data: dict,
    expiry: timedelta = timedelta(minutes=Config.TOKEN_EXPIRE_MINUTES),
    refresh: bool = False,
):
    return jwt.encode(
        payload={
            "user_data": user_data,
            "exp": datetime.now() + expiry,
            "jti": str(uuid4()),
            "refresh": refresh,
        },
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM,
    )


def decode_token(token: str):
    try:
        token_data = jwt.decode(
            token, key=Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.auth_service = AuthService()

    async def __call__(
        self, request: Request, session: AsyncSession = Depends(get_session)
    ) -> Optional[HTTPAuthorizationCredentials]:
        # Getting bearer token
        auth_credentials = await super().__call__(request)

        # If auth credentials are missing
        if not auth_credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
            )

        token_data = decode_token(auth_credentials.credentials)

        # If token data is missing -> token has been expired or invalid
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Invalid or expired token",
                    "resolution": "Get a new token",
                },
            )

        # If token is revoked
        if await token_is_in_blocklist(token_data["jti"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Invalid or revoked token",
                    "resolution": "Get a new token",
                },
            )

        if self.auth_service:
            user_id = token_data["user_data"]["sub"]
            user = await self.auth_service.get_user_by_id(user_id, session)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated or not found",
                )

        if datetime.fromtimestamp(token_data["exp"]) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )

        # Making sure we're getting the right token
        self.verify_token(token_data)

        return token_data

    def verify_token(self, token_data):
        raise NotImplementedError("Please override this method")


class AccessTokenBearer(TokenBearer):
    def verify_token(self, token_data):
        if token_data is not None and token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide an access token",
            )


class RefreshTokenBearer(TokenBearer):
    def verify_token(self, token_data):
        if token_data is not None and not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide a refresh token",
            )
