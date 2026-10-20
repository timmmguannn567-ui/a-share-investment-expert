"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiSend, money, pct, Portfolio } from "@/lib/api";

const emptyForm = { instrument_code: "", name: "", instrument_type: "etf", quantity: "", cost_price: "", current_price: "", industry_l1: "" };

export default function PortfolioPage() {
  const [data, setData] = useState<Portfolio | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const load = () => apiGet<Portfolio>("/api/portfolio").then(setData).catch((err: Error) => setError(err.message));
  useEffect(() => { void load(); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      await apiSend("/api/portfolio/positions", "POST", { ...form, quantity: Number(form.quantity), cost_price: Number(form.cost_price), current_price: Number(form.current_price), industry_l1: form.industry_l1 || null });
      setForm(emptyForm); load();
    } catch (err) { setError(err instanceof Error ? err.message : "保存失败"); }
  }
  async function remove(id: number) { await apiSend(`/api/portfolio/positions/${id}`, "DELETE"); load(); }
  if (!data) return <div className="loading">正在读取组合…</div>;
  return <>
    <header className="page-head"><div><div className="eyebrow">PORTFOLIO RISK BOOK</div><h1>我的持仓</h1><div className="subtitle">录入真实持仓后，所有新建议会同时检查现金、单品种仓位和行业重复暴露。</div></div></header>
    <section className="grid grid-4"><div className="card"><div className="card-label">组合总值</div><div className="metric">{money(data.total_value)}</div></div><div className="card"><div className="card-label">可用现金</div><div className="metric">{money(data.cash)}</div></div><div className="card"><div className="card-label">总仓位</div><div className="metric">{pct(data.position_ratio)}</div><div className="metric-note">ETF {pct(data.etf_ratio)} · 个股 {pct(data.stock_ratio)}</div></div><div className="card"><div className="card-label">当前回撤</div><div className="metric">{pct(data.drawdown)}</div><div className="metric-note">峰值 {money(data.nav_peak)}</div></div></section>
    <section className="card section"><div className="section-head"><h2>新增持仓</h2><span>请使用真实成本与最新价格</span></div>{error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}<form onSubmit={submit}><div className="form-grid">
      <div className="field"><label>证券代码</label><input className="input" required value={form.instrument_code} onChange={(e) => setForm({ ...form, instrument_code: e.target.value })} /></div>
      <div className="field"><label>名称</label><input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
      <div className="field"><label>类型</label><select className="input" value={form.instrument_type} onChange={(e) => setForm({ ...form, instrument_type: e.target.value })}><option value="etf">ETF</option><option value="stock">个股</option></select></div>
      <div className="field"><label>份额</label><input className="input" type="number" min="0.01" step="0.01" required value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} /></div>
      <div className="field"><label>成本价</label><input className="input" type="number" min="0.001" step="0.001" required value={form.cost_price} onChange={(e) => setForm({ ...form, cost_price: e.target.value })} /></div>
      <div className="field"><label>最新价格</label><input className="input" type="number" min="0.001" step="0.001" required value={form.current_price} onChange={(e) => setForm({ ...form, current_price: e.target.value })} /></div>
      <div className="field"><label>申万一级行业</label><input className="input" value={form.industry_l1} onChange={(e) => setForm({ ...form, industry_l1: e.target.value })} /></div>
    </div><button className="button" style={{ marginTop: 14 }}>保存持仓</button></form></section>
    <section className="card section table-wrap"><div className="section-head"><h2>持仓明细</h2><span>{data.positions.length} 个标的</span></div>{data.positions.length === 0 ? <div className="empty">尚未录入持仓。当前分析按10万元现金账户计算。</div> : <table><thead><tr><th>证券</th><th>类型</th><th>行业</th><th>市值</th><th>成本价</th><th>现价</th><th>浮盈亏</th><th /></tr></thead><tbody>{data.positions.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><div className="code">{item.instrument_code}</div></td><td>{item.instrument_type === "etf" ? "ETF" : "个股"}</td><td>{item.industry_l1 ?? "未分类"}</td><td>{money(item.market_value)}</td><td>{item.cost_price.toFixed(3)}</td><td>{item.current_price.toFixed(3)}</td><td className={item.pnl >= 0 ? "positive" : "negative"}>{money(item.pnl)} · {pct(item.pnl_pct)}</td><td><button className="button danger" onClick={() => remove(item.id)}>删除</button></td></tr>)}</tbody></table>}</section>
  </>;
}

