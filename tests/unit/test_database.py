import pytest
from datetime import date
from sqlalchemy import select

from database import (
    get_last_trading_dates,
    get_trading_dynamics,
    get_last_trading_results,
    spimex_trading_results
)


@pytest.mark.asyncio
async def test_get_last_trading_dates(test_session, setup_test_data):
    result = await get_last_trading_dates(test_session, 2)

    assert len(result) == 2
    assert result[0] == date(2023, 1, 2)
    assert result[1] == date(2023, 1, 1)


@pytest.mark.asyncio
async def test_get_trading_dynamics_with_filters(test_session, setup_test_data):
    result = await get_trading_dynamics(
        test_session,
        oil_id="A100",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1)
    )

    assert len(result) == 2
    for item in result:
        assert item.oil_id == "A100"
        assert item.date == date(2023, 1, 1)


@pytest.mark.asyncio
async def test_get_trading_dynamics_without_filters(test_session, setup_test_data):
    result = await get_trading_dynamics(
        test_session,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 2)
    )

    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_last_trading_results_with_filters(test_session, setup_test_data):
    result = await get_last_trading_results(
        test_session,
        oil_id="A200"
    )

    print(result)
    assert len(result) == 1
    assert result[0].oil_id == "A200"
    assert result[0].date == date(2023, 1, 2)


@pytest.mark.asyncio
async def test_get_last_trading_results_without_filters(test_session, setup_test_data):
    result = await get_last_trading_results(test_session)

    assert len(result) == 1
    assert result[0].date == date(2023, 1, 2)


@pytest.mark.asyncio
async def test_truncate_table(test_session, setup_test_data):
    from database import truncate_table

    result = await test_session.execute(select(spimex_trading_results))
    assert len(result.scalars().all()) == 3

    success = await truncate_table(test_session)
    assert success is True

    result = await test_session.execute(select(spimex_trading_results))
    assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_create_table(test_session):
    from database import create_table

    result = await create_table()
    assert result is False
