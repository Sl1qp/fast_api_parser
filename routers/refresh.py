import database as db
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.params import Depends
from fastapi_cache import FastAPICache

from parser.parser import run_parser

refresh_router = APIRouter()


@refresh_router.delete("/", tags=["update data"],
                       description="Эндпоинт для обновления данных. База данных будет очищена и будет запущен парсер для актуализации данных. Обновление данных в среднем занимает 3-5 минут")
async def refresh_data(session: AsyncSession = Depends(db.get_async_session)):
    await db.truncate_table(session)
    await run_parser()

    redis = FastAPICache.get_backend().redis
    await redis.flushall()
    return {'msg': 'success'}
