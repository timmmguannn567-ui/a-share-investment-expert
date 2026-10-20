from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


InstrumentType = Literal["stock", "etf"]
Action = Literal["WATCH", "BUY", "ADD", "HOLD", "REDUCE", "SELL", "CASH"]


class PositionCreate(BaseModel):
    instrument_code: str = Field(min_length=6, max_length=16)
    name: str = Field(min_length=1, max_length=80)
    instrument_type: InstrumentType
    quantity: float = Field(gt=0)
    cost_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    industry_l1: str | None = None

    @field_validator("instrument_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class PositionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    quantity: float | None = Field(default=None, gt=0)
    cost_price: float | None = Field(default=None, gt=0)
    current_price: float | None = Field(default=None, gt=0)
    industry_l1: str | None = None


class PositionRead(PositionCreate):
    id: int
    market_value: float
    pnl: float
    pnl_pct: float
    model_config = ConfigDict(from_attributes=True)


class PortfolioUpdate(BaseModel):
    cash: float = Field(ge=0)
    nav_peak: float | None = Field(default=None, gt=0)


class PortfolioRead(BaseModel):
    id: int
    name: str
    cash: float
    invested_value: float
    total_value: float
    nav_peak: float
    drawdown: float
    position_ratio: float
    stock_ratio: float
    etf_ratio: float
    industry_exposure: dict[str, float]
    positions: list[PositionRead]


class AnalysisRequest(BaseModel):
    trade_date: date | None = None


class RecommendationStatusUpdate(BaseModel):
    status: Literal["pending", "executed", "ignored"]


class SettingsUpdate(BaseModel):
    values: dict[str, Any]


class BacktestRequest(BaseModel):
    name: str = "Mock策略管线验证"
    initial_capital: float = Field(default=150000, gt=0)
    trading_days: int = Field(default=120, ge=30, le=1000)
    fee_rate: float = Field(default=0.0003, ge=0, le=0.02)
    slippage_rate: float = Field(default=0.0005, ge=0, le=0.02)


class HealthRead(BaseModel):
    status: str
    app: str
    data_provider: str
    is_demo: bool
    timestamp: datetime

