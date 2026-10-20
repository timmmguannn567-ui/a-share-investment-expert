from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    instrument_type: Mapped[str] = mapped_column(String(16), index=True)
    board: Mapped[str | None] = mapped_column(String(24), nullable=True)
    industry_l1: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    industry_l2: Mapped[str | None] = mapped_column(String(60), nullable=True)
    list_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_st: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    data_source: Mapped[str] = mapped_column(String(32), default="mock")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), default="我的组合")
    cash: Mapped[float] = mapped_column(Float, default=100000.0)
    nav_peak: Mapped[float] = mapped_column(Float, default=100000.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    positions: Mapped[list["Position"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    instrument_code: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(80))
    instrument_type: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[float] = mapped_column(Float)
    cost_price: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    industry_l1: Mapped[str | None] = mapped_column(String(40), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    portfolio: Mapped[Portfolio] = relationship(back_populates="positions")


class Trade(Base):
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    instrument_code: Mapped[str] = mapped_column(String(16), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    value: Mapped[Any] = mapped_column(JSON)
    description: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MarketRegime(Base):
    __tablename__ = "market_regimes"
    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    regime: Mapped[str] = mapped_column(String(32))
    risk_score: Mapped[float] = mapped_column(Float)
    equity_min: Mapped[float] = mapped_column(Float)
    equity_max: Mapped[float] = mapped_column(Float)
    reasons: Mapped[list[str]] = mapped_column(JSON)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class IndustryScore(Base):
    __tablename__ = "industry_scores"
    __table_args__ = (UniqueConstraint("trade_date", "industry_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    industry_code: Mapped[str] = mapped_column(String(16))
    industry_name: Mapped[str] = mapped_column(String(40), index=True)
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(24))
    metrics: Mapped[dict[str, float]] = mapped_column(JSON)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    candidate_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    candidate_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class InstrumentScore(Base):
    __tablename__ = "instrument_scores"
    __table_args__ = (UniqueConstraint("trade_date", "instrument_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    instrument_code: Mapped[str] = mapped_column(String(16), index=True)
    score: Mapped[float] = mapped_column(Float)
    components: Mapped[dict[str, float]] = mapped_column(JSON)
    passed_filters: Mapped[bool] = mapped_column(Boolean, default=True)
    filter_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    valid_from: Mapped[date] = mapped_column(Date, index=True)
    instrument_code: Mapped[str] = mapped_column(String(16), index=True)
    instrument_name: Mapped[str] = mapped_column(String(80))
    instrument_type: Mapped[str] = mapped_column(String(16))
    industry_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    industry_name: Mapped[str | None] = mapped_column(String(40), nullable=True)
    action: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String(16))
    suggested_amount: Mapped[float] = mapped_column(Float)
    max_amount: Mapped[float] = mapped_column(Float)
    entry_condition: Mapped[str] = mapped_column(Text)
    invalidation_condition: Mapped[str] = mapped_column(Text)
    exit_condition: Mapped[str] = mapped_column(Text)
    risk_notes: Mapped[list[str]] = mapped_column(JSON)
    reasoning: Mapped[list[str]] = mapped_column(JSON)
    score_components: Mapped[dict[str, float]] = mapped_column(JSON)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    strategy_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class RecommendationSnapshot(Base):
    __tablename__ = "recommendation_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DailyReport(Base):
    __tablename__ = "daily_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    strategy_version: Mapped[str] = mapped_column(String(32))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    equity_curve: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="running")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), index=True)
    signal_date: Mapped[date] = mapped_column(Date)
    execution_date: Mapped[date] = mapped_column(Date)
    instrument_code: Mapped[str] = mapped_column(String(16))
    side: Mapped[str] = mapped_column(String(8))
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float)


class DataSourceStatus(Base):
    __tablename__ = "data_source_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), unique=True)
    status: Mapped[str] = mapped_column(String(16))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    completeness: Mapped[float] = mapped_column(Float, default=1.0)
    message: Mapped[str] = mapped_column(Text)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


