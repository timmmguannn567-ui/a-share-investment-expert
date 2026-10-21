const states = ["冰封", "磨底", "反弹", "回踩", "趋势", "强攻"];

export function MarketStateBand({ current }: { current: string }) {
  return (
    <div className="state-band" aria-label={`当前市场状态：${current}`}>
      {states.map((state) => (
        <div className={`state-segment ${state === current ? "is-current" : ""}`} key={state}>
          <span className="state-segment-dot" />
          <span>{state}</span>
        </div>
      ))}
    </div>
  );
}
