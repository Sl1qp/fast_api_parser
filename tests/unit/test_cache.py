import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from freezegun import freeze_time

from cache import get_cache_expiration, cache_until_1411, clear_cache_daily, init_redis


@pytest.mark.parametrize("current_time,expected_delta", [
    ("2023-01-01 10:00:00", 4 * 3600 + 11 * 60),  # До 14:11
    ("2023-01-01 14:10:00", 60),  # 1 минута до 14:11
    ("2023-01-01 14:11:00", 24 * 3600),  # Ровно 14:11
    ("2023-01-01 15:00:00", 23 * 3600 + 11 * 60),  # После 14:11
])
def test_get_cache_expiration(current_time, expected_delta):
    with freeze_time(current_time):
        expiration = get_cache_expiration()
        assert expiration == expected_delta


@pytest.mark.asyncio
async def test_cache_until_1411_decorator(mocker):
    mock_backend = AsyncMock()
    mock_backend.redis = AsyncMock()

    with patch('cache.FastAPICache.get_backend', return_value=mock_backend):
        with patch('cache.get_cache_expiration', return_value=3600):
            mock_func = AsyncMock(return_value="test_result")

            decorated_func = cache_until_1411()(mock_func)

            result = await decorated_func()

            assert result == "test_result"
            mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_init_redis(mocker):
    mock_redis = AsyncMock()
    mock_redis_from_url = mocker.patch('cache.aioredis.from_url', return_value=mock_redis)
    mock_fastapi_cache_init = mocker.patch('cache.FastAPICache.init')

    result = await init_redis()

    mock_redis_from_url.assert_called_once()
    mock_fastapi_cache_init.assert_called_once()
    assert result == mock_redis


@pytest.mark.asyncio
async def test_clear_cache_daily(mocker):
    mock_redis = AsyncMock()
    mock_backend = AsyncMock()
    mock_backend.redis = mock_redis

    with patch('cache.FastAPICache.get_backend', return_value=mock_backend):
        with patch('cache.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 14, 10, 0)
            mock_datetime.now.return_value = mock_now
            mock_datetime.combine.side_effect = lambda date, time: datetime.combine(date, time)

            sleep_calls = []

            async def mock_sleep(seconds):
                sleep_calls.append(seconds)
                if len(sleep_calls) == 1:
                    await mock_redis.flushall()
                    raise StopAsyncIteration("Test completed")

            mocker.patch('cache.asyncio.sleep', side_effect=mock_sleep)

            try:
                await clear_cache_daily()
            except StopAsyncIteration as e:
                if str(e) != "Test completed":
                    raise

            expected_sleep_time = 60
            assert len(sleep_calls) == 1
            assert sleep_calls[0] == expected_sleep_time
            mock_redis.flushall.assert_called_once()


@pytest.mark.asyncio
async def test_clear_cache_daily_after_1411(mocker):
    mock_redis = AsyncMock()
    mock_backend = AsyncMock()
    mock_backend.redis = mock_redis

    with patch('cache.FastAPICache.get_backend', return_value=mock_backend):
        with patch('cache.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 14, 12, 0)
            mock_datetime.now.return_value = mock_now
            mock_datetime.combine.side_effect = lambda date, time: datetime.combine(date, time)

            sleep_calls = []

            async def mock_sleep(seconds):
                sleep_calls.append(seconds)
                if len(sleep_calls) == 1:
                    await mock_redis.flushall()
                    raise StopAsyncIteration("Test completed")

            mocker.patch('cache.asyncio.sleep', side_effect=mock_sleep)

            try:
                await clear_cache_daily()
            except StopAsyncIteration as e:
                if str(e) != "Test completed":
                    raise

            expected_sleep_time = 23 * 3600 + 59 * 60
            assert len(sleep_calls) == 1
            assert sleep_calls[0] == expected_sleep_time
            mock_redis.flushall.assert_called_once()
