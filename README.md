# 鲜标智投 FreshBid Pro

> AI 驱动的生鲜食材配送投标文档智能生成平台 — 从招标解析到合规标书，全流程自动化

[![Backend CI](https://github.com/jdeng0936-blip/-/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/jdeng0936-blip/-/actions)

## 项目概述

**鲜标智投** 是一套专为生鲜食材配送企业打造的 SaaS 投标辅助平台，能够：

- 📄 **一键解析招标文件** — 上传 PDF/DOCX 后自动提取评分标准、资质要求和商务条款
- 🤖 **AI 多节点生成引擎** — 基于企业画像和知识库，分章节智能生成合规的投标文档
- ✅ **三级合规审查** — 格式规则（L1）+ 语义校验（L2）+ 废标项检测（L3）
- 📊 **报价智能编制** — 结合历史中标数据，支持 6 品类自动报价计算
- 🔍 **反 AI 痕迹检测** — 降低生成文本的机器识别风险

## 技术架构

| 层 | 技术栈 |
|---|---|
| 前端 | Next.js 16 + TypeScript + TailwindCSS + shadcn/ui |
| 后端 | FastAPI + Python 3.11 + SQLAlchemy（异步）|
| 数据库 | PostgreSQL 16 + pgvector（向量检索）+ Redis |
| AI 引擎 | LLMSelector 多供应商路由（OpenAI / DeepSeek / Qwen / Gemini）|
| 部署 | Docker Compose + Nginx |

## 快速启动

```bash
# 复制环境配置
cp backend/.env.example backend/.env
# 填入必要的 API Key 和数据库配置后执行：
docker compose up -d
```

访问 `http://localhost:3000` 打开平台界面。

## 目录结构

```
-/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/    # 路由层
│   │   ├── services/  # 业务逻辑层
│   │   ├── models/    # 数据库模型
│   │   └── core/      # 配置、LLM 选择器、安全
│   ├── alembic/       # 数据库迁移
│   ├── tests/         # 测试文件
│   └── llm_registry.yaml  # LLM 任务路由注册表
├── frontend/          # Next.js 前端
├── nginx/             # Nginx 反向代理配置
├── docs/              # 设计文档与规划
└── docker-compose.yml
```

## 开发规范

- 所有 LLM 调用必须通过 `LLMSelector`，严禁硬编码模型名或 API Key
- 所有业务数据读写必须携带 `tenant_id` 过滤（多租户隔离）
- 数据库变更必须通过 `alembic revision --autogenerate` 生成迁移文件
- 详见 `.antigravity_rules.md` 中的双代理开发协作规范
