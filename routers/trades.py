from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, distinct
from datetime import date
from typing import Optional, List

from database import get_async_session, spimex_trading_results
from schemas import TradingResultResponse, TradingDatesResponse
from cache import cache_until_1411

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/dates/", response_model=TradingDatesResponse)
@cache_until_1411()  # Добавляем кэширование
async def get_last_trading_dates(
        limit: int = Query(10, ge=1, le=100, description="Количество последних торговых дней"),
        session: AsyncSession = Depends(get_async_session)
):
    """
    Получить список дат последних торговых дней.

    Args:
        limit: Количество возвращаемых дат (по умолчанию 10, максимум 100)
    """
    try:
        query = select(distinct(spimex_trading_results.date)) \
            .order_by(spimex_trading_results.date.desc()) \
            .limit(limit)

        result = await session.execute(query)
        dates = [row[0] for row in result.all()]

        return TradingDatesResponse(dates=dates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")


@router.get("/dynamics/", response_model=List[TradingResultResponse])
@cache_until_1411()  # Добавляем кэширование
async def get_dynamics(
        oil_id: Optional[str] = Query(None, description="Код нефтепродукта (например: A100)"),
        delivery_type_id: Optional[str] = Query(None, description="Тип поставки (например: E, T)"),
        delivery_basis_id: Optional[str] = Query(None, description="Базис поставки (например: 000, 001)"),
        start_date: date = Query(..., description="Начальная дата периода в формате YYYY-MM-DD"),
        end_date: date = Query(..., description="Конечная дата периода в формате YYYY-MM-DD"),
        session: AsyncSession = Depends(get_async_session)
):
    """
    Получить список торгов за заданный период с возможностью фильтрации.

    Args:
        oil_id: Фильтр по коду нефтепродукта
        delivery_type_id: Фильтр по типу поставки
        delivery_basis_id: Фильтр по базису поставки
        start_date: Начальная дата периода
        end_date: Конечная дата периода
    """
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Начальная дата не может быть больше конечной")

        conditions = [
            spimex_trading_results.date >= start_date,
            spimex_trading_results.date <= end_date
        ]

        if oil_id:
            conditions.append(spimex_trading_results.oil_id == oil_id)
        if delivery_type_id:
            conditions.append(spimex_trading_results.delivery_type_id == delivery_type_id)
        if delivery_basis_id:
            conditions.append(spimex_trading_results.delivery_basis_id == delivery_basis_id)

        query = select(spimex_trading_results).where(and_(*conditions))
        result = await session.execute(query)
        trades = result.scalars().all()

        if not trades:
            raise HTTPException(status_code=404, detail="Данные за указанный период не найдены")

        return trades
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")


@router.get("/results/", response_model=List[TradingResultResponse])
@cache_until_1411()  # Добавляем кэширование
async def get_trading_results(
        oil_id: Optional[str] = Query(None, description="Код нефтепродукта (например: A100)"),
        delivery_type_id: Optional[str] = Query(None, description="Тип поставки (например: E, T)"),
        delivery_basis_id: Optional[str] = Query(None, description="Базис поставки (например: 000, 001)"),
        session: AsyncSession = Depends(get_async_session)
):
    """
    Получить список последних торгов с возможностью фильтрации.

    Args:
        oil_id: Фильтр по коду нефтепродукта
        delivery_type_id: Фильтр по типу поставки
        delivery_basis_id: Фильтр по базису поставки
    """
    try:
        max_date_query = select(func.max(spimex_trading_results.date))
        max_date_result = await session.execute(max_date_query)
        max_date = max_date_result.scalar()

        if not max_date:
            raise HTTPException(status_code=404, detail="Данные о торгах не найдены")

        conditions = [spimex_trading_results.date == max_date]

        if oil_id:
            conditions.append(spimex_trading_results.oil_id == oil_id)
        if delivery_type_id:
            conditions.append(spimex_trading_results.delivery_type_id == delivery_type_id)
        if delivery_basis_id:
            conditions.append(spimex_trading_results.delivery_basis_id == delivery_basis_id)

        query = select(spimex_trading_results).where(and_(*conditions))
        result = await session.execute(query)
        trades = result.scalars().all()

        if not trades:
            raise HTTPException(status_code=404, detail="Данные за последний торговый день не найдены")

        return trades
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")