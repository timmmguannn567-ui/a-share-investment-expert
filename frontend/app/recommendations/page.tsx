"use client";

import { useEffect, useState } from "react";
import { actionLabel, apiGet, apiSend, money, Recommendation } from "@/lib/api";

export default function RecommendationsPage() {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [error, setError] = useState("");
  const load = () => apiGet<{ items: Recommendation[] }>("/api/recommendations").then((data) => setItems(data.items)).catch((err: Error) => setError(err.message));
  useEffect(() => { void load(); }, []);
  async function setStatus(id: number, status: "executed" | "ignored") { await apiSend(`/api/recommendations/${id}/status`, "PATCH", { status }); load(); }
  return <>
    <header className="page-head"><div><div className="eyebrow">CONDITIONAL PLAYBOOK</div><h1>次日操作建议</h1><div className="subtitle">每条建议都包含触发、失效与退出条件。建议金额已受现金、单品种上限、市场风险和行业暴露约束。</div></div><span className="demo-pill">T日信号 → T+1执行</span></header>
    {error && <div className="error">{error}</div>}
    <div className="grid grid-2">{items.map((item) => <article className="card" key={item.id}>
      <div className="section-head"><div><span className="code">{item.instrument_type === "etf" ? "ETF" : "个股"} · {item.instrument_code}</span><h2 style={{ marginTop: 5 }}>{item.instrument_name}</h2></div><span className={item.action === "BUY" ? "tag tag-buy" : "tag tag-watch"}>{actionLabel[item.action]}</span></div>
      <div className="grid grid-3" style={{ margin: "18px 0" }}><div><div className="card-label">综合评分</div><div className="metric">{item.score.toFixed(1)}</div></div><div><div className="card-label">建议金额</div><strong>{item.suggested_amount ? money(item.suggested_amount) : "暂不建仓"}</strong></div><div><div className="card-label">硬性上限</div><strong>{money(item.max_amount)}</strong></div></div>
      <p><b>触发：</b>{item.entry_condition}</p><p><b>失效：</b>{item.invalidation_condition}</p><p><b>退出：</b>{item.exit_condition}</p>
      <div className="notice">{item.risk_notes.join("；")}</div>
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}><button className="button" onClick={() => setStatus(item.id, "executed")}>标记已执行</button><button className="button secondary" onClick={() => setStatus(item.id, "ignored")}>忽略</button><span className="tag tag-neutral" style={{ marginLeft: "auto" }}>{item.status}</span></div>
    </article>)}</div>
  </>;
}

