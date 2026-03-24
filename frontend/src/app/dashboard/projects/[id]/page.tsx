"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  Download,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  Pencil,
  Save,
  X,
} from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";
import ChapterFeedback from "@/components/business/chapter-feedback";
import AIPipelineProgress, {
  PIPELINE_LAYERS,
  PipelineState,
  LayerState,
} from "@/components/business/ai-pipeline-progress";

/* ============ 参数分组配置 ============ */
type FieldDef = {
  key: string; label: string;
  type: "text" | "number" | "select"; options?: string[];
};

const GEOLOGY_FIELDS: FieldDef[] = [
  { key: "rock_class", label: "围岩级别", type: "select", options: ["I", "II", "III", "IV", "V"] },
  { key: "coal_thickness", label: "煤层厚度 (m)", type: "number" },
  { key: "coal_dip_angle", label: "煤层倾角 (°)", type: "number" },
  { key: "gas_level", label: "瓦斯等级", type: "select", options: ["低瓦斯", "高瓦斯", "突出"] },
  { key: "hydro_type", label: "水文地质类型", type: "select", options: ["简单", "中等", "复杂", "复杂水文地质"] },
  { key: "geo_structure", label: "地质构造特征", type: "text" },
  { key: "spontaneous_combustion", label: "自燃倾向性", type: "select", options: ["不易自燃", "自燃", "容易自燃"] },
];

const ROADWAY_FIELDS: FieldDef[] = [
  { key: "roadway_type", label: "巷道类型", type: "select", options: ["进风巷", "回风巷", "高抽巷", "低抽巷", "切巷", "运输巷", "联络巷", "石门"] },
  { key: "excavation_type", label: "掘进类型", type: "select", options: ["煤巷", "岩巷", "半煤岩巷"] },
  { key: "section_form", label: "断面形式", type: "select", options: ["矩形", "拱形", "梯形"] },
  { key: "section_width", label: "断面宽度 (m)", type: "number" },
  { key: "section_height", label: "断面高度 (m)", type: "number" },
  { key: "excavation_length", label: "掘进长度 (m)", type: "number" },
  { key: "service_years", label: "服务年限 (年)", type: "number" },
];

const EQUIP_FIELDS: FieldDef[] = [
  { key: "dig_method", label: "掘进方式", type: "select", options: ["综掘", "炮掘", "手工掘进"] },
  { key: "dig_equipment", label: "掘进设备型号", type: "text" },
  { key: "transport_method", label: "运输方式", type: "text" },
];

const ALL_FIELDS = [...GEOLOGY_FIELDS, ...ROADWAY_FIELDS, ...EQUIP_FIELDS];

/** 参数中文标签映射（用于只读展示） */
const PARAM_LABELS: Record<string, string> = Object.fromEntries(
  ALL_FIELDS.map(f => [f.key, f.label])
);

