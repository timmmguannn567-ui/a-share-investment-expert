from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class MarketMetrics:
    index_trend: float
    momentum_20d: float
    breadth: float
    volume_ratio: float
    volatility: float
    drawdown: float
    industry_diffusion: float
    proxy_ratio: float
    proxy_rate: float
    proxy_slope_3d: float
    proxy_percentile: float
    broad_selloff_pressure: float
    deep_bear_count: float
    trend_bull_count: float
    wave_continuity: float


@dataclass(frozen=True)
class IndustryMetrics:
    code: str
    name: str
    subindustry: str
    relative_strength: float
    trend: float
    breadth: float
    volume_change: float
    risk_quality: float
    fundamentals: float
    event_safety: float


@dataclass(frozen=True)
class InstrumentMetrics:
    code: str
    name: str
    instrument_type: str
    board: str
    industry_code: str | None
    industry_name: str | None
    subindustry: str | None
    price: float
    momentum: float
    trend: float
    liquidity: float
    volatility_quality: float
    fundamentals: float
    valuation: float
    leadership: float
    event_safety: float
    scale: float = 70.0
    tracking_quality: float = 75.0
    premium_discount_quality: float = 80.0
    listed_days: int = 1200
    is_st: bool = False
    is_suspended: bool = False
    risk_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarketSnapshot:
    trade_date: date
    next_trade_date: date
    source_timestamp: datetime
    source_name: str
    is_demo: bool
    completeness: float
    market: MarketMetrics
    industries: list[IndustryMetrics] = field(default_factory=list)
    stocks: list[InstrumentMetrics] = field(default_factory=list)
    etfs: list[InstrumentMetrics] = field(default_factory=list)


class DataProvider(Protocol):
    name: str
    is_demo: bool

    def get_snapshot(self, trade_date: date | None = None) -> MarketSnapshot:
        ...

    def status(self) -> dict[str, object]:
        ...

