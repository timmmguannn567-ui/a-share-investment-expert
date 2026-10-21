import Link from "next/link";

const links = [
  ["OV", "总览", "/"],
  ["MK", "市场环境", "/market"],
  ["SW", "行业强弱", "/industries"],
  ["AI", "操作建议", "/recommendations"],
  ["PF", "我的持仓", "/portfolio"],
  ["DR", "盘后报告", "/reports"],
  ["BT", "策略回测", "/backtests"],
  ["ST", "系统设置", "/settings"],
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">析</div>
        <div><strong>见微 · 股市专家</strong><span>环境 / 行业 / 执行</span></div>
      </div>
      <nav className="nav">
        {links.map(([icon, label, href]) => (
          <Link href={href} key={href}><span className="nav-icon">{icon}</span>{label}</Link>
        ))}
      </nav>
      <div className="sidebar-foot">
        <b>辅助决策，不代替判断</b>
        <p>盘后信号仅用于下一交易日计划。任何建议都可能失效，请先核对真实行情与公告。</p>
      </div>
    </aside>
  );
}

