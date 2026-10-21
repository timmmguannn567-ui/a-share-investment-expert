"use client";

import { useCallback, useEffect, useState } from "react";
import { IndustryChart } from "@/components/IndustryChart";
import { MarketStateBand } from "@/components/MarketStateBand";
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

  if (error) return <><div className="page-head"><div><div className="context-line">连接状态</div><h1>无法读取分析结果</h1></div></div><div className="error">{error}<br/>请检查在线快照 API，或在本地启动 FastAPI。</div></>;
  if (!data) return <div className="loading">正在读取盘后分析…</div>;
  const buys = data.recommendations.filter((item) => item.action === "BUY");
  const schedule = data.online_api?.schedule_label ?? "交易日 18:30（北京时间）";

  return (
    <>
      <header className="page-head">
        <div>
          <div className="context-line">盘后决策 · {data.analysis_date}</div>
          <h1>先看环境，再做交易</h1>
          <div className="subtitle">市场状态决定仓位，行业强度决定方向，触发与失效条件决定执行。没有合格机会时，现金也是正式答案。</div>
        </div>
        <div className="head-actions"><span className="online-pill"><i />快照 API 在线</span><span className="demo-pill">演示数据 · 非真实行情</span><button className="button secondary" onClick={rerun} disabled={running}>{running ? "分析中…" : "重新分析"}</button></div>
      </header>

      <section className="decision-console">
        <div className="decision-state">
          <span>当前市场状态</span>
          <strong>{data.market.regime}</strong>
          <p>风险分 {data.market.risk_score.toFixed(1)} · {data.market.model_status}</p>
        </div>
        <div className="decision-band">
          <MarketStateBand current={data.market.regime} />
          <div className="decision-band-foot"><span>代理多空比 <b>{data.market.proxy_ratio.toFixed(2)}</b></span><span>速率 <b>{data.market.proxy_rate.toFixed(2)}</b></span><span>历史分位 <b>{data.market.proxy_percentile.toFixed(1)}%</b></span></div>
        </div>
        <div className="decision-allocation">
          <span>允许权益仓位</span>
          <strong>{pct(data.market.equity_min)}—{pct(data.market.equity_max)}</strong>
          <p>当前仓位 {pct(data.portfolio.position_ratio)}</p>
        </div>
      </section>

      <section className="summary-strip">
        <div><span>账户总资产</span><strong>{money(data.portfolio.total_value)}</strong><small>现金 {money(data.portfolio.cash)}</small></div>
        <div><span>组合回撤</span><strong>{pct(data.portfolio.drawdown)}</strong><small>10%开始主动降仓</small></div>
        <div><span>明日可执行</span><strong>{buys.length} 项</strong><small>未触发则不交易</small></div>
        <div><span>每日更新时间</span><strong>18:30</strong><small>{schedule}</small></div>
      </section>

      <section className="grid grid-2 section">
        <div className="panel">
          <div className="section-head"><h2>重点行业</h2><span>申万一级 · 横截面评分</span></div>
          <IndustryChart industries={data.industries} />
        </div>
        <div className="panel">
          <div className="section-head"><h2>次日操作清单</h2><span>{data.recommendations.length} 项候选</span></div>
          {data.recommendations.slice(0, 6).map((item) => (
            <div className="recommendation" key={item.id}>
              <div><h3>{item.instrument_name} <span className="code">{item.instrument_code}</span> <ActionTag item={item} /></h3><p>{item.entry_condition}</p><p>失效：{item.invalidation_condition}</p></div>
              <div className="amount"><strong>{item.suggested_amount ? money(item.suggested_amount) : "—"}</strong><span>评分 {item.score.toFixed(1)}</span></div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel section">
        <div className="section-head"><h2>市场判断证据</h2><span>完整度 {(data.data_status.completeness * 100).toFixed(0)}%</span></div>
        <div className="evidence-row">{data.market.reasons.map((reason) => <div key={reason}><span className="signal-marker" /><strong>{reason}</strong></div>)}</div>
        <div className="notice" style={{ marginTop: 18 }}>{data.market.proxy_notice}。{data.data_status.message} 上次生成：{new Date(data.online_api?.generated_at ?? data.data_status.last_updated).toLocaleString("zh-CN")}。</div>
      </section>
    </>
  );
}

