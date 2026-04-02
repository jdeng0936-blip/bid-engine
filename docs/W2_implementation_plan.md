# W2 实施计划：风险报告 + 支付 + 导出确认 + Prompt优化

> **用途**: 提供给 IDE Agent（Claude Code / Antigravity）直接执行
> **前置条件**: W1 已完成（注册/RBAC/HTTPS/合规清理/Embedding重建）
> **时间**: 5个工作日
> **交付物**: 完整的「付费→生成→检查→确认→导出」商业闭环

---

## 执行总览

| 天 | 主题 | 交付验收物 |
|---|---|---|
| D1 | 风险报告服务——后端核心 | `risk_report_service.py` + 3类检查逻辑 + API + 测试 |
| D2 | 风险报告——前端面板 + 跳转定位 | RiskReportPanel组件 + 章节跳转 + 修复状态追踪 |
| D3 | 支付集成——后端 | 数据模型 + 支付服务 + API + Alembic迁移 |
| D4 | 支付集成——前端 + 导出前确认机制 | 计费页面 + ExportConfirmDialog + 水印逻辑 |
| D5 | 废标Prompt优化 + 联调测试 + 验收 | Prompt更新 + 端到端测试 + 全部验收项通过 |

---

## D1：风险报告服务——后端核心

### 任务 1.1：新建 `risk_report_service.py`

**文件路径**: `backend/app/services/risk_report_service.py`

**前置查阅**（Agent 必须先执行）:
```bash
# 理解现有合规检查能力
view_file backend/app/services/ai_router.py  # 找 compliance_scan 和 check_credentials Tool 定义
view_file backend/app/models/bid_project.py   # 理解 tender_requirement / bid_chapter 表结构
view_file backend/app/models/credential.py    # 理解 credential 表结构
view_file backend/app/models/enterprise.py    # 理解 enterprise 表字段
```

**核心类设计**:

```python
# backend/app/services/risk_report_service.py

from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RiskLevel(str, Enum):
    FATAL = "fatal"       # 红色 — 必定或极大概率废标，阻断导出
    CRITICAL = "critical"  # 橙色 — 极可能失分，强烈建议修改
    WARNING = "warning"    # 黄色 — 优化建议，不阻断

class RiskItem(BaseModel):
    """单个风险项"""
    id: str                          # 唯一标识，如 "DATA_CONSISTENCY_001"
    level: RiskLevel
    category: str                    # 检查类别: "data_consistency" | "qualification" | "scoring_coverage" | "disqualification"
    title: str                       # 简短标题，如 "车辆数量前后不一致"
    description: str                 # 详细描述
    chapter_id: Optional[str]        # 关联的 bid_chapter.id，用于前端跳转定位
    chapter_title: Optional[str]     # 章节标题，便于展示
    field_name: Optional[str]        # 涉及的字段名
    expected_value: Optional[str]    # 企业资料库中的值
    actual_value: Optional[str]      # 标书中出现的值
    suggestion: str                  # 修复建议
    is_resolved: bool = False        # 是否已标记修复

class RiskReport(BaseModel):
    """完整风险报告"""
    bid_project_id: str
    generated_at: datetime
    total_items: int
    fatal_count: int
    critical_count: int
    warning_count: int
    items: list[RiskItem]
    can_export: bool                 # fatal_count == 0 时为 True
    
class RiskReportService:
    """
    风险报告生成服务
    
    三类检查按顺序执行:
    1. 数据一致性检查 — 标书正文数字 vs enterprise/credential 表
    2. 资质覆盖与有效期检查 — credential 表 vs tender_requirement
    3. 评分响应覆盖检查 — 评分矩阵子项 vs bid_chapter 内容
    """
    
    def __init__(self, db_session, tenant_id: str):
        self.db = db_session
        self.tenant_id = tenant_id
    
    async def generate_report(self, bid_project_id: str) -> RiskReport:
        """生成完整风险报告 — 主入口"""
        # 1. 加载项目数据
        # 2. 执行三类检查
        # 3. 汇总生成报告
        pass
    
    async def _check_data_consistency(self, project, chapters, enterprise) -> list[RiskItem]:
        """
        检查一：数据一致性
        
        必检字段:
        - 企业名称（全文统一性）
        - 项目名称（全文统一性）
        - 车辆数量（正文 vs enterprise.vehicle_count 或 enterprise.vehicles JSON）
        - 人员数量（正文 vs enterprise 相关字段）
        - 仓储面积（正文 vs enterprise.warehouse_area）
        - 资质编号（正文中出现的编号 vs credential 表）
        
        实现方式:
        - 用正则从 chapter.content 中提取数字+上下文
        - 与 enterprise 表结构化字段比对
        - 不一致的生成 RiskItem(level=FATAL)
        """
        pass
    
    async def _check_qualifications(self, project, credentials, tender_requirements) -> list[RiskItem]:
        """
        检查二：资质覆盖与有效期
        
        逻辑:
        - 从 tender_requirement 中提取资格要求列表
        - 逐条比对 credential 表中企业已有资质
        - 缺失的资质 → FATAL
        - 30天内过期的资质 → WARNING
        - 已过期的资质 → FATAL
        - 投标截止日前过期的 → FATAL
        
        注意: 投标截止日从 bid_project.deadline 获取
        """
        pass
    
    async def _check_scoring_coverage(self, project, chapters, scoring_matrix) -> list[RiskItem]:
        """
        检查三：评分响应覆盖
        
        逻辑:
        - 从 tender_requirement 中提取评分矩阵（scoring_matrix JSON字段）
        - 拆解为评分子项列表
        - 对每个子项，在对应章节内容中搜索关键词/语义匹配
        - 未找到响应内容的子项:
          - 权重>=10分的子项漏答 → CRITICAL
          - 废标类评分项漏答 → FATAL
          - 其他子项漏答 → WARNING
        
        实现方式（MVP简化版）:
        - 关键词匹配为主（从评分子项描述中提取关键词）
        - 不用向量相似度（Phase 2再升级）
        """
        pass
```

