"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Calculator,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Info,
  Wind,
  Timer,
  Loader2,
  Cable,
  ClipboardCheck,
  Siren,
  CheckCircle,
  XCircle,
} from "lucide-react";
import api from "@/lib/api";

/* ===== Tab 定义（6 个） ===== */
const TABS = [
  { key: "support", label: "支护计算", icon: ShieldCheck },
  { key: "vent", label: "通风计算", icon: Wind },
  { key: "cycle", label: "循环作业", icon: Timer },
  { key: "cable", label: "锚索计算", icon: Cable },
  { key: "compliance", label: "合规校验", icon: ClipboardCheck },
  { key: "conflicts", label: "规则冲突", icon: Siren },
] as const;
type Tab = (typeof TABS)[number]["key"];

const ROCK_CLASSES = ["I", "II", "III", "IV", "V"];
const SECTION_FORMS = ["矩形", "拱形", "梯形"];
const GAS_LEVELS = ["低瓦斯", "高瓦斯", "突出"];
const DIG_METHODS = ["钻爆法", "综掘"];

/* 预警等级颜色 */
const LEVEL_COLORS: Record<string, { bg: string; text: string; icon: any }> = {
  error: { bg: "bg-red-50", text: "text-red-700", icon: ShieldAlert },
  warning: { bg: "bg-amber-50", text: "text-amber-700", icon: AlertTriangle },
  info: { bg: "bg-blue-50", text: "text-blue-700", icon: Info },
};

/* 合规状态颜色 */
const STATUS_COLORS: Record<string, { bg: string; text: string; icon: any }> = {
  pass: { bg: "bg-green-50", text: "text-green-700", icon: CheckCircle },
  fail: { bg: "bg-red-50", text: "text-red-700", icon: XCircle },
  warning: { bg: "bg-amber-50", text: "text-amber-700", icon: AlertTriangle },
};

