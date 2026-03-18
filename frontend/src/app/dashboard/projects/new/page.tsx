"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  MapPin,
  Mountain,
  Ruler,
  Wrench,
  Zap,
} from "lucide-react";
import api from "@/lib/api";

/* ============ 步骤定义 ============ */
const STEPS = [
  { no: 1, title: "基本信息", icon: MapPin, desc: "项目名称与矿井信息" },
  { no: 2, title: "地质条件", icon: Mountain, desc: "围岩、瓦斯、水文参数" },
  { no: 3, title: "巷道参数", icon: Ruler, desc: "断面形式与尺寸" },
  { no: 4, title: "设备配置", icon: Wrench, desc: "掘进方式与装备" },
  { no: 5, title: "确认提交", icon: Zap, desc: "检查参数并创建项目" },
];

/* ============ 表单初始值 ============ */
const INIT_FORM = {
  // Step 1
  face_name: "",
  mine_id: "",
  // Step 2
  rock_class: "",
  coal_thickness: "",
  coal_dip_angle: "",
  gas_level: "",
  hydro_type: "",
  geo_structure: "",
  spontaneous_combustion: "",
  // Step 3
  roadway_type: "",
  excavation_type: "",
  section_form: "",
  section_width: "",
  section_height: "",
  excavation_length: "",
  service_years: "",
  // Step 4
  dig_method: "",
  dig_equipment: "",
  transport_method: "",
};

