from api.schemas import UserCreate
from api.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.security.utils import hash_password
from sqlalchemy import select


class AuthService:
    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_username(
        self, username: str, session: AsyncSession
    ) -> User | None:
        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, id: str, session: AsyncSession) -> User | None:
        statement = select(User).where(User.uuid == id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def create_user(self, data: UserCreate, session: AsyncSession) -> User:
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password1),
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def deactivate_user_account(self, user_id, session: AsyncSession):
        user = await self.get_user_by_id(user_id, session)
        if not user:
            return None

        user.is_active = False
        await session.commit()
        await session.refresh(user)
        return user
