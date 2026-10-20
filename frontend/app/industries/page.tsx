"use client";

import { useEffect, useState } from "react";
import { apiGet, Industry } from "@/lib/api";

export default function IndustriesPage() {
  const [items, setItems] = useState<Industry[]>([]);
  const [date, setDate] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { apiGet<{ trade_date: string; items: Industry[] }>("/api/industries/rankings").then((data) => { setItems(data.items); setDate(data.trade_date); }).catch((err: Error) => setError(err.message)); }, []);
  return <>
    <header className="page-head"><div><div className="eyebrow">SHENWAN INDUSTRY MAP · {date}</div><h1>行业强弱地图</h1><div className="subtitle">覆盖31个申万一级行业。原始指标先转为当日横截面百分位，再合成综合评分。</div></div><span className="demo-pill">演示数据</span></header>
    {error ? <div className="error">{error}</div> : <div className="card table-wrap"><table><thead><tr><th>排名</th><th>行业</th><th>综合分</th><th>状态</th><th>候选股票</th><th>相对强度</th><th>趋势</th><th>市场宽度</th></tr></thead><tbody>{items.map((item) => <tr key={item.industry_code}><td className="rank">{item.rank}</td><td><strong>{item.industry_name}</strong><div className="code">{item.industry_code}</div></td><td><span className="score">{item.score.toFixed(1)}</span><div className="bar" style={{ width: 110, marginTop: 6 }}><span style={{ width: `${item.score}%` }} /></div></td><td><span className={item.state.includes("强") ? "tag tag-buy" : item.state.includes("风险") || item.state === "转弱" ? "tag tag-risk" : "tag tag-neutral"}>{item.state}</span></td><td>{item.candidate_name ? <><strong>{item.candidate_name}</strong><div className="code">{item.candidate_code}</div></> : "—"}</td><td>{item.metrics.relative_strength?.toFixed(1)}</td><td>{item.metrics.trend?.toFixed(1)}</td><td>{item.metrics.breadth?.toFixed(1)}</td></tr>)}</tbody></table></div>}
  </>;
}

