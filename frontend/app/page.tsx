"use client";

import { useCallback, useEffect, useState } from "react";
import { IndustryChart } from "@/components/IndustryChart";
import { actionLabel, apiGet, apiSend, Dashboard, money, pct, Recommendation } from "@/lib/api";

function ActionTag({ item }: { item: Recommendation }) {
  const className = item.action === "BUY" ? "tag tag-buy" : item.action === "WATCH" ? "tag tag-watch" : "tag tag-neutral";
  return <span className={className}>{actionLabel[item.action] ?? item.action}</span>;
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const load = useCallback(() => {
    setError("");
    apiGet<Dashboard>("/api/dashboard").then(setData).catch((err: Error) => setError(err.message));
  }, []);
  useEffect(load, [load]);

  async function rerun() {
    setRunning(true); setError("");
    try { await apiSend("/api/analysis/run", "POST", {}); load(); }
    catch (err) { setError(err instanceof Error ? err.message : "分析失败"); }
    finally { setRunning(false); }
  }

  if (error) return <><div className="page-head"><div><div className="eyebrow">SYSTEM STATUS</div><h1>无法读取分析结果</h1></div></div><div className="error">{error}<br/>请确认后端已在 http://localhost:8000 启动。</div></>;
  if (!data) return <div className="loading">正在读取盘后分析…</div>;
  const buys = data.recommendations.filter((item) => item.action === "BUY");

  return (
    <>
      <header className="page-head">
        <div>
          <div className="eyebrow">DAILY DECISION BRIEF · {data.analysis_date}</div>
          <h1>今日盘后决策台</h1>
          <div className="subtitle">从市场环境到行业与标的，所有结论均经过组合风险约束。只有条件满足时，建议才从下一交易日起生效。</div>
        </div>
        <div><span className="demo-pill">演示数据 · 非真实行情</span> <button className="button secondary" onClick={rerun} disabled={running}>{running ? "分析中…" : "重新分析"}</button></div>
      </header>

      <section className="grid grid-4">
        <div className="card"><div className="card-label">市场状态</div><div className="metric"><span className="state-dot" />{data.market.regime}</div><div className="metric-note">风险分 {data.market.risk_score.toFixed(1)} / 100</div><div className="risk-track"><div className="risk-fill" style={{ width: `${data.market.risk_score}%` }} /></div></div>
        <div className="card"><div className="card-label">账户总资产</div><div className="metric">{money(data.portfolio.total_value)}</div><div className="metric-note">现金 {money(data.portfolio.cash)} · 仓位 {pct(data.portfolio.position_ratio)}</div></div>
        <div className="card"><div className="card-label">建议权益仓位</div><div className="metric">{pct(data.market.equity_min)}—{pct(data.market.equity_max)}</div><div className="metric-note">组合回撤 {pct(data.portfolio.drawdown)}</div></div>
        <div className="card"><div className="card-label">明日可执行机会</div><div className="metric">{buys.length}<span style={{ fontSize: 14, marginLeft: 5 }}>项</span></div><div className="metric-note">未触发条件时保持现金，不强制交易</div></div>
      </section>

      <section className="grid grid-2 section">
        <div className="card">
          <div className="section-head"><h2>重点行业</h2><span>申万一级 · 横截面评分</span></div>
          <IndustryChart industries={data.industries} />
        </div>
        <div className="card">
          <div className="section-head"><h2>次日操作清单</h2><span>{data.recommendations.length} 项候选</span></div>
          {data.recommendations.slice(0, 6).map((item) => (
            <div className="recommendation" key={item.id}>
              <div><h3>{item.instrument_name} <span className="code">{item.instrument_code}</span> <ActionTag item={item} /></h3><p>{item.entry_condition}</p><p>失效：{item.invalidation_condition}</p></div>
              <div className="amount"><strong>{item.suggested_amount ? money(item.suggested_amount) : "—"}</strong><span>评分 {item.score.toFixed(1)}</span></div>
            </div>
          ))}
        </div>
      </section>

      <section className="card section">
        <div className="section-head"><h2>市场判断依据</h2><span>数据完整度 {(data.data_status.completeness * 100).toFixed(0)}%</span></div>
        <div className="grid grid-4">{data.market.reasons.map((reason) => <div key={reason}><div className="card-label">观测项</div><strong>{reason}</strong></div>)}</div>
        <div className="notice" style={{ marginTop: 18 }}>{data.data_status.message} 数据更新时间：{new Date(data.data_status.last_updated).toLocaleString("zh-CN")}</div>
      </section>
    </>
  );
}

