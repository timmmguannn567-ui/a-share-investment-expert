"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiSend } from "@/lib/api";

type Values = Record<string, string | number | boolean | string[]>;

const labels: Record<string, string> = {
  max_drawdown: "最大组合回撤",
  etf_absolute_cap: "单只ETF金额上限",
  etf_nav_cap: "单只ETF净值比例",
  stock_absolute_cap: "单只股票金额上限",
  stock_nav_cap: "单只股票净值比例",
  stock_total_cap: "个股合计比例",
  etf_total_cap: "ETF合计比例",
  industry_exposure_cap: "单行业暴露上限",
  selected_industry_count: "每日重点行业数",
  industry_score_threshold: "行业入选分数",
  minimum_listed_days: "最低上市天数",
  fee_rate: "交易费率",
  slippage_rate: "滑点率",
  report_time: "盘后报告时间",
};

export default function SettingsPage() {
  const [values, setValues] = useState<Values>({}); const [message, setMessage] = useState(""); const [error, setError] = useState("");
  useEffect(() => { apiGet<{ values: Values }>("/api/settings").then((data) => setValues(data.values)).catch((err: Error) => setError(err.message)); }, []);
  async function save(event: FormEvent) { event.preventDefault(); setMessage(""); try { const data = await apiSend<{ values: Values }>("/api/settings", "PUT", { values }); setValues(data.values); setMessage("设置已保存。重新运行分析后生效。"); } catch (err) { setError(err instanceof Error ? err.message : "保存失败"); } }
  const editable = Object.keys(labels);
  return <><header className="page-head"><div><div className="eyebrow">RISK & STRATEGY CONTROLS</div><h1>系统设置</h1><div className="subtitle">阈值集中保存在策略配置中，避免散落在业务代码里。风险上限调整后需要重新运行分析。</div></div></header>{error && <div className="error">{error}</div>}<form className="card" onSubmit={save}><div className="form-grid">{editable.map((key) => <div className="field" key={key}><label>{labels[key]}</label><input className="input" type={key === "report_time" ? "time" : "number"} step={key.includes("cap") || key.includes("rate") || key === "max_drawdown" ? "0.001" : "1"} value={String(values[key] ?? "")} onChange={(e) => setValues({ ...values, [key]: key === "report_time" ? e.target.value : Number(e.target.value) })} /></div>)}</div><div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 18 }}><button className="button">保存设置</button>{message && <span className="positive">{message}</span>}</div></form><section className="card section"><div className="section-head"><h2>固定策略边界</h2></div><div className="notice">当前数据源：Mock演示数据。首版不连接券商、不自动下单；ST排除、允许空仓及支持板块等安全边界暂不在此页放开。</div><pre style={{ overflow: "auto", color: "#52635b", fontSize: 12, lineHeight: 1.6 }}>{JSON.stringify(values, null, 2)}</pre></section></>;
}

