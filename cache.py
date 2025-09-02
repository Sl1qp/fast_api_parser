import os

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from datetime import datetime, time, timedelta
import asyncio
from config import REDIS_HOST, REDIS_PORT, REDIS_DB



TESTING = os.getenv("TESTING", "False").lower() == "true"


async def init_redis():
    """Инициализация Redis подключения"""
    if TESTING:
        # В тестовом режиме используем InMemoryBackend
        from fastapi_cache.backends.inmemory import InMemoryBackend
        FastAPICache.init(InMemoryBackend())
        return None
    redis = aioredis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        encoding="utf8",
        decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    return redis


def get_cache_expiration():
    """Вычисляет время до 14:11 следующего дня"""
    now = datetime.now()
    target_time = time(14, 11)  # 14:11

    if now.time() < target_time:
        expiration_time = datetime.combine(now.date(), target_time)
    else:
        expiration_time = datetime.combine(now.date() + timedelta(days=1), target_time)

    return int((expiration_time - now).total_seconds())


def cache_until_1411():
    if TESTING:
        # В тестовом режиме возвращаем пустой декоратор
        def dummy_decorator(func):
            return func
        return dummy_decorator
    return cache(expire=get_cache_expiration())


async def clear_cache_daily():
    """Фоновая задача для очистки кэша в 14:11"""
    while True:
        now = datetime.now()
        target_time = time(14, 11)

        if now.time() < target_time:
            wait_until = datetime.combine(now.date(), target_time)
        else:
            wait_until = datetime.combine(now.date() + timedelta(days=1), target_time)

        wait_seconds = (wait_until - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        redis = FastAPICache.get_backend().redis
        await redis.flushall()
        print(f"Кэш очищен в {datetime.now()}")
