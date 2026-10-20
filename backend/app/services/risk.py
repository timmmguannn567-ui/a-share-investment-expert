from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioRisk:
    total_value: float
    invested_value: float
    stock_value: float
    etf_value: float
    drawdown: float
    industry_exposure: dict[str, float]


def drawdown_equity_cap(drawdown: float) -> float:
    if drawdown >= 0.15:
        return 0.0
    if drawdown >= 0.12:
        return 0.10
    if drawdown >= 0.10:
        return 0.30
    if drawdown >= 0.08:
        return 0.60
    if drawdown >= 0.05:
        return 0.80
    return 1.0


def calculate_max_amount(
    instrument_type: str,
    total_value: float,
    drawdown: float,
    board: str = "主板",
    risk_score: float = 50.0,
    etf_absolute_cap: float = 30000.0,
    etf_nav_cap: float = 0.20,
    stock_absolute_cap: float = 15000.0,
    stock_nav_cap: float = 0.08,
) -> float:
    if total_value <= 0:
        return 0.0
    if instrument_type == "etf":
        base = min(etf_absolute_cap, total_value * etf_nav_cap)
    else:
        base = min(stock_absolute_cap, total_value * stock_nav_cap)

    board_multiplier = {
        "北交所": 0.65,
        "科创板": 0.85,
        "创业板": 0.85,
    }.get(board, 1.0)
    market_multiplier = 1.0 if risk_score < 30 else 0.8 if risk_score < 50 else 0.5 if risk_score < 70 else 0.0
    max_amount = base * board_multiplier * market_multiplier * drawdown_equity_cap(drawdown)
    return round(max_amount / 100) * 100


def suggested_amount(max_amount: float, score: float) -> float:
    if max_amount <= 0 or score < 65:
        return 0.0
    multiplier = 0.45 if score < 72 else 0.65 if score < 82 else 0.8
    return min(max_amount, round(max_amount * multiplier / 100) * 100)


def remaining_industry_capacity(total_value: float, current_exposure: float, exposure_cap: float = 0.30) -> float:
    return max(0.0, total_value * exposure_cap - current_exposure)


def cap_recommendation(
    amount: float,
    max_amount: float,
    available_cash: float,
    industry_capacity: float,
) -> float:
    return max(0.0, round(min(amount, max_amount, available_cash, industry_capacity) / 100) * 100)