**关键约束**:
- 所有数据库查询必须带 `tenant_id` 过滤
- 不调用 LLM（风险检查是规则+数据比对，不依赖大模型）
- RiskItem 的 `chapter_id` 必须填写，前端需要用它做跳转

### 任务 1.2：新建风险报告 API

**文件路径**: `backend/app/api/v1/risk_report.py`

```python
# backend/app/api/v1/risk_report.py

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, get_db, get_tenant_id
from app.services.risk_report_service import RiskReportService, RiskReport

router = APIRouter(prefix="/bid-projects/{project_id}/risk", tags=["风险检查"])

@router.post("/check", response_model=RiskReport)
async def run_risk_check(
    project_id: str,
    db=Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user=Depends(get_current_user),
):
    """触发风险检查，返回完整报告"""
    service = RiskReportService(db, tenant_id)
    return await service.generate_report(project_id)

@router.get("/report", response_model=RiskReport)
async def get_risk_report(
    project_id: str,
    db=Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user=Depends(get_current_user),
):
    """获取最近一次风险报告（缓存在DB或内存中）"""
    # 从缓存或DB获取
    pass

@router.put("/items/{item_id}/resolve")
async def resolve_risk_item(
    project_id: str,
    item_id: str,
    db=Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user=Depends(get_current_user),
):
    """标记风险项为已修复"""
    # 更新 is_resolved = True
    # 重新计算 can_export
    pass

@router.post("/export-check")
async def check_export_readiness(
    project_id: str,
    db=Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user=Depends(get_current_user),
):
    """检查是否满足导出前置条件"""
    # 1. Fatal项是否全部resolved
    # 2. 高风险字段是否已确认（从前端传入确认状态）
    # 返回 { can_export: bool, blocking_reasons: [...] }
    pass
```

**路由注册**: 在 `app/main.py` 中注册该 router。

**前置查阅**:
```bash
# 查看现有路由注册方式
grep_search "include_router" backend/app/main.py
# 查看现有依赖注入写法
view_file backend/app/core/deps.py
```

