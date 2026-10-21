# 技术架构

## 1. 总览

```text
数据提供者 → 标准化快照 → 评分引擎 → 风控引擎 → 推荐/报告
     ↓            ↓             ↓          ↓          ↓
 数据状态       SQLite       版本化配置   组合约束    FastAPI
                                                        ↓
                                                  Next.js UI
```

系统采用前后端分离结构。后端是唯一的业务规则来源，前端不重复计算交易信号。

线上 GitHub Pages 使用由同一 FastAPI 规则引擎导出的只读 JSON 快照。GitHub Actions 在交易日 18:30（Asia/Shanghai）启动临时 API、运行当日分析、导出 `frontend/public/api/*.json` 并重新部署。该路径不依赖用户电脑常驻进程；本地 FastAPI 继续承担开发、完整读写和 OpenAPI 文档。

## 2. 目录

```text
backend/
  app/
    api/            API路由
    providers/      数据源抽象与适配器
    services/       评分、风控、报告、回测
    config.py       环境配置
    database.py     SQLAlchemy会话
    models.py       持久化模型
    schemas.py      API契约
    main.py         FastAPI入口
  tests/
frontend/
  app/              Next.js App Router页面
  components/       导航、卡片、图表
  lib/              API客户端、类型、格式化
docs/
scripts/
data/
```

## 3. 数据提供者

业务服务仅依赖 `DataProvider` 协议。Provider返回统一的市场快照并报告来源、数据时间、完整性和是否为演示数据。

MVP包含确定性 `MockProvider`。真实数据适配器在第二阶段实现；切换时无需修改评分、风控或API层。

## 4. 分析流水线

1. 验证交易日和数据完整性
2. 获取市场、行业、股票、ETF标准化快照
3. 对行业指标做横截面百分位转换
4. 计算市场状态与行业分数
5. 筛出3～5个合格行业
6. 每个行业选择最多一只通过排除规则的股票
7. 计算ETF候选
8. 将候选交给组合风控，裁剪或否决金额
9. 持久化建议、评分、市场状态及数据快照
10. 生成结构化盘后报告
11. 导出版本化只读API快照，记录生成时间和下次更新时间

## 5. 避免未来数据

- 报告的 `trade_date` 表示信号日
- `valid_from` 固定为下一交易日
- 回测成交索引必须大于信号索引
- 财务数据后续按实际可见日期而非报告期入库
- 数据快照与策略版本一起保存

## 6. 风险优先级

```text
数据完整性 > 暂停/退市/风险排除 > 组合回撤 > 行业暴露
> 品种金额上限 > 策略信号 > 文本解释
```

低优先级模块不得覆盖高优先级约束。

## 7. 数据库

MVP使用SQLite，SQLAlchemy模型避免SQLite专有语法，为迁移PostgreSQL保留空间。JSON字段以标准JSON类型保存结构化分项和报告内容。

核心表包括证券、价格、持仓、配置、市场状态、行业评分、推荐、日报、回测和数据源状态。

## 8. API与前端

FastAPI暴露 `/api` 下的JSON接口，并生成OpenAPI文档。Next.js页面通过 `NEXT_PUBLIC_API_BASE_URL` 调用后端。请求失败时页面显示明确错误，不回退为伪造实时数据。

GitHub Pages 构建设置 `NEXT_PUBLIC_STATIC_DEMO=true` 后，前端改读站点同源的 `/api/*.json`。线上快照仅提供读取；持仓和设置等写操作只在浏览器会话中模拟，不能冒充持久化后端。

## 9. 安全边界

- 无券商凭据和下单接口
- 密钥只来自环境变量
- 外部文本不进入代码执行或系统提示
- CORS默认只允许本地前端
- Mock与真实数据在API和UI双重标记

## 10. 后续扩展

- 第二阶段：真实Provider、数据质量监控、公告事件抽取
- 第三阶段：真实历史回测、样本外滚动验证、推荐归因
- 第四阶段：盘后定时任务、备份、报告导出和通知

