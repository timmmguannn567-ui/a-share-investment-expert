from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from app.providers.base import IndustryMetrics, InstrumentMetrics, MarketMetrics


INDUSTRY_WEIGHTS = {
    "relative_strength": 0.25,
    "trend": 0.20,
    "breadth": 0.20,
    "volume_change": 0.15,
    "risk_quality": 0.10,
    "fundamentals": 0.05,
    "event_safety": 0.05,
}

STOCK_WEIGHTS = {
    "industry_strength": 0.25,
    "fundamentals": 0.20,
    "technical": 0.20,
    "liquidity": 0.10,
    "valuation": 0.10,
    "leadership": 0.10,
    "event_safety": 0.05,
}

ETF_WEIGHTS = {
    "momentum": 0.18,
    "trend": 0.20,
    "liquidity": 0.12,
    "volatility_quality": 0.10,
    "scale": 0.10,
    "tracking_quality": 0.12,
    "premium_discount_quality": 0.10,
    "leadership": 0.08,
}


def weighted_score(values: dict[str, float], weights: dict[str, float]) -> float:
    missing = set(weights) - set(values)
    if missing:
        raise ValueError(f"Missing score components: {sorted(missing)}")
    return round(sum(max(0.0, min(100.0, values[key])) * weight for key, weight in weights.items()), 2)


def percentile_ranks(values: Iterable[float]) -> list[float]:
    data = list(values)
    if not data:
        return []
    if len(data) == 1:
        return [100.0]
    sorted_values = sorted(data)
    output: list[float] = []
    for value in data:
        first = sorted_values.index(value)
        last = len(sorted_values) - 1 - sorted_values[::-1].index(value)
        average_index = (first + last) / 2
        output.append(round(average_index / (len(data) - 1) * 100, 2))
    return output


def score_industries(industries: list[IndustryMetrics]) -> list[dict[str, object]]:
    if not industries:
        return []
    raw = [asdict(industry) for industry in industries]
    percentile_by_metric: dict[str, list[float]] = {}
    for metric in INDUSTRY_WEIGHTS:
        percentile_by_metric[metric] = percentile_ranks(float(item[metric]) for item in raw)

    results: list[dict[str, object]] = []
    for index, industry in enumerate(industries):
        components = {metric: percentile_by_metric[metric][index] for metric in INDUSTRY_WEIGHTS}
        score = weighted_score(components, INDUSTRY_WEIGHTS)
        if score >= 75:
            state = "强势延续"
        elif score >= 65:
            state = "转强观察"
        elif score >= 45:
            state = "震荡"
        elif score >= 30:
            state = "转弱"
        else:
            state = "高风险回避"
        results.append(
            {
                "code": industry.code,
                "name": industry.name,
                "subindustry": industry.subindustry,
                "score": score,
                "state": state,
                "components": components,
            }
        )
    results.sort(key=lambda item: float(item["score"]), reverse=True)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank
    return results


def score_stock(stock: InstrumentMetrics, industry_score: float) -> tuple[float, dict[str, float]]:
    components = {
        "industry_strength": industry_score,
        "fundamentals": stock.fundamentals,
        "technical": (stock.momentum + stock.trend) / 2,
        "liquidity": stock.liquidity,
        "valuation": stock.valuation,
        "leadership": stock.leadership,
        "event_safety": stock.event_safety,
    }
    return weighted_score(components, STOCK_WEIGHTS), {key: round(value, 2) for key, value in components.items()}


def score_etf(etf: InstrumentMetrics) -> tuple[float, dict[str, float]]:
    components = {key: float(getattr(etf, key)) for key in ETF_WEIGHTS}
    return weighted_score(components, ETF_WEIGHTS), {key: round(value, 2) for key, value in components.items()}


def market_regime(metrics: MarketMetrics) -> dict[str, object]:
    strength = (
        metrics.index_trend * 0.25
        + metrics.momentum_20d * 0.20
        + metrics.breadth * 0.20
        + metrics.volume_ratio * 0.10
        + metrics.industry_diffusion * 0.10
        + metrics.volatility * 0.075
        + metrics.drawdown * 0.075
    )
    risk_score = round(100 - strength, 2)
    if risk_score < 30:
        regime, equity_range = "风险偏好上升", (0.55, 0.80)
    elif risk_score < 50:
        regime, equity_range = "正常震荡", (0.35, 0.65)
    elif risk_score < 70:
        regime, equity_range = "风险偏好下降", (0.10, 0.40)
    else:
        regime, equity_range = "高风险防守", (0.0, 0.15)
    reasons = [
        f"趋势强度 {metrics.index_trend:.1f}",
        f"市场宽度 {metrics.breadth:.1f}",
        f"20日动量 {metrics.momentum_20d:.1f}",
        f"行业扩散 {metrics.industry_diffusion:.1f}",
    ]
    return {
        "regime": regime,
        "risk_score": risk_score,
        "equity_min": equity_range[0],
        "equity_max": equity_range[1],
        "reasons": reasons,
    }

