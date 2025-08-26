import asyncio

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi.params import Depends
from fastapi.middleware.cors import CORSMiddleware
from routers import main_router
from cache import init_redis, clear_cache_daily
from contextlib import asynccontextmanager
from database import init_db, create_table
from config import DEBUG


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

app.include_router(main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
