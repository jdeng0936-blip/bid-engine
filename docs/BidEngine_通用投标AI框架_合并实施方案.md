# 通用投标 AI 框架（BidEngine）合并实施方案

> 基于「标标AI」与「鲜标智投」两大项目的深度分析，制定的分阶段合并实施方案。
> 
> 创建日期：2026-03-31

---

## 一、项目背景

### 两大项目定位

| 维度 | 标标AI (biaobiao) | 鲜标智投 (shangxianshicai) |
|------|-------------------|---------------------------|
| **行业** | 建筑工程招投标 | 生鲜食材配送招投标 |
| **数据库表** | ~6 核心表 | 23 张表 |
| **后端服务** | ~15 个 | 28 个 |
| **API 端点** | ~38 个 | 80+ 个 |
| **前端页面** | ~10 个 | ~10 个 |
| **测试用例** | 240+ | 较少 |
| **LLM 供应商** | Gemini + OpenAI（2家） | OpenAI + Gemini + Deepseek + Qwen（4家） |

### 核心结论

**两个项目互补性极强，合并为通用框架完全可行。**

- **标标AI** 在生成质量控制上更成熟（7节点流水线、5级润色、反AI检测、数据脱敏、变体生成）
- **鲜标智投** 在业务完整度上更强（企业管理、商机漏斗、报价引擎、计费中心、审计日志）

**合并策略：以鲜标的完整业务模型为骨架，嫁接标标的 AI 生成质量引擎，再做行业插件化抽象。**

---

## 二、共同技术基座（可直接复用）

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + SQLAlchemy 2.0 (async) + Pydantic V2 |
| 数据库 | PostgreSQL 16 + pgvector（向量检索） |
| 前端 | Next.js + React + TypeScript + Tailwind CSS |
| LLM 路由 | llm_registry.yaml + LLMSelector 多模型调度 |
| Prompt 管理 | YAML 注册表 + 版本管理 |
| 向量检索 | Gemini Embedding + pgvector 余弦相似度 |
| 认证 | JWT + 多租户隔离 (tenant_id) |
| 文档导出 | python-docx (Word 生成) |
| 反馈飞轮 | accept/edit/reject → diff_ratio → SFT 数据 |
| 部署 | Docker Compose + Nginx |

---

## 三、各自独有能力清单

### 标标AI 独有（待移植到框架）

| 能力 | 说明 | 移植优先级 |
|------|------|----------|
| **7 节点生成流水线** | Planner→Retriever→Writer→ComplianceGate→Polish→Reviewer→Formatter，最多3轮迭代 | **P0 — 极高** |
| **5 级润色引擎** | 术语规范→文风一致→逻辑连贯→专业深化→亮点提炼，3-5轮自动迭代，质量分≥90停止 | **P0 — 极高** |
| **反 AI 检测引擎** | L1 统计特征（句长/词汇丰富度/重复率/连接词密度）+ L2 基线 n-gram 对比 | **P1 — 高** |
| **数据脱敏系统** | Regex + NER 双引擎，发 LLM 前掩码，返回后还原，保护企业敏感信息 | **P1 — 高** |
| **评分点驱动目录** | 从招标文件提取评分标准 → 驱动生成章节大纲，确保所有得分项都有章节覆盖 | **P1 — 高** |
| **3 级合规审查** | L1 格式规则(毫秒) + L2 LLM语义(秒) + L3 废标硬规则 | **P1 — 高** |
| **变体生成引擎** | 工艺路线/语言风格/排版结构/参数浮动多维变体，防撞标 | **P2 — 中** |
| **工艺知识树** | 施工方法数据库 + 高分段落模板 | **P2 — 中（行业特定）** |

### 鲜标智投 独有（框架已包含）

