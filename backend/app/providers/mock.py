from __future__ import annotations

import hashlib
import math
import random
from datetime import date, datetime, timedelta, timezone

from app.providers.base import IndustryMetrics, InstrumentMetrics, MarketMetrics, MarketSnapshot


SHENWAN_INDUSTRIES = [
    ("801010", "农林牧渔", "养殖业"),
    ("801030", "基础化工", "化学制品"),
    ("801040", "钢铁", "普钢"),
    ("801050", "有色金属", "工业金属"),
    ("801080", "电子", "半导体"),
    ("801880", "汽车", "乘用车"),
    ("801110", "家用电器", "白色家电"),
    ("801120", "食品饮料", "饮料乳品"),
    ("801130", "纺织服饰", "服装家纺"),
    ("801140", "轻工制造", "家居用品"),
    ("801150", "医药生物", "化学制药"),
    ("801160", "公用事业", "电力"),
    ("801170", "交通运输", "物流"),
    ("801180", "房地产", "房地产开发"),
    ("801200", "商贸零售", "一般零售"),
    ("801210", "社会服务", "旅游及景区"),
    ("801780", "银行", "股份制银行"),
    ("801790", "非银金融", "证券"),
    ("801230", "综合", "综合"),
    ("801710", "建筑材料", "水泥"),
    ("801720", "建筑装饰", "基础建设"),
    ("801730", "电力设备", "电池"),
    ("801890", "机械设备", "自动化设备"),
    ("801740", "国防军工", "航空装备"),
    ("801750", "计算机", "软件开发"),
    ("801760", "传媒", "游戏"),
    ("801770", "通信", "通信设备"),
    ("801950", "煤炭", "煤炭开采"),
    ("801960", "石油石化", "油气开采"),
    ("801970", "环保", "环境治理"),
    ("801980", "美容护理", "化妆品"),
]


STOCK_NAMES = {
    "农林牧渔": ("600101", "丰牧示例", "主板"),
    "基础化工": ("600102", "新材示例", "主板"),
    "钢铁": ("600103", "精钢示例", "主板"),
    "有色金属": ("600104", "铜业示例", "主板"),
    "电子": ("688105", "芯片示例", "科创板"),
    "汽车": ("002106", "汽车示例", "主板"),
    "家用电器": ("000107", "家电示例", "主板"),
    "食品饮料": ("000108", "食品示例", "主板"),
    "纺织服饰": ("600109", "服饰示例", "主板"),
    "轻工制造": ("603110", "家居示例", "主板"),
    "医药生物": ("300111", "创新药示例", "创业板"),
    "公用事业": ("600112", "电力示例", "主板"),
    "交通运输": ("601113", "物流示例", "主板"),
    "房地产": ("600114", "地产示例", "主板"),
    "商贸零售": ("600115", "零售示例", "主板"),
    "社会服务": ("300116", "旅游示例", "创业板"),
    "银行": ("601117", "银行示例", "主板"),
    "非银金融": ("600118", "证券示例", "主板"),
    "综合": ("600119", "综合示例", "主板"),
    "建筑材料": ("600120", "建材示例", "主板"),
    "建筑装饰": ("601121", "基建示例", "主板"),
    "电力设备": ("300122", "电池示例", "创业板"),
    "机械设备": ("920123", "机械示例", "北交所"),
    "国防军工": ("600124", "航空示例", "主板"),
    "计算机": ("300125", "软件示例", "创业板"),
    "传媒": ("300126", "传媒示例", "创业板"),
    "通信": ("600127", "通信示例", "主板"),
    "煤炭": ("601128", "煤炭示例", "主板"),
    "石油石化": ("600129", "能源示例", "主板"),
    "环保": ("300130", "环保示例", "创业板"),
    "美容护理": ("603131", "美护示例", "主板"),
}


ETF_DEFINITIONS = [
    ("588000", "科创50ETF", "科创50"),
    ("512010", "医药ETF", "医药生物"),
    ("510300", "沪深300ETF", "宽基"),
    ("510500", "中证500ETF", "宽基"),
    ("512100", "中证1000ETF", "宽基"),
    ("159915", "创业板ETF", "宽基"),
    ("510880", "红利ETF", "红利"),
    ("511010", "国债ETF", "债券"),
    ("511990", "货币ETF", "货币"),
    ("518880", "黄金ETF", "黄金"),
]


def _next_weekday(day: date) -> date:
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


