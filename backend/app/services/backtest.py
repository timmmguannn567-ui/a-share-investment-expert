from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import BacktestRun, BacktestTrade
from app.schemas import BacktestRequest


def _business_days(end: date, count: int) -> list[date]:
    days: list[date] = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(days))


def run_mock_backtest(db: Session, request: BacktestRequest) -> BacktestRun:
    """Validate the backtest pipeline with deterministic synthetic returns.

    This is intentionally not evidence of strategy quality. Every result is marked demo.
    Signals observed on day t affect returns starting on day t+1.
    """
    rng = random.Random(20261020 + request.trading_days)
    days = _business_days(date.today(), request.trading_days)
    capital = request.initial_capital
    peak = capital
    max_drawdown = 0.0
    daily_returns: list[float] = []
    equity_curve: list[dict[str, object]] = []
    signal = 0.0
    pending_signal = 0.0
    trade_count = 0

    run = BacktestRun(
        name=request.name,
        parameters=request.model_dump(),
        status="running",
        is_demo=True,
    )
    db.add(run)
    db.flush()

    for index, day in enumerate(days):
        market_return = rng.gauss(0.00025, 0.012)
        executed_signal = pending_signal
        if executed_signal != signal:
            trade_count += 1
            side = "BUY" if executed_signal > signal else "SELL"
            db.add(
                BacktestTrade(
                    backtest_run_id=run.id,
                    signal_date=days[max(0, index - 1)],
                    execution_date=day,
                    instrument_code="MOCK300",
                    side=side,
                    price=100 * (1 + market_return),
                    quantity=abs(executed_signal - signal) * capital / 100,
                )
            )
        turnover = abs(executed_signal - signal)
        cost = turnover * (request.fee_rate + request.slippage_rate)
        signal = executed_signal
        strategy_return = market_return * signal - cost
        capital *= 1 + strategy_return
        peak = max(peak, capital)
        drawdown = (peak - capital) / peak
        max_drawdown = max(max_drawdown, drawdown)
        daily_returns.append(strategy_return)
        equity_curve.append({"date": day.isoformat(), "value": round(capital, 2), "drawdown": round(drawdown, 6)})

        # Today's close signal becomes eligible on the next iteration only.
        momentum_proxy = math.sin(index / 11) + rng.uniform(-0.35, 0.35)
        pending_signal = 0.7 if momentum_proxy > 0.15 else 0.25 if momentum_proxy > -0.25 else 0.0

    total_return = capital / request.initial_capital - 1
    years = max(request.trading_days / 252, 1 / 252)
    annual_return = (1 + total_return) ** (1 / years) - 1
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean_return) ** 2 for value in daily_returns) / max(1, len(daily_returns) - 1)
    annual_volatility = math.sqrt(variance) * math.sqrt(252)
    sharpe = annual_return / annual_volatility if annual_volatility else 0.0
    calmar = annual_return / max_drawdown if max_drawdown else 0.0
    positive_days = sum(1 for value in daily_returns if value > 0)

    run.metrics = {
        "initial_capital": request.initial_capital,
        "ending_capital": round(capital, 2),
        "total_return": round(total_return, 6),
        "annual_return": round(annual_return, 6),
        "max_drawdown": round(max_drawdown, 6),
        "annual_volatility": round(annual_volatility, 6),
        "sharpe": round(sharpe, 3),
        "calmar": round(calmar, 3),
        "positive_day_ratio": round(positive_days / len(daily_returns), 4),
        "trade_count": trade_count,
        "notice": "Mock演示回测，仅验证T+1、费用和指标管线，不代表策略有效性。",
    }
    run.equity_curve = equity_curve
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run

