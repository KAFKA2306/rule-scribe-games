
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
import structlog

from app.core.config import settings
from app.core.supabase import supabase_client

logger = structlog.get_logger()

# Create async engine with Supabase PostgreSQL or fallback to SQLite
def create_database_engine():
    if settings.SUPABASE_URL and "postgresql" in settings.DATABASE_URL:
        return create_async_engine(
            settings.get_database_url(),
            echo=settings.is_development(),
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
        )
    elif "sqlite" in settings.DATABASE_URL:
        return create_async_engine(
            "sqlite+aiosqlite:///./rulescribe_v2.db",
            echo=settings.is_development(),
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
    else:
        return create_async_engine(
            settings.get_database_url(),
            echo=settings.is_development(),
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
        )

engine = create_database_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def init_db():
    try:
        await supabase_client.initialize()
        async with engine.begin() as conn:
            from app.models import game, user, analytics
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        if settings.is_production():
            raise


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()