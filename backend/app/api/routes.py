from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import BacktestRun, DailyReport, DataSourceStatus, IndustryScore, MarketRegime, Position, Recommendation
from app.schemas import (
    AnalysisRequest,
    BacktestRequest,
    PortfolioUpdate,
    PositionCreate,
    PositionUpdate,
    RecommendationStatusUpdate,
    SettingsUpdate,
)
from app.services.analysis import run_analysis
from app.services.backtest import run_mock_backtest
from app.services.portfolio import ensure_default_portfolio, portfolio_payload
from app.services.settings import settings_payload, update_settings


router = APIRouter(prefix="/api")


def _latest_analysis_date(db: Session) -> date | None:
    return db.scalar(select(func.max(IndustryScore.trade_date)))


def _industry_payload(row: IndustryScore) -> dict[str, object]:
    return {
        "id": row.id,
        "trade_date": row.trade_date,
        "industry_code": row.industry_code,
        "industry_name": row.industry_name,
        "score": row.score,
        "rank": row.rank,
        "state": row.state,
        "metrics": row.metrics,
        "is_selected": row.is_selected,
        "candidate_code": row.candidate_code,
        "candidate_name": row.candidate_name,
        "source_timestamp": row.source_timestamp,
    }


def _recommendation_payload(row: Recommendation) -> dict[str, object]:
    return {
        "id": row.id,
        "trade_date": row.trade_date,
        "valid_from": row.valid_from,
        "instrument_code": row.instrument_code,
        "instrument_name": row.instrument_name,
        "instrument_type": row.instrument_type,
        "industry_code": row.industry_code,
        "industry_name": row.industry_name,
        "action": row.action,
        "score": row.score,
        "confidence": row.confidence,
        "suggested_amount": row.suggested_amount,
        "max_amount": row.max_amount,
        "entry_condition": row.entry_condition,
        "invalidation_condition": row.invalidation_condition,
        "exit_condition": row.exit_condition,
        "risk_notes": row.risk_notes,
        "reasoning": row.reasoning,
        "score_components": row.score_components,
        "source_timestamp": row.source_timestamp,
        "strategy_version": row.strategy_version,
        "status": row.status,
        "is_demo": row.is_demo,
    }


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "data_provider": settings.data_provider,
        "is_demo": settings.data_provider == "mock",
        "timestamp": datetime.now(timezone.utc),
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict[str, object]:
    latest_date = _latest_analysis_date(db)
    if latest_date is None:
        run_analysis(db)
        latest_date = _latest_analysis_date(db)
    portfolio = ensure_default_portfolio(db)
    regime = db.scalar(select(MarketRegime).where(MarketRegime.trade_date == latest_date))
    industries = db.scalars(
        select(IndustryScore)
        .where(IndustryScore.trade_date == latest_date, IndustryScore.is_selected.is_(True))
        .order_by(IndustryScore.rank)
    ).all()
    recommendations = db.scalars(
        select(Recommendation)
        .where(Recommendation.trade_date == latest_date)
        .order_by(Recommendation.score.desc())
    ).all()
    source = db.scalar(select(DataSourceStatus).order_by(DataSourceStatus.last_updated.desc()))
    return {
        "analysis_date": latest_date,
        "is_demo": bool(source.is_demo) if source else True,
        "portfolio": portfolio_payload(portfolio),
        "market": {
            "regime": regime.regime,
            "risk_score": regime.risk_score,
            "equity_min": regime.equity_min,
            "equity_max": regime.equity_max,
            "reasons": regime.reasons,
            "source_timestamp": regime.source_timestamp,
        }
        if regime
        else None,
        "industries": [_industry_payload(row) for row in industries],
        "recommendations": [_recommendation_payload(row) for row in recommendations],
        "data_status": {
            "provider": source.provider,
            "status": source.status,
            "is_demo": source.is_demo,
            "completeness": source.completeness,
            "message": source.message,
            "last_updated": source.last_updated,
        }
        if source
        else None,
    }


@router.get("/market/regime")
def get_market_regime(db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.scalar(select(MarketRegime).order_by(MarketRegime.trade_date.desc()))
    if row is None:
        raise HTTPException(status_code=404, detail="尚未生成市场状态")
    return {
        "trade_date": row.trade_date,
        "regime": row.regime,
        "risk_score": row.risk_score,
        "equity_min": row.equity_min,
        "equity_max": row.equity_max,
        "reasons": row.reasons,
        "source_timestamp": row.source_timestamp,
        "is_demo": row.is_demo,
    }


@router.get("/industries/rankings")
def industry_rankings(
    trade_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    target = trade_date or _latest_analysis_date(db)
    if target is None:
        raise HTTPException(status_code=404, detail="尚未生成行业排名")
    rows = db.scalars(
        select(IndustryScore).where(IndustryScore.trade_date == target).order_by(IndustryScore.rank)
    ).all()
    return {"trade_date": target, "count": len(rows), "items": [_industry_payload(row) for row in rows]}


@router.get("/industries/{industry_code}")
def industry_detail(industry_code: str, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.scalar(
        select(IndustryScore)
        .where(IndustryScore.industry_code == industry_code)
        .order_by(IndustryScore.trade_date.desc())
    )
    if row is None:
        raise HTTPException(status_code=404, detail="行业不存在")
    recommendation = db.scalar(
        select(Recommendation)
        .where(
            Recommendation.trade_date == row.trade_date,
            Recommendation.industry_code == industry_code,
        )
        .order_by(Recommendation.score.desc())
    )
    return {
        "industry": _industry_payload(row),
        "candidate": _recommendation_payload(recommendation) if recommendation else None,
    }


@router.get("/recommendations")
def recommendations(
    trade_date: date | None = Query(default=None),
    instrument_type: str | None = Query(default=None, pattern="^(stock|etf)$"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    target = trade_date or db.scalar(select(func.max(Recommendation.trade_date)))
    if target is None:
        return {"trade_date": None, "items": []}
    query = select(Recommendation).where(Recommendation.trade_date == target)
    if instrument_type:
        query = query.where(Recommendation.instrument_type == instrument_type)
    rows = db.scalars(query.order_by(Recommendation.score.desc())).all()
    return {"trade_date": target, "items": [_recommendation_payload(row) for row in rows]}


@router.get("/recommendations/{recommendation_id}")
def recommendation_detail(recommendation_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.get(Recommendation, recommendation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="建议不存在")
    return _recommendation_payload(row)


@router.patch("/recommendations/{recommendation_id}/status")
def recommendation_status(
    recommendation_id: int,
    payload: RecommendationStatusUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    row = db.get(Recommendation, recommendation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="建议不存在")
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return _recommendation_payload(row)


@router.get("/reports/daily")
def daily_reports(db: Session = Depends(get_db)) -> dict[str, object]:
    rows = db.scalars(select(DailyReport).order_by(DailyReport.report_date.desc()).limit(30)).all()
    return {
        "items": [
            {
                "report_date": row.report_date,
                "is_demo": row.is_demo,
                "source_timestamp": row.source_timestamp,
                "strategy_version": row.strategy_version,
            }
            for row in rows
        ]
    }


@router.get("/reports/daily/{report_date}")
def daily_report_detail(report_date: date, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.scalar(select(DailyReport).where(DailyReport.report_date == report_date))
    if row is None:
        raise HTTPException(status_code=404, detail="日报不存在")
    return {
        "report_date": row.report_date,
        "content": row.content,
        "source_timestamp": row.source_timestamp,
        "strategy_version": row.strategy_version,
        "is_demo": row.is_demo,
    }


@router.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)) -> dict[str, object]:
    return portfolio_payload(ensure_default_portfolio(db))


@router.put("/portfolio")
def update_portfolio(payload: PortfolioUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    portfolio = ensure_default_portfolio(db)
    portfolio.cash = payload.cash
    if payload.nav_peak is not None:
        portfolio.nav_peak = payload.nav_peak
    db.commit()
    db.refresh(portfolio)
    return portfolio_payload(portfolio)


@router.post("/portfolio/positions", status_code=status.HTTP_201_CREATED)
def create_position(payload: PositionCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    portfolio = ensure_default_portfolio(db)
    existing = db.scalar(
        select(Position).where(
            Position.portfolio_id == portfolio.id,
            Position.instrument_code == payload.instrument_code,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="该证券已在持仓中，请编辑现有记录")
    row = Position(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(portfolio)
    return portfolio_payload(portfolio)


@router.put("/portfolio/positions/{position_id}")
def update_position(
    position_id: int,
    payload: PositionUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    row = db.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=404, detail="持仓不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    portfolio = ensure_default_portfolio(db)
    db.refresh(portfolio)
    return portfolio_payload(portfolio)


@router.delete(
    "/portfolio/positions/{position_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_position(position_id: int, db: Session = Depends(get_db)) -> Response:
    row = db.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=404, detail="持仓不存在")
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/analysis/run")
def trigger_analysis(payload: AnalysisRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return run_analysis(db, trade_date=payload.trade_date)


@router.post("/backtests", status_code=status.HTTP_201_CREATED)
def create_backtest(payload: BacktestRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    row = run_mock_backtest(db, payload)
    return {
        "id": row.id,
        "name": row.name,
        "status": row.status,
        "metrics": row.metrics,
        "equity_curve": row.equity_curve,
        "parameters": row.parameters,
        "is_demo": row.is_demo,
    }


@router.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.get(BacktestRun, backtest_id)
    if row is None:
        raise HTTPException(status_code=404, detail="回测不存在")
    return {
        "id": row.id,
        "name": row.name,
        "status": row.status,
        "metrics": row.metrics,
        "equity_curve": row.equity_curve,
        "parameters": row.parameters,
        "is_demo": row.is_demo,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
    }


@router.get("/settings")
def get_strategy_settings(db: Session = Depends(get_db)) -> dict[str, object]:
    return {"values": settings_payload(db)}


@router.put("/settings")
def put_strategy_settings(payload: SettingsUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    return {"values": update_settings(db, payload.values)}


@router.get("/data/status")
def data_status(db: Session = Depends(get_db)) -> dict[str, object]:
    rows = db.scalars(select(DataSourceStatus).order_by(DataSourceStatus.provider)).all()
    return {
        "items": [
            {
                "provider": row.provider,
                "status": row.status,
                "is_demo": row.is_demo,
                "completeness": row.completeness,
                "message": row.message,
                "last_updated": row.last_updated,
            }
            for row in rows
        ]
    }


