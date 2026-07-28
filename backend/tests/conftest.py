from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings


def test_database_name() -> str:
    name = settings.POSTGRES_DB
    return name if name.endswith("_test") else f"{name}_test"


def _test_database_url() -> str:
    base = str(settings.DATABASE_URL).rsplit("/", 1)[0]
    return f"{base}/{test_database_name()}"


TEST_DATABASE_URL = _test_database_url()

test_engine: AsyncEngine = create_async_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"command_timeout": 5.0},
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
