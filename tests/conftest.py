import pytest
import asyncio
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_async_session

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@test_db:5432/test_EM2_2dz"


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_session(test_db):
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )

    session = async_session()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest_asyncio.fixture
async def setup_test_data(test_session):
    from database import spimex_trading_results
    from datetime import date, datetime

    test_data = [
        spimex_trading_results(
            exchange_product_id="A100000E",
            exchange_product_name="Test Product 1",
            oil_id="A100",
            delivery_basis_id="000",
            delivery_basis_name="Test Basis 1",
            delivery_type_id="E",
            volume=100.0,
            total=500000,
            count=10,
            date=date(2023, 1, 1),
            created_on=datetime.now(),
            updated_on=datetime.now()
        ),
        spimex_trading_results(
            exchange_product_id="A200000T",
            exchange_product_name="Test Product 2",
            oil_id="A200",
            delivery_basis_id="001",
            delivery_basis_name="Test Basis 2",
            delivery_type_id="T",
            volume=200.0,
            total=1000000,
            count=20,
            date=date(2023, 1, 2),
            created_on=datetime.now(),
            updated_on=datetime.now()
        ),
        spimex_trading_results(
            exchange_product_id="A100001E",
            exchange_product_name="Test Product 3",
            oil_id="A100",
            delivery_basis_id="001",
            delivery_basis_name="Test Basis 3",
            delivery_type_id="E",
            volume=150.0,
            total=750000,
            count=15,
            date=date(2023, 1, 1),
            created_on=datetime.now(),
            updated_on=datetime.now()
        )
    ]

    test_session.add_all(test_data)
    await test_session.commit()

    yield test_data

    await test_session.execute(text("TRUNCATE TABLE spimex_trading_results RESTART IDENTITY CASCADE"))
    await test_session.commit()


@pytest_asyncio.fixture(autouse=True)
async def override_dependency(test_session):
    async def override_get_async_session():
        try:
            yield test_session
        finally:
            pass

    app.dependency_overrides[get_async_session] = override_get_async_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def initialize_cache():
    from cache import init_redis
    await init_redis()
    yield