| 能力 | 说明 | 状态 |
|------|------|------|
| **商机漏斗** | 多平台抓取 → AI匹配分析 → 转化投标项目 | ✅ 已有 |
| **企业能力画像** | CapabilityGraphService 结构化能力输出 | ✅ 已有 |
| **AI Tool Calling 路由** | LLM 意图识别 → 8个业务工具自动调度 | ✅ 已有 |
| **完整企业管理** | 资质(15类) + 图片资产(13类) + 冷链资产 | ✅ 已有 |
| **报价引擎** | 6品类自动初始化 + 下浮率计算 | ✅ 已有 |
| **配额计费** | 用量限制 + 使用日志 | ✅ 已有 |
| **审计日志** | 全操作审计追踪 | ✅ 已有 |
| **招标文件解析** | PDF/Word → LLM 结构化提取需求 | ✅ 已有 |

---

## 四、前置决策

| 决策项 | 建议 | 原因 |
|-------|------|------|
| **代码基座** | 鲜标智投 | 23张表、80+ API、业务完整度高，改造成本远低于反向移植 |
| **生成引擎** | 标标AI 的 7 节点流水线 | 质量控制远优于鲜标的单次调用 |
| **LLM 路由** | 合并：鲜标的多供应商 + 标标的 Provider 抽象类 | 鲜标支持4家供应商但架构不够清晰，标标架构好但只支持2家 |
| **主键策略** | 保持 Int（鲜标现状） | UUID 迁移代价大，Int 对现有数据库兼容 |
| **租户隔离** | 鲜标现有方案（所有表强制 tenant_id） | 已经是最佳实践 |

---

## 五、分阶段实施计划

### Phase 0：准备工作（第 1 周）

**目标：建立新仓库 + 统一开发环境**

| 任务 | 具体操作 | 产出 |
|------|---------|------|
| 0.1 创建新仓库 | `bid-engine` 新仓库，从鲜标 fork | 干净的起点 |
| 0.2 清理鲜标代码 | 移除食材硬编码（6品类报价、冷链字段名等），保留结构 | 行业无关的骨架 |
| 0.3 复制标标关键文件 | 将标标的 7 个核心服务复制到 `staging/biaobiao/` 目录备用 | 待移植的代码就位 |
| 0.4 统一 Docker 环境 | 合并两个 docker-compose.yml，统一端口/资源限制 | 单一开发环境 |
| 0.5 建立测试基线 | 当前鲜标所有功能跑通一遍，记录基准 | 回归测试基准 |

**待讨论：** 新仓库名？从鲜标 fork 还是全新仓库拷贝代码？

---

### Phase 1：引擎层移植（第 2-3 周）

**目标：把标标的 AI 生成质量引擎嫁接到鲜标骨架上**

#### 1.1 LLM 路由层重构

```
当前鲜标:  LLMSelector (静态方法, 返回 config dict, 每次创建 AsyncOpenAI 客户端)
当前标标:  LLMSelector (单例, BaseLLMProvider 抽象类, generate/stream/embed 方法)
目标:     合并为 Provider 抽象 + 4 供应商支持
```

| 文件 | 动作 |
|------|------|
| `backend/app/core/llm_selector.py` | **重写** — 引入标标的 `BaseLLMProvider` 抽象类，保留鲜标的 4 供应商配置 |
| `backend/app/core/providers/` | **新建** — `gemini.py`, `openai_compat.py`, `deepseek.py`, `qwen.py` |
| `backend/llm_registry.yaml` | **合并** — 增加标标的 `polish`, `bid_extract`, `bid_outline`, `anti_rewrite` 等任务 |

改造后的调用方式：

```python
# 改造前（鲜标）
cfg = LLMSelector.get_client_config("bid_section_generate")
client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
response = await client.chat.completions.create(...)

# 改造后（统一）
selector = LLMSelector.instance()
response = await selector.generate("bid_section_generate", system_prompt, user_prompt)
# 或流式
async for chunk in selector.stream("bid_section_generate", system_prompt, user_prompt):
    yield chunk
```

#### 1.2 移植 7 节点生成流水线

