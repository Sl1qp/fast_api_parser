from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class TradingResultResponse(BaseModel):
    exchange_product_id: str = Field(..., description="Код инструмента")
    exchange_product_name: str = Field(..., description="Наименование инструмента")
    oil_id: str = Field(..., description="Код нефтепродукта")
    delivery_basis_id: str = Field(..., description="Код базиса поставки")
    delivery_basis_name: str = Field(..., description="Наименование базиса поставки")
    delivery_type_id: str = Field(..., description="Тип поставки")
    volume: float = Field(..., description="Объем договоров в единицах измерения")
    total: int = Field(..., description="Объем договоров, руб.")
    count: int = Field(..., description="Количество договоров, шт.")
    trade_date: date = Field(..., description="Дата торгов", alias="date")

    class Config:
        from_attributes = True
        populate_by_name = True


class TradingDatesResponse(BaseModel):
    dates: List[date] = Field(..., description="Список дат торговых дней")


class TradingDynamicsFilters(BaseModel):
    oil_id: Optional[str] = Field(None, description="Код нефтепродукта")
    delivery_type_id: Optional[str] = Field(None, description="Тип поставки")
    delivery_basis_id: Optional[str] = Field(None, description="Базис поставки")
    start_date: date = Field(..., description="Начальная дата периода")
    end_date: date = Field(..., description="Конечная дата периода")


class TradingResultsFilters(BaseModel):
    oil_id: Optional[str] = Field(None, description="Код нефтепродукта")
    delivery_type_id: Optional[str] = Field(None, description="Тип поставки")
    delivery_basis_id: Optional[str] = Field(None, description="Базис поставки")
