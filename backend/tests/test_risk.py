from app.services.risk import calculate_max_amount, cap_recommendation, drawdown_equity_cap


def test_stock_and_etf_caps() -> None:
    assert calculate_max_amount("stock", 200000, 0, risk_score=20) == 15000
    assert calculate_max_amount("stock", 100000, 0, risk_score=20) == 8000
    assert calculate_max_amount("etf", 200000, 0, risk_score=20) == 30000
    assert calculate_max_amount("etf", 100000, 0, risk_score=20) == 20000


def test_board_risk_reduces_stock_cap() -> None:
    main_board = calculate_max_amount("stock", 200000, 0, board="主板", risk_score=20)
    bse = calculate_max_amount("stock", 200000, 0, board="北交所", risk_score=20)
    assert bse < main_board


def test_drawdown_overrides_signal() -> None:
    assert drawdown_equity_cap(0.15) == 0
    assert calculate_max_amount("stock", 200000, 0.15, risk_score=10) == 0


def test_recommendation_never_exceeds_cash_or_industry_capacity() -> None:
    assert cap_recommendation(12000, 15000, 5000, 3000) == 3000

