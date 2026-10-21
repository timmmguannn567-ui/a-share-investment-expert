"use client";

import { useEffect, useState } from "react";
import { apiGet, Industry } from "@/lib/api";

export default function IndustriesPage() {
  const [items, setItems] = useState<Industry[]>([]);
  const [date, setDate] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { apiGet<{ trade_date: string; items: Industry[] }>("/api/industries/rankings").then((data) => { setItems(data.items); setDate(data.trade_date); }).catch((err: Error) => setError(err.message)); }, []);
  return <>
    <header className="page-head"><div><div className="context-line">申万行业地图 · {date}</div><h1>寻找最小阻力方向</h1><div className="subtitle">覆盖31个申万一级行业。只有排名、广度、趋势和拥挤度同时合格的行业，才会进入可交易名单。</div></div><span className="demo-pill">前5名可交易候选</span></header>
    {error ? <div className="error">{error}</div> : <div className="panel table-wrap"><table><thead><tr><th>排名</th><th>行业</th><th>综合分</th><th>状态</th><th>行业样本股</th><th>相对强度</th><th>趋势质量</th><th>行业广度</th></tr></thead><tbody>{items.map((item) => <tr key={item.industry_code}><td className="rank">{item.rank}</td><td><strong>{item.industry_name}</strong><div className="code">{item.industry_code}</div></td><td><span className="score">{item.score.toFixed(1)}</span><div className="bar" style={{ width: 110, marginTop: 6 }}><span style={{ width: `${item.score}%` }} /></div></td><td><span className={item.state === "领涨扩散" ? "tag tag-buy" : ["走弱", "过热"].includes(item.state) ? "tag tag-risk" : "tag tag-neutral"}>{item.state}</span></td><td>{item.candidate_name ? <><strong>{item.candidate_name}</strong><div className="code">{item.candidate_code} · 观察样本</div></> : "—"}</td><td>{item.metrics.relative_strength?.toFixed(1)}</td><td>{item.metrics.trend_quality?.toFixed(1)}</td><td>{item.metrics.breadth?.toFixed(1)}</td></tr>)}</tbody></table></div>}
  </>;
}

