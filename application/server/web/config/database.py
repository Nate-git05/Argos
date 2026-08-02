from collections.abc import AsyncGenerator  # type hint for the async generator get_db yields from

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # async SQLAlchemy building blocks
from sqlalchemy.orm import DeclarativeBase  # SQLAlchemy 2.0 base class for ORM models

from application.server.web.config.config import POSTGRES_URI  # connection string loaded from .env


class Base(DeclarativeBase):  # shared base every table model inherits from
    pass


engine = create_async_engine(
    POSTGRES_URI,
    connect_args={"statement_cache_size": 0},  # Supabase's pooler (port 6543) runs PgBouncer in transaction mode, which is incompatible with asyncpg's server-side prepared statement cache
)  # async engine, owns the connection pool to Postgres

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)  # factory that produces new AsyncSession instances


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:  # open a session for the lifetime of one request
        yield session  # hand it to the route via FastAPI's Depends(get_db)
