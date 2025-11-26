from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.database.models import EmailVerification, User
from api.core.config import Config
from api.tasks.send_email import send_verification_email
from typing import Optional
from api.database import async_session


def generate_token() -> str:
    return uuid4().hex  # 32 chars, URL safe


async def create_verification_for_user(user_id: str) -> EmailVerification:
    async with async_session() as session:
        try:
            # invalidate old tokens for this user:
            await session.execute(
                update(EmailVerification)
                .where(EmailVerification.user_id == user_id)
                .values(used=True)
            )
            token = generate_token()
            expires_at = datetime.now(tz=timezone.utc) + timedelta(
                hours=Config.VERIFICATION_TOKEN_EXPIRE_HOURS
            )
            ev = EmailVerification(token=token, user_id=user_id, expires_at=expires_at)
            session.add(ev)
            await session.commit()
            await session.refresh(ev)
            return ev
        finally:
            await session.close()


def send_verification_email_bg(user_email: str, token: str):
    link = f"{Config.FRONTEND_URL.rstrip('/')}/auth/verify-email?token={token}"
    html = f"<p>Click to verify: <a href='{link}'>{link}</a></p>"
    subject = "Verify your email"

    send_verification_email.delay([user_email], subject, html)  # type: ignore


async def verify_token_and_activate(
    token: str, session: AsyncSession
) -> Optional[User]:
    statement = select(EmailVerification).where(EmailVerification.token == token)
    result = await session.execute(statement)
    ev = result.scalar_one_or_none()
    if not ev:
        return None
    if ev.used:
        return None
    if ev.expires_at < datetime.now(tz=timezone.utc):
        return None

    # mark used and activate user
    ev.used = True
    user_statement = select(User).where(User.uuid == ev.user_id)
    res = await session.execute(user_statement)
    user = res.scalar_one_or_none()
    if not user:
        return None

    user.is_verified = True
    await session.commit()
    await session.refresh(user)
    return user
