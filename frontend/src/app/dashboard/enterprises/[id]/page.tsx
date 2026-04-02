"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ArrowLeft,
  Loader2,
  Save,
  Plus,
  Trash2,
  Building2,
  ShieldCheck,
  Truck,
  AlertTriangle,
  CheckCircle2,
  ImageIcon,
  Upload,
  X,
  Star,
  Sparkles,
  ChevronDown,
  ChevronRight,
  FileImage,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import FileDropZone from "@/components/ui/file-drop-zone";

interface Enterprise {
  id: number;
  name: string;
  short_name?: string;
  credit_code?: string;
  legal_representative?: string;
  registered_capital?: string;
  established_date?: string;
  business_scope?: string;
  food_license_no?: string;
  food_license_expiry?: string;
  haccp_certified: boolean;
  iso22000_certified: boolean;
  sc_certified: boolean;
  cold_chain_vehicles: number;
  normal_vehicles: number;
  warehouse_area?: number;
  cold_storage_area?: number;
  cold_storage_temp?: string;
  address?: string;
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  employee_count?: number;
  annual_revenue?: string;
  service_customers?: number;
  description?: string;
  competitive_advantages?: string;
}

interface Credential {
  id: number;
  enterprise_id: number;
  cred_type: string;
  cred_name: string;
  cred_no?: string;
  issue_date?: string;
  expiry_date?: string;
  is_permanent: boolean;
  issuing_authority?: string;
  is_verified: boolean;
}

interface ImageAsset {
  id: number;
  enterprise_id: number;
  category: string;
  title: string;
  description?: string;
  file_name?: string;
  file_size?: number;
  width?: number;
  height?: number;
  tags?: string;
  suggested_chapter?: string;
  is_default: boolean;
}

const IMAGE_CATEGORIES = [
  { value: "cold_chain_vehicle", label: "冷链车辆" },
  { value: "warehouse", label: "仓库/冷库" },
  { value: "testing_equipment", label: "检测设备" },
  { value: "food_sample", label: "食材样品" },
  { value: "process_flow", label: "流程图/架构图" },
  { value: "company_environment", label: "公司环境" },
  { value: "sample_retention", label: "留样柜" },
  { value: "inspection_report", label: "检验报告" },
  { value: "certificate", label: "证书/奖项" },
  { value: "delivery_scene", label: "配送现场" },
  { value: "training", label: "培训场景" },
  { value: "canteen", label: "食堂/餐厅" },
  { value: "traceability", label: "追溯系统" },
  { value: "other", label: "其他" },
];

const IMAGE_CAT_LABELS: Record<string, string> = Object.fromEntries(
  IMAGE_CATEGORIES.map((c) => [c.value, c.label])
);

const CRED_TYPE_OPTIONS = [
  { value: "business_license", label: "营业执照" },
  { value: "food_license", label: "食品经营许可证" },
  { value: "haccp", label: "HACCP认证" },
  { value: "iso22000", label: "ISO22000认证" },
  { value: "sc", label: "SC认证" },
  { value: "animal_quarantine", label: "动物防疫合格证" },
  { value: "cold_chain_transport", label: "冷链运输资质" },
  { value: "health_certificate", label: "从业人员健康证" },
  { value: "liability_insurance", label: "公众责任险" },
  { value: "quality_inspection", label: "质量检验报告" },
  { value: "organic_cert", label: "有机认证" },
  { value: "green_food", label: "绿色食品认证" },
  { value: "performance", label: "业绩证明" },
  { value: "award", label: "荣誉证书" },
  { value: "other", label: "其他" },
];

const CRED_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  CRED_TYPE_OPTIONS.map((o) => [o.value, o.label])
);