### 任务 1.3：测试用例

**文件路径**: `backend/tests/test_risk_report.py`

```python
# backend/tests/test_risk_report.py

import pytest
from app.services.risk_report_service import RiskReportService, RiskLevel

class TestDataConsistency:
    """数据一致性检查测试"""
    
    async def test_vehicle_count_mismatch(self):
        """正文写30辆，enterprise表记录20辆 → 应产生FATAL"""
        # 构造测试数据: enterprise.vehicle_count=20, chapter.content包含"30辆冷链车"
        # 执行检查
        # 断言: 结果中有level=FATAL的RiskItem, field_name="vehicle_count"
        pass
    
    async def test_company_name_inconsistent(self):
        """不同章节企业名称不一致 → 应产生FATAL"""
        pass
    
    async def test_credential_number_mismatch(self):
        """正文中的资质编号与credential表不一致 → 应产生FATAL"""
        pass
    
    async def test_all_consistent(self):
        """所有数据一致 → 不应产生任何FATAL"""
        pass

class TestQualificationCheck:
    """资质覆盖与有效期检查测试"""
    
    async def test_missing_required_credential(self):
        """招标要求食品经营许可证但企业未上传 → FATAL"""
        pass
    
    async def test_expired_credential(self):
        """资质已过期 → FATAL"""
        pass
    
    async def test_expiring_soon_credential(self):
        """资质30天内过期 → WARNING"""
        pass
    
    async def test_all_credentials_valid(self):
        """全部资质齐全且在有效期 → 无风险项"""
        pass

class TestScoringCoverage:
    """评分响应覆盖检查测试"""
    
    async def test_high_weight_item_missing(self):
        """权重>=10分的评分项未响应 → CRITICAL"""
        pass
    
    async def test_disqualification_item_missing(self):
        """废标类评分项未响应 → FATAL"""
        pass
    
    async def test_low_weight_item_missing(self):
        """低权重评分项未响应 → WARNING"""
        pass
    
    async def test_full_coverage(self):
        """所有评分项都有响应 → can_export=True"""
        pass

class TestExportReadiness:
    """导出前置条件检查"""
    
    async def test_has_unresolved_fatal(self):
        """存在未修复Fatal → can_export=False"""
        pass
    
    async def test_all_fatal_resolved(self):
        """所有Fatal已修复 → can_export=True"""
        pass
```

### D1 验收标准

- [ ] `risk_report_service.py` 文件存在且包含三类检查方法
- [ ] `risk_report.py` API 路由已注册并可访问
- [ ] 数据一致性检查：能检出车辆数/人员数/企业名前后不一致（至少3种场景）
- [ ] 资质检查：能检出缺失资质、过期资质、即将过期资质
- [ ] 评分覆盖：能检出漏答的评分子项并按权重分级
- [ ] `can_export` 在有FATAL时为False，FATAL全清后为True
- [ ] pytest 测试全部通过（≥12个用例）
- [ ] 所有查询带 `tenant_id` 过滤

---

## D2：风险报告——前端面板 + 跳转定位

### 任务 2.1：新建 RiskReportPanel 组件

**文件路径**: `frontend/src/components/business/risk-report-panel.tsx`

**前置查阅**:
```bash
# 理解现有组件风格
view_file frontend/src/components/business/markdown-editor.tsx
# 理解API调用方式
view_file frontend/src/lib/api.ts
# 理解现有项目详情页结构
view_file frontend/src/app/dashboard/bid-projects/[id]/page.tsx
```

**组件设计**:

```typescript
// frontend/src/components/business/risk-report-panel.tsx

interface RiskItem {
  id: string;
  level: 'fatal' | 'critical' | 'warning';
  category: string;
  title: string;
  description: string;
  chapter_id: string | null;
  chapter_title: string | null;
  field_name: string | null;
  expected_value: string | null;
  actual_value: string | null;
  suggestion: string;
  is_resolved: boolean;
}

interface RiskReport {
  bid_project_id: string;
  generated_at: string;
  total_items: number;
  fatal_count: number;
  critical_count: number;
  warning_count: number;
  items: RiskItem[];
  can_export: boolean;
}

// 组件功能:
// 1. 顶部统计栏: Fatal(红) / Critical(橙) / Warning(黄) 数量卡片
// 2. 风险项列表: 按级别排序（Fatal在前），每项显示:
//    - 左侧: 级别色标（红/橙/黄竖条）
//    - 标题 + 描述
//    - 期望值 vs 实际值（如果有）
//    - 「跳转到章节」按钮（chapter_id 不为空时显示）
//    - 「标记已修复」按钮 → 调用 PUT /risk/items/{id}/resolve
// 3. 底部: 「重新检查」按钮 → 调用 POST /risk/check
// 4. 导出状态: can_export 为 true 时显示绿色「可以导出」，false 时显示红色「存在未修复的致命问题」

// UI 规范:
// - 使用 shadcn Card, Badge, Button, Alert 组件
// - Fatal: bg-red-50 border-red-500
// - Critical: bg-orange-50 border-orange-500  
// - Warning: bg-yellow-50 border-yellow-500
// - 已修复项: 灰色背景 + 删除线标题
```

### 任务 2.2：风险报告页面

**文件路径**: `frontend/src/app/dashboard/bid-projects/[id]/risk-report/page.tsx`

```typescript
// 页面结构:
// 1. 页面标题: "投标文件风险检查"
// 2. 「开始检查」按钮 (首次) / 「重新检查」按钮 (已有报告)
// 3. 检查中: Loading 动画 + "正在检查数据一致性..." / "正在核验资质..." / "正在检查评分覆盖..."
// 4. 检查完成: 渲染 RiskReportPanel
// 5. 侧边导航: 添加到项目详情的 Tab 导航中

// API 调用:
// POST /api/v1/bid-projects/{id}/risk/check  → 触发检查
// GET  /api/v1/bid-projects/{id}/risk/report  → 获取报告
// PUT  /api/v1/bid-projects/{id}/risk/items/{rid}/resolve → 标记修复
```

### 任务 2.3：章节跳转定位

**改造文件**: `frontend/src/app/dashboard/bid-projects/[id]/chapters/page.tsx`

```typescript
// 改造内容:
// 1. 接收 URL 参数 ?highlight=chapter_id
// 2. 页面加载时如果有 highlight 参数:
//    - 自动滚动到对应章节
//    - 该章节卡片添加红色/橙色边框高亮（根据风险级别）
//    - 3秒后高亮自动淡出
// 3. RiskReportPanel 中的「跳转到章节」按钮:
//    - 路由到 /dashboard/bid-projects/{id}/chapters?highlight={chapter_id}
```

### D2 验收标准

- [ ] RiskReportPanel 组件渲染三种级别风险项，样式正确
- [ ] 统计栏显示 Fatal/Critical/Warning 数量
- [ ] 「跳转到章节」按钮可导航到章节编辑页并高亮定位
- [ ] 「标记已修复」按钮调用 API 后更新 UI 状态
- [ ] 「重新检查」按钮重新触发检查并刷新报告
- [ ] can_export 状态正确展示（绿色/红色）

---

## D3：支付集成——后端

### 任务 3.1：支付数据模型 + Alembic 迁移

**文件路径**: `backend/app/models/payment.py`