**这是最关键的改造。** 把标标的 `generate_service.py` (541行) 适配到鲜标的数据模型上。

```
适配后流程（保留鲜标的数据流）:

  ┌─────────────────────────────────────────────────────┐
  │ 输入: BidProject + BidChapter + TenderRequirement    │  ← 鲜标数据模型
  │       + Enterprise + Credential + ImageAsset         │
  └──────────────────┬──────────────────────────────────┘
                     ▼
  Node 1: Planner    — 生成章节大纲 + 知识检索查询词
                     ▼
  Node 2: Retriever  — RAG 三层检索 (StdClause + ChapterSnippet + BidCase)  ← 鲜标知识库
                     ▼
  ┌── Node 3: Writer — 结合企业画像+RAG结果+评分要求生成草稿
  │                  ▼
  │   Node 4: ComplianceGate — 格式规则(L1) + LLM语义(L2) + 废标检测(L3)
  │            │ critical → 回到 Node 3 (最多3轮)
  │            ▼ passed
  │   Node 5: PolishPipeline — 术语→文风→逻辑→专业→亮点 (3-5轮)
  │                  ▼
  │   Node 6: Reviewer — 评分点覆盖校验（对照 TenderRequirement）
  │            │ failed → 回到 Node 3
  └────────────┘
                     ▼ passed
  Node 7: Formatter  — 输出到 BidChapter.content + SSE 流式推送
```

| 文件 | 动作 |
|------|------|
| `backend/app/services/bid_generation_service.py` | **重写核心方法** — 替换 `generate_single_chapter()` 为 7 节点流水线 |
| `backend/app/services/generation/` | **新建目录** |
| `├── planner.py` | Node 1: 大纲规划 (from 标标) |
| `├── retriever.py` | Node 2: RAG 检索 (复用鲜标的 embedding_service) |
| `├── writer.py` | Node 3: 内容生成 (合并两者 Prompt) |
| `├── compliance_gate.py` | Node 4: 合规网关 (from 标标, 对接鲜标的 TenderRequirement) |
| `├── polish_pipeline.py` | Node 5: 5 级润色 (from 标标) |
| `├── reviewer.py` | Node 6: 评分覆盖 (from 标标, 对接鲜标的 max_score) |
| `└── formatter.py` | Node 7: 格式化输出 |
| `backend/app/services/bid_critic_service.py` | **保留** — 作为 Node 4 的补充校验层 |

#### 1.3 移植反 AI 检测引擎

| 文件 | 动作 |
|------|------|
| `backend/app/services/anti_review_service.py` | **新建** — 从标标移植 L1 统计 + L2 基线检测 |
| `backend/app/api/v1/anti_review.py` | **新建** — `POST /anti-review/check` + `POST /anti-review/batch` |
| 前端 `anti-review/page.tsx` | **新建** — AI 检测页面 |

#### 1.4 移植数据脱敏系统

| 文件 | 动作 |
|------|------|
| `backend/app/services/desensitize_service.py` | **新建** — Regex + NER 双引擎 |
| `backend/app/models/desensitize_dict.py` | **新建** — 脱敏映射表 |
| 7 节点流水线中 | Writer 节点调用前 `mask()`，返回后 `unmask()` |

#### Phase 1 验收标准

- [ ] 用鲜标的食材配送测试数据，走通 7 节点流水线生成一个完整章节
- [ ] 生成内容经过合规校验 + 润色 + 评分覆盖检查
- [ ] SSE 流式输出正常
- [ ] 反 AI 检测能对生成内容打分
- [ ] 脱敏系统在 LLM 调用前后正确 mask/unmask

---

### Phase 2：行业插件化抽象（第 4-5 周）

**目标：将行业特定逻辑从硬编码变为可配置插件**

#### 2.1 定义行业插件接口

