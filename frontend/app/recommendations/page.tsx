"use client";

import { useEffect, useState } from "react";
import { actionLabel, apiGet, apiSend, money, Recommendation } from "@/lib/api";

export default function RecommendationsPage() {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [error, setError] = useState("");
  const load = () => apiGet<{ items: Recommendation[] }>("/api/recommendations").then((data) => setItems(data.items)).catch((err: Error) => setError(err.message));
  useEffect(() => { void load(); }, []);
  async function setStatus(id: number, status: "executed" | "ignored") { await apiSend(`/api/recommendations/${id}/status`, "PATCH", { status }); load(); }
  const sortedItems = [...items].sort((a, b) => Number(b.instrument_type === "etf") - Number(a.instrument_type === "etf") || b.score - a.score);
  return <>
    <header className="page-head"><div><div className="context-line">条件式执行清单</div><h1>ETF优先，个股增强</h1><div className="subtitle">每条建议都包含触发、失效、时间止损与退出条件。观察不是买入；未触发条件时保持现金。</div></div><span className="demo-pill">T日信号 → T+1执行</span></header>
    {error && <div className="error">{error}</div>}
    <div className="grid grid-2">{sortedItems.map((item) => <article className="panel recommendation-card" key={item.id}>
      <div className="section-head"><div><span className="code">{item.instrument_type === "etf" ? "ETF" : "个股"} · {item.instrument_code}</span><h2 style={{ marginTop: 5 }}>{item.instrument_name}</h2></div><span className={item.action === "BUY" ? "tag tag-buy" : "tag tag-watch"}>{actionLabel[item.action]}</span></div>
      <div className="grid grid-3" style={{ margin: "18px 0" }}><div><div className="card-label">综合评分</div><div className="metric">{item.score.toFixed(1)}</div></div><div><div className="card-label">建议金额</div><strong>{item.suggested_amount ? money(item.suggested_amount) : "暂不建仓"}</strong></div><div><div className="card-label">硬性上限</div><strong>{money(item.max_amount)}</strong></div></div>
      <p><b>触发：</b>{item.entry_condition}</p><p><b>失效：</b>{item.invalidation_condition}</p><p><b>退出：</b>{item.exit_condition}</p>
      <div className="notice">{item.risk_notes.join("；")}</div>
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}><button className="button" onClick={() => setStatus(item.id, "executed")}>标记已执行</button><button className="button secondary" onClick={() => setStatus(item.id, "ignored")}>忽略</button><span className="tag tag-neutral" style={{ marginLeft: "auto" }}>{item.status}</span></div>
    </article>)}</div>
  </>;
}

