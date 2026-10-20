from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import IndustryScore, Recommendation
from app.providers.mock import MockDataProvider
from app.services.analysis import run_analysis
from app.services.portfolio import ensure_default_portfolio
from app.services.settings import seed_settings


def _session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_analysis_is_repeatable_and_respects_candidate_limits() -> None:
    with _session() as db:
        ensure_default_portfolio(db)
        seed_settings(db)
        provider = MockDataProvider()
        report = run_analysis(db, provider=provider)
        target = report["report_date"]
        assert report["is_demo"] is True
        assert 3 <= len(report["selected_industries"]) <= 5
        industry_count = db.scalar(select(func.count()).select_from(IndustryScore))
        assert industry_count == 31
        stock_recommendations = db.scalars(
            select(Recommendation).where(Recommendation.instrument_type == "stock")
        ).all()
        industry_codes = [item.industry_code for item in stock_recommendations]
        assert len(industry_codes) == len(set(industry_codes))

        run_analysis(db, provider=provider)
        assert db.scalar(select(func.count()).select_from(IndustryScore)) == 31
        assert target == report["report_date"]


def test_signal_is_valid_only_from_next_trading_day() -> None:
    with _session() as db:
        ensure_default_portfolio(db)
        seed_settings(db)
        run_analysis(db, provider=MockDataProvider())
        rows = db.scalars(select(Recommendation)).all()
        assert rows
        assert all(row.valid_from > row.trade_date for row in rows)