```python
# backend/app/plugins/base.py

from abc import ABC, abstractmethod

class IndustryPlugin(ABC):
    """行业插件基类 — 所有行业特定逻辑的抽象"""
    
    @property
    @abstractmethod
    def industry_code(self) -> str:
        """行业代码: "fresh_food" / "construction" / "it_service" """
        ...
    
    @property
    @abstractmethod
    def industry_name(self) -> str:
        """行业名称: "生鲜食材配送" / "建筑工程" """
        ...
    
    @abstractmethod
    def get_chapter_templates(self, customer_type: str) -> list[ChapterTemplate]:
        """返回该行业的章节模板列表"""
        ...
    
    @abstractmethod
    def get_customer_types(self) -> list[CustomerTypeDef]:
        """返回该行业支持的客户类型"""
        ...
    
    @abstractmethod
    def get_compliance_rules(self) -> list[ComplianceRule]:
        """返回该行业的合规检查规则"""
        ...
    
    @abstractmethod
    def get_industry_keywords(self) -> dict:
        """返回行业关键词、标准、评分要点"""
        ...
    
    @abstractmethod
    def get_quotation_engine(self) -> QuotationEngine | None:
        """返回报价引擎（部分行业无报价）"""
        ...
    
    @abstractmethod
    def get_enterprise_fields(self) -> list[FieldDef]:
        """返回行业特定的企业扩展字段定义"""
        ...
    
    @abstractmethod
    def get_credential_types(self) -> list[CredentialTypeDef]:
        """返回行业相关的资质类型"""
        ...
    
    @abstractmethod
    def get_domain_prompts(self) -> dict[str, str]:
        """返回章节→领域 Prompt 映射"""
        ...
```

#### 2.2 实现两个行业插件

**食材配送插件（从鲜标提取）：**

| 文件 | 内容 |
|------|------|
| `backend/app/plugins/fresh_food/plugin.py` | `FreshFoodPlugin(IndustryPlugin)` 实现类 |
| `backend/app/plugins/fresh_food/chapter_templates.json` | 9 章模板 (from bid_chapter_engine.py) |
| `backend/app/plugins/fresh_food/quotation_engine.py` | 6 品类报价引擎 (from bid_quotation_service.py) |
| `backend/app/plugins/fresh_food/compliance_rules.yaml` | 食品安全合规规则 |
| `backend/app/plugins/fresh_food/keywords.json` | 食材配送关键词 |
| `backend/app/plugins/fresh_food/prompts.yaml` | 冷链/配送/食品安全等领域 Prompt |

**建筑工程插件（从标标提取）：**

| 文件 | 内容 |
|------|------|
| `backend/app/plugins/construction/plugin.py` | `ConstructionPlugin(IndustryPlugin)` 实现类 |
| `backend/app/plugins/construction/chapter_templates.json` | 评分驱动模板 |
| `backend/app/plugins/construction/craft_tree.json` | 工艺知识树 (from seed data) |
| `backend/app/plugins/construction/compliance_rules.yaml` | 建筑工程合规规则 |
| `backend/app/plugins/construction/keywords.json` | industry_keywords.json |
| `backend/app/plugins/construction/prompts.yaml` | 施工组织/质量管理等 Prompt |

#### 2.3 改造核心服务使用插件

```python
# 改造前（硬编码食材配送）
class BidGenerationService:
    def _get_domain_requirements(self, chapter_title):
        if "冷链" in chapter_title:
            return "冷链运输温度控制在2-8℃..."

# 改造后（插件化）
class BidGenerationService:
    def __init__(self, session, industry_plugin: IndustryPlugin):
        self.plugin = industry_plugin
    
    def _get_domain_requirements(self, chapter_title):
        return self.plugin.get_domain_prompts().get(chapter_title, "")
```

需要改造的核心服务：