```python
# backend/app/models/payment.py

from app.models.base import Base, AuditMixin
from sqlalchemy import Column, String, Enum, Numeric, DateTime, Integer, ForeignKey, Text
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"

class SubscriptionType(str, enum.Enum):
    FREE_TRIAL = "free_trial"    # 免费试用（1篇带水印）
    PER_DOCUMENT = "per_document" # 按篇付费 ¥199
    QUARTERLY = "quarterly"       # 季度包 ¥999/10篇
    YEARLY = "yearly"             # 年度包 ¥2988/不限

class Order(Base, AuditMixin):
    """订单表"""
    __tablename__ = "order"
    
    # 基础字段
    order_no = Column(String(64), unique=True, nullable=False, comment="订单号")
    user_id = Column(String(36), ForeignKey("sys_user.id"), nullable=False)
    
    # 订单内容
    order_type = Column(String(32), nullable=False, comment="per_document|quarterly|yearly")
    amount = Column(Numeric(10, 2), nullable=False, comment="订单金额（元）")
    quantity = Column(Integer, default=1, comment="数量（按篇付费时为1）")
    
    # 支付信息
    payment_method = Column(String(32), comment="alipay|wechat")
    payment_trade_no = Column(String(128), comment="第三方支付交易号")
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    paid_at = Column(DateTime, comment="支付完成时间")
    
    # 备注
    remark = Column(Text, comment="备注")

class Subscription(Base, AuditMixin):
    """订阅/用量表 — 每个租户一条记录"""
    __tablename__ = "subscription"
    
    # tenant_id 通过 AuditMixin 注入
    plan_type = Column(Enum(SubscriptionType), default=SubscriptionType.FREE_TRIAL)
    
    # 用量追踪
    total_quota = Column(Integer, default=1, comment="总配额（免费试用=1）")
    used_count = Column(Integer, default=0, comment="已使用次数")
    
    # 有效期
    start_date = Column(DateTime, comment="订阅开始时间")
    end_date = Column(DateTime, comment="订阅到期时间")
    
    @property
    def remaining_quota(self) -> int:
        if self.plan_type == SubscriptionType.YEARLY:
            return 999999  # 不限
        return max(0, self.total_quota - self.used_count)
    
    @property
    def is_active(self) -> bool:
        from datetime import datetime
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return self.remaining_quota > 0
```

**Alembic 迁移**: 
```bash
# 在 backend/ 目录下执行
cd backend
alembic revision --autogenerate -m "add_payment_tables"
# 检查生成的迁移文件
# 确认 upgrade() 包含 create_table("order") 和 create_table("subscription")
# 确认 downgrade() 包含 drop_table
alembic upgrade head
```

### 任务 3.2：支付服务

**文件路径**: `backend/app/services/payment_service.py`

```python
# backend/app/services/payment_service.py

class PaymentService:
    """
    支付服务
    
    MVP阶段支付策略:
    - 支付宝/微信支付（如果商户号已审批通过）
    - 如果商户号未到位: 提供手动转账+人工开通的备用方案
    
    核心流程:
    1. create_order() → 创建订单 + 生成支付链接/二维码
    2. handle_callback() → 支付回调验证 + 更新订单状态 + 开通权限
    3. check_quota() → 检查当前租户是否有剩余配额
    4. consume_quota() → 生成一次标书时扣减配额
    """
    
    def __init__(self, db_session, tenant_id: str):
        self.db = db_session
        self.tenant_id = tenant_id
    
    async def create_order(self, order_type: str, payment_method: str) -> dict:
        """创建支付订单"""
        # 1. 根据 order_type 确定金额
        # 2. 生成唯一 order_no
        # 3. 调用支付宝/微信创建预付单（或返回手动转账信息）
        # 4. 写入 Order 表
        # 5. 返回 { order_no, payment_url, amount }
        pass
    
    async def handle_callback(self, payment_data: dict) -> bool:
        """处理支付回调"""
        # 1. 验证签名
        # 2. 更新 Order 状态为 PAID
        # 3. 更新 Subscription: 增加配额/延长有效期
        # 4. 写审计日志
        pass
    
    async def check_quota(self) -> dict:
        """检查当前租户配额"""
        # 返回 { plan_type, remaining_quota, is_active, end_date }
        pass
    
    async def consume_quota(self) -> bool:
        """消耗一次配额（在标书生成时调用）"""
        # 1. 检查是否有剩余配额
        # 2. used_count += 1
        # 3. 返回是否成功
        pass
    
    async def is_free_trial_used(self) -> bool:
        """检查是否已使用免费试用"""
        pass
```

### 任务 3.3：支付 API

**文件路径**: `backend/app/api/v1/payment.py`

