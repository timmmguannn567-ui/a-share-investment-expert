"use client";

import * as echarts from "echarts";
import { useEffect, useRef } from "react";
import type { Industry } from "@/lib/api";

export function IndustryChart({ industries }: { industries: Industry[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption({
      grid: { left: 5, right: 24, top: 8, bottom: 5, containLabel: true },
      xAxis: { type: "value", min: 0, max: 100, splitLine: { lineStyle: { color: "#edf1ef" } }, axisLabel: { color: "#7b8a83" } },
      yAxis: { type: "category", inverse: true, data: industries.map((item) => item.industry_name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: "#384840" } },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, formatter: (items: unknown) => {
        const rows = items as Array<{ name: string; value: number }>;
        return rows.length ? `${rows[0].name}<br/>综合评分：${rows[0].value.toFixed(1)}` : "";
      } },
      series: [{
        type: "bar",
        data: industries.map((item) => item.score),
        barWidth: 13,
        itemStyle: { borderRadius: [0, 7, 7, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: "#197a69" }, { offset: 1, color: "#c3db54" }]) },
      }],
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [industries]);
  return <div ref={ref} style={{ height: 285, width: "100%" }} aria-label="重点行业评分图" />;
}

