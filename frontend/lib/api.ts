export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const STATIC_DEMO = process.env.NEXT_PUBLIC_STATIC_DEMO === "true";
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const staticCache = new Map<string, unknown>();

function staticFileFor(path: string): string | null {
  const files: Record<string, string> = {
    "/api/health": "health.json",
    "/api/dashboard": "dashboard.json",
    "/api/industries/rankings": "industries.json",
    "/api/recommendations": "recommendations.json",
    "/api/portfolio": "portfolio.json",
    "/api/reports/daily": "reports.json",
    "/api/settings": "settings.json",
    "/api/backtests": "backtest.json",
  };
  if (files[path]) return files[path];
  const report = path.match(/^\/api\/reports\/daily\/(\d{4}-\d{2}-\d{2})$/);
  return report ? `report-${report[1]}.json` : null;
}

async function staticGet<T>(path: string): Promise<T> {
  if (staticCache.has(path)) return staticCache.get(path) as T;
  const file = staticFileFor(path);
  if (!file) throw new Error(`静态演示模式不支持：${path}`);
  const response = await fetch(`${BASE_PATH}/api/${file}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`演示数据加载失败：${response.status}`);
  const data = await response.json() as T;
  staticCache.set(path, data);
  return data;
}

export async function apiGet<T>(path: string): Promise<T> {
  if (STATIC_DEMO) return staticGet<T>(path);
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `请求失败：${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiSend<T>(path: string, method: string, body?: unknown): Promise<T> {
  if (STATIC_DEMO) {
    if (path === "/api/analysis/run") return staticGet<T>("/api/dashboard");
    if (path === "/api/backtests") return staticGet<T>("/api/backtests");
    if (path === "/api/settings" && method === "PUT") {
      const data = { values: (body as { values: unknown }).values };
      staticCache.set("/api/settings", data);
      return data as T;
    }
    const statusMatch = path.match(/^\/api\/recommendations\/(\d+)\/status$/);
    if (statusMatch) {
      const data = await staticGet<{ items: Recommendation[] }>("/api/recommendations");
      const item = data.items.find((entry) => entry.id === Number(statusMatch[1]));
      if (item) item.status = String((body as { status?: string })?.status ?? item.status);
      return item as T;
    }
    if (path === "/api/portfolio/positions" && method === "POST") {
      const portfolio = await staticGet<Portfolio>("/api/portfolio");
      const input = body as Omit<Position, "id" | "market_value" | "pnl" | "pnl_pct">;
      const marketValue = Number(input.quantity) * Number(input.current_price);
      const costValue = Number(input.quantity) * Number(input.cost_price);
      portfolio.positions.push({
        ...input,
        id: Math.max(0, ...portfolio.positions.map((item) => item.id)) + 1,
        market_value: marketValue,
        pnl: marketValue - costValue,
        pnl_pct: costValue ? (marketValue - costValue) / costValue : 0,
      });
      return portfolio as T;
    }
    const deleteMatch = path.match(/^\/api\/portfolio\/positions\/(\d+)$/);
    if (deleteMatch && method === "DELETE") {
      const portfolio = await staticGet<Portfolio>("/api/portfolio");
      portfolio.positions = portfolio.positions.filter((item) => item.id !== Number(deleteMatch[1]));
      return undefined as T;
    }
    throw new Error(`静态演示模式不支持：${method} ${path}`);
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `请求失败：${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type Recommendation = {
  id: number;
  trade_date: string;
  valid_from: string;
  instrument_code: string;
  instrument_name: string;
  instrument_type: "stock" | "etf";
  industry_name: string | null;
  action: string;
  score: number;
  confidence: string;
  suggested_amount: number;
  max_amount: number;
  entry_condition: string;
  invalidation_condition: string;
  exit_condition: string;
  risk_notes: string[];
  reasoning: string[];
  score_components: Record<string, number>;
  source_timestamp: string;
  strategy_version: string;
  status: string;
  is_demo: boolean;
};

export type Industry = {
  industry_code: string;
  industry_name: string;
  score: number;
  rank: number;
  state: string;
  metrics: Record<string, number>;
  is_selected: boolean;
  candidate_code: string | null;
  candidate_name: string | null;
};

export type Position = {
  id: number;
  instrument_code: string;
  name: string;
  instrument_type: "stock" | "etf";
  quantity: number;
  cost_price: number;
  current_price: number;
  industry_l1: string | null;
  market_value: number;
  pnl: number;
  pnl_pct: number;
};

export type Portfolio = {
  id: number;
  name: string;
  cash: number;
  invested_value: number;
  total_value: number;
  nav_peak: number;
  drawdown: number;
  position_ratio: number;
  stock_ratio: number;
  etf_ratio: number;
  industry_exposure: Record<string, number>;
  positions: Position[];
};

export type Dashboard = {
  analysis_date: string;
  is_demo: boolean;
  portfolio: Portfolio;
  market: {
    regime: string;
    risk_score: number;
    equity_min: number;
    equity_max: number;
    reasons: string[];
    source_timestamp: string;
    proxy_ratio: number;
    proxy_rate: number;
    proxy_slope_3d: number;
    proxy_percentile: number;
    broad_selloff_pressure: number;
    deep_bear_count: number;
    trend_bull_count: number;
    wave_continuity: number;
    divergence: boolean;
    research_signals: string[];
    model_status: string;
    proxy_notice: string;
  };
  industries: Industry[];
  recommendations: Recommendation[];
  data_status: {
    provider: string;
    status: string;
    is_demo: boolean;
    completeness: number;
    message: string;
    last_updated: string;
    update_schedule?: {
      time: string;
      timezone: string;
      trading_days_only: boolean;
    };
  };
  online_api?: {
    status: string;
    mode: string;
    base_url: string;
    health_url: string;
    generated_at: string;
    next_update_at: string;
    schedule_label: string;
  };
};

export const money = (value: number) =>
  new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 0 }).format(value);

export const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export const actionLabel: Record<string, string> = {
  WATCH: "观察",
  BUY: "买入",
  ADD: "加仓",
  HOLD: "持有",
  REDUCE: "减仓",
  SELL: "卖出",
  CASH: "空仓",
};