```python
# 核心端点:
# POST /api/v1/payments/create-order     → 创建订单
# POST /api/v1/payments/callback/alipay  → 支付宝回调
# POST /api/v1/payments/callback/wechat  → 微信支付回调
# GET  /api/v1/subscriptions/current     → 当前订阅状态
# GET  /api/v1/usage/summary             → 用量统计
```

### 任务 3.4：标书生成接入配额检查

**改造文件**: `backend/app/services/bid_generation_service.py`

```python
# 在生成入口方法中增加配额检查:
# 1. 调用 PaymentService.check_quota()
# 2. 如果无配额 → 返回 HTTP 402 (Payment Required)
# 3. 生成成功后调用 PaymentService.consume_quota()
# 4. 免费试用标记: 如果是 FREE_TRIAL，在生成结果中标记 is_trial=True（后续导出时加水印）
```

**前置查阅**:
```bash
view_file backend/app/services/bid_generation_service.py  # 找到生成入口方法
grep_search "async def generate" backend/app/services/bid_generation_service.py
```

### D3 验收标准

- [ ] Alembic 迁移成功执行，order + subscription 表已创建
- [ ] 新建表继承 AuditMixin（含 tenant_id）
- [ ] 免费试用用户首次可生成1篇，第二次返回 402
- [ ] 按篇付费/订阅用户配额正确扣减
- [ ] 支付回调后 Subscription 配额正确更新
- [ ] downgrade() 可正确回滚（删除表）

---

## D4：支付前端 + 导出前确认机制

### 任务 4.1：计费中心页面

**文件路径**: `frontend/src/app/dashboard/billing/page.tsx`

```typescript
// 页面结构:
// 1. 当前套餐状态卡片: 套餐类型 + 剩余配额 + 到期时间
// 2. 套餐选择: 4个定价卡片（免费试用/按篇¥199/季度¥999/年度¥2988）
// 3. 支付方式选择: 支付宝 / 微信支付
// 4. 支付确认弹窗 → 跳转支付 → 回调成功页

// API:
// GET  /api/v1/subscriptions/current → 当前状态
// POST /api/v1/payments/create-order → 创建订单
```

### 任务 4.2：导出前确认弹窗（ExportConfirmDialog）

**文件路径**: `frontend/src/components/business/export-confirm-dialog.tsx`

```typescript
// ExportConfirmDialog 组件设计
// 
// 触发条件: 用户点击「导出Word」按钮时弹出
// 
// 弹窗内容（4步确认）:
//
// Step 1: 风险检查状态
// - 显示: Fatal X项 / Critical Y项 / Warning Z项
// - 如果 Fatal > 0: 红色警告「存在X个致命问题未修复，无法导出」+ 「前往修复」按钮
// - 如果 Fatal == 0: 绿色「致命问题已全部修复 ✓」
//
// Step 2: 高风险字段人工确认（5类，逐项勾选）
// - [ ] 资质证书编号与有效期（展示引用的资质列表）
// - [ ] 业绩案例信息（展示引用的案例）
// - [ ] 关键承诺指标（展示量化承诺列表）
// - [ ] 人员信息（展示关键人员）
// - [ ] 车辆/设备数据（展示车辆清单）
// - [ ] 报价表结构与填报责任（确认报价由企业自行填写/复核）
// 全部勾选才能进入下一步
//
// Step 3: 免责声明
// - 「本文档为AI辅助生成首稿，最终提交前请自行审核全部内容。
//   鲜标通不对标书内容的真实性和最终投标结果承担法律责任。」
// - [ ] 我已阅读并同意
//
// Step 4: 导出格式选择
// - Word (.docx) [默认]
// - PDF (.pdf) [如果已实现]
// - Word + PDF 打包 (.zip)
//
// 按钮: 「确认导出」（4步全部完成后可点击）
//
// API调用:
// 1. 弹窗打开时: GET /risk/report 获取最新风险状态
// 2. 确认导出时: POST /export-check 服务端二次校验 → POST /export/word 下载
// 3. 确认记录写入 audit_log
```

### 任务 4.3：水印逻辑

**改造文件**: `backend/app/services/bid_doc_exporter.py`