class MockDataProvider:
    name = "mock"
    is_demo = True

    @staticmethod
    def _rng(day: date, namespace: str) -> random.Random:
        digest = hashlib.sha256(f"{day.isoformat()}:{namespace}".encode()).hexdigest()
        return random.Random(int(digest[:16], 16))

    def status(self) -> dict[str, object]:
        return {
            "provider": self.name,
            "status": "ok",
            "is_demo": True,
            "completeness": 1.0,
            "message": "确定性演示数据，仅用于功能验证，不能作为真实交易依据。",
            "last_updated": datetime.now(timezone.utc),
        }

    def get_snapshot(self, trade_date: date | None = None) -> MarketSnapshot:
        day = trade_date or date.today()
        market_rng = self._rng(day, "market")
        market = MarketMetrics(
            index_trend=market_rng.uniform(42, 72),
            momentum_20d=market_rng.uniform(38, 74),
            breadth=market_rng.uniform(35, 72),
            volume_ratio=market_rng.uniform(45, 75),
            volatility=market_rng.uniform(30, 67),
            drawdown=market_rng.uniform(25, 62),
            industry_diffusion=market_rng.uniform(36, 75),
        )

        industries: list[IndustryMetrics] = []
        stocks: list[InstrumentMetrics] = []
        for index, (code, name, subindustry) in enumerate(SHENWAN_INDUSTRIES):
            rng = self._rng(day, name)
            cycle = 11 * math.sin((day.toordinal() + index * 5) / 17)
            relative_strength = max(12, min(95, rng.uniform(35, 78) + cycle))
            metrics = IndustryMetrics(
                code=code,
                name=name,
                subindustry=subindustry,
                relative_strength=relative_strength,
                trend=max(10, min(95, relative_strength + rng.uniform(-14, 12))),
                breadth=rng.uniform(25, 88),
                volume_change=rng.uniform(28, 90),
                risk_quality=rng.uniform(30, 88),
                fundamentals=rng.uniform(35, 85),
                event_safety=rng.uniform(45, 95),
            )
            industries.append(metrics)
            stock_code, stock_name, board = STOCK_NAMES[name]
            stock_rng = self._rng(day, stock_code)
            stocks.append(
                InstrumentMetrics(
                    code=stock_code,
                    name=stock_name,
                    instrument_type="stock",
                    board=board,
                    industry_code=code,
                    industry_name=name,
                    subindustry=subindustry,
                    price=round(stock_rng.uniform(8, 86), 2),
                    momentum=max(10, min(96, relative_strength + stock_rng.uniform(-12, 16))),
                    trend=max(10, min(96, metrics.trend + stock_rng.uniform(-10, 14))),
                    liquidity=stock_rng.uniform(42, 95),
                    volatility_quality=stock_rng.uniform(35, 88),
                    fundamentals=stock_rng.uniform(38, 92),
                    valuation=stock_rng.uniform(30, 86),
                    leadership=stock_rng.uniform(40, 94),
                    event_safety=stock_rng.uniform(55, 96),
                )
            )

        etfs: list[InstrumentMetrics] = []
        for code, name, industry in ETF_DEFINITIONS:
            rng = self._rng(day, code)
            focus_boost = 7 if industry in {"医药生物", "科创50"} else 0
            etfs.append(
                InstrumentMetrics(
                    code=code,
                    name=name,
                    instrument_type="etf",
                    board="ETF",
                    industry_code=None,
                    industry_name=industry,
                    subindustry=None,
                    price=round(rng.uniform(0.7, 5.2), 3),
                    momentum=min(96, rng.uniform(35, 84) + focus_boost),
                    trend=min(96, rng.uniform(38, 86) + focus_boost),
                    liquidity=rng.uniform(62, 98),
                    volatility_quality=rng.uniform(45, 90),
                    fundamentals=70,
                    valuation=rng.uniform(40, 82),
                    leadership=rng.uniform(52, 92),
                    event_safety=rng.uniform(72, 98),
                    scale=rng.uniform(55, 98),
                    tracking_quality=rng.uniform(72, 98),
                    premium_discount_quality=rng.uniform(74, 99),
                )
            )

        return MarketSnapshot(
            trade_date=day,
            next_trade_date=_next_weekday(day),
            source_timestamp=datetime.now(timezone.utc),
            source_name=self.name,
            is_demo=True,
            completeness=1.0,
            market=market,
            industries=industries,
            stocks=stocks,
            etfs=etfs,
        )