export default function CalcPage() {
  const [tab, setTab] = useState<Tab>("support");
  const [loading, setLoading] = useState(false);

  /* ===== 支护 ===== */
  const [supportForm, setSupportForm] = useState({
    rock_class: "III", section_form: "拱形",
    section_width: 5.0, section_height: 4.0, rock_density: 2.5,
    bolt_length: 2.4, bolt_diameter: 22,
    bolt_spacing: "", bolt_row_spacing: "",
    cable_count: 0, cable_strength: 260,
  });
  const [supportResult, setSupportResult] = useState<any>(null);

  /* ===== 通风 ===== */
  const [ventForm, setVentForm] = useState({
    gas_emission: 3.0, gas_level: "高瓦斯",
    section_area: 20.0, excavation_length: 560,
    max_workers: 20, explosive_per_cycle: 0,
    design_air_volume: "", design_wind_speed: "",
  });
  const [ventResult, setVentResult] = useState<any>(null);

  /* ===== 循环 ===== */
  const [cycleForm, setCycleForm] = useState({
    dig_method: "钻爆法",
    hole_depth: 2.0, utilization_rate: 0.85, cut_depth: 0.8,
    t_drilling: 60, t_charging: 20, t_blasting: 15, t_ventilation: 30,
    t_mucking: 90, t_support: 60, t_other: 15,
    shifts_per_day: 3, hours_per_shift: 8, effective_rate: 0.75,
    work_days_per_month: 26, design_monthly_advance: "",
  });
  const [cycleResult, setCycleResult] = useState<any>(null);

  /* ===== 锚索 ===== */
  const [cableForm, setCableForm] = useState({
    rock_class: "III", section_form: "拱形",
    section_width: 5.0, section_height: 3.6,
    rock_density: 2.5, cable_length: 6.3,
    cable_diameter: 17.8, cable_strength: 353,
    cable_count: "", pretension: "",
    row_spacing: 1600,
  });
  const [cableResult, setCableResult] = useState<any>(null);

  /* ===== 合规 ===== */
  const [compForm, setCompForm] = useState({
    rock_class: "III", gas_level: "低瓦斯",
    coal_thickness: 3.0, spontaneous_combustion: "不易自燃",
    section_form: "矩形", section_width: 4.5,
    section_height: 3.2, excavation_length: 600,
    bolt_spacing: 800, bolt_row_spacing: 800,
    cable_count: 3, gas_emission: 1.0,
    design_air_volume: 0, max_workers: 25,
  });
  const [compResult, setCompResult] = useState<any>(null);

  /* ===== 规则冲突 ===== */
  const [conflictGroupId, setConflictGroupId] = useState("");
  const [conflictResult, setConflictResult] = useState<any>(null);

  /* ===== 统一提交 ===== */
  const handleCalc = async () => {
    setLoading(true);
    try {
      if (tab === "support") {
        const payload: any = { ...supportForm,
          bolt_spacing: supportForm.bolt_spacing ? parseFloat(supportForm.bolt_spacing as string) : null,
          bolt_row_spacing: supportForm.bolt_row_spacing ? parseFloat(supportForm.bolt_row_spacing as string) : null,
        };
        const res = await api.post("/calc/support", payload);
        setSupportResult(res.data?.data);
      } else if (tab === "vent") {
        const payload: any = { ...ventForm,
          design_air_volume: ventForm.design_air_volume ? parseFloat(ventForm.design_air_volume as string) : null,
          design_wind_speed: ventForm.design_wind_speed ? parseFloat(ventForm.design_wind_speed as string) : null,
        };
        const res = await api.post("/calc/ventilation", payload);
        setVentResult(res.data?.data);
      } else if (tab === "cycle") {
        const payload: any = { ...cycleForm,
          design_monthly_advance: cycleForm.design_monthly_advance ? parseFloat(cycleForm.design_monthly_advance as string) : null,
        };
        const res = await api.post("/calc/cycle", payload);
        setCycleResult(res.data?.data);
      } else if (tab === "cable") {
        const payload: any = { ...cableForm,
          cable_count: cableForm.cable_count ? parseInt(cableForm.cable_count as string) : null,
          pretension: cableForm.pretension ? parseFloat(cableForm.pretension as string) : null,
        };
        const res = await api.post("/calc/cable", payload);
        setCableResult(res.data?.data);
      } else if (tab === "compliance") {
        const res = await api.post("/calc/compliance", compForm);
        setCompResult(res.data?.data);
      } else if (tab === "conflicts") {
        const params = conflictGroupId ? { group_id: parseInt(conflictGroupId) } : {};
        const res = await api.get("/calc/rule-conflicts", { params });
        setConflictResult(res.data?.data);
      }
    } catch (e: any) {
      alert("计算失败: " + (e.response?.data?.detail || e.message));
    } finally { setLoading(false); }
  };

  /* 渲染预警列表 */
  const renderWarnings = (warnings: any[]) => {
    if (!warnings?.length) return null;
    return (
      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase text-slate-500">合规校核预警</h4>
        {warnings.map((w: any, i: number) => {
          const style = LEVEL_COLORS[w.level] || LEVEL_COLORS.info;
          const Icon = style.icon;
          return (
            <div key={i} className={`flex items-start gap-2 rounded-md px-3 py-2 ${style.bg}`}>
              <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${style.text}`} />
              <div className={`text-sm ${style.text}`}>
                <span className="font-medium">{w.field}：</span>{w.message}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  /* 结果卡片 */
  const ResultCard = ({ icon, data }: { icon: React.ReactNode; data: [string, string, string?][] }) => (
    <div className="grid grid-cols-2 gap-3 text-sm">
      {data.map(([label, value, color]) => (
        <div key={label} className={`rounded-md p-3 ${color || "bg-slate-50"}`}>
          <div className={`text-xs ${color ? color.replace("bg-", "text-").replace("-50", "-500") : "text-slate-500"}`}>{label}</div>
          <div className={`text-lg font-bold ${color ? color.replace("bg-", "text-").replace("-50", "-700") : ""}`}>{value}</div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white">计算校验</h2>
          <p className="mt-1 text-sm text-slate-500">支护 · 通风 · 循环 · 锚索 · 合规校验 · 规则冲突检测</p>
        </div>
        <Button className="gap-2" onClick={handleCalc} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
          {tab === "conflicts" ? "检测冲突" : tab === "compliance" ? "开始校验" : "开始计算"}
        </Button>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-1 rounded-lg border bg-slate-100 p-1 dark:bg-slate-900">
        {TABS.map((t) => (
          <button key={t.key}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm transition-colors ${
              tab === t.key ? "bg-white font-medium shadow dark:bg-slate-800" : "text-slate-500 hover:text-slate-700"
            }`}
            onClick={() => setTab(t.key)}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ===== 支护计算 ===== */}
        {tab === "support" && (
          <>
            <Card>
              <CardHeader><CardTitle className="text-base">输入参数</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">围岩级别</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={supportForm.rock_class} onChange={e => setSupportForm({ ...supportForm, rock_class: e.target.value })}>{ROCK_CLASSES.map(r => <option key={r}>{r}</option>)}</select></div>
                  <div><label className="mb-1 block text-xs font-medium">断面形式</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={supportForm.section_form} onChange={e => setSupportForm({ ...supportForm, section_form: e.target.value })}>{SECTION_FORMS.map(s => <option key={s}>{s}</option>)}</select></div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">净宽 (m)</label><Input type="number" value={supportForm.section_width} onChange={e => setSupportForm({ ...supportForm, section_width: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">净高 (m)</label><Input type="number" value={supportForm.section_height} onChange={e => setSupportForm({ ...supportForm, section_height: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">容重 (t/m³)</label><Input type="number" value={supportForm.rock_density} onChange={e => setSupportForm({ ...supportForm, rock_density: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">锚杆长度 (m)</label><Input type="number" value={supportForm.bolt_length} onChange={e => setSupportForm({ ...supportForm, bolt_length: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">锚杆直径 (mm)</label><Input type="number" value={supportForm.bolt_diameter} onChange={e => setSupportForm({ ...supportForm, bolt_diameter: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">指定间距 (mm) <span className="text-slate-400">可选</span></label><Input placeholder="留空自动计算" value={supportForm.bolt_spacing} onChange={e => setSupportForm({ ...supportForm, bolt_spacing: e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">指定排距 (mm) <span className="text-slate-400">可选</span></label><Input placeholder="留空自动计算" value={supportForm.bolt_row_spacing} onChange={e => setSupportForm({ ...supportForm, bolt_row_spacing: e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">锚索数量</label><Input type="number" value={supportForm.cable_count} onChange={e => setSupportForm({ ...supportForm, cable_count: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">锚索破断力 (kN)</label><Input type="number" value={supportForm.cable_strength} onChange={e => setSupportForm({ ...supportForm, cable_strength: +e.target.value })} /></div>
                </div>
              </CardContent>
            </Card>
            {supportResult && (
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2 text-base">{supportResult.is_compliant ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <ShieldAlert className="h-5 w-5 text-red-500" />} 支护计算结果</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <ResultCard icon={null} data={[
                    ["净断面积", `${supportResult.section_area} m²`],
                    ["单根锚固力", `${supportResult.bolt_force} kN`],
                    ["最大间距", `${supportResult.max_bolt_spacing} mm`],
                    ["最大排距", `${supportResult.max_bolt_row_spacing} mm`],
                    ["推荐每排", `${supportResult.recommended_bolt_count_per_row} 根`],
                    ["最少锚索", `${supportResult.min_cable_count} 根`],
                    ["安全系数", `${supportResult.safety_factor}`],
                    ["支护密度", `${supportResult.support_density} 根/m²`],
                  ]} />
                  {renderWarnings(supportResult.warnings)}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* ===== 通风计算 ===== */}
        {tab === "vent" && (
          <>
            <Card>
              <CardHeader><CardTitle className="text-base">输入参数</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">瓦斯涌出量 (m³/min)</label><Input type="number" value={ventForm.gas_emission} onChange={e => setVentForm({ ...ventForm, gas_emission: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">瓦斯等级</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={ventForm.gas_level} onChange={e => setVentForm({ ...ventForm, gas_level: e.target.value })}>{GAS_LEVELS.map(g => <option key={g}>{g}</option>)}</select></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">净断面积 (m²)</label><Input type="number" value={ventForm.section_area} onChange={e => setVentForm({ ...ventForm, section_area: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">掘进长度 (m)</label><Input type="number" value={ventForm.excavation_length} onChange={e => setVentForm({ ...ventForm, excavation_length: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">最多人数</label><Input type="number" value={ventForm.max_workers} onChange={e => setVentForm({ ...ventForm, max_workers: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">炸药消耗 (kg)</label><Input type="number" value={ventForm.explosive_per_cycle} onChange={e => setVentForm({ ...ventForm, explosive_per_cycle: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">设计风量 <span className="text-slate-400">可选</span></label><Input placeholder="留空跳过" value={ventForm.design_air_volume} onChange={e => setVentForm({ ...ventForm, design_air_volume: e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">设计风速 <span className="text-slate-400">可选</span></label><Input placeholder="留空跳过" value={ventForm.design_wind_speed} onChange={e => setVentForm({ ...ventForm, design_wind_speed: e.target.value })} /></div>
                </div>
              </CardContent>
            </Card>
            {ventResult && (
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2 text-base">{ventResult.is_compliant ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <ShieldAlert className="h-5 w-5 text-red-500" />} 通风计算结果</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <ResultCard icon={null} data={[
                    ["瓦斯法需风量", `${ventResult.q_gas} m³/min`, "bg-blue-50"],
                    ["人数法需风量", `${ventResult.q_people} m³/min`, "bg-blue-50"],
                    ["炸药法需风量", `${ventResult.q_explosive} m³/min`, "bg-blue-50"],
                    ["最终需风量", `${ventResult.q_required} m³/min`, "bg-green-50"],
                    ["风速范围", `${ventResult.wind_speed_min}~${ventResult.wind_speed_max} m/s`],
                    ["推荐局扇", `${ventResult.recommended_fan}`],
                  ]} />
                  {renderWarnings(ventResult.warnings)}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* ===== 循环作业 ===== */}
        {tab === "cycle" && (
          <>
            <Card>
              <CardHeader><CardTitle className="text-base">输入参数</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div><label className="mb-1 block text-xs font-medium">掘进方式</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={cycleForm.dig_method} onChange={e => setCycleForm({ ...cycleForm, dig_method: e.target.value })}>{DIG_METHODS.map(d => <option key={d}>{d}</option>)}</select></div>
                {cycleForm.dig_method === "钻爆法" ? (
                  <div className="grid grid-cols-2 gap-3">
                    <div><label className="mb-1 block text-xs font-medium">炮眼深度 (m)</label><Input type="number" value={cycleForm.hole_depth} onChange={e => setCycleForm({ ...cycleForm, hole_depth: +e.target.value })} /></div>
                    <div><label className="mb-1 block text-xs font-medium">利用率</label><Input type="number" step="0.01" value={cycleForm.utilization_rate} onChange={e => setCycleForm({ ...cycleForm, utilization_rate: +e.target.value })} /></div>
                  </div>
                ) : (
                  <div><label className="mb-1 block text-xs font-medium">截割深度 (m)</label><Input type="number" value={cycleForm.cut_depth} onChange={e => setCycleForm({ ...cycleForm, cut_depth: +e.target.value })} /></div>
                )}
                <p className="text-xs font-semibold text-slate-500">工序时间 (min)</p>
                <div className="grid grid-cols-4 gap-2">
                  {(["t_drilling", "t_charging", "t_blasting", "t_ventilation", "t_mucking", "t_support", "t_other"] as const).map(key => (
                    <div key={key}><label className="mb-0.5 block text-[10px] text-slate-400">{{ t_drilling: "打眼", t_charging: "装药", t_blasting: "放炮", t_ventilation: "通风", t_mucking: "出矸", t_support: "支护", t_other: "其他" }[key]}</label><Input type="number" value={cycleForm[key]} onChange={e => setCycleForm({ ...cycleForm, [key]: +e.target.value })} /></div>
                  ))}
                </div>
                <p className="text-xs font-semibold text-slate-500">工作制度</p>
                <div className="grid grid-cols-4 gap-2">
                  <div><label className="mb-0.5 block text-[10px] text-slate-400">日班次</label><Input type="number" value={cycleForm.shifts_per_day} onChange={e => setCycleForm({ ...cycleForm, shifts_per_day: +e.target.value })} /></div>
                  <div><label className="mb-0.5 block text-[10px] text-slate-400">班工时</label><Input type="number" value={cycleForm.hours_per_shift} onChange={e => setCycleForm({ ...cycleForm, hours_per_shift: +e.target.value })} /></div>
                  <div><label className="mb-0.5 block text-[10px] text-slate-400">有效率</label><Input type="number" step="0.01" value={cycleForm.effective_rate} onChange={e => setCycleForm({ ...cycleForm, effective_rate: +e.target.value })} /></div>
                  <div><label className="mb-0.5 block text-[10px] text-slate-400">月工作日</label><Input type="number" value={cycleForm.work_days_per_month} onChange={e => setCycleForm({ ...cycleForm, work_days_per_month: +e.target.value })} /></div>
                </div>
                <div><label className="mb-1 block text-xs font-medium">设计月进尺 (m) <span className="text-slate-400">可选</span></label><Input placeholder="留空跳过" value={cycleForm.design_monthly_advance} onChange={e => setCycleForm({ ...cycleForm, design_monthly_advance: e.target.value })} /></div>
              </CardContent>
            </Card>
            {cycleResult && (
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2 text-base">{cycleResult.is_compliant ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <ShieldAlert className="h-5 w-5 text-red-500" />} 循环作业结果</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <ResultCard icon={null} data={[
                    ["循环进尺", `${cycleResult.cycle_advance} m`, "bg-emerald-50"],
                    ["单循环时间", `${cycleResult.cycle_time} min`, "bg-emerald-50"],
                    ["日循环数", `${cycleResult.cycles_per_day}`],
                    ["日进尺", `${cycleResult.daily_advance} m`],
                    ["月进尺", `${cycleResult.monthly_advance} m`, "bg-purple-50"],
                    ["循环率", `${cycleResult.cycle_rate}%`, "bg-purple-50"],
                  ]} />
                  {renderWarnings(cycleResult.warnings)}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* ===== 锚索计算 (新增) ===== */}
        {tab === "cable" && (
          <>
            <Card>
              <CardHeader><CardTitle className="text-base">锚索受力参数</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">围岩级别</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={cableForm.rock_class} onChange={e => setCableForm({ ...cableForm, rock_class: e.target.value })}>{ROCK_CLASSES.map(r => <option key={r}>{r}</option>)}</select></div>
                  <div><label className="mb-1 block text-xs font-medium">断面形式</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={cableForm.section_form} onChange={e => setCableForm({ ...cableForm, section_form: e.target.value })}>{SECTION_FORMS.map(s => <option key={s}>{s}</option>)}</select></div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">净宽 (m)</label><Input type="number" value={cableForm.section_width} onChange={e => setCableForm({ ...cableForm, section_width: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">净高 (m)</label><Input type="number" value={cableForm.section_height} onChange={e => setCableForm({ ...cableForm, section_height: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">容重 (t/m³)</label><Input type="number" value={cableForm.rock_density} onChange={e => setCableForm({ ...cableForm, rock_density: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">锚索长度 (m)</label><Input type="number" value={cableForm.cable_length} onChange={e => setCableForm({ ...cableForm, cable_length: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">直径 (mm)</label><Input type="number" value={cableForm.cable_diameter} onChange={e => setCableForm({ ...cableForm, cable_diameter: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">破断力 (kN)</label><Input type="number" value={cableForm.cable_strength} onChange={e => setCableForm({ ...cableForm, cable_strength: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">数量 <span className="text-slate-400">可选</span></label><Input placeholder="校核用" value={cableForm.cable_count} onChange={e => setCableForm({ ...cableForm, cable_count: e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">预紧力 (kN) <span className="text-slate-400">可选</span></label><Input placeholder="校核用" value={cableForm.pretension} onChange={e => setCableForm({ ...cableForm, pretension: e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">排距 (mm)</label><Input type="number" value={cableForm.row_spacing} onChange={e => setCableForm({ ...cableForm, row_spacing: +e.target.value })} /></div>
                </div>
              </CardContent>
            </Card>
            {cableResult && (
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2 text-base">{cableResult.is_compliant ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <ShieldAlert className="h-5 w-5 text-red-500" />} 锚索计算结果</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <ResultCard icon={null} data={[
                    ["松动圈高度", `${cableResult.loosening_height} m`, "bg-orange-50"],
                    ["松动体体积", `${cableResult.loosening_volume} m³/m`, "bg-orange-50"],
                    ["总悬吊载荷", `${cableResult.total_load} kN`],
                    ["设计承载力", `${cableResult.design_capacity} kN`],
                    ["最少锚索", `${cableResult.min_cable_count} 根/排`, "bg-blue-50"],
                    ["推荐间距", `${cableResult.recommended_spacing} mm`, "bg-blue-50"],
                    ["最小预紧力", `${cableResult.min_pretension} kN`],
                    ["安全系数", `${cableResult.safety_factor}`],
                  ]} />
                  {renderWarnings(cableResult.warnings)}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* ===== 批量合规校验 (新增) ===== */}
        {tab === "compliance" && (
          <>
            <Card>
              <CardHeader><CardTitle className="text-base">项目参数一键校核</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-slate-500 mb-2">填入项目全参数，一键完成断面/支护/通风/安全四维度合规校验</p>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">围岩级别</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={compForm.rock_class} onChange={e => setCompForm({ ...compForm, rock_class: e.target.value })}>{ROCK_CLASSES.map(r => <option key={r}>{r}</option>)}</select></div>
                  <div><label className="mb-1 block text-xs font-medium">瓦斯等级</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={compForm.gas_level} onChange={e => setCompForm({ ...compForm, gas_level: e.target.value })}>{GAS_LEVELS.map(g => <option key={g}>{g}</option>)}</select></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">断面形式</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={compForm.section_form} onChange={e => setCompForm({ ...compForm, section_form: e.target.value })}>{SECTION_FORMS.map(s => <option key={s}>{s}</option>)}</select></div>
                  <div><label className="mb-1 block text-xs font-medium">自燃倾向性</label><select className="w-full rounded-md border px-3 py-2 text-sm" value={compForm.spontaneous_combustion} onChange={e => setCompForm({ ...compForm, spontaneous_combustion: e.target.value })}><option>不易自燃</option><option>自燃</option><option>容易自燃</option></select></div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">宽 (m)</label><Input type="number" value={compForm.section_width} onChange={e => setCompForm({ ...compForm, section_width: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">高 (m)</label><Input type="number" value={compForm.section_height} onChange={e => setCompForm({ ...compForm, section_height: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">掘进长度 (m)</label><Input type="number" value={compForm.excavation_length} onChange={e => setCompForm({ ...compForm, excavation_length: +e.target.value })} /></div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="mb-1 block text-xs font-medium">锚杆间距 (mm)</label><Input type="number" value={compForm.bolt_spacing} onChange={e => setCompForm({ ...compForm, bolt_spacing: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">锚杆排距 (mm)</label><Input type="number" value={compForm.bolt_row_spacing} onChange={e => setCompForm({ ...compForm, bolt_row_spacing: +e.target.value })} /></div>
                  <div><label className="mb-1 block text-xs font-medium">锚索数量</label><Input type="number" value={compForm.cable_count} onChange={e => setCompForm({ ...compForm, cable_count: +e.target.value })} /></div>
                </div>
              </CardContent>
            </Card>
            {compResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    {compResult.is_compliant ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <ShieldAlert className="h-5 w-5 text-red-500" />}
                    校验报告
                  </CardTitle>
                  <div className="flex gap-3 text-sm">
                    <span className="text-green-600">✅ 通过 {compResult.passed}</span>
                    <span className="text-red-600">❌ 不合规 {compResult.failed}</span>
                    <span className="text-amber-600">⚠️ 预警 {compResult.warned}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  {compResult.items?.map((item: any, i: number) => {
                    const style = STATUS_COLORS[item.status] || STATUS_COLORS.pass;
                    const Icon = style.icon;
                    return (
                      <div key={i} className={`flex items-start gap-2 rounded-md px-3 py-2.5 ${style.bg}`}>
                        <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${style.text}`} />
                        <div className="flex-1">
                          <div className={`text-sm font-medium ${style.text}`}>
                            [{item.category}] {item.item}
                          </div>
                          <div className="text-xs text-slate-600">{item.message}</div>
                          {item.suggestion && <div className="mt-1 text-xs text-slate-500 italic">💡 {item.suggestion}</div>}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* ===== 规则冲突检测 (新增) ===== */}
        {tab === "conflicts" && (
          <>
            <Card>
              <CardHeader><CardTitle className="text-base">规则冲突检测</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-slate-500">分析规则库中的逻辑冲突（条件矛盾、优先级歧义、覆盖冲突）</p>
                <div><label className="mb-1 block text-xs font-medium">规则组 ID <span className="text-slate-400">不填检测全部</span></label><Input placeholder="留空检测所有规则组" value={conflictGroupId} onChange={e => setConflictGroupId(e.target.value)} /></div>
              </CardContent>
            </Card>
            {conflictResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    {conflictResult.total_conflicts === 0 ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <ShieldAlert className="h-5 w-5 text-red-500" />}
                    检测报告
                  </CardTitle>
                  <p className="text-sm text-slate-500">
                    分析了 {conflictResult.total_rules} 条规则，发现 {conflictResult.total_conflicts} 个冲突
                    {conflictResult.errors > 0 && <span className="ml-2 text-red-600">（{conflictResult.errors} 严重）</span>}
                  </p>
                </CardHeader>
                <CardContent className="space-y-2">
                  {conflictResult.total_conflicts === 0 ? (
                    <div className="flex items-center justify-center py-8 text-green-600">
                      <CheckCircle className="mr-2 h-5 w-5" /> 未发现规则冲突，规则库结构良好
                    </div>
                  ) : (
                    conflictResult.conflicts?.map((c: any, i: number) => (
                      <div key={i} className={`rounded-md px-3 py-2.5 ${c.severity === "error" ? "bg-red-50" : "bg-amber-50"}`}>
                        <div className={`text-sm font-medium ${c.severity === "error" ? "text-red-700" : "text-amber-700"}`}>
                          [{c.type}] 规则#{c.rule_a_id}「{c.rule_a_name}」↔ 规则#{c.rule_b_id}「{c.rule_b_name}」
                        </div>
                        <div className="text-xs text-slate-600 mt-1">{c.detail}</div>
                        {c.suggestion && <div className="text-xs text-slate-500 mt-1 italic">💡 {c.suggestion}</div>}
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}