```python
# 在 _render_docx() 方法中增加水印参数:
#
# def _render_docx(self, ..., is_trial: bool = False):
#     ...
#     if is_trial:
#         # 在每页添加斜体灰色水印文字「鲜标通试用版 — 付费后去除水印」
#         # 使用 python-docx 的 Header 区域添加水印效果
#         # 或在每个 section 的 header 中加入浅灰色大字
#     ...
#
# 注意: 增量注入，默认 is_trial=False 不影响现有逻辑
```

**前置查阅**:
```bash
view_file backend/app/services/bid_doc_exporter.py  # 找到 _render_docx 方法签名
grep_search "_render_docx" backend/app/services/bid_doc_exporter.py
```

### D4 验收标准

- [ ] 计费页面正确展示当前套餐和剩余配额
- [ ] 导出确认弹窗完整展示4步确认流程
- [ ] Fatal未清零时「确认导出」按钮禁用
- [ ] 6类高风险字段必须全部勾选确认
- [ ] 免责声明必须勾选
- [ ] 确认操作写入 audit_log
- [ ] 免费试用文档带水印，付费文档无水印
- [ ] 水印逻辑为增量注入，`is_trial=False` 时行为与原来完全一致

---

## D5：Prompt优化 + 联调测试 + 验收

### 任务 5.1：废标条款识别增强

**改造文件**: `backend/app/services/tender_parser.py`

```python
# 新增方法: _extract_disqualification_items()
#
# 实现方式: 关键词库 + 否定条件句式双重机制
#
# 关键词库（至少120个短语）:
DISQUALIFICATION_KEYWORDS = [
    "将被否决", "取消投标资格", "不予评审", "视为无效投标",
    "按废标处理", "投标无效", "否决其投标", "不得进入评审",
    "不予受理", "拒绝投标", "取消中标资格", "失去中标资格",
    "不合格投标", "无效标", "废标", "不予通过",
    "不符合资格", "丧失投标资格", "自动放弃", "视为放弃",
    # ... 补充到120+
]
#
# 执行逻辑:
# 1. 在全文中搜索关键词，提取包含关键词的完整句子
# 2. 用简单NLP规则识别否定条件句式（如"如果...则..."、"未...将..."、"不...则..."）
# 3. 两者取并集
# 4. 去重后存入 tender_requirement 表（类型=disqualification）
```

**前置查阅**:
```bash
view_file backend/app/services/tender_parser.py  # 理解现有解析流程
grep_search "disqualif" backend/app/services/tender_parser.py
grep_search "废标" backend/app/services/tender_parser.py
```

### 任务 5.2：评分矩阵解析Prompt优化

**改造文件**: `backend/prompts_registry.yaml`

```yaml
# 在 tender_parse 部分，升级或新增 v2 版本:
#
# tender_parse:
#   v2:
#     description: "招标文件结构化解析 — 评分矩阵精细化版"
#     template: |
#       请解析以下招标文件内容，提取评分标准矩阵。
#       
#       要求输出JSON格式，每个评分项包含:
#       - dimension: 评分维度名称（如"技术方案"）
#       - sub_items: 评分子项列表，每个子项包含:
#         - name: 子项名称（如"冷链运输方案"）
#         - weight: 分值权重（数字）
#         - criteria: 各等级评分标准（如 优秀/良好/一般/较差 分别对应的分值和条件）
#         - keywords: 关键词列表（用于后续响应覆盖检查）
#         - is_mandatory: 是否为必答项（缺失即废标）
#       
#       招标文件内容:
#       {{ tender_content }}
#
# 注意: 保留 v1 不删除，v2 作为新版本
```

**前置查阅**:
```bash
view_file backend/prompts_registry.yaml  # 查看现有 tender_parse 版本
```

### 任务 5.3：端到端联调测试

