from app.providers.mock import MockDataProvider, SHENWAN_INDUSTRIES
from app.services.scoring import market_regime, percentile_ranks, score_industries, weighted_score


def test_percentile_ranks_are_cross_sectional() -> None:
    assert percentile_ranks([10, 20, 30]) == [0.0, 50.0, 100.0]
    assert percentile_ranks([5, 5]) == [50.0, 50.0]


def test_weighted_score_rejects_missing_component() -> None:
    try:
        weighted_score({"a": 80}, {"a": 0.5, "b": 0.5})
    except ValueError as exc:
        assert "b" in str(exc)
    else:
        raise AssertionError("missing score component must be rejected")


def test_mock_provider_has_all_shenwan_level_one_industries() -> None:
    snapshot = MockDataProvider().get_snapshot()
    assert len(snapshot.industries) == len(SHENWAN_INDUSTRIES) == 31
    results = score_industries(snapshot.industries)
    assert [item["rank"] for item in results] == list(range(1, 32))
    assert results[0]["score"] >= results[-1]["score"]


def test_market_regime_returns_valid_equity_range() -> None:
    snapshot = MockDataProvider().get_snapshot()
    result = market_regime(snapshot.market)
    assert 0 <= result["risk_score"] <= 100
    assert 0 <= result["equity_min"] <= result["equity_max"] <= 1
    assert result["regime"] in {"强攻", "趋势", "回踩", "反弹", "磨底", "冰封"}
    assert result["proxy_notice"]
    assert 0 <= result["proxy_percentile"] <= 100

