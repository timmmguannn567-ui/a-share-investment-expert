from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DataSourceStatus
from app.providers.mock import MockDataProvider
from app.services.analysis import latest_report, run_analysis
from app.services.portfolio import ensure_default_portfolio
from app.services.settings import seed_settings


def initialize_app_data(db: Session) -> None:
    ensure_default_portfolio(db)
    seed_settings(db)
    provider = MockDataProvider()
    status = db.scalar(select(DataSourceStatus).where(DataSourceStatus.provider == provider.name))
    if status is None:
        payload = provider.status()
        db.add(
            DataSourceStatus(
                provider=str(payload["provider"]),
                status=str(payload["status"]),
                is_demo=bool(payload["is_demo"]),
                completeness=float(payload["completeness"]),
                message=str(payload["message"]),
                last_updated=payload["last_updated"],
            )
        )
        db.commit()
    if latest_report(db) is None:
        run_analysis(db, provider=provider)

