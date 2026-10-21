# A股ETF与个股辅助决策系统

一个面向个人使用的A股盘后辅助决策系统。系统按“市场环境 → 允许仓位 → 行业最小阻力 → ETF优先/个股增强 → 条件式执行”生成计划；页面只解释结构化结果，不执行自动交易。

> 当前版本默认使用可重复的 Mock 演示数据。所有演示页面均显示“演示数据”标识，不能将其作为真实交易依据。

## 已实现

- FastAPI + SQLite 后端与数据库模型
- MockProvider 和数据源状态接口
- 市场状态、31个申万一级行业排名、重点行业筛选
- 代理多空比、速率、历史分位与六状态市场环境
- 每个重点行业最多一只候选股
- ETF候选与医药/科创50重点覆盖
- ETF、个股、行业暴露和组合回撤风控
- 持仓增删改查
- 结构化盘后报告与历史报告
- 推荐记录、执行/忽略状态
- 中文 Next.js 仪表盘及主要页面
- Mock回测烟雾验证（显著标记演示数据）
- 核心评分和风险规则测试
- GitHub Pages只读快照API，交易日18:30（北京时间）自动更新

详细范围见 [PRD](docs/PRD.md) 与 [架构说明](docs/ARCHITECTURE.md)。

## Windows 本地运行

### 1. 后端

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

若系统没有 `py` 命令，请用已安装的 Python 3.12 可执行文件替代。

API文档：<http://localhost:8000/docs>

本地健康检查：<http://localhost:8000/api/health>

线上只读快照API：<https://timmmguannn567-ui.github.io/a-share-investment-expert/api/health.json>

### 2. 前端

另开一个PowerShell窗口：

```powershell
cd frontend
corepack pnpm install
Copy-Item ..\.env.example .env.local
corepack pnpm dev
```

访问：<http://localhost:3000>

### 3. 测试

```powershell
cd backend
python -m pytest
```

```powershell
cd frontend
corepack pnpm lint
corepack pnpm build
```

## 一键启动

依赖安装完成后，可在项目根目录执行：

```powershell
.\scripts\start.ps1
```

脚本会分别启动后端和前端。停止时关闭对应终端窗口。

## 数据安全

- 默认只绑定本机端口，不连接券商，不自动下单。
- API密钥只通过环境变量或本地 `.env` 提供。
- 外部公告、新闻和文本一律作为不可信数据处理。
- T日收盘后生成的信号仅用于T+1计划。

## 在线更新时间

GitHub Actions 在每个交易日 18:30（北京时间）重新生成并部署只读快照 API。静态快照不依赖本机 FastAPI 常驻，因此电脑关闭后仍可访问。当前数据提供者仍为 Mock，页面和 API 会明确标注“演示数据”。

## 下一阶段

- 接入并验证合法、稳定的真实行情与申万分类数据源
- 完整的数据质量监控和公告风险识别
- 真实历史数据回测、滚动样本外验证
- APScheduler盘后任务与备份机制

