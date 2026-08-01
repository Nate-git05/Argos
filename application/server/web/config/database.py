from collections.abc import AsyncGenerator  # type hint for the async generator get_db yields from

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # async SQLAlchemy building blocks

from application.server.web.config.config import POSTGRES_URI  # connection string loaded from .env

engine = create_async_engine(POSTGRES_URI)  # async engine, owns the connection pool to Postgres

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)  # factory that produces new AsyncSession instances


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:  # open a session for the lifetime of one request
        yield session  # hand it to the route via FastAPI's Depends(get_db)
