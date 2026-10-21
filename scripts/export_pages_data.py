"""Export FastAPI responses as an always-available GitHub Pages snapshot API."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_OUTPUT = ROOT / "frontend" / "public" / "data"
API_OUTPUT = ROOT / "frontend" / "public" / "api"
API_BASE = "http://127.0.0.1:8000"
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")


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


def write_json(directory: Path, name: str, value: object) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def write_snapshot(name: str, value: object) -> None:
    write_json(DATA_OUTPUT, name, value)
    write_json(API_OUTPUT, name, value)


def next_update(now: datetime) -> datetime:
    candidate = now.replace(hour=18, minute=30, second=0, microsecond=0)
    if now >= candidate:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def main() -> None:
    now = datetime.now(SHANGHAI)
    generated_at = now.isoformat()
    next_update_at = next_update(now).isoformat()
    public_base = os.getenv("PUBLIC_API_BASE", "/api")
    # Always refresh the current trade-date snapshot before exporting. The
    # provider decides whether the date represents live, delayed, or demo data.
    request_json("/api/analysis/run", method="POST", payload={})
    endpoints = {
        "dashboard.json": "/api/dashboard",
        "industries.json": "/api/industries/rankings",
        "recommendations.json": "/api/recommendations",
        "portfolio.json": "/api/portfolio",
        "reports.json": "/api/reports/daily",
        "settings.json": "/api/settings",
    }
    snapshots: dict[str, object] = {}
    for filename, endpoint in endpoints.items():
        snapshots[filename] = request_json(endpoint)

    dashboard = dict(snapshots["dashboard.json"])
    dashboard["online_api"] = {
        "status": "online",
        "mode": "read_only_snapshot",
        "base_url": public_base,
        "health_url": f"{public_base}/health.json",
        "generated_at": generated_at,
        "next_update_at": next_update_at,
        "schedule_label": "交易日 18:30（北京时间）",
    }
    snapshots["dashboard.json"] = dashboard
    for filename, value in snapshots.items():
        write_snapshot(filename, value)

    reports = snapshots["reports.json"]
    for item in reports["items"]:
        report_date = item["report_date"]
        write_snapshot(
            f"report-{report_date}.json",
            request_json(f"/api/reports/daily/{report_date}"),
        )

    write_snapshot(
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
    health = dict(request_json("/api/health"))
    health.update(
        {
            "status": "online",
            "mode": "read_only_snapshot",
            "generated_at": generated_at,
            "next_update_at": next_update_at,
            "public_api_base": public_base,
        }
    )
    write_snapshot("health.json", health)
    write_snapshot(
        "manifest.json",
        {
            "name": "股市专家公开快照 API",
            "status": "online",
            "mode": "read_only_snapshot",
            "generated_at": generated_at,
            "next_update_at": next_update_at,
            "schedule": "30 10 * * 1-5",
            "timezone": "Asia/Shanghai",
            "endpoints": sorted(["health.json", "manifest.json", *snapshots.keys(), "backtest.json"]),
            "notice": "当前为演示数据快照；真实行情提供者接入并验证前不得作为交易依据。",
        },
    )


if __name__ == "__main__":
    main()
