from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Portfolio, Position
from app.services.risk import PortfolioRisk


def ensure_default_portfolio(db: Session) -> Portfolio:
    portfolio = db.scalar(select(Portfolio).order_by(Portfolio.id))
    if portfolio is None:
        portfolio = Portfolio(name="我的组合", cash=100000.0, nav_peak=100000.0)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


def calculate_portfolio_risk(portfolio: Portfolio) -> PortfolioRisk:
    invested = 0.0
    stock_value = 0.0
    etf_value = 0.0
    exposure: dict[str, float] = {}
    for position in portfolio.positions:
        market_value = position.quantity * position.current_price
        invested += market_value
        if position.instrument_type == "stock":
            stock_value += market_value
        else:
            etf_value += market_value
        industry = position.industry_l1 or "未分类"
        exposure[industry] = exposure.get(industry, 0.0) + market_value
    total = portfolio.cash + invested
    peak = max(portfolio.nav_peak, total)
    drawdown = max(0.0, (peak - total) / peak) if peak else 0.0
    return PortfolioRisk(
        total_value=round(total, 2),
        invested_value=round(invested, 2),
        stock_value=round(stock_value, 2),
        etf_value=round(etf_value, 2),
        drawdown=round(drawdown, 6),
        industry_exposure={key: round(value, 2) for key, value in exposure.items()},
    )


def portfolio_payload(portfolio: Portfolio) -> dict[str, object]:
    risk = calculate_portfolio_risk(portfolio)
    total = risk.total_value or 1.0
    positions = []
    for position in portfolio.positions:
        market_value = position.quantity * position.current_price
        cost_value = position.quantity * position.cost_price
        pnl = market_value - cost_value
        positions.append(
            {
                "id": position.id,
                "instrument_code": position.instrument_code,
                "name": position.name,
                "instrument_type": position.instrument_type,
                "quantity": position.quantity,
                "cost_price": position.cost_price,
                "current_price": position.current_price,
                "industry_l1": position.industry_l1,
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl / cost_value, 6) if cost_value else 0.0,
            }
        )
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "cash": round(portfolio.cash, 2),
        "invested_value": risk.invested_value,
        "total_value": risk.total_value,
        "nav_peak": round(max(portfolio.nav_peak, risk.total_value), 2),
        "drawdown": risk.drawdown,
        "position_ratio": round(risk.invested_value / total, 6),
        "stock_ratio": round(risk.stock_value / total, 6),
        "etf_ratio": round(risk.etf_value / total, 6),
        "industry_exposure": risk.industry_exposure,
        "positions": positions,
    }