| 服务 | 改造点 |
|------|--------|
| `bid_generation_service.py` | 章节模板、领域 Prompt、RAG 检索过滤 |
| `bid_compliance_service.py` | 合规规则来源从插件加载 |
| `bid_quotation_service.py` | 报价引擎由插件提供（食材有报价，建筑可能用工程量清单） |
| `bid_chapter_engine.py` | 章节结构由插件定义 |
| `capability_graph_service.py` | 企业能力维度由插件定义 |
| `tender_aggregator_service.py` | 关键词过滤由插件提供 |
| `bid_doc_exporter.py` | 文档格式由插件可选定制（中文编号格式等） |

#### 2.4 数据库适配

```sql
-- bid_project 表增加行业字段
ALTER TABLE bid_project ADD COLUMN industry_code VARCHAR(50) DEFAULT 'fresh_food';

-- enterprise 表拆分行业特定字段到 JSONB
ALTER TABLE enterprise ADD COLUMN industry_data JSONB DEFAULT '{}';
-- 食材: {"cold_chain_vehicles": 5, "warehouse_area": 200, "cold_storage_temp": "2-8℃"}
-- 建筑: {"safety_permit": "xxx", "qualification_level": "一级", "registered_capital": 5000}
```

#### Phase 2 验收标准

- [ ] 同一套代码，切换 `industry_code=fresh_food` 生成食材配送投标书
- [ ] 切换 `industry_code=construction` 生成建筑工程投标书
- [ ] 两个行业的合规检查规则不同
- [ ] 新增行业只需写一个 Plugin 类 + 配置文件，不改核心代码

---

### Phase 3：前端统一 + 评分驱动目录（第 5-6 周）

**目标：前端工作台融合 + 评分驱动 + 变体引擎**

#### 3.1 移植评分点提取

标标的核心优势 — 从招标文件自动提取评分标准，驱动目录生成。

| 文件 | 动作 |
|------|------|
| `backend/app/services/scoring_extract_service.py` | **新建** — 从标标移植评分点提取逻辑 |
| `backend/app/api/v1/scoring.py` | **新建** — `POST /scoring/extract` + `POST /scoring/outline` |
| 前端评分提取页面 | **新建** — 上传招标文件 → 显示提取的评分项 → 生成目录 |

对接鲜标的 `TenderRequirement` 模型：

```python
# 提取结果 → 自动写入 TenderRequirement
for item in extracted_scoring_points:
    req = TenderRequirement(
        bid_project_id=project_id,
        category="scoring",
        content=item["description"],
        max_score=item["max_score"],
        score_weight=item["weight"],
    )
```

#### 3.2 移植变体生成引擎

| 文件 | 动作 |
|------|------|
| `backend/app/services/variant_service.py` | **新建** — 从标标移植 |
| `backend/app/api/v1/variant.py` | **新建** — 生成/列表/相似度矩阵 |
| 前端变体对比页 | **新建** — 相似度热力图 |

#### 3.3 前端工作台融合

```
合并后的项目工作台:

  Dashboard
    ├── 商机漏斗 (鲜标)
    ├── 项目列表 (鲜标)
    └── 项目工作台 (合并后的 7 步流程)
         ├── Step 1: 项目信息 + 上传招标文件 (鲜标)
         ├── Step 2: 评分点提取 + 需求解析 (标标)
         ├── Step 3: 目录大纲生成 (标标)
         ├── Step 4: AI 章节生成 (7节点流水线)
         │    ├── 实时进度 (Node 1-7 状态展示)
         │    ├── 章节编辑器 + AI 对话 (鲜标)
         │    └── 合规检查 + 润色 (标标)
         ├── Step 5: 报价管理 (鲜标，行业插件化)
         ├── Step 6: 风险报告 + 反AI检测 (合并)
         └── Step 7: 导出 + 变体对比 (标标)
```

#### Phase 3 验收标准

- [ ] 前端工作台 7 步流程完整可用
- [ ] 评分点提取 → 目录生成 → 章节生成全链路打通
- [ ] 变体生成 + 相似度矩阵展示正常
- [ ] 反 AI 检测页面可用

---