const SOURCE_BADGE: Record<string, { label: string; color: string }> = {
  template: { label: "模板", color: "bg-slate-200 text-slate-600" },
  calc_engine: { label: "计算引擎", color: "bg-blue-100 text-blue-700" },
  rule_match: { label: "规则匹配", color: "bg-purple-100 text-purple-700" },
  ai: { label: "AI 生成", color: "bg-green-100 text-green-700" },
  ai_polished: { label: "AI 润色", color: "bg-emerald-100 text-emerald-700" },
  group_standard: { label: "集团标准", color: "bg-amber-100 text-amber-700" },
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [projectParams, setProjectParams] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [generating, setGenerating] = useState(false);
  const [generateResult, setGenerateResult] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [expandedChapter, setExpandedChapter] = useState<string | null>(null);

  // 七层流水线状态
  const initPipeline = (): PipelineState => ({
    layers: Object.fromEntries(PIPELINE_LAYERS.map(l => [l.id, "pending" as LayerState])),
    chapters: [],
    totalChapters: 19,
    doneChapters: 0,
    totalWords: 0,
    elapsedSeconds: 0,
  });
  const [pipeline, setPipeline] = useState<PipelineState>(initPipeline());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  // 参数编辑状态
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  // 加载项目数据
  const fetchProject = useCallback(async () => {
    setLoading(true);
    try {
      const [projRes, paramsRes] = await Promise.allSettled([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/params`),
      ]);
      if (projRes.status === "fulfilled") setProject(projRes.value.data?.data);
      if (paramsRes.status === "fulfilled") setProjectParams(paramsRes.value.data?.data);
      try {
        const docsRes = await api.get(`/projects/${projectId}/documents`);
        setDocuments(docsRes.data?.data || []);
      } catch { /* 静默 */ }
    } catch (e: any) {
      alert("加载项目失败: " + (e.response?.data?.detail || e.message));
    } finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => { fetchProject(); }, [fetchProject]);

  // 进入编辑模式
  const startEditing = () => {
    const form: Record<string, any> = {};
    ALL_FIELDS.forEach(f => {
      form[f.key] = projectParams?.[f.key] ?? "";
    });
    setEditForm(form);
    setEditing(true);
  };

  // 保存参数
  const handleSaveParams = async () => {
    setSaving(true);
    try {
      // 数值类型转换，空字符串转 null
      const payload: Record<string, any> = {};
      ALL_FIELDS.forEach(f => {
        const val = editForm[f.key];
        if (val === "" || val === null || val === undefined) {
          payload[f.key] = null;
        } else if (f.type === "number") {
          payload[f.key] = Number(val);
        } else {
          payload[f.key] = val;
        }
      });
      const res = await api.put(`/projects/${projectId}/params`, payload);
      setProjectParams(res.data?.data);
      setEditing(false);
    } catch (e: any) {
      alert("保存失败: " + (e.response?.data?.detail || e.message));
    } finally { setSaving(false); }
  };

  // 一键生成（SSE 流式进度推送 + 兜底 fallback）
  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateResult(null);
    const fresh = initPipeline();
    setPipeline(fresh);
    startTimeRef.current = Date.now();

    // 计时器：每秒更新已用时间
    timerRef.current = setInterval(() => {
      setPipeline(prev => ({ ...prev, elapsedSeconds: Math.round((Date.now() - startTimeRef.current) / 1000) }));
    }, 1000);

    // 尝试 SSE 订阅
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const sseUrl = `${baseUrl}/projects/${projectId}/generate/stream`;

    let sseSupported = false;
    try {
      const es = new EventSource(`${sseUrl}?token=${token}`);
      sseSupported = true;

      es.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          // data 格式: { type: 'layer_start'|'layer_done'|'chapter_start'|'chapter_done'|'done', ... }
          setPipeline(prev => {
            const next = { ...prev, layers: { ...prev.layers }, chapters: [...prev.chapters] };

            if (data.type === "layer_start" && data.layer_id) {
              next.layers[data.layer_id] = "running";
            } else if (data.type === "layer_done" && data.layer_id) {
              next.layers[data.layer_id] = "done";
            } else if (data.type === "chapter_start") {
              // 添加或更新章节状态
              const idx = next.chapters.findIndex(c => c.name === data.chapter);
              if (idx >= 0) { next.chapters[idx] = { ...next.chapters[idx], layer: data.layer_id || "" }; }
              else { next.chapters.push({ name: data.chapter, layer: data.layer_id || "", done: false }); }
            } else if (data.type === "chapter_done") {
              const idx = next.chapters.findIndex(c => c.name === data.chapter);
              if (idx >= 0) { next.chapters[idx] = { ...next.chapters[idx], done: true, words: data.words, layer: "" }; }
              next.doneChapters = next.chapters.filter(c => c.done).length;
              next.totalWords = next.chapters.reduce((s, c) => s + (c.words || 0), 0);
            } else if (data.type === "done") {
              // SSE 完成
              PIPELINE_LAYERS.forEach(l => { next.layers[l.id] = "done"; });
            }
            return next;
          });

          if (data.type === "done") {
            es.close();
            if (timerRef.current) clearInterval(timerRef.current);
            // 请求最终结果
            api.post(`/projects/${projectId}/generate`).then(res => {
              setGenerateResult(res.data?.data);
              return api.get(`/projects/${projectId}/documents`);
            }).then(r => {
              setDocuments(r.data?.data || []);
            }).catch(() => {}).finally(() => setGenerating(false));
          }
        } catch { /* 忽略解析错误 */ }
      };

      es.onerror = () => {
        es.close();
        sseSupported = false;
        // 降级为普通 HTTP 请求
        fallbackGenerate();
      };
    } catch {
      sseSupported = false;
    }

    if (!sseSupported) {
      fallbackGenerate();
    }
  };

  // 兜底：普通 HTTP 生成（无 SSE 时使用，同时模拟流水线动画）
  const fallbackGenerate = async () => {
    // 依次模拟七层流水线动画
    const layerIds = PIPELINE_LAYERS.map(l => l.id);
    const animateLayer = async (idx: number) => {
      if (idx >= layerIds.length) return;
      setPipeline(prev => ({ ...prev, layers: { ...prev.layers, [layerIds[idx]]: "running" } }));
      await new Promise(r => setTimeout(r, 800 + Math.random() * 400));
      setPipeline(prev => ({ ...prev, layers: { ...prev.layers, [layerIds[idx]]: "done" } }));
    };

    // 章节动画：边等待API边逐章展示
    const chapterNames = [
      "编制依据","矿井概况","地质概况","巷道布置与断面",
      "支护设计","掘进施工工艺","通风系统","运输系统",
      "供电系统","管路系统","劳动组织","主要技术经济指标",
      "安全管理","安全技术措施","矿压监测","灾害预防处理",
      "避灾路线","合规校验","附图附录"
    ];

    // 同时发起 API 请求
    const generatePromise = api.post(`/projects/${projectId}/generate`);

    // 逐层动画
    for (let i = 0; i < layerIds.length; i++) {
      await animateLayer(i);
      // 每层完成时更新若干章节
      const batchStart = Math.floor((i / layerIds.length) * chapterNames.length);
      const batchEnd = Math.floor(((i + 1) / layerIds.length) * chapterNames.length);
      const batchChapters = chapterNames.slice(batchStart, batchEnd).map(name => ({
        name, layer: "", done: true, words: Math.floor(6000 + Math.random() * 6000)
      }));
      setPipeline(prev => {
        const updated = [...prev.chapters];
        batchChapters.forEach(c => {
          if (!updated.find(x => x.name === c.name)) updated.push(c);
        });
        return {
          ...prev,
          chapters: updated,
          doneChapters: updated.filter(c => c.done).length,
          totalWords: updated.reduce((s, c) => s + (c.words || 0), 0),
        };
      });
    }

    try {
      const res = await generatePromise;
      setGenerateResult(res.data?.data);
      const docsRes = await api.get(`/projects/${projectId}/documents`);
      setDocuments(docsRes.data?.data || []);
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      alert("生成失败: " + (typeof detail === "string" ? detail : JSON.stringify(detail)));
    } finally {
      if (timerRef.current) clearInterval(timerRef.current);
      setGenerating(false);
    }
  };

  // 下载文档
  const handleDownload = async (filename: string) => {
    try {
      const res = await api.get(`/projects/${projectId}/documents/download`, {
        params: { filename },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url; a.download = filename; a.click();
      window.URL.revokeObjectURL(url);
    } catch { alert("下载失败"); }
  };

  if (loading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-slate-300" /></div>;
  }

  // 渲染字段输入控件
  const renderField = (f: FieldDef) => {
    const val = editForm[f.key] ?? "";
    if (f.type === "select" && f.options) {
      return (
        <Select value={String(val)} onValueChange={(v) => setEditForm(prev => ({ ...prev, [f.key]: v }))}>
          <SelectTrigger className="h-8 text-sm"><SelectValue placeholder="请选择" /></SelectTrigger>
          <SelectContent>
            {f.options.map(opt => (
              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }
    return (
      <Input
        type={f.type === "number" ? "number" : "text"}
        className="h-8 text-sm"
        placeholder={f.label}
        value={val}
        onChange={(e) => setEditForm(prev => ({ ...prev, [f.key]: e.target.value }))}
      />
    );
  };

  // 渲染字段组
  const renderFieldGroup = (title: string, fields: FieldDef[]) => (
    <div className="space-y-2.5">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</h4>
      {fields.map(f => (
        <div key={f.key} className="space-y-1">
          <Label className="text-xs text-slate-500">{f.label}</Label>
          {renderField(f)}
        </div>
      ))}
    </div>
  );

  // 只读参数展示
  const paramEntries: [string, string][] = projectParams
    ? Object.entries(projectParams)
        .filter(([k]) => !["id", "project_id", "created_at", "updated_at", "created_by", "tenant_id"].includes(k))
        .filter(([, v]) => v !== null && v !== "")
        .map(([k, v]) => [PARAM_LABELS[k] || k, String(v)])
    : [];

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard/projects">
            <Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="h-4 w-4" /></Button>
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white">
              {project?.face_name || project?.name || `项目 #${projectId}`}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {project?.mine_name || ""} · {({draft:"草稿",in_progress:"进行中",completed:"已完成"} as Record<string,string>)[project?.status || ""] || project?.status || "草稿"}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button className="gap-2" onClick={handleGenerate} disabled={generating || editing}>
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            {generating ? "生成中..." : "一键生成规程"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* 左侧：项目参数（编辑/只读切换） */}
        <Card className="col-span-4">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm">项目参数</CardTitle>
            {!editing ? (
              <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs" onClick={startEditing}>
                <Pencil className="h-3 w-3" />编辑
              </Button>
            ) : (
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs" onClick={() => setEditing(false)} disabled={saving}>
                  <X className="h-3 w-3" />取消
                </Button>
                <Button size="sm" className="h-7 gap-1 text-xs" onClick={handleSaveParams} disabled={saving}>
                  {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                  保存
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {editing ? (
              /* 编辑模式：分组表单 */
              <div className="space-y-5 max-h-[600px] overflow-y-auto pr-1">
                {renderFieldGroup("🪨 地质条件", GEOLOGY_FIELDS)}
                <hr className="border-dashed" />
                {renderFieldGroup("🚇 巷道参数", ROADWAY_FIELDS)}
                <hr className="border-dashed" />
                {renderFieldGroup("⚙️ 设备配置", EQUIP_FIELDS)}
              </div>
            ) : (
              /* 只读模式 */
              <div className="space-y-2">
                {paramEntries.length > 0 ? paramEntries.map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">{k}</span>
                    <span className="font-medium">{v}</span>
                  </div>
                )) : (
                  <div className="py-6 text-center">
                    <p className="text-sm text-slate-400 mb-3">暂未填写参数</p>
                    <Button variant="outline" size="sm" className="gap-1" onClick={startEditing}>
                      <Pencil className="h-3.5 w-3.5" />填写参数
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 右侧：文档 */}
        <div className="col-span-8 space-y-4">
          {/* 已生成文档列表 */}
          {documents.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">已生成文档</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {documents.map((doc: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border px-4 py-2.5">
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-blue-500" />
                      <span className="text-sm font-medium">{doc.filename}</span>
                      <span className="text-xs text-slate-400">{doc.size_kb} KB</span>
                    </div>
                    <Button size="sm" variant="outline" className="gap-1" onClick={() => handleDownload(doc.filename)}>
                      <Download className="h-3.5 w-3.5" />下载
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* 生成结果预览 */}
          {generateResult ? (
            <>
              <div className="grid grid-cols-4 gap-3">
                <Card><CardContent className="py-3 text-center"><div className="text-xs text-slate-500">文件</div><div className="mt-1 text-sm font-bold truncate">{generateResult.file_path || "-"}</div></CardContent></Card>
                <Card><CardContent className="py-3 text-center"><div className="text-xs text-slate-500">章节数</div><div className="mt-1 text-lg font-bold">{generateResult.chapters?.length || 0}</div></CardContent></Card>
                <Card><CardContent className="py-3 text-center"><div className="text-xs text-slate-500">预警数</div><div className="mt-1 text-lg font-bold text-red-500">{generateResult.total_warnings || 0}</div></CardContent></Card>
                <Card className="border-green-200 bg-green-50"><CardContent className="flex items-center justify-center gap-2 py-3"><CheckCircle2 className="h-5 w-5 text-green-600" /><span className="font-medium text-green-700">生成完成</span></CardContent></Card>
              </div>

              {generateResult.chapters && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2"><FileText className="h-4 w-4" />文档结构预览</span>
                      <span className="text-xs font-normal text-slate-400">共 {generateResult.chapters?.length || 0} 章</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-1">
                    {generateResult.chapters.map((ch: any, i: number) => {
                      const chKey = ch.chapter_no || ch.no || `ch-${i}`;
                      const isExpanded = expandedChapter === chKey;
                      return (
                        <div key={i} className="overflow-hidden rounded-lg border">
                          <div
                            className={`flex cursor-pointer items-center justify-between px-4 py-2.5 transition-colors hover:bg-slate-50 ${ch.has_warning ? "bg-red-50/50" : ""}`}
                            onClick={() => setExpandedChapter(isExpanded ? null : chKey)}
                          >
                            <div className="flex items-center gap-3">
                              {isExpanded ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
                              <span className="font-mono text-xs text-slate-400">{chKey}</span>
                              <span className="font-medium">{ch.title}</span>
                              {ch.source && <span className={`rounded-full px-2 py-0.5 text-xs ${SOURCE_BADGE[ch.source]?.color || "bg-slate-100"}`}>{SOURCE_BADGE[ch.source]?.label || ch.source}</span>}
                            </div>
                            {ch.has_warning && <AlertTriangle className="h-4 w-4 text-red-500" />}
                          </div>
                          {isExpanded && (
                            <div className="border-t bg-slate-50 px-4 py-3 space-y-2">
                              {ch.has_warning && (
                                <div className="mb-2 rounded bg-red-50 px-3 py-2 text-sm text-red-700 flex items-center gap-2">
                                  <AlertTriangle className="h-4 w-4 shrink-0" />
                                  <span>本章节存在合规预警，请重点审查</span>
                                </div>
                              )}
                              <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-relaxed font-sans">{ch.content}</pre>
                              <ChapterFeedback
                                projectId={projectId}
                                chapterNo={chKey}
                                chapterTitle={ch.title}
                                content={ch.content || ""}
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              )}
            </>
          ) : !generating && (
            <Card className="flex h-64 items-center justify-center">
              <div className="text-center text-slate-400">
                <FileText className="mx-auto mb-3 h-12 w-12 opacity-30" />
                <p>点击&quot;一键生成规程&quot;开始</p>
                <p className="mt-1 text-xs">系统将自动匹配规则、计算校核、生成 Word 文档</p>
              </div>
            </Card>
          )}

          {generating && (
            <AIPipelineProgress state={pipeline} />
          )}
        </div>
      </div>
    </div>
  );
}
