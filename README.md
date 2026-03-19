# 掘进工作面规程智能生成平台

> AI 赋能煤矿掘进工作面作业规程编制，从 3\~5 天缩短到 30 分钟

[![Backend CI](https://github.com/jdeng0936-blip/-/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/jdeng0936-blip/-/actions)

## ✨ 核心功能

| 模块 | 描述 | 技术 |
|---|---|---|
| 🤖 AI 智能对话 | 自然语言提问 → Tool Calling 自动路由 → 专业回答 | Gemini 2.5 Flash + SSE |
| 📐 支护计算引擎 | 锚杆/锚索间距、排距、数量自动计算 + 合规校验 | 确定性算法 |
| 🌬️ 通风计算引擎 | 瓦斯/人数/炸药/风速 四法取最大值 + 局扇推荐 | 确定性算法 |
| 📋 规则匹配引擎 | 围岩级别 × 断面形式 × 瓦斯等级 → 命中规则推荐 | DSL 规则树 |
| 📄 文档生成引擎 | 参数 → 计算 → 规则 → AI 润色 → Word 导出 | python-docx |
| 📚 标准库语义检索 | pgvector 向量检索 + 关键词混合检索 | RAG |
| 🔄 数据飞轮 | 用户反馈（采纳/修改/拒绝）→ 差异度量化 → SFT 数据池 | Jaccard 距离 |

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (Next.js 15)                    │
│          TypeScript · Tailwind CSS · Framer Motion       │
├─────────────────────────────────────────────────────────┤
│                  Backend (FastAPI)                        │
│   async/await · Pydantic V2 · JWT · SSE/WebSocket        │
├────────┬────────┬────────┬────────┬─────────┬───────────┤
│ AI     │ Calc   │ Rule   │ Doc    │ RAG     │ Feedback  │
│ Router │ Engine │ Engine │ Gen    │ Search  │ Flywheel  │
├────────┴────────┴────────┴────────┴─────────┴───────────┤
│        PostgreSQL 16 + pgvector │ Redis Stack            │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速启动

### 前置条件

- Python 3.11+ / Node.js 18+
- PostgreSQL 16 + pgvector 扩展
- Redis Stack

### 1. 克隆 & 安装

```bash
git clone https://github.com/jdeng0936-blip/-.git
cd -

# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env 填入真实的 GEMINI_API_KEY
```

### 3. 数据库初始化

```bash
cd backend

# 创建数据库 + pgvector 扩展
psql -U postgres -c "CREATE DATABASE excavation_platform;"
psql -U postgres -d excavation_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 运行迁移
source venv/bin/activate
alembic upgrade head
```

### 4. 启动服务

```bash
# 后端（终端 1）
cd backend && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（终端 2）
cd frontend && npm run dev
```

访问 http://localhost:3000 | API 文档 http://localhost:8000/docs

### Docker 一键部署

```bash
docker-compose up -d
```

## 📁 项目结构

```
backend/
├── app/
│   ├── api/v1/          # FastAPI 路由（auth / projects / ai / feedback ...）
│   ├── core/            # 配置 / 数据库 / 安全
│   ├── models/          # SQLAlchemy 模型（10 个业务表）
│   ├── schemas/         # Pydantic V2 请求/响应模型
│   └── services/        # 业务逻辑层
│       ├── ai_router.py     # AI 智能路由引擎（6 个 Tool）
│       ├── calc_engine.py   # 支护计算引擎
│       ├── vent_engine.py   # 通风计算引擎
│       ├── rule_service.py  # 规则匹配引擎
│       ├── doc_generator.py # 文档生成引擎
│       └── diff_sink.py     # 差异度下沉管道
├── migrations/          # Alembic 数据库迁移
├── tests/               # pytest 单元测试（79 用例）
└── requirements.txt

frontend/
├── src/app/dashboard/   # 页面路由
│   ├── page.tsx         # 工作台（统计 + 飞轮面板）
│   ├── ai/page.tsx      # AI 智能助手
│   ├── projects/        # 规程项目管理
│   └── ...
└── package.json
```

## 🧪 测试

```bash
# ===== 后端 (79 用例) =====
cd backend && source venv/bin/activate
python -m pytest tests/ -q          # 全量运行
python -m pytest tests/ -q -x       # 遇到第一个失败即停止
python -m pytest tests/ -v -k "calc" # 只跑计算引擎测试

# ===== 前端 (5 用例) =====
cd frontend
npm test                             # 全量运行
npm run test:watch                   # 监听模式（改代码自动重跑）
```

## 📊 API 概览

| 方法 | 路径 | 描述 |
|---|---|---|
| POST | `/api/v1/auth/login` | 用户登录（JWT） |
| GET | `/api/v1/projects` | 项目列表（分页） |
| POST | `/api/v1/ai/chat` | AI 对话（SSE 流式） |
| POST | `/api/v1/ai/industries` | 行业类型列表 |
| POST | `/api/v1/docs/generate/{id}` | 生成 Word 文档 |
| POST | `/api/v1/feedback` | 提交用户反馈 |
| GET | `/api/v1/feedback/stats` | 飞轮统计数据 |
| GET | `/api/v1/standards` | 标准库列表 |
| GET | `/api/v1/rules/groups` | 规则组列表 |

完整文档：http://localhost:8000/docs

## 📄 License

私有项目 · 华阳集团内部使用