### Phase 4：新行业验证 + 稳定化（第 7-8 周）

**目标：用第三个行业验证框架通用性**

#### 4.1 新增第三个行业插件（候选：IT 服务 / 物业管理）

| 任务 | 说明 |
|------|------|
| 编写 `ITServicePlugin` | 章节模板(技术方案/人员配置/SLA/应急预案)、资质类型(CMMI/ISO27001)、关键词 |
| 编写 Prompt | IT 服务领域的专业 Prompt |
| 编写合规规则 | IT 投标的废标项/资格要求 |
| 测试验证 | 用真实 IT 招标文件走通全流程 |

#### 4.2 验证检查清单

- [ ] 新行业插件开发不需要修改核心引擎代码
- [ ] 章节模板、合规规则、关键词通过配置文件即可定义
- [ ] 评分点提取 Prompt 适配新行业
- [ ] 报价引擎可选（IT 服务用人天报价）
- [ ] 文档导出格式正确

#### 4.3 性能 + 稳定性

| 任务 | 说明 |
|------|------|
| 7 节点流水线超时处理 | 单节点超时 30s，整体超时 180s，优雅降级 |
| LLM 并发控制 | 信号量控制同时生成的章节数 |
| 错误恢复 | 某个节点失败后可从断点重试 |
| LangFuse 集成 | 从标标移植，全链路追踪 |
| 回归测试 | 食材配送 + 建筑工程 + 新行业三个场景 E2E |

---

## 六、整体时间线

```
Week 1        Week 2-3           Week 4-5              Week 5-6           Week 7-8
┌─────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐   ┌───────────┐
│ P0  │──▶│     P1       │──▶│      P2         │──▶│     P3       │──▶│    P4     │
│准备 │   │ 引擎层移植    │   │ 行业插件化抽象   │   │ 前端+评分驱动 │   │ 新行业验证 │
│环境 │   │ 7节点流水线   │   │ 2个行业插件     │   │ 工作台融合    │   │ 稳定化    │
│清理 │   │ 反AI+脱敏     │   │ 核心服务改造    │   │ 变体引擎     │   │ E2E测试   │
└─────┘   └──────────────┘   └─────────────────┘   └──────────────┘   └───────────┘
```

---

## 七、通用框架最终架构

