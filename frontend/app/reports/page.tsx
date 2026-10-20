"use client";

import { useEffect, useState } from "react";
import { actionLabel, apiGet, money, Recommendation } from "@/lib/api";

type Report = { report_date: string; content: { market: { regime: string; risk_score: number; reasons: string[] }; recommendations: Recommendation[]; selected_industries: Array<{ name: string; score: number; state: string }>; medium_term_view: string; suggested_equity_range: number[]; risk_notice: string }; source_timestamp: string; is_demo: boolean };

export default function ReportsPage() {
  const [dates, setDates] = useState<string[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { apiGet<{ items: Array<{ report_date: string }> }>("/api/reports/daily").then(async (data) => { const list = data.items.map((item) => item.report_date); setDates(list); if (list[0]) setReport(await apiGet<Report>(`/api/reports/daily/${list[0]}`)); }).catch((err: Error) => setError(err.message)); }, []);
  async function choose(value: string) { setReport(await apiGet<Report>(`/api/reports/daily/${value}`)); }
  return <>
    <header className="page-head"><div><div className="eyebrow">DAILY RESEARCH ARCHIVE</div><h1>盘后报告</h1><div className="subtitle">报告保存当时的数据与策略版本，方便复核，而不是事后改写结论。</div></div><select className="input" style={{ width: 160 }} onChange={(e) => choose(e.target.value)}>{dates.map((date) => <option key={date}>{date}</option>)}</select></header>
    {error && <div className="error">{error}</div>}{report && <>
      <section className="grid grid-3"><div className="card"><div className="card-label">市场状态</div><div className="metric">{report.content.market.regime}</div><div className="metric-note">风险分 {report.content.market.risk_score.toFixed(1)}</div></div><div className="card"><div className="card-label">20日趋势</div><div className="metric">{report.content.medium_term_view}</div></div><div className="card"><div className="card-label">建议仓位</div><div className="metric">{(report.content.suggested_equity_range[0] * 100).toFixed(0)}%—{(report.content.suggested_equity_range[1] * 100).toFixed(0)}%</div></div></section>
      <section className="grid grid-2 section"><div className="card"><div className="section-head"><h2>重点行业</h2><span>{report.content.selected_industries.length} 个</span></div>{report.content.selected_industries.map((item, index) => <div className="recommendation" key={item.name}><div><h3>{index + 1}. {item.name}</h3><p>{item.state}</p></div><div className="amount"><strong>{item.score.toFixed(1)}</strong><span>综合评分</span></div></div>)}</div><div className="card"><div className="section-head"><h2>条件式建议</h2><span>{report.content.recommendations.length} 项</span></div>{report.content.recommendations.slice(0, 7).map((item) => <div className="recommendation" key={item.id}><div><h3>{item.instrument_name} <span className="tag tag-neutral">{actionLabel[item.action]}</span></h3><p>{item.entry_condition}</p></div><div className="amount"><strong>{item.suggested_amount ? money(item.suggested_amount) : "—"}</strong><span>{item.score.toFixed(1)}分</span></div></div>)}</div></section>
      <div className="notice section">{report.content.risk_notice} · 生成时间 {new Date(report.source_timestamp).toLocaleString("zh-CN")}</div>
    </>}
  </>;
}

