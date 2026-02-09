"""
Pytest configuration and fixtures for WorkClock tests.

Provides test database setup, async client, and common fixtures.
"""
import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.models.admin_user import AdminUser
from app.utils.security import get_password_hash


# Test database URL - use separate database for tests
TEST_DATABASE_URL = "postgresql+asyncpg://workclock:dev_password@postgres/workclock_test"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.

    Required for pytest-asyncio to work with session-scoped async fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create async engine for test database.

    Uses NullPool to avoid connection issues in tests.
    Creates all tables before tests, drops after.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Uses nested transactions to ensure each test is isolated and rolled back.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    async_session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    session = async_session_maker()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for API testing.

    Overrides the get_db dependency to use the test database session.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> AdminUser:
    """
    Create a test admin user.

    Email: test@example.com
    Password: testpass123
    """
    admin = AdminUser(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        role="admin"
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: AdminUser) -> str:
    """
    Get JWT token for test admin user.

    Returns the access token string that can be used in Authorization headers.
    """
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(admin_token: str) -> dict:
    """
    Get authorization headers with admin token.

    Returns dict ready to use with client.get/post/etc.
    """
    return {"Authorization": f"Bearer {admin_token}"}