```bash
# 手工测试流程（用真实或模拟招标文件）:
#
# 1. 创建测试用户 + 企业资料
# 2. 上传一份招标文件 → 确认解析出评分矩阵+废标条款+资格要求
# 3. 启动标书生成 → 确认9章节正常生成
# 4. 执行风险检查 → 确认报告正确（故意制造数据不一致，验证能否检出）
# 5. 在风险报告中点击「跳转」→ 确认跳转到正确章节并高亮
# 6. 修复所有Fatal → 确认can_export变为True
# 7. 点击导出 → 弹出确认弹窗 → 完成4步确认 → 下载Word
# 8. 打开Word → 验证格式正确、内容完整
# 9. 免费用户 → 确认Word带水印
# 10. 付费用户 → 确认Word无水印
```

### D5 验收标准

- [ ] 废标关键词库≥120个短语，能识别常见废标条款
- [ ] 评分矩阵Prompt v2注册成功，输出包含子项+权重+关键词
- [ ] v1 Prompt保留不删除
- [ ] 端到端流程跑通：上传→解析→生成→检查→确认→导出
- [ ] 故意制造的数据不一致被正确检出
- [ ] 免费试用水印正常显示
- [ ] 付费后水印消失

---

## W2 总验收清单

### 功能验收

| # | 验收项 | 通过条件 | 状态 |
|---|---|---|---|
| 1 | 风险报告生成 | 三类检查全部可执行，结果结构化输出 | □ |
| 2 | 数据一致性检查 | 至少能检出5种数据不一致场景 | □ |
| 3 | 资质有效期校验 | 过期=Fatal，30天内=Warning | □ |
| 4 | 评分覆盖检查 | 能检出漏答项并按权重分级 | □ |
| 5 | 风险报告前端面板 | 三级告警展示+跳转+标记修复 | □ |
| 6 | 章节跳转定位 | 点击跳转到正确章节并高亮 | □ |
| 7 | 支付订单创建 | 可生成订单+支付链接（或手动方案） | □ |
| 8 | 配额扣减 | 免费1篇/按篇1篇/季度10篇/年度不限 | □ |
| 9 | 导出前4步确认 | Fatal清零+6类字段确认+免责+格式选择 | □ |
| 10 | 水印逻辑 | 试用版有水印，付费版无水印 | □ |
| 11 | 废标关键词库 | ≥120个短语 | □ |
| 12 | 评分Prompt v2 | 注册成功，输出含子项+权重+关键词 | □ |

### 工程规范验收

| # | 验收项 | 通过条件 | 状态 |
|---|---|---|---|
| 1 | tenant_id隔离 | 所有新建查询均带tenant_id过滤 | □ |
| 2 | Alembic迁移 | upgrade()+downgrade()均可执行 | □ |
| 3 | 自动化测试 | pytest新增≥15个用例，全部通过 | □ |
| 4 | 代码规范 | 新Service遵循async模式，API层不含业务逻辑 | □ |
| 5 | 增量兼容 | bid_doc_exporter.py改动不影响默认行为 | □ |
| 6 | Prompt版本 | v2新增，v1保留不删除 | □ |

---

## 注意事项（给IDE Agent的特别提醒）

### 红线约束
1. **所有数据库查询必须过滤 `tenant_id`** — 这是多租户隔离的硬红线
2. **不要直接实例化 LLM 客户端** — 必须经过 `LLMSelector.get_model()`
3. **不要硬编码 Prompt** — 必须经过 `PromptManager.get_prompt()`
4. **改 bid_doc_exporter.py 时必须保持默认行为不变** — 水印是可选参数
5. **改 tender_parser.py 时不能破坏现有 PDF 解析链路**
6. **新建表必须继承 AuditMixin**

### 执行顺序
1. 每个任务开始前，先执行「前置查阅」命令，理解现有代码
2. 改动超过50行的文件前，先输出 implementation_plan 并标注 `[User Review Required]`
3. 每完成一个任务，运行对应的测试用例确认通过
4. D5的端到端测试必须在所有任务完成后执行

### 如果遇到问题
- 现有代码结构与本文档描述不符 → 以实际代码为准，调整实现方式
- 支付商户号未审批通过 → 先实现「手动转账+人工开通」方案，支付接口预留
- bid_generation_service.py 中找不到明确的生成入口 → 用 `grep_search "generate"` 搜索
