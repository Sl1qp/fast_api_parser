from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select, func, distinct, and_
from sqlalchemy import text, Text, Integer, Float, DateTime, Date, Column
from typing import List, Optional, AsyncGenerator
from datetime import date
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

Base = declarative_base()
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class spimex_trading_results(Base):
    __tablename__ = "spimex_trading_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange_product_id = Column(Text)
    exchange_product_name = Column(Text)
    oil_id = Column(Text)
    delivery_basis_id = Column(Text)
    delivery_basis_name = Column(Text)
    delivery_type_id = Column(Text)
    volume = Column(Float)
    total = Column(Integer)
    count = Column(Integer)
    date = Column(Date)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)


async_engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker] = None

__all__ = [
    'get_async_session',
    'async_session_maker',
    'spimex_trading_results',
    'truncate_table',
    'create_table',
    'get_last_trading_dates',
    'get_trading_dynamics',
    'get_last_trading_results'
]


async def init_db():
    global async_engine, async_session_maker
    async_engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if not async_session_maker:
        await init_db()

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_engine_and_session():
    return async_engine, async_session_maker


async def truncate_table(session: AsyncSession):
    try:
        await session.execute(text("TRUNCATE TABLE spimex_trading_results RESTART IDENTITY CASCADE"))
        await session.commit()
        print("Таблица успешно очищена с сбросом идентификаторов")
        return True
    except Exception as e:
        await session.rollback()
        print(f"Ошибка при очистке таблицы: {str(e)}")


async def create_table() -> bool:
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(str(e))
        print("БД уже существует")
        return False
    print("БД успешно создана")
    return True


async def async_insert_to_db(obj: spimex_trading_results, session):
    session.add(obj)
    await session.commit()


async def get_last_trading_dates(session: AsyncSession, limit: int) -> List[date]:
    query = select(distinct(spimex_trading_results.date)) \
        .order_by(spimex_trading_results.date.desc()) \
        .limit(limit)

    result = await session.execute(query)
    return [row[0] for row in result.all()]


async def get_trading_dynamics(
        session: AsyncSession,
        oil_id: Optional[str] = None,
        delivery_type_id: Optional[str] = None,
        delivery_basis_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> List[spimex_trading_results]:
    conditions = []

    if oil_id:
        conditions.append(spimex_trading_results.oil_id == oil_id)
    if delivery_type_id:
        conditions.append(spimex_trading_results.delivery_type_id == delivery_type_id)
    if delivery_basis_id:
        conditions.append(spimex_trading_results.delivery_basis_id == delivery_basis_id)
    if start_date:
        conditions.append(spimex_trading_results.date >= start_date)
    if end_date:
        conditions.append(spimex_trading_results.date <= end_date)

    if conditions:
        query = select(spimex_trading_results).where(and_(*conditions))
    else:
        query = select(spimex_trading_results)

    result = await session.execute(query)
    return result.scalars().all()


async def get_last_trading_results(
        session: AsyncSession,
        oil_id: Optional[str] = None,
        delivery_type_id: Optional[str] = None,
        delivery_basis_id: Optional[str] = None
) -> List[spimex_trading_results]:
    max_date_query = select(func.max(spimex_trading_results.date))
    max_date_result = await session.execute(max_date_query)
    max_date = max_date_result.scalar()

    if not max_date:
        return []

    conditions = [spimex_trading_results.date == max_date]

    if oil_id:
        conditions.append(spimex_trading_results.oil_id == oil_id)
    if delivery_type_id:
        conditions.append(spimex_trading_results.delivery_type_id == delivery_type_id)
    if delivery_basis_id:
        conditions.append(spimex_trading_results.delivery_basis_id == delivery_basis_id)

    query = select(spimex_trading_results).where(and_(*conditions))
    result = await session.execute(query)
    return result.scalars().all()
