"use client";

import { useEffect, useState } from "react";
import { Dashboard, apiGet, pct } from "@/lib/api";
import { MarketStateBand } from "@/components/MarketStateBand";

const evidenceLabels: Array<[keyof Dashboard["market"], string, string]> = [
  ["proxy_ratio", "代理多空比", "市场内部多空结构的公开代理"],
  ["proxy_rate", "变化速率", "大于1表示较前一日修复"],
  ["proxy_slope_3d", "三日斜率", "短期结构变化方向"],
  ["proxy_percentile", "历史分位", "滚动历史中的相对位置"],
  ["trend_bull_count", "趋势多头", "稳定趋势股票的标准化强度"],
  ["broad_selloff_pressure", "普遍杀跌压力", "越高代表全市场压力越大"],
  ["deep_bear_count", "深度弱势", "长期弱势股票的标准化数量"],
  ["wave_continuity", "波段连续性", "趋势、广度与新高扩散的组合"],
];

export default function MarketPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    apiGet<Dashboard>("/api/dashboard").then(setData).catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="loading">正在读取市场环境…</div>;

  const schedule = data.online_api?.schedule_label ?? "交易日 18:30（北京时间）";
  return (
    <>
      <header className="page-head">
        <div>
          <div className="context-line">市场环境 · {data.analysis_date}</div>
          <h1>先判断能不能做，再判断做什么</h1>
          <div className="subtitle">六状态是所有行业、ETF和个股建议的上层闸门。风险降级立即生效，升级需要连续确认。</div>
        </div>
        <span className="demo-pill">{data.market.model_status} · 代理模型</span>
      </header>

      <section className="market-hero">
        <div className="market-hero-copy">
          <span>当前状态</span>
          <strong>{data.market.regime}</strong>
          <p>{data.market.proxy_notice}</p>
        </div>
        <div className="market-hero-band">
          <MarketStateBand current={data.market.regime} />
          <div className="market-hero-meta">
            <span>允许仓位 {pct(data.market.equity_min)}—{pct(data.market.equity_max)}</span>
            <span>风险分 {data.market.risk_score.toFixed(1)}</span>
            <span>每日更新 {schedule}</span>
          </div>
        </div>
      </section>

      <section className="evidence-grid section">
        {evidenceLabels.map(([key, label, note]) => {
          const value = data.market[key];
          return (
            <article className="evidence-cell" key={String(key)}>
              <span>{label}</span>
              <strong>{typeof value === "number" ? value.toFixed(key === "proxy_slope_3d" ? 3 : 2) : String(value)}</strong>
              <p>{note}</p>
            </article>
          );
        })}
      </section>

      <section className="grid grid-2 section">
        <article className="panel">
          <div className="section-head"><h2>研究级信号</h2><span>不直接覆盖正式仓位</span></div>
          <div className="signal-list">
            {data.market.research_signals.map((signal) => <div key={signal}><span className="signal-marker" />{signal}</div>)}
          </div>
          {data.market.divergence && <div className="notice">指数与内部广度出现背离，系统暂停激进加仓并提高风险等级。</div>}
        </article>
        <article className="panel">
          <div className="section-head"><h2>在线数据状态</h2><span>{data.online_api?.status === "online" ? "在线" : data.data_status.status}</span></div>
          <dl className="status-list">
            <div><dt>模式</dt><dd>{data.online_api?.mode === "read_only_snapshot" ? "只读快照 API" : "本地 FastAPI"}</dd></div>
            <div><dt>上次生成</dt><dd>{new Date(data.online_api?.generated_at ?? data.data_status.last_updated).toLocaleString("zh-CN")}</dd></div>
            <div><dt>下次更新</dt><dd>{data.online_api?.next_update_at ? new Date(data.online_api.next_update_at).toLocaleString("zh-CN") : schedule}</dd></div>
          </dl>
          {data.online_api?.health_url && <a className="api-link" href={data.online_api.health_url} target="_blank" rel="noreferrer">打开健康检查 JSON</a>}
        </article>
      </section>
    </>
  );
}
