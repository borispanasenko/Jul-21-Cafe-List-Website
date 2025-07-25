from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import Config
from app.models import Base


engine = create_async_engine(Config.ASYNC_SQLALCHEMY_DATABASE_URI, echo=Config.SQLALCHEMY_ECHO)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