export default function NewProjectWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(INIT_FORM);
  const [mines, setMines] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [loadedMines, setLoadedMines] = useState(false);

  // 加载矿井列表
  const loadMines = async () => {
    if (loadedMines) return;
    try {
      const res = await api.get("/system/mines");
      setMines(res.data?.data || []);
    } catch { /* 静默 */ }
    setLoadedMines(true);
  };

  // 首次渲染时加载
  if (!loadedMines) loadMines();

  const set = (key: string, val: string) =>
    setForm((prev) => ({ ...prev, [key]: val }));

  // 提交创建
  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // 1. 创建项目
      const projRes = await api.post("/projects", {
        face_name: form.face_name,
        mine_id: Number(form.mine_id),
      });
      const projectId = projRes.data?.data?.id;

      // 2. 填写参数
      const params: Record<string, any> = {};
      const numFields = [
        "coal_thickness", "coal_dip_angle", "section_width",
        "section_height", "excavation_length", "service_years",
      ];
      Object.entries(form).forEach(([k, v]) => {
        if (k === "face_name" || k === "mine_id") return;
        if (!v) return;
        params[k] = numFields.includes(k) ? Number(v) : v;
      });
      await api.put(`/projects/${projectId}/params`, params);

      // 跳转到项目详情
      router.push(`/dashboard/projects/${projectId}`);
    } catch (e: any) {
      alert("创建失败: " + (e.response?.data?.detail || e.message));
    } finally {
      setSubmitting(false);
    }
  };

  // 渲染输入组件
  const renderInput = (key: string, label: string, type = "text") => (
    <div className="space-y-1.5">
      <Label className="text-sm text-slate-600">{label}</Label>
      <Input
        type={type}
        value={(form as any)[key]}
        onChange={(e) => set(key, e.target.value)}
        placeholder={label}
        className="h-9"
      />
    </div>
  );

  const renderSelect = (key: string, label: string, options: string[]) => (
    <div className="space-y-1.5">
      <Label className="text-sm text-slate-600">{label}</Label>
      <Select value={(form as any)[key]} onValueChange={(v) => set(key, v)}>
        <SelectTrigger className="h-9">
          <SelectValue placeholder="请选择" />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o} value={o}>{o}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );

  // 各步骤内容
  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="grid gap-4">
            {renderInput("face_name", "工作面名称")}
            <div className="space-y-1.5">
              <Label className="text-sm text-slate-600">所属矿井</Label>
              <Select value={form.mine_id || undefined} onValueChange={(v) => set("mine_id", v ?? "")}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="选择矿井" />
                </SelectTrigger>
                <SelectContent>
                  {mines.map((m: any) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="grid grid-cols-2 gap-4">
            {renderSelect("rock_class", "围岩级别", ["I","II","III","IV","V"])}
            {renderInput("coal_thickness", "煤层厚度 (m)", "number")}
            {renderInput("coal_dip_angle", "煤层倾角 (°)", "number")}
            {renderSelect("gas_level", "瓦斯等级", ["低瓦斯","高瓦斯","突出"])}
            {renderSelect("hydro_type", "水文地质类型", ["简单","中等","复杂","复杂水文地质"])}
            {renderInput("geo_structure", "地质构造特征")}
            {renderSelect("spontaneous_combustion", "自燃倾向性", ["不易自燃","自燃","容易自燃"])}
          </div>
        );
      case 3:
        return (
          <div className="grid grid-cols-2 gap-4">
            {renderSelect("roadway_type", "巷道类型", ["进风巷","回风巷","运输巷","联络巷","石门"])}
            {renderSelect("excavation_type", "掘进类型", ["煤巷","岩巷","半煤岩巷"])}
            {renderSelect("section_form", "断面形式", ["矩形","拱形","梯形"])}
            {renderInput("section_width", "断面宽度 (m)", "number")}
            {renderInput("section_height", "断面高度 (m)", "number")}
            {renderInput("excavation_length", "掘进长度 (m)", "number")}
            {renderInput("service_years", "服务年限 (年)", "number")}
          </div>
        );
      case 4:
        return (
          <div className="grid grid-cols-2 gap-4">
            {renderSelect("dig_method", "掘进方式", ["综掘","炮掘","手工掘进"])}
            {renderInput("dig_equipment", "掘进设备型号")}
            {renderInput("transport_method", "运输方式")}
          </div>
        );
      case 5:
        // 确认页：展示所有已填参数
        const filled = Object.entries(form).filter(([, v]) => v);
        const LABELS: Record<string, string> = {
          face_name: "工作面名称", mine_id: "矿井 ID",
          rock_class: "围岩级别", coal_thickness: "煤层厚度",
          coal_dip_angle: "煤层倾角", gas_level: "瓦斯等级",
          hydro_type: "水文地质", geo_structure: "地质构造",
          spontaneous_combustion: "自燃倾向性", roadway_type: "巷道类型",
          excavation_type: "掘进类型", section_form: "断面形式",
          section_width: "断面宽度", section_height: "断面高度",
          excavation_length: "掘进长度", service_years: "服务年限",
          dig_method: "掘进方式", dig_equipment: "设备型号",
          transport_method: "运输方式",
        };
        return (
          <div className="space-y-3">
            <p className="text-sm text-slate-500 mb-4">
              请确认以下参数无误后点击"创建项目"
            </p>
            <div className="grid grid-cols-2 gap-2">
              {filled.map(([k, v]) => (
                <div key={k} className="flex items-center justify-between rounded bg-slate-50 px-3 py-2">
                  <span className="text-xs text-slate-500">{LABELS[k] || k}</span>
                  <span className="text-sm font-medium">{v}</span>
                </div>
              ))}
            </div>
          </div>
        );
    }
  };

  const canNext = () => {
    if (step === 1) return form.face_name && form.mine_id;
    return true;
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* 页头 */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => router.push("/dashboard/projects")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white">新建规程项目</h2>
          <p className="text-sm text-slate-500">按步骤填写工程参数，一站式创建掘进作业规程</p>
        </div>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s.no} className="flex items-center gap-2">
            <button
              onClick={() => s.no < step && setStep(s.no)}
              className={`flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
                step === s.no
                  ? "bg-blue-600 text-white shadow-md shadow-blue-200"
                  : step > s.no
                  ? "bg-green-100 text-green-700 cursor-pointer hover:bg-green-200"
                  : "bg-slate-100 text-slate-400"
              }`}
            >
              {step > s.no ? <Check className="h-3.5 w-3.5" /> : <s.icon className="h-3.5 w-3.5" />}
              {s.title}
            </button>
            {i < STEPS.length - 1 && (
              <div className={`h-px w-6 ${step > s.no ? "bg-green-300" : "bg-slate-200"}`} />
            )}
          </div>
        ))}
      </div>

      {/* 表单卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            {(() => { const Icon = STEPS[step - 1].icon; return <Icon className="h-5 w-5 text-blue-500" />; })()}
            {STEPS[step - 1].title}
          </CardTitle>
          <p className="text-sm text-slate-500">{STEPS[step - 1].desc}</p>
        </CardHeader>
        <CardContent>{renderStepContent()}</CardContent>
      </Card>

      {/* 导航按钮 */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setStep(step - 1)}
          disabled={step === 1}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          上一步
        </Button>
        {step < 5 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canNext()} className="gap-2">
            下一步
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={handleSubmit} disabled={submitting} className="gap-2 bg-blue-600 hover:bg-blue-700">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            {submitting ? "创建中..." : "创建项目"}
          </Button>
        )}
      </div>
    </div>
  );
}
