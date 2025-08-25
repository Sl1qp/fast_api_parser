import database as db
import asyncio

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi.params import Depends
from fastapi.middleware.cors import CORSMiddleware
from cache import init_redis, clear_cache_daily
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from database import init_db, create_table
from routers import trades
from config import DEBUG
from parser.parser import run_parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    print("Инициализация приложения...")
    await init_db()
    await create_table()
    await init_redis()

    asyncio.create_task(clear_cache_daily())

    print("Приложение инициализировано")

    yield

    # Действия при остановке
    print("Приложение завершает работу")


app = FastAPI(
    title="Spimex Trading API",
    description="Микросервис для получения данных о торгах",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

app.include_router(trades.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.delete("/refresh/", tags=["update data"],
            description="Эндпоинт для обновления данных. База данных будет очищена и будет запущен парсер для актуализации данных. Обновление данных в среднем занимает 3-5 минут")
async def refresh_data(session: AsyncSession = Depends(db.get_async_session)):
    await db.truncate_table(session)
    await run_parser()

    redis = FastAPICache.get_backend().redis
    await redis.flushall()
    return {'msg': 'success'}
