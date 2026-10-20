"""Export the running demo API into static JSON files for GitHub Pages."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "frontend" / "public" / "data"
API_BASE = "http://127.0.0.1:8000"


def request_json(path: str, *, method: str = "GET", payload: dict | None = None) -> object:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def write_json(name: str, value: object) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main() -> None:
    endpoints = {
        "dashboard.json": "/api/dashboard",
        "industries.json": "/api/industries/rankings",
        "recommendations.json": "/api/recommendations",
        "portfolio.json": "/api/portfolio",
        "reports.json": "/api/reports/daily",
        "settings.json": "/api/settings",
    }
    for filename, endpoint in endpoints.items():
        write_json(filename, request_json(endpoint))

    reports = request_json("/api/reports/daily")
    for item in reports["items"]:
        report_date = item["report_date"]
        write_json(
            f"report-{report_date}.json",
            request_json(f"/api/reports/daily/{report_date}"),
        )

    write_json(
        "backtest.json",
        request_json(
            "/api/backtests",
            method="POST",
            payload={
                "name": "Mock策略管线验证",
                "initial_capital": 150000,
                "trading_days": 120,
                "fee_rate": 0.0003,
                "slippage_rate": 0.0005,
            },
        ),
    )


if __name__ == "__main__":
    main()
