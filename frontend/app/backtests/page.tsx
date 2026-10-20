"use client";

import * as echarts from "echarts";
import { useEffect, useRef, useState } from "react";
import { apiSend, money, pct } from "@/lib/api";

type Result = { id: number; metrics: Record<string, number | string>; equity_curve: Array<{ date: string; value: number; drawdown: number }>; is_demo: boolean };

function EquityChart({ result }: { result: Result }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (!ref.current) return; const chart = echarts.init(ref.current); chart.setOption({ grid: { left: 48, right: 15, top: 18, bottom: 35 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: result.equity_curve.map((x) => x.date), axisLabel: { show: false } }, yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: "#edf1ef" } } }, series: [{ type: "line", symbol: "none", smooth: true, data: result.equity_curve.map((x) => x.value), lineStyle: { width: 3, color: "#0f766e" }, areaStyle: { color: "rgba(15,118,110,.12)" } }] }); const resize = () => chart.resize(); window.addEventListener("resize", resize); return () => { window.removeEventListener("resize", resize); chart.dispose(); }; }, [result]);
  return <div ref={ref} style={{ height: 330 }} />;
}

export default function BacktestsPage() {
  const [result, setResult] = useState<Result | null>(null); const [running, setRunning] = useState(false); const [error, setError] = useState("");
  async function run() { setRunning(true); setError(""); try { setResult(await apiSend<Result>("/api/backtests", "POST", { name: "Mock策略管线验证", initial_capital: 150000, trading_days: 120, fee_rate: .0003, slippage_rate: .0005 })); } catch (err) { setError(err instanceof Error ? err.message : "回测失败"); } finally { setRunning(false); } }
  return <><header className="page-head"><div><div className="eyebrow">BACKTEST LAB</div><h1>策略回测</h1><div className="subtitle">当前仅提供合成数据管线验证，用来检查T+1执行、成本和指标计算。它不证明策略有效。</div></div><button className="button" onClick={run} disabled={running}>{running ? "运行中…" : "运行演示回测"}</button></header>{error && <div className="error">{error}</div>}{!result ? <div className="card empty">点击“运行演示回测”检查完整回测管线。</div> : <><div className="notice">{String(result.metrics.notice)}</div><section className="grid grid-4 section"><div className="card"><div className="card-label">期末资产</div><div className="metric">{money(Number(result.metrics.ending_capital))}</div></div><div className="card"><div className="card-label">年化收益</div><div className="metric">{pct(Number(result.metrics.annual_return))}</div></div><div className="card"><div className="card-label">最大回撤</div><div className="metric">{pct(Number(result.metrics.max_drawdown))}</div></div><div className="card"><div className="card-label">Sharpe / Calmar</div><div className="metric">{Number(result.metrics.sharpe).toFixed(2)} / {Number(result.metrics.calmar).toFixed(2)}</div></div></section><div className="card section"><div className="section-head"><h2>演示净值曲线</h2><span>{String(result.metrics.trade_count)} 次调仓</span></div><EquityChart result={result} /></div></>}</>;
}

