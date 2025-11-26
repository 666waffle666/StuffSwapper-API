from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from api.core.config import Config

async_engine = create_async_engine(Config.DATABASE_URL)
async_session = async_sessionmaker(async_engine)
Base = declarative_base()


async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
