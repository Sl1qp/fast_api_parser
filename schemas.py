from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class TradingResultResponse(BaseModel):
    """Схема для ответа с данными о торговых результатах"""
    exchange_product_id: str = Field(..., description="Код инструмента")
    exchange_product_name: str = Field(..., description="Наименование инструмента")
    oil_id: str = Field(..., description="Код нефтепродукта")
    delivery_basis_id: str = Field(..., description="Код базиса поставки")
    delivery_basis_name: str = Field(..., description="Наименование базиса поставки")
    delivery_type_id: str = Field(..., description="Тип поставки")
    volume: float = Field(..., description="Объем договоров в единицах измерения")
    total: int = Field(..., description="Объем договоров, руб.")
    count: int = Field(..., description="Количество договоров, шт.")
    trade_date: date = Field(..., description="Дата торгов", alias="date")  # Изменено здесь

    class Config:
        from_attributes = True
        populate_by_name = True  # Добавлено для работы с alias


class TradingDatesResponse(BaseModel):
    """Схема для ответа со списком дат торгов"""
    dates: List[date] = Field(..., description="Список дат торговых дней")


class TradingDynamicsFilters(BaseModel):
    """Схема для параметров фильтрации динамики торгов"""
    oil_id: Optional[str] = Field(None, description="Код нефтепродукта")
    delivery_type_id: Optional[str] = Field(None, description="Тип поставки")
    delivery_basis_id: Optional[str] = Field(None, description="Базис поставки")
    start_date: date = Field(..., description="Начальная дата периода")
    end_date: date = Field(..., description="Конечная дата периода")


class TradingResultsFilters(BaseModel):
    """Схема для параметров фильтрации торговых результатов"""
    oil_id: Optional[str] = Field(None, description="Код нефтепродукта")
    delivery_type_id: Optional[str] = Field(None, description="Тип поставки")
    delivery_basis_id: Optional[str] = Field(None, description="Базис поставки")