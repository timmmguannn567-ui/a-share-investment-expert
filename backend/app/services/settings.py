from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StrategyConfig


DEFAULT_SETTINGS: dict[str, object] = {
    "max_drawdown": 0.15,
    "etf_absolute_cap": 30000,
    "etf_nav_cap": 0.20,
    "stock_absolute_cap": 15000,
    "stock_nav_cap": 0.08,
    "stock_total_cap": 0.30,
    "etf_total_cap": 0.80,
    "industry_exposure_cap": 0.30,
    "selected_industry_count": 5,
    "industry_score_threshold": 62,
    "minimum_listed_days": 365,
    "exclude_st": True,
    "allow_cash": True,
    "focus_etfs": ["588000", "512010"],
    "supported_boards": ["主板", "创业板", "科创板", "北交所"],
    "fee_rate": 0.0003,
    "slippage_rate": 0.0005,
    "report_time": "16:30",
}


def seed_settings(db: Session) -> None:
    existing = set(db.scalars(select(StrategyConfig.key)).all())
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            db.add(StrategyConfig(key=key, value=value, description="MVP默认参数，可在设置页调整"))
    db.commit()


def settings_payload(db: Session) -> dict[str, object]:
    rows = db.scalars(select(StrategyConfig).order_by(StrategyConfig.key)).all()
    return {row.key: row.value for row in rows}


def update_settings(db: Session, values: dict[str, object]) -> dict[str, object]:
    rows = {row.key: row for row in db.scalars(select(StrategyConfig)).all()}
    for key, value in values.items():
        if key in rows:
            rows[key].value = value
        else:
            db.add(StrategyConfig(key=key, value=value, description="用户自定义参数"))
    db.commit()
    return settings_payload(db)