```
┌─────────────────────────────────────────────────────────────┐
│                通用投标 AI 框架 (BidEngine)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  行业插件注册  │  │  知识库插件   │  │   报价插件    │       │
│  │  (Industry)   │  │  (Knowledge) │  │   (Quote)    │       │
│  │ - 食材配送    │  │ - 法规标准    │  │ - 品类定价    │       │
│  │ - 建筑工程    │  │ - 工艺方法    │  │ - 工程量清单  │       │
│  │ - IT 服务     │  │ - 行业规范    │  │ - 人天报价    │       │
│  │ - 医疗器械    │  │ - 案例库      │  │ - 服务费      │       │
│  │ - 物业管理    │  │              │  │              │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│  ┌──────▼─────────────────▼──────────────────▼──────────┐   │
│  │                  核心引擎层（行业无关）                  │   │
│  │                                                       │   │
│  │  🔄 7 节点生成流水线 (Planner→...→Formatter)           │   │
│  │  📊 评分点提取 + 驱动目录生成                           │   │
│  │  🔍 3 层 RAG 检索 (向量+结构+融合)                     │   │
│  │  ✅ 3 级合规审查 (格式+语义+废标)                       │   │
│  │  💎 5 级润色引擎 (术语→文风→逻辑→专业→亮点)            │   │
│  │  🛡️ 反 AI 检测 + 数据脱敏                              │   │
│  │  📈 变体生成引擎 (多维防撞标)                           │   │
│  │  🎯 商机漏斗 + AI 匹配分析                             │   │
│  │  🏢 企业能力画像                                       │   │
│  │  🤖 AI Tool Calling 路由                               │   │
│  │  💬 反馈飞轮 → SFT 数据积累                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  基础设施层（不变）                      │   │
│  │  Auth(JWT) │ Multi-Tenant │ LLM Selector(4供应商)     │   │
│  │  Prompt Registry │ Embedding │ DocExport(Word)        │   │
│  │  Billing │ Audit │ Storage │ LangFuse                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 八、关键技术对照表

### LLM 路由改造对照

| 任务 | 鲜标当前 | 标标当前 | 合并后 |
|------|---------|---------|--------|
| 章节生成 | `bid_section_generate` | `bid_generate` | `bid_generate` |
| 合规检查 | `compliance_check` | `compliance_check` | `compliance_check` |
| 润色 | ❌ 无 | `polish` | `polish` |
| 评分提取 | ❌ 无 | `bid_extract` | `bid_extract` |
| 目录生成 | ❌ 无 | `bid_outline` | `bid_outline` |
| 反AI改写 | ❌ 无 | `anti_rewrite` | `anti_rewrite` |
| 脱敏识别 | ❌ 无 | `desensitize` | `desensitize` |
| 对话聊天 | `chat` | `bid_chat` | `chat` |
| 向量化 | `embedding` | `embedding` | `embedding` |
| 招标解析 | `tender_parse` | ❌ 无 | `tender_parse` |
| 商机匹配 | `tender_match_analysis` | ❌ 无 | `tender_match_analysis` |
| Tool路由 | `tool_calling` | ❌ 无 | `tool_calling` |

### 数据库改造对照

| 表 | 鲜标 | 标标 | 合并后 |
|----|------|------|--------|
| 项目 | `bid_project` (Int PK) | `projects` (UUID PK) | `bid_project` + `industry_code` 字段 |
| 章节 | `bid_chapter` (结构化) | JSONB `generated_sections` | `bid_chapter`（保留结构化） |
| 需求 | `tender_requirement` | ❌ 无 | `tender_requirement`（保留） |
| 企业 | `enterprise` (食材字段) | ❌ 无(User.company) | `enterprise` + `industry_data` JSONB |
| 资质 | `credential` (15类) | ❌ 无 | `credential`（保留，类型由插件定义） |
| 用户 | `sys_user` + `sys_role` | `users` (含tenant) | `sys_user`（保留） |
| 脱敏 | ❌ 无 | `desensitize_dict` | **新增** `desensitize_dict` |
| 商机 | `tender_notice` | ❌ 无 | `tender_notice`（保留） |
| 知识 | `std_clause` + `chapter_snippet` + `bid_case` | `training_chunks` + `structured_tables` | 全部保留，按行业 namespace 隔离 |

---

## 九、风险与应对

| 风险 | 等级 | 应对策略 |
|------|------|---------|
| 7 节点流水线移植后，与鲜标数据模型不兼容 | **高** | P1 先做最小可用版（3 节点：Writer+Compliance+Polish），逐步加节点 |
| 行业 Prompt 编写需要领域专家 | **高** | 先用 AI 生成初版 Prompt，再用真实招标文件迭代调优 |
| 前端工作台改动量大 | **中** | P3 可以先不改前端，后端先跑通 |
| 两个项目的 Alembic 迁移冲突 | **低** | P0 统一到一个迁移线，手动合并 |
| 新行业插件的合规规则难以穷举 | **中** | 规则引擎 + LLM 兜底：先走规则，规则未覆盖的走 LLM 语义判断 |

---

## 十、待讨论事项

1. **新仓库命名** — `bid-engine` / `smart-bid` / 其他？
2. **第三个验证行业** — IT 服务 / 物业管理 / 医疗器械？
3. **时间节奏** — 8 周是否合理？是否需要压缩或分期？
4. **是否优先做原型验证** — 先在鲜标上跑通 3 节点流水线（Writer+Compliance+Polish）验证可行性？
5. **团队分工** — 前后端是否需要并行开发？
