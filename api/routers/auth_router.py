from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from api.core.config import Config
from api.services import AuthService
from api.database import get_session
from api.schemas import UserCreate, UserRead, UserLogin
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.security.utils import verify_password
from api.core.security.security import (
    create_token,
    AccessTokenBearer,
    RefreshTokenBearer,
)
from datetime import timedelta
from api.database.redis import (
    add_jti_to_blocklist,
    get_resend_count,
    increment_resend_count,
)
from api.services.vefification import (
    create_verification_for_user,
    verify_token_and_activate,
    send_verification_email_bg,
)

auth_router = APIRouter(prefix="/auth")
auth_service = AuthService()


@auth_router.post(
    "/register", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
async def register_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    email_existing = await auth_service.get_user_by_email(data.email, session)
    if email_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken"
        )

    username_existing = await auth_service.get_user_by_username(data.username, session)
    if username_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="username unavailable"
        )

    if data.password1 != data.password2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password don't match"
        )

    new_user = await auth_service.create_user(data, session)

    verification_token = await create_verification_for_user(str(new_user.uuid))
    send_verification_email_bg(new_user.email, verification_token.token)

    return new_user


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(data: UserLogin, session: AsyncSession = Depends(get_session)):
    user = await auth_service.get_user_by_email(data.email, session)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password"
        )

    user_data = {"sub": str(user.uuid)}

    access_token = create_token(user_data)
    refresh_token = create_token(user_data, expiry=timedelta(days=7), refresh=True)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@auth_router.get("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_token(refresh_token_data=Depends(RefreshTokenBearer())):
    user_id = refresh_token_data["user_data"]["sub"]
    user_data = {"sub": user_id}
    access_token = create_token(user_data)
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/logout")
async def logout_user(access_token_data=Depends(AccessTokenBearer())):
    jti = access_token_data["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content="Logged out succesfully", status_code=status.HTTP_200_OK
    )


@auth_router.get("/me", response_model=UserRead)
async def get_current_user(
    access_token_data=Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user = await auth_service.get_user_by_id(
        access_token_data["user_data"]["sub"], session
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@auth_router.patch("/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user_account(
    access_token_data=Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_id = access_token_data["user_data"]["sub"]

    deactivated = await auth_service.deactivate_user_account(user_id, session)
    if not deactivated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Something went wrong"
        )

    return JSONResponse(content="Account deactivated")


@auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_session),
    access_token_data=Depends(AccessTokenBearer()),
):
    user = await verify_token_and_activate(token, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    return {"detail": "Email verified"}


@auth_router.get("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    session: AsyncSession = Depends(get_session),
    access_token_data=Depends(AccessTokenBearer()),
):
    current_user = await auth_service.get_user_by_id(
        access_token_data["user_data"]["sub"], session
    )
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already verified"
        )

    cnt = await get_resend_count(str(current_user.uuid))
    if cnt >= Config.RESEND_LIMIT_PER_HOUR:
        raise HTTPException(status_code=429, detail="Resend limit exceeded. Try later.")

    verification_token = await create_verification_for_user(str(current_user.uuid))
    await increment_resend_count(str(current_user.uuid))
    send_verification_email_bg(current_user.email, verification_token.token)
    return JSONResponse(content={"detail": "Verification sent"})
