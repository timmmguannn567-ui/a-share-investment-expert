from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from app.providers.base import IndustryMetrics, InstrumentMetrics, MarketMetrics


INDUSTRY_WEIGHTS = {
    "relative_strength": 0.25,
    "breadth": 0.20,
    "trend_quality": 0.15,
    "price_volume_confirmation": 0.15,
    "flow_persistence": 0.10,
    "valuation_earnings": 0.10,
    "crowding_quality": 0.05,
}

STOCK_WEIGHTS = {
    "industry_position_liquidity": 0.25,
    "trend_relative_strength": 0.25,
    "earnings_quality": 0.15,
    "price_volume_flow": 0.15,
    "valuation": 0.10,
    "risk_quality": 0.10,
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
    raw = []
    for industry in industries:
        values = asdict(industry)
        raw.append(
            {
                "relative_strength": values["relative_strength"],
                "breadth": values["breadth"],
                "trend_quality": (values["trend"] + values["risk_quality"]) / 2,
                "price_volume_confirmation": values["volume_change"],
                "flow_persistence": (values["volume_change"] + values["relative_strength"]) / 2,
                "valuation_earnings": (values["fundamentals"] + values["event_safety"]) / 2,
                "crowding_quality": values["risk_quality"],
            }
        )
    percentile_by_metric: dict[str, list[float]] = {}
    for metric in INDUSTRY_WEIGHTS:
        percentile_by_metric[metric] = percentile_ranks(float(item[metric]) for item in raw)

    results: list[dict[str, object]] = []
    for index, industry in enumerate(industries):
        components = {metric: percentile_by_metric[metric][index] for metric in INDUSTRY_WEIGHTS}
        score = weighted_score(components, INDUSTRY_WEIGHTS)
        breadth = components["breadth"]
        crowding = components["crowding_quality"]
        if score >= 78 and breadth >= 60 and crowding >= 35:
            state = "领涨扩散"
        elif score >= 72 and breadth < 60:
            state = "强势集中"
        elif score >= 65:
            state = "修复"
        elif score >= 48:
            state = "回踩"
        elif score >= 30:
            state = "走弱"
        else:
            state = "过热" if crowding < 20 and components["relative_strength"] > 75 else "走弱"
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
        "industry_position_liquidity": (industry_score + stock.leadership + stock.liquidity) / 3,
        "trend_relative_strength": (stock.momentum + stock.trend) / 2,
        "earnings_quality": stock.fundamentals,
        "price_volume_flow": (stock.momentum + stock.liquidity + stock.leadership) / 3,
        "valuation": stock.valuation,
        "risk_quality": (stock.volatility_quality + stock.event_safety) / 2,
    }
    return weighted_score(components, STOCK_WEIGHTS), {key: round(value, 2) for key, value in components.items()}


def score_etf(etf: InstrumentMetrics) -> tuple[float, dict[str, float]]:
    components = {key: float(getattr(etf, key)) for key in ETF_WEIGHTS}
    return weighted_score(components, ETF_WEIGHTS), {key: round(value, 2) for key, value in components.items()}


def market_regime(metrics: MarketMetrics) -> dict[str, object]:
    defensive_quality = (
        metrics.broad_selloff_pressure * 0.35
        + metrics.deep_bear_count * 0.25
        + (100 - metrics.breadth) * 0.20
        + (100 - metrics.trend_bull_count) * 0.20
    )
    risk_score = round(max(0.0, min(100.0, defensive_quality)), 2)

    if metrics.proxy_ratio < 0.60 and metrics.proxy_rate < 1.0 and risk_score >= 55:
        regime, equity_range = "冰封", (0.0, 0.15)
    elif metrics.proxy_ratio < 0.60 and metrics.proxy_rate >= 1.35:
        regime, equity_range = "反弹", (0.25, 0.45)
    elif metrics.proxy_ratio < 0.60:
        regime, equity_range = "磨底", (0.10, 0.30)
    elif metrics.proxy_ratio >= 1.50 and metrics.proxy_rate >= 1.0 and metrics.trend_bull_count >= 55:
        regime, equity_range = "强攻", (0.60, 0.75)
    elif metrics.proxy_rate < 0.92 or metrics.proxy_slope_3d < -0.12:
        regime, equity_range = "回踩", (0.35, 0.55)
    elif metrics.proxy_rate >= 1.20 and metrics.wave_continuity < 60:
        regime, equity_range = "反弹", (0.25, 0.45)
    else:
        regime, equity_range = "趋势", (0.50, 0.70)

    divergence = bool(
        metrics.index_trend >= 62
        and metrics.proxy_slope_3d < 0
        and metrics.proxy_rate < 1
    )
    retreat_warning = bool(metrics.proxy_ratio > 1.5 and metrics.proxy_rate < 1.0)
    ice_reversal = bool(metrics.proxy_ratio < 0.5 and metrics.proxy_rate > 1.5)
    research_signals = []
    if retreat_warning:
        research_signals.append("高位退潮候选")
    if ice_reversal:
        research_signals.append("冰点修复候选")
    if divergence:
        research_signals.append("市场内部顶背离")
    if not research_signals:
        research_signals.append("暂无研究级预警")

    reasons = [
        f"代理多空比 {metrics.proxy_ratio:.2f}",
        f"变化速率 {metrics.proxy_rate:.2f}",
        f"趋势多头 {metrics.trend_bull_count:.1f}",
        f"普遍杀跌压力 {metrics.broad_selloff_pressure:.1f}",
    ]
    return {
        "regime": regime,
        "risk_score": risk_score,
        "equity_min": equity_range[0],
        "equity_max": equity_range[1],
        "reasons": reasons,
        "proxy_ratio": round(metrics.proxy_ratio, 3),
        "proxy_rate": round(metrics.proxy_rate, 3),
        "proxy_slope_3d": round(metrics.proxy_slope_3d, 3),
        "proxy_percentile": round(metrics.proxy_percentile, 1),
        "broad_selloff_pressure": round(metrics.broad_selloff_pressure, 1),
        "deep_bear_count": round(metrics.deep_bear_count, 1),
        "trend_bull_count": round(metrics.trend_bull_count, 1),
        "wave_continuity": round(metrics.wave_continuity, 1),
        "divergence": divergence,
        "research_signals": research_signals,
        "model_status": "待回测",
        "proxy_notice": "公开可复现的代理指标，不是未公开原公式",
    }

