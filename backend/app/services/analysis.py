from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    DailyReport,
    DataSourceStatus,
    IndustryScore,
    InstrumentScore,
    MarketRegime,
    Recommendation,
    RecommendationSnapshot,
)
from app.providers.base import InstrumentMetrics, MarketSnapshot
from app.providers.mock import MockDataProvider
from app.services.portfolio import calculate_portfolio_risk, ensure_default_portfolio
from app.services.risk import calculate_max_amount, cap_recommendation, remaining_industry_capacity, suggested_amount
from app.services.scoring import market_regime, score_etf, score_industries, score_stock
from app.services.settings import settings_payload


def _confidence(score: float) -> str:
    if score >= 82:
        return "较高"
    if score >= 70:
        return "中等"
    return "较低"


def _passes_stock_filters(stock: InstrumentMetrics, config: dict[str, object]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if bool(config.get("exclude_st", True)) and stock.is_st:
        reasons.append("ST或退市风险标的")
    if stock.is_suspended:
        reasons.append("当前停牌")
    if stock.listed_days < int(config.get("minimum_listed_days", 365)):
        reasons.append("上市时间不足")
    if stock.liquidity < 40:
        reasons.append("流动性不足")
    reasons.extend(stock.risk_flags)
    return not reasons, reasons


def _recommendation_payload(item: Recommendation) -> dict[str, object]:
    return {
        "id": item.id,
        "trade_date": item.trade_date.isoformat(),
        "valid_from": item.valid_from.isoformat(),
        "instrument_code": item.instrument_code,
        "instrument_name": item.instrument_name,
        "instrument_type": item.instrument_type,
        "industry_code": item.industry_code,
        "industry_name": item.industry_name,
        "action": item.action,
        "score": item.score,
        "confidence": item.confidence,
        "suggested_amount": item.suggested_amount,
        "max_amount": item.max_amount,
        "entry_condition": item.entry_condition,
        "invalidation_condition": item.invalidation_condition,
        "exit_condition": item.exit_condition,
        "risk_notes": item.risk_notes,
        "reasoning": item.reasoning,
        "score_components": item.score_components,
        "source_timestamp": item.source_timestamp.isoformat(),
        "strategy_version": item.strategy_version,
        "status": item.status,
        "is_demo": item.is_demo,
    }


def _build_recommendation(
    snapshot: MarketSnapshot,
    instrument: InstrumentMetrics,
    score: float,
    components: dict[str, float],
    industry_code: str | None,
    industry_name: str | None,
    portfolio_total: float,
    portfolio_drawdown: float,
    market_risk: float,
    available_cash: float,
    industry_capacity: float,
    config: dict[str, object],
    allow_buy: bool,
) -> Recommendation:
    max_amount = calculate_max_amount(
        instrument_type=instrument.instrument_type,
        total_value=portfolio_total,
        drawdown=portfolio_drawdown,
        board=instrument.board,
        risk_score=market_risk,
        etf_absolute_cap=float(config.get("etf_absolute_cap", 30000)),
        etf_nav_cap=float(config.get("etf_nav_cap", 0.20)),
        stock_absolute_cap=float(config.get("stock_absolute_cap", 15000)),
        stock_nav_cap=float(config.get("stock_nav_cap", 0.08)),
    )
    raw_suggested = suggested_amount(max_amount, score)
    amount = cap_recommendation(raw_suggested, max_amount, available_cash, industry_capacity)
    action = "BUY" if allow_buy and amount > 0 and score >= 72 else "WATCH"
    if not allow_buy:
        amount = 0.0
    return Recommendation(
        trade_date=snapshot.trade_date,
        valid_from=snapshot.next_trade_date,
        instrument_code=instrument.code,
        instrument_name=instrument.name,
        instrument_type=instrument.instrument_type,
        industry_code=industry_code,
        industry_name=industry_name,
        action=action,
        score=score,
        confidence=_confidence(score),
        suggested_amount=amount,
        max_amount=max_amount,
        entry_condition=f"次日价格不高于 {instrument.price * 1.015:.2f}，且所属行业强度未转弱",
        invalidation_condition=f"价格跌破 {instrument.price * 0.94:.2f}，或行业状态降至转弱",
        exit_condition=(
            "个股3日无相对收益减半、5日无跟随退出；ETF 10日无跟随复核。"
            "市场降级或组合回撤规则优先执行"
        ),
        risk_notes=[
            "该结果由演示数据生成，不能作为真实交易依据" if snapshot.is_demo else "需结合最新公告和成交状态复核",
            "T日收盘信号仅从下一交易日起有效",
            "金额可能因组合现金和行业暴露被进一步压缩",
            "代理多空比与研究阈值当前处于待回测状态",
        ],
        reasoning=[
            f"综合评分 {score:.1f}",
            f"市场风险分 {market_risk:.1f}",
            f"所属方向：{industry_name or '宽基/跨资产'}",
        ],
        score_components=components,
        source_timestamp=snapshot.source_timestamp,
        strategy_version=get_settings().strategy_version,
        is_demo=snapshot.is_demo,
    )


def _clear_analysis_date(db: Session, trade_date: date) -> None:
    recommendation_ids = select(Recommendation.id).where(Recommendation.trade_date == trade_date)
    db.execute(
        delete(RecommendationSnapshot).where(
            RecommendationSnapshot.recommendation_id.in_(recommendation_ids)
        )
    )
    db.execute(delete(Recommendation).where(Recommendation.trade_date == trade_date))
    db.execute(delete(IndustryScore).where(IndustryScore.trade_date == trade_date))
    db.execute(delete(InstrumentScore).where(InstrumentScore.trade_date == trade_date))
    db.execute(delete(MarketRegime).where(MarketRegime.trade_date == trade_date))
    db.execute(delete(DailyReport).where(DailyReport.report_date == trade_date))
    db.flush()


def run_analysis(
    db: Session,
    trade_date: date | None = None,
    provider: MockDataProvider | None = None,
) -> dict[str, object]:
    provider = provider or MockDataProvider()
    snapshot = provider.get_snapshot(trade_date)
    _clear_analysis_date(db, snapshot.trade_date)

    config = settings_payload(db)
    portfolio = ensure_default_portfolio(db)
    portfolio_risk = calculate_portfolio_risk(portfolio)
    regime = market_regime(snapshot.market)
    db.add(
        MarketRegime(
            trade_date=snapshot.trade_date,
            regime=str(regime["regime"]),
            risk_score=float(regime["risk_score"]),
            equity_min=float(regime["equity_min"]),
            equity_max=float(regime["equity_max"]),
            reasons=list(regime["reasons"]),
            source_timestamp=snapshot.source_timestamp,
            is_demo=snapshot.is_demo,
        )
    )

    industry_results = score_industries(snapshot.industries)
    threshold = float(config.get("industry_score_threshold", 62))
    selection_count = min(5, max(3, int(config.get("selected_industry_count", 5))))
    selected_codes = {
        str(item["code"])
        for item in industry_results
        if float(item["score"]) >= threshold
    }
    ordered_selected_codes = [
        str(item["code"])
        for item in industry_results
        if str(item["code"]) in selected_codes
    ][:selection_count]
    selected_codes = set(ordered_selected_codes)
    industry_by_code = {str(item["code"]): item for item in industry_results}
    stock_by_industry = {stock.industry_code: stock for stock in snapshot.stocks}

    for item in industry_results:
        candidate = stock_by_industry.get(str(item["code"])) if str(item["code"]) in selected_codes else None
        db.add(
            IndustryScore(
                trade_date=snapshot.trade_date,
                industry_code=str(item["code"]),
                industry_name=str(item["name"]),
                score=float(item["score"]),
                rank=int(item["rank"]),
                state=str(item["state"]),
                metrics=dict(item["components"]),
                is_selected=str(item["code"]) in selected_codes,
                candidate_code=candidate.code if candidate else None,
                candidate_name=candidate.name if candidate else None,
                source_timestamp=snapshot.source_timestamp,
            )
        )

    recommendations: list[Recommendation] = []
    remaining_cash = portfolio.cash
    planned_exposure = dict(portfolio_risk.industry_exposure)
    total_equity_cap = min(float(regime["equity_max"]), float(config.get("total_equity_cap", 0.75)))
    remaining_equity_capacity = max(
        0.0,
        portfolio_risk.total_value * total_equity_cap - portfolio_risk.invested_value,
    )
    remaining_stock_capacity = max(
        0.0,
        portfolio_risk.total_value * float(config.get("stock_total_cap", 0.30)) - portfolio_risk.stock_value,
    )
    remaining_etf_capacity = max(
        0.0,
        portfolio_risk.total_value * float(config.get("etf_total_cap", 0.80)) - portfolio_risk.etf_value,
    )

    for industry_item in industry_results:
        industry_code = str(industry_item["code"])
        if industry_code not in selected_codes:
            continue
        stock = stock_by_industry.get(industry_code)
        if stock is None:
            continue
        passed, filter_reasons = _passes_stock_filters(stock, config)
        stock_score, components = score_stock(stock, float(industry_item["score"]))
        db.add(
            InstrumentScore(
                trade_date=snapshot.trade_date,
                instrument_code=stock.code,
                score=stock_score,
                components=components,
                passed_filters=passed,
                filter_reasons=filter_reasons,
            )
        )
        if not passed:
            continue
        current_exposure = planned_exposure.get(str(industry_item["name"]), 0.0)
        capacity = min(
            remaining_industry_capacity(
                portfolio_risk.total_value,
                current_exposure,
                float(config.get("industry_exposure_cap", 0.30)),
            ),
            remaining_equity_capacity,
            remaining_stock_capacity,
        )
        recommendation = _build_recommendation(
            snapshot=snapshot,
            instrument=stock,
            score=stock_score,
            components=components,
            industry_code=industry_code,
            industry_name=str(industry_item["name"]),
            portfolio_total=portfolio_risk.total_value,
            portfolio_drawdown=portfolio_risk.drawdown,
            market_risk=float(regime["risk_score"]),
            available_cash=remaining_cash,
            industry_capacity=capacity,
            config=config,
            allow_buy=str(regime["regime"]) in {"反弹", "趋势", "强攻"},
        )
        recommendations.append(recommendation)
        if recommendation.action == "BUY":
            remaining_cash -= recommendation.suggested_amount
            remaining_equity_capacity -= recommendation.suggested_amount
            remaining_stock_capacity -= recommendation.suggested_amount
            planned_exposure[str(industry_item["name"])] = current_exposure + recommendation.suggested_amount

    scored_etfs: list[tuple[InstrumentMetrics, float, dict[str, float]]] = []
    for etf in snapshot.etfs:
        etf_score, components = score_etf(etf)
        scored_etfs.append((etf, etf_score, components))
        db.add(
            InstrumentScore(
                trade_date=snapshot.trade_date,
                instrument_code=etf.code,
                score=etf_score,
                components=components,
                passed_filters=True,
                filter_reasons=[],
            )
        )
    scored_etfs.sort(key=lambda item: item[1], reverse=True)
    focus_codes = set(str(code) for code in config.get("focus_etfs", ["588000", "512010"]))
    chosen_etfs: list[tuple[InstrumentMetrics, float, dict[str, float]]] = []
    for item in scored_etfs:
        if item[0].code in focus_codes or len(chosen_etfs) < 4:
            chosen_etfs.append(item)
        if len(chosen_etfs) >= 5 and focus_codes.issubset({row[0].code for row in chosen_etfs}):
            break

    for etf, etf_score, components in chosen_etfs:
        exposure_name = etf.industry_name or "ETF"
        current_exposure = planned_exposure.get(exposure_name, 0.0)
        capacity = min(
            remaining_industry_capacity(
                portfolio_risk.total_value,
                current_exposure,
                float(config.get("industry_exposure_cap", 0.30)),
            ),
            remaining_equity_capacity,
            remaining_etf_capacity,
        )
        recommendation = _build_recommendation(
            snapshot=snapshot,
            instrument=etf,
            score=etf_score,
            components=components,
            industry_code=None,
            industry_name=exposure_name,
            portfolio_total=portfolio_risk.total_value,
            portfolio_drawdown=portfolio_risk.drawdown,
            market_risk=float(regime["risk_score"]),
            available_cash=remaining_cash,
            industry_capacity=capacity,
            config=config,
            allow_buy=str(regime["regime"]) in {"磨底", "反弹", "回踩", "趋势", "强攻"},
        )
        recommendations.append(recommendation)
        if recommendation.action == "BUY":
            remaining_cash -= recommendation.suggested_amount
            remaining_equity_capacity -= recommendation.suggested_amount
            remaining_etf_capacity -= recommendation.suggested_amount
            planned_exposure[exposure_name] = current_exposure + recommendation.suggested_amount

    db.add_all(recommendations)
    db.flush()
    for recommendation in recommendations:
        db.add(RecommendationSnapshot(recommendation_id=recommendation.id, payload=_recommendation_payload(recommendation)))

    selected_industries = [item for item in industry_results if str(item["code"]) in selected_codes]
    cash_recommended = str(regime["regime"]) == "冰封" or portfolio_risk.drawdown >= 0.12
    report_content = {
        "report_date": snapshot.trade_date.isoformat(),
        "valid_from": snapshot.next_trade_date.isoformat(),
        "is_demo": snapshot.is_demo,
        "data_source": snapshot.source_name,
        "data_completeness": snapshot.completeness,
        "market": regime,
        "portfolio": {
            "total_value": portfolio_risk.total_value,
            "invested_value": portfolio_risk.invested_value,
            "cash": portfolio.cash,
            "drawdown": portfolio_risk.drawdown,
        },
        "selected_industries": selected_industries,
        "recommendations": [_recommendation_payload(item) for item in recommendations],
        "suggested_equity_range": [regime["equity_min"], regime["equity_max"]],
        "cash_recommended": cash_recommended,
        "medium_term_view": {
            "强攻": "趋势扩张",
            "趋势": "温和上升",
            "回踩": "上升趋势中的风险收缩",
            "反弹": "低位修复，等待趋势确认",
            "磨底": "底部震荡",
            "冰封": "防守与现金优先",
        }[str(regime["regime"])],
        "update_schedule": {
            "time": str(config.get("daily_update_time", "18:30")),
            "timezone": str(config.get("daily_update_timezone", "Asia/Shanghai")),
            "trading_days_only": True,
        },
        "changes": ["MVP首次分析，无前一交易日可比记录"],
        "risk_notice": "演示数据仅用于验证系统功能，不构成投资建议。",
        "strategy_version": get_settings().strategy_version,
    }
    db.add(
        DailyReport(
            report_date=snapshot.trade_date,
            content=report_content,
            source_timestamp=snapshot.source_timestamp,
            strategy_version=get_settings().strategy_version,
            is_demo=snapshot.is_demo,
        )
    )

    provider_status = provider.status()
    status_row = db.scalar(select(DataSourceStatus).where(DataSourceStatus.provider == provider.name))
    if status_row is None:
        status_row = DataSourceStatus(provider=provider.name, status="ok", message="", is_demo=True)
        db.add(status_row)
    status_row.status = str(provider_status["status"])
    status_row.is_demo = bool(provider_status["is_demo"])
    status_row.completeness = float(provider_status["completeness"])
    status_row.message = str(provider_status["message"])
    status_row.last_updated = snapshot.source_timestamp
    db.commit()
    return report_content


def latest_report(db: Session) -> DailyReport | None:
    return db.scalar(select(DailyReport).order_by(DailyReport.report_date.desc()))