function isExpiringSoon(expiryDate?: string): boolean {
  if (!expiryDate) return false;
  const diffDays = (new Date(expiryDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= 90;
}

function isExpired(expiryDate?: string): boolean {
  if (!expiryDate) return false;
  return new Date(expiryDate) < new Date();
}

/** 构建图片 URL（兼容容器内相对路径和本地开发） */
function imageUrl(imageId: number): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base}/images/file/${imageId}`;
}

/** 顶级标书结构框架 */
const CHAPTER_FRAMEWORKS: Record<string, { title: string; sections: string[] }> = {
  description: {
    title: "第二章 投标人基本情况（推荐结构）",
    sections: [
      "一、公司概况：成立时间、注册资本、经营范围、行业深耕年限",
      "二、资质能力：食品经营许可证、质量/环境/食品安全管理体系认证、荣誉奖项",
      "三、企业规模：员工人数、核心团队构成、组织架构",
      "四、硬件设施：仓储中心、冷库、分拣线、检测室、配送车队",
      "五、服务业绩：近三年同类项目业绩、重点客户案例、合同金额",
      "六、客户评价：满意度数据、表扬信、履约考核结果",
    ],
  },
  advantages: {
    title: "技术方案 核心竞争优势（推荐结构）",
    sections: [
      "一、供应链管理：源头直采基地、供应商准入机制、多级供应保障",
      "二、冷链物流保障：全程温控体系、车辆GPS监控、温度记录与异常预警",
      "三、食品安全管控：HACCP体系运行、农残快检能力、留样制度、追溯机制",
      "四、应急响应能力：突发事件预案、备用供货渠道、1小时应急响应",
      "五、信息化系统：订单管理平台、食品追溯系统、配送调度系统",
      "六、差异化服务：定制化菜单服务、营养膳食指导、满意度回访机制",
    ],
  },
};

/** AI 结构化建议面板（含编辑模式） */
function AiSuggestionPanel({ draft, credentials, images, enterprise, onAcceptText, onReject, onReOptimize }: {
  draft: {
    field: string;
    optimized_text: string;
    score_analysis?: string;
    missing_items?: string[];
    suggestions?: string[];
    materials_needed?: string[];
  };
  credentials: Credential[];
  images: ImageAsset[];
  enterprise: Partial<Enterprise>;
  onAcceptText: (text: string) => void;
  onReject: () => void;
  onReOptimize: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(draft.optimized_text);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  // 自动检查已有资料能覆盖哪些项
  const autoChecked = new Set<string>();
  const autoNotes: Record<string, string> = {};

  // 从资质证书库匹配
  const credNames = credentials.map(c => `${CRED_TYPE_LABELS[c.cred_type] || c.cred_type}: ${c.cred_name}`);
  const allItems = [
    ...(draft.missing_items || []),
    ...(draft.suggestions || []),
    ...(draft.materials_needed || []),
  ];

  allItems.forEach((item) => {
    const lower = item.toLowerCase();
    // 资质证书匹配
    if (lower.includes("营业执照") || lower.includes("基础资质")) {
      const found = credentials.filter(c => c.cred_type === "business_license");
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有: ${found[0].cred_name}`; }
    }
    if (lower.includes("食品经营许可") || lower.includes("食品许可")) {
      const found = credentials.filter(c => c.cred_type === "food_license");
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有: ${found[0].cred_name}${found[0].cred_no ? ` (${found[0].cred_no})` : ""}`; }
    }
    if (lower.includes("haccp") || lower.includes("iso22000") || lower.includes("质量管理") || lower.includes("食品安全管理")) {
      const found = credentials.filter(c => ["haccp", "iso22000", "sc"].includes(c.cred_type));
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有: ${found.map(f => f.cred_name).join("、")}`; }
    }
    if (lower.includes("检测报告") || lower.includes("检测能力")) {
      const found = credentials.filter(c => c.cred_type === "quality_inspection");
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有: ${found[0].cred_name}`; }
    }
    if (lower.includes("业绩") || lower.includes("合同")) {
      const found = credentials.filter(c => c.cred_type === "performance");
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有 ${found.length} 份业绩证明`; }
    }
    if (lower.includes("健康证")) {
      const found = credentials.filter(c => c.cred_type === "health_certificate");
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有 ${found.length} 份健康证`; }
    }
    if (lower.includes("荣誉") || lower.includes("获奖") || lower.includes("奖项")) {
      const found = credentials.filter(c => c.cred_type === "award");
      if (found.length > 0) { autoChecked.add(item); autoNotes[item] = `已有 ${found.length} 项荣誉`; }
    }
    // 企业数据匹配
    if (lower.includes("冷链车") || lower.includes("配送车辆") || lower.includes("车辆")) {
      if (enterprise.cold_chain_vehicles && enterprise.cold_chain_vehicles > 0) {
        autoChecked.add(item);
        autoNotes[item] = `冷链车 ${enterprise.cold_chain_vehicles} 辆，常温车 ${enterprise.normal_vehicles || 0} 辆`;
      }
    }
    if (lower.includes("仓储") || lower.includes("冷库") || lower.includes("面积")) {
      if (enterprise.warehouse_area || enterprise.cold_storage_area) {
        autoChecked.add(item);
        autoNotes[item] = `仓储 ${enterprise.warehouse_area || 0}㎡，冷库 ${enterprise.cold_storage_area || 0}㎡`;
      }
    }
    if (lower.includes("员工") || lower.includes("人数") || lower.includes("团队")) {
      if (enterprise.employee_count) {
        autoChecked.add(item);
        autoNotes[item] = `员工 ${enterprise.employee_count} 人`;
      }
    }
    if (lower.includes("成立时间") || lower.includes("成立年") || lower.includes("经验年限")) {
      if (enterprise.established_date) {
        const years = new Date().getFullYear() - parseInt(enterprise.established_date);
        autoChecked.add(item);
        autoNotes[item] = `成立于 ${enterprise.established_date}，深耕行业 ${years > 0 ? years : "?"}年`;
      }
    }
    // 图片匹配
    if (lower.includes("照片") || lower.includes("现场") || lower.includes("图片")) {
      const matchCats = lower.includes("冷链") ? ["cold_chain_vehicle"] :
        lower.includes("仓") || lower.includes("冷库") ? ["warehouse"] :
        lower.includes("检测") ? ["testing_equipment", "inspection_report"] :
        lower.includes("配送") ? ["delivery_scene"] : [];
      const found = images.filter(i => matchCats.includes(i.category));
      if (found.length > 0) {
        autoChecked.add(item);
        autoNotes[item] = `已有 ${found.length} 张相关图片`;
      }
    }
  });

  const isChecked = (item: string) => checkedItems.has(item) || autoChecked.has(item);
  const toggleCheck = (item: string) => {
    setCheckedItems(prev => {
      const next = new Set(prev);
      if (next.has(item)) next.delete(item);
      else next.add(item);
      return next;
    });
  };

  const framework = CHAPTER_FRAMEWORKS[draft.field] || CHAPTER_FRAMEWORKS.description;
  const totalItems = allItems.length;
  const completedItems = allItems.filter(i => isChecked(i)).length;

  // 根据内容判断跳转目标
  const getSectionTarget = (item: string): { id: string; label: string } | null => {
    const lower = item.toLowerCase();
    if (lower.includes("成立时间") || lower.includes("注册资本") || lower.includes("员工") || lower.includes("人数") || lower.includes("经验年限") || lower.includes("经营范围"))
      return { id: "section-basic", label: "工商信息" };
    if (lower.includes("冷链") || lower.includes("车辆") || lower.includes("仓储") || lower.includes("冷库") || lower.includes("面积") || lower.includes("配送车"))
      return { id: "section-coldchain", label: "冷链资产" };
    if (lower.includes("营业执照") || lower.includes("许可证") || lower.includes("认证") || lower.includes("haccp") || lower.includes("iso") || lower.includes("资质") || lower.includes("证书") || lower.includes("业绩") || lower.includes("合同") || lower.includes("健康证") || lower.includes("检测") || lower.includes("荣誉") || lower.includes("获奖"))
      return { id: "section-credentials", label: "资质证书库" };
    if (lower.includes("照片") || lower.includes("图片") || lower.includes("现场") || lower.includes("截图"))
      return { id: "section-images", label: "图片资源库" };
    return null;
  };

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // 渲染 checklist 项
  const renderCheckItem = (item: string, i: number, color: string) => {
    const target = getSectionTarget(item);
    return (
      <li key={i} className="flex items-start gap-2 group">
        <button
          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors ${
            isChecked(item)
              ? "border-green-500 bg-green-500 text-white"
              : `border-slate-300 hover:border-${color}-500`
          }`}
          onClick={() => toggleCheck(item)}
        >
          {isChecked(item) && <CheckCircle2 className="h-3.5 w-3.5" />}
        </button>
        <div className="flex-1">
          <span className={`text-sm ${isChecked(item) ? "text-slate-400 line-through" : "text-slate-700"}`}>
            {item}
          </span>
          {autoNotes[item] && (
            <span className="ml-2 text-xs text-green-600">({autoNotes[item]})</span>
          )}
          {!isChecked(item) && target && (
            <button
              className="ml-2 text-xs text-blue-500 hover:text-blue-700 hover:underline"
              onClick={() => scrollToSection(target.id)}
            >
              前往{target.label}补充 →
            </button>
          )}
        </div>
      </li>
    );
  };

  // 建议模式
  if (!editing) {
    return (
      <div className="mt-3 rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-3">
        {draft.score_analysis && (
          <div>
            <div className="flex items-center gap-1.5 text-sm font-medium text-blue-700 mb-1">
              <Sparkles className="h-4 w-4" />
              得分分析
            </div>
            <p className="text-sm text-slate-700">{draft.score_analysis}</p>
          </div>
        )}
        {draft.missing_items && draft.missing_items.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-sm font-medium text-amber-700 mb-1">
              <AlertTriangle className="h-4 w-4" />
              缺失的得分点
            </div>
            <ul className="space-y-1.5">
              {draft.missing_items.map((item, i) => renderCheckItem(item, i, "amber"))}
            </ul>
          </div>
        )}
        {draft.suggestions && draft.suggestions.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-sm font-medium text-green-700 mb-1">
              <CheckCircle2 className="h-4 w-4" />
              改进建议
            </div>
            <ul className="space-y-1.5">
              {draft.suggestions.map((item, i) => renderCheckItem(item, i, "green"))}
            </ul>
          </div>
        )}
        {draft.materials_needed && draft.materials_needed.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-sm font-medium text-purple-700 mb-1">
              <Upload className="h-4 w-4" />
              建议补充资料
            </div>
            <ul className="space-y-1.5">
              {draft.materials_needed.map((item, i) => renderCheckItem(item, i, "purple"))}
            </ul>
          </div>
        )}
        <div className="flex gap-2 pt-2">
          <Button size="sm" onClick={() => setEditing(true)}>
            <Sparkles className="mr-1 h-3.5 w-3.5" />
            采纳并编辑
          </Button>
          <Button size="sm" variant="outline" onClick={onReject}>
            关闭
          </Button>
        </div>
      </div>
    );
  }

  // 编辑模式
  return (
    <div className="mt-3 space-y-4">
      {/* 结构框架 */}
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="mb-2 text-sm font-medium text-slate-800">{framework.title}</div>
        <ol className="space-y-1">
          {framework.sections.map((s, i) => (
            <li key={i} className="text-xs text-slate-600">{s}</li>
          ))}
        </ol>
      </div>

      {/* 完成进度 */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
          <div
            className="h-full rounded-full bg-green-500 transition-all"
            style={{ width: totalItems > 0 ? `${(completedItems / totalItems) * 100}%` : "0%" }}
          />
        </div>
        <span className="text-xs text-slate-500 shrink-0">{completedItems}/{totalItems} 项已补充</span>
      </div>

      {/* 优化文本编辑区 */}
      <div className="rounded-lg border border-blue-200 bg-white p-4">
        <div className="mb-2 flex items-center justify-between">
          <label className="text-sm font-medium text-slate-700">编辑优化后的内容</label>
          <span className="text-xs text-slate-400">{editText.length} 字</span>
        </div>
        <textarea
          className="w-full rounded-md border border-slate-200 p-3 text-sm text-slate-700 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
          rows={12}
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
        />
      </div>

      {/* Checklist 侧边栏 */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <div className="text-sm font-medium text-slate-700">待补充项（勾选已完成的）</div>
        {draft.missing_items && draft.missing_items.length > 0 && (
          <div>
            <div className="text-xs font-medium text-amber-600 mb-1">缺失得分点</div>
            <ul className="space-y-1.5">{draft.missing_items.map((item, i) => renderCheckItem(item, i, "amber"))}</ul>
          </div>
        )}
        {draft.suggestions && draft.suggestions.length > 0 && (
          <div>
            <div className="text-xs font-medium text-green-600 mb-1">改进建议</div>
            <ul className="space-y-1.5">{draft.suggestions.map((item, i) => renderCheckItem(item, i, "green"))}</ul>
          </div>
        )}
        {draft.materials_needed && draft.materials_needed.length > 0 && (
          <div>
            <div className="text-xs font-medium text-purple-600 mb-1">待补充资料</div>
            <ul className="space-y-1.5">{draft.materials_needed.map((item, i) => renderCheckItem(item, i, "purple"))}</ul>
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <Button onClick={() => onAcceptText(editText)}>
          <CheckCircle2 className="mr-2 h-4 w-4" />
          完成编辑
        </Button>
        <Button variant="outline" onClick={() => { onReOptimize(); setEditing(false); }}>
          <Sparkles className="mr-2 h-4 w-4" />
          基于最新资料重新优化
        </Button>
        <Button variant="ghost" onClick={onReject}>
          取消
        </Button>
      </div>
    </div>
  );
}

export default function EnterpriseDetailPage() {
  const params = useParams();
  const enterpriseId = params.id as string;

  const [enterprise, setEnterprise] = useState<Enterprise | null>(null);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [form, setForm] = useState<Partial<Enterprise>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 图片管理
  const [images, setImages] = useState<ImageAsset[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [imageUploadProgress, setImageUploadProgress] = useState(0);
  const [imageUploadError, setImageUploadError] = useState("");
  const [imageCategory, setImageCategory] = useState("other");
  const [imageTitle, setImageTitle] = useState("");
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [expandedCats, setExpandedCats] = useState<Set<string>>(new Set());

  // 资质管理
  const [showNewCred, setShowNewCred] = useState(false);
  const [newCred, setNewCred] = useState({
    cred_type: "business_license",
    cred_name: "",
    cred_no: "",
    issue_date: "",
    expiry_date: "",
    is_permanent: false,
    issuing_authority: "",
  });

  // AI 优化
  const [aiOptimizing, setAiOptimizing] = useState<"description" | "advantages" | null>(null);
  const [aiDraft, setAiDraft] = useState<{
    field: string;
    optimized_text: string;
    score_analysis?: string;
    missing_items?: string[];
    suggestions?: string[];
    materials_needed?: string[];
  } | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [entRes, credRes, imgRes] = await Promise.all([
        api.get(`/enterprises/${enterpriseId}`),
        api.get(`/credentials/enterprise/${enterpriseId}`),
        api.get(`/images/enterprise/${enterpriseId}`).catch(() => ({ data: { data: [] } })),
      ]);
      const ent = entRes.data?.data as Enterprise;
      setEnterprise(ent);
      setForm(ent);
      setCredentials(credRes.data?.data || []);
      const imgs = imgRes.data?.data || [];
      setImages(imgs);
      // 默认展开所有有图片的分类
      setExpandedCats(new Set(imgs.map((i: ImageAsset) => i.category)));
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [enterpriseId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFormChange = (field: string, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (!enterprise) return;
    setSaving(true);
    try {
      await api.put(`/enterprises/${enterprise.id}`, form);
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  // AI 优化文本（结构化输出：优化文本 + 得分分析 + 缺失项 + 建议）
  const handleAiOptimize = async (field: "description" | "advantages") => {
    const text = field === "description" ? form.description : form.competitive_advantages;
    if (!text?.trim()) {
      alert("请先填写内容，再使用 AI 优化");
      return;
    }
    setAiOptimizing(field);
    try {
      const chapterDef = field === "description"
        ? "投标文件第二章「投标人基本情况」，评分要点包括：企业规模与实力、行业经验年限、资质证书齐全度、服务客户数量与质量、团队专业能力。"
        : "投标文件技术方案章节「核心竞争优势」，评分要点包括：供应链管理能力、冷链物流保障、食品安全管控体系、应急响应能力、信息化追溯系统、差异化服务亮点。";

      const prompt = `你是一位资深的投标文件顾问。请从招投标评分得分的角度，分析并优化以下内容。

## 章节定义
${chapterDef}

## 当前内容
${text}

## 企业已有资质信息
- 资质证书数量：${credentials.length} 项
- 冷链车辆：${form.cold_chain_vehicles || 0} 辆
- 常温车辆：${form.normal_vehicles || 0} 辆
- 仓储面积：${form.warehouse_area || "未填写"} ㎡
- 冷库面积：${form.cold_storage_area || "未填写"} ㎡
- 员工人数：${form.employee_count || "未填写"}

## 要求
请严格按以下 JSON 格式返回（不要包含 markdown 代码块标记）：
{
  "optimized_text": "优化后的完整文本，300-500字，专业精炼",
  "score_analysis": "基于评分要点的得分分析，指出当前内容大约能覆盖多少评分点",
  "missing_items": ["当前内容缺失的得分要点1", "缺失要点2"],
  "suggestions": ["具体改进建议1：如何补强某个评分点", "建议2"],
  "materials_needed": ["建议补充的证明材料1", "材料2"]
}`;

      const res = await api.post("/ai/chat", {
        message: prompt,
        history: [],
        stream: false,
      });
      const reply = res.data?.data?.reply;
      if (reply) {
        try {
          // 尝试解析 JSON（兼容 AI 可能包裹 markdown 代码块）
          const cleaned = reply.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim();
          const parsed = JSON.parse(cleaned);
          setAiDraft({
            field,
            optimized_text: parsed.optimized_text || reply,
            score_analysis: parsed.score_analysis,
            missing_items: parsed.missing_items,
            suggestions: parsed.suggestions,
            materials_needed: parsed.materials_needed,
          });
        } catch {
          // JSON 解析失败，降级为纯文本
          setAiDraft({ field, optimized_text: reply });
        }
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "AI 优化失败");
    } finally {
      setAiOptimizing(null);
    }
  };

  const handleAcceptAiDraft = () => {
    if (!aiDraft) return;
    const formField = aiDraft.field === "description" ? "description" : "competitive_advantages";
    handleFormChange(formField, aiDraft.optimized_text);
    setAiDraft(null);
  };

  const handleRejectAiDraft = () => {
    setAiDraft(null);
  };

  // 资质
  const handleAddCredential = async () => {
    if (!enterprise || !newCred.cred_name) return;
    try {
      await api.post("/credentials", {
        enterprise_id: enterprise.id,
        ...newCred,
      });
      setShowNewCred(false);
      setNewCred({
        cred_type: "business_license", cred_name: "", cred_no: "",
        issue_date: "", expiry_date: "", is_permanent: false, issuing_authority: "",
      });
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "添加失败");
    }
  };

  const handleDeleteCredential = async (credId: number) => {
    try {
      await api.delete(`/credentials/${credId}`);
      await fetchData();
    } catch {
      alert("删除失败");
    }
  };

  // 图片
  const handleUploadImage = async () => {
    if (!enterprise || !imageFile) return;
    setImageUploading(true);
    setImageUploadProgress(0);
    setImageUploadError("");
    try {
      const formData = new FormData();
      formData.append("file", imageFile);
      formData.append("enterprise_id", String(enterprise.id));
      formData.append("category", imageCategory);
      formData.append("title", imageTitle || imageFile.name);
      await api.post("/images/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) setImageUploadProgress(Math.round((e.loaded * 100) / e.total));
        },
      });
      setImageUploadProgress(100);
      setImageFile(null);
      setImageTitle("");
      setImageCategory("other");
      setShowImageUpload(false);
      await fetchData();
    } catch (err: any) {
      setImageUploadError(err.response?.data?.detail || "上传失败");
    } finally {
      setImageUploading(false);
    }
  };

  const handleDeleteImage = async (imageId: number) => {
    if (!confirm("确认删除此图片？")) return;
    try {
      await api.delete(`/images/${imageId}`);
      setImages((prev) => prev.filter((i) => i.id !== imageId));
    } catch {
      alert("删除失败");
    }
  };

  const toggleCat = (cat: string) => {
    setExpandedCats((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  // 按分类分组图片
  const imagesByCategory = images.reduce((acc, img) => {
    if (!acc[img.category]) acc[img.category] = [];
    acc[img.category].push(img);
    return acc;
  }, {} as Record<string, ImageAsset[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!enterprise) {
    return (
      <div className="text-center py-20 text-slate-500">企业不存在</div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/enterprises">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold text-slate-900">{enterprise.name}</h1>
            {enterprise.short_name && (
              <p className="text-sm text-slate-400">{enterprise.short_name}</p>
            )}
          </div>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          保存
        </Button>
      </div>

      {/* 工商信息 */}
      <Card id="section-basic">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            工商信息
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs text-slate-500">企业名称 *</label>
              <Input value={form.name || ""} onChange={(e) => handleFormChange("name", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">企业简称</label>
              <Input value={form.short_name || ""} onChange={(e) => handleFormChange("short_name", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">统一社会信用代码</label>
              <Input value={form.credit_code || ""} onChange={(e) => handleFormChange("credit_code", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">法定代表人</label>
              <Input value={form.legal_representative || ""} onChange={(e) => handleFormChange("legal_representative", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">注册资本（万元）</label>
              <Input value={form.registered_capital || ""} onChange={(e) => handleFormChange("registered_capital", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">成立日期</label>
              <Input type="date" value={form.established_date || ""} onChange={(e) => handleFormChange("established_date", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">员工人数</label>
              <Input type="number" value={form.employee_count ?? ""} onChange={(e) => handleFormChange("employee_count", e.target.value ? parseInt(e.target.value) : null)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">年营收（万元）</label>
              <Input value={form.annual_revenue || ""} onChange={(e) => handleFormChange("annual_revenue", e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">服务客户数</label>
              <Input type="number" value={form.service_customers ?? ""} onChange={(e) => handleFormChange("service_customers", e.target.value ? parseInt(e.target.value) : null)} />
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs text-slate-500">公司地址</label>
              <Input value={form.address || ""} onChange={(e) => handleFormChange("address", e.target.value)} />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="mb-1 block text-xs text-slate-500">联系人</label>
                <Input value={form.contact_person || ""} onChange={(e) => handleFormChange("contact_person", e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-500">联系电话</label>
                <Input value={form.contact_phone || ""} onChange={(e) => handleFormChange("contact_phone", e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-500">邮箱</label>
                <Input value={form.contact_email || ""} onChange={(e) => handleFormChange("contact_email", e.target.value)} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 冷链资产 */}
      <Card id="section-coldchain">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="h-5 w-5" />
            冷链资产
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
            <div>
              <label className="mb-1 block text-xs text-slate-500">冷链车辆（辆）</label>
              <Input type="number" value={form.cold_chain_vehicles ?? 0} onChange={(e) => handleFormChange("cold_chain_vehicles", parseInt(e.target.value) || 0)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">常温车辆（辆）</label>
              <Input type="number" value={form.normal_vehicles ?? 0} onChange={(e) => handleFormChange("normal_vehicles", parseInt(e.target.value) || 0)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">仓储面积（㎡）</label>
              <Input type="number" value={form.warehouse_area ?? ""} onChange={(e) => handleFormChange("warehouse_area", e.target.value ? parseFloat(e.target.value) : null)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">冷库面积（㎡）</label>
              <Input type="number" value={form.cold_storage_area ?? ""} onChange={(e) => handleFormChange("cold_storage_area", e.target.value ? parseFloat(e.target.value) : null)} />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">冷库温度范围</label>
              <Input placeholder="-18℃~4℃" value={form.cold_storage_temp || ""} onChange={(e) => handleFormChange("cold_storage_temp", e.target.value)} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 企业简介与竞争优势 — 带 AI 优化 */}
      <Card>
        <CardHeader>
          <CardTitle>企业简介与竞争优势</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 企业简介 */}
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="text-xs text-slate-500">企业简介（用于投标文件第二章）</label>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAiOptimize("description")}
                disabled={aiOptimizing !== null || !form.description?.trim()}
              >
                {aiOptimizing === "description" ? (
                  <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="mr-1 h-3.5 w-3.5" />
                )}
                AI 优化
              </Button>
            </div>
            <Textarea
              rows={4}
              value={form.description || ""}
              onChange={(e) => handleFormChange("description", e.target.value)}
              placeholder="介绍企业的基本情况、发展历程、主营业务等..."
            />
            {/* AI 优化结果 — 结构化建议面板 */}
            {aiDraft && aiDraft.field === "description" && (
              <AiSuggestionPanel
                draft={aiDraft}
                credentials={credentials}
                images={images}
                enterprise={form}
                onAcceptText={(text) => {
                  const formField = aiDraft.field === "description" ? "description" : "competitive_advantages";
                  handleFormChange(formField, text);
                  setAiDraft(null);
                }}
                onReject={handleRejectAiDraft}
                onReOptimize={() => {
                  setAiDraft(null);
                  handleAiOptimize(aiDraft.field as "description" | "advantages");
                }}
              />
            )}
          </div>

          {/* 核心竞争优势 */}
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="text-xs text-slate-500">核心竞争优势（用于技术方案章节）</label>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAiOptimize("advantages")}
                disabled={aiOptimizing !== null || !form.competitive_advantages?.trim()}
              >
                {aiOptimizing === "advantages" ? (
                  <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="mr-1 h-3.5 w-3.5" />
                )}
                AI 优化
              </Button>
            </div>
            <Textarea
              rows={4}
              value={form.competitive_advantages || ""}
              onChange={(e) => handleFormChange("competitive_advantages", e.target.value)}
              placeholder="如：自有基地直供、全程冷链可追溯、服务XX所学校食堂等..."
            />
            {aiDraft && aiDraft.field === "advantages" && (
              <AiSuggestionPanel
                draft={aiDraft}
                credentials={credentials}
                images={images}
                enterprise={form}
                onAcceptText={(text) => {
                  const formField = aiDraft.field === "description" ? "description" : "competitive_advantages";
                  handleFormChange(formField, text);
                  setAiDraft(null);
                }}
                onReject={handleRejectAiDraft}
                onReOptimize={() => {
                  setAiDraft(null);
                  handleAiOptimize(aiDraft.field as "description" | "advantages");
                }}
              />
            )}
          </div>
        </CardContent>
      </Card>

      {/* 资质证书库 */}
      <Card id="section-credentials">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              资质证书库（{credentials.length} 项）
            </CardTitle>
            <Button size="sm" variant="outline" onClick={() => setShowNewCred(!showNewCred)}>
              <Plus className="mr-1 h-4 w-4" />
              添加证书
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showNewCred && (
            <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                <div>
                  <label className="mb-1 block text-xs text-slate-500">证书类型</label>
                  <select
                    className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm"
                    value={newCred.cred_type}
                    onChange={(e) => setNewCred({ ...newCred, cred_type: e.target.value })}
                  >
                    {CRED_TYPE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-slate-500">证书名称 *</label>
                  <Input value={newCred.cred_name} onChange={(e) => setNewCred({ ...newCred, cred_name: e.target.value })} placeholder="如：食品经营许可证" />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-slate-500">证书编号</label>
                  <Input value={newCred.cred_no} onChange={(e) => setNewCred({ ...newCred, cred_no: e.target.value })} />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-slate-500">到期日期</label>
                  <Input type="date" value={newCred.expiry_date} onChange={(e) => setNewCred({ ...newCred, expiry_date: e.target.value })} />
                </div>
              </div>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-4">
                <div>
                  <label className="mb-1 block text-xs text-slate-500">发证机关</label>
                  <Input value={newCred.issuing_authority} onChange={(e) => setNewCred({ ...newCred, issuing_authority: e.target.value })} />
                </div>
                <div className="flex items-end pb-1">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={newCred.is_permanent} onChange={(e) => setNewCred({ ...newCred, is_permanent: e.target.checked })} className="h-4 w-4 rounded border-slate-300" />
                    长期有效
                  </label>
                </div>
                <div className="col-span-2 flex items-end gap-2">
                  <Button size="sm" onClick={handleAddCredential} disabled={!newCred.cred_name}>
                    <Plus className="mr-1 h-3.5 w-3.5" />
                    添加
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowNewCred(false)}>取消</Button>
                </div>
              </div>
            </div>
          )}

          {credentials.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">
              暂无资质证书，点击「添加证书」录入
            </p>
          ) : (
            <div className="space-y-2">
              {credentials.map((cred) => {
                const expired = isExpired(cred.expiry_date);
                const expiring = isExpiringSoon(cred.expiry_date);
                return (
                  <div
                    key={cred.id}
                    className={`flex items-center justify-between rounded-lg border p-3 ${
                      expired ? "border-red-200 bg-red-50" :
                      expiring ? "border-amber-200 bg-amber-50" :
                      "border-slate-200"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="shrink-0">
                        {CRED_TYPE_LABELS[cred.cred_type] || cred.cred_type}
                      </Badge>
                      <div>
                        <div className="text-sm font-medium">{cred.cred_name}</div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          {cred.cred_no && <span>编号: {cred.cred_no}</span>}
                          {cred.issuing_authority && <span>发证: {cred.issuing_authority}</span>}
                          {cred.is_permanent ? (
                            <span className="text-green-600">长期有效</span>
                          ) : cred.expiry_date ? (
                            <span className={expired ? "text-red-600 font-medium" : expiring ? "text-amber-600" : ""}>
                              {expired ? "已过期: " : expiring ? "即将到期: " : "有效期至: "}
                              {cred.expiry_date}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {expired && <AlertTriangle className="h-4 w-4 text-red-500" />}
                      {expiring && !expired && <AlertTriangle className="h-4 w-4 text-amber-500" />}
                      {cred.is_verified && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-slate-400 hover:text-red-500"
                        onClick={() => handleDeleteCredential(cred.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 图片资源库 — 分类列表视图 */}
      <Card id="section-images">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              图片资源库（{images.length} 张）
            </CardTitle>
            <Button size="sm" variant="outline" onClick={() => setShowImageUpload(!showImageUpload)}>
              <Upload className="mr-1 h-4 w-4" />
              上传图片
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* 上传表单 */}
          {showImageUpload && (
            <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-3">
              <FileDropZone
                accept={[".jpg", ".jpeg", ".png", ".gif", ".webp"]}
                file={imageFile}
                onFileSelect={(f) => { setImageFile(f); setImageUploadError(""); }}
                onFileRemove={() => { setImageFile(null); setImageUploadError(""); }}
                uploading={imageUploading}
                progress={imageUploadProgress}
                error={imageUploadError}
                hint="支持 JPG/PNG/GIF/WebP 格式"
              />
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <div>
                  <label className="mb-1 block text-xs text-slate-500">图片分类</label>
                  <select
                    className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm"
                    value={imageCategory}
                    onChange={(e) => setImageCategory(e.target.value)}
                  >
                    {IMAGE_CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-slate-500">图片标题</label>
                  <Input
                    value={imageTitle}
                    onChange={(e) => setImageTitle(e.target.value)}
                    placeholder="如：冷链配送车-京A12345"
                  />
                </div>
                <div className="flex items-end gap-2">
                  <Button size="sm" onClick={handleUploadImage} disabled={!imageFile || imageUploading}>
                    {imageUploading ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Upload className="mr-1 h-3.5 w-3.5" />}
                    上传
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setShowImageUpload(false); setImageFile(null); }}>取消</Button>
                </div>
              </div>
            </div>
          )}

          {/* 分类列表 */}
          {images.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">
              暂无图片，点击「上传图片」添加企业资质照片、冷链车辆照片等
            </p>
          ) : (
            <div className="space-y-2">
              {Object.entries(imagesByCategory).map(([cat, catImages]) => (
                <div key={cat} className="rounded-lg border border-slate-200">
                  {/* 分类头 */}
                  <button
                    className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                    onClick={() => toggleCat(cat)}
                  >
                    <div className="flex items-center gap-2">
                      {expandedCats.has(cat) ? (
                        <ChevronDown className="h-4 w-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      )}
                      <FileImage className="h-4 w-4 text-slate-500" />
                      <span className="text-sm font-medium text-slate-700">
                        {IMAGE_CAT_LABELS[cat] || cat}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {catImages.length}
                      </Badge>
                    </div>
                  </button>

                  {/* 展开的图片列表 */}
                  {expandedCats.has(cat) && (
                    <div className="border-t px-4 py-2 space-y-1">
                      {catImages.map((img) => (
                        <div
                          key={img.id}
                          className="flex items-center gap-3 rounded-lg p-2 hover:bg-slate-50 group"
                        >
                          {/* 缩略图 */}
                          <div className="h-12 w-16 shrink-0 overflow-hidden rounded border bg-slate-100">
                            <img
                              src={imageUrl(img.id)}
                              alt={img.title}
                              className="h-full w-full object-cover"
                              onError={(e) => {
                                const el = e.target as HTMLImageElement;
                                el.style.display = "none";
                                el.parentElement!.innerHTML = '<div class="flex h-full w-full items-center justify-center"><svg class="h-5 w-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg></div>';
                              }}
                            />
                          </div>
                          {/* 信息 */}
                          <div className="flex-1 min-w-0">
                            <p className="truncate text-sm font-medium text-slate-700">{img.title}</p>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                              {img.file_name && <span className="truncate max-w-[200px]">{img.file_name}</span>}
                              {img.file_size && <span>{(img.file_size / 1024).toFixed(0)} KB</span>}
                              {img.width && img.height && <span>{img.width}x{img.height}</span>}
                              {img.is_default && (
                                <span className="flex items-center gap-0.5 text-amber-500">
                                  <Star className="h-3 w-3 fill-amber-500" />
                                  默认
                                </span>
                              )}
                            </div>
                          </div>
                          {/* 删除按钮 */}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 shrink-0 text-slate-400 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-opacity"
                            onClick={() => handleDeleteImage(img.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
