"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Upload,
  Plus,
  Search,
  Wrench,
  Package,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  Trash2,
  ChevronDown,
} from "lucide-react";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

/* ============ 类型定义 ============ */
interface EquipmentItem {
  id: number;
  name: string;
  category: string;
  model_spec: string | null;
  manufacturer: string | null;
  power_kw: number | null;
  weight_t: number | null;
}

interface MaterialItem {
  id: number;
  name: string;
  category: string;
  model_spec: string | null;
  unit: string;
  consumption_per_cycle: number | null;
}

interface ImportResult {
  success: number;
  failed: number;
  errors: string[];
}

/* ============ Tab 配置 ============ */
type TabKey = "equipment" | "materials";
const TABS: { key: TabKey; label: string; icon: any }[] = [
  { key: "equipment", label: "设备目录", icon: Wrench },
  { key: "materials", label: "材料目录", icon: Package },
];

export default function EquipmentPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("equipment");
  const [searchTerm, setSearchTerm] = useState("");

  // 设备
  const [equipment, setEquipment] = useState<EquipmentItem[]>([]);
  const [loadingEq, setLoadingEq] = useState(false);

  // 材料
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [loadingMat, setLoadingMat] = useState(false);

  // 导入
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /** 加载设备目录 */
  const loadEquipment = useCallback(async () => {
    setLoadingEq(true);
    try {
      const res = await api.get("/equipment/catalog/equipment");
      setEquipment(res.data?.data || []);
    } catch { /* 静默 */ } finally { setLoadingEq(false); }
  }, []);

  /** 加载材料目录 */
  const loadMaterials = useCallback(async () => {
    setLoadingMat(true);
    try {
      const res = await api.get("/equipment/catalog/materials");
      setMaterials(res.data?.data || []);
    } catch { /* 静默 */ } finally { setLoadingMat(false); }
  }, []);

  useEffect(() => {
    loadEquipment();
    loadMaterials();
  }, [loadEquipment, loadMaterials]);

  /** 批量导入 */
  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    setImportResult(null);

    const formData = new FormData();
    formData.append("file", file);

    const endpoint =
      activeTab === "equipment"
        ? "/equipment/catalog/equipment/import"
        : "/equipment/catalog/materials/import";

    try {
      const res = await api.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportResult(res.data?.data);
      // 刷新列表
      if (activeTab === "equipment") loadEquipment();
      else loadMaterials();
    } catch (err: any) {
      setImportResult({
        success: 0,
        failed: 1,
        errors: [err.response?.data?.detail || err.message],
      });
    } finally {
      setImporting(false);
      // 重置 file input
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  /** 过滤列表 */
  const filteredEquipment = equipment.filter(
    (i) =>
      i.name.includes(searchTerm) ||
      i.category.includes(searchTerm) ||
      (i.model_spec && i.model_spec.includes(searchTerm))
  );

  const filteredMaterials = materials.filter(
    (i) =>
      i.name.includes(searchTerm) ||
      i.category.includes(searchTerm) ||
      (i.model_spec && i.model_spec.includes(searchTerm))
  );

  /** 统计设备类别 */
  const eqCategories = [...new Set(equipment.map((e) => e.category))];
  const matCategories = [...new Set(materials.map((m) => m.category))];

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white">
            设备材料管理
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            管理设备和材料基础数据目录，支持 Excel/CSV 批量导入
          </p>
        </div>
        <div className="flex gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            className="hidden"
            onChange={handleImport}
          />
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
          >
            {importing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {importing ? "导入中..." : `导入${activeTab === "equipment" ? "设备" : "材料"}数据`}
          </Button>
        </div>
      </div>

      {/* 导入结果提示 */}
      <AnimatePresence>
        {importResult && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <Card
              className={`border ${
                importResult.failed > 0
                  ? "border-amber-200 bg-amber-50"
                  : "border-green-200 bg-green-50"
              }`}
            >
              <CardContent className="flex items-start gap-3 py-3">
                {importResult.failed > 0 ? (
                  <AlertTriangle className="h-5 w-5 shrink-0 text-amber-500 mt-0.5" />
                ) : (
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-500 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium">
                    导入完成：成功 {importResult.success} 条
                    {importResult.failed > 0 &&
                      `，失败 ${importResult.failed} 条`}
                  </p>
                  {importResult.errors.length > 0 && (
                    <ul className="mt-1.5 space-y-0.5">
                      {importResult.errors.slice(0, 5).map((err, i) => (
                        <li key={i} className="text-xs text-amber-700">
                          {err}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <button
                  onClick={() => setImportResult(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  ×
                </button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-xs text-slate-500">设备总数</div>
            <div className="mt-1 text-2xl font-bold text-blue-600">
              {equipment.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-xs text-slate-500">设备类别</div>
            <div className="mt-1 text-2xl font-bold text-indigo-600">
              {eqCategories.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-xs text-slate-500">材料总数</div>
            <div className="mt-1 text-2xl font-bold text-emerald-600">
              {materials.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-xs text-slate-500">材料类别</div>
            <div className="mt-1 text-2xl font-bold text-amber-600">
              {matCategories.length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tab 切换 + 搜索 */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key);
                setSearchTerm("");
              }}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                activeTab === tab.key
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            className="pl-9 rounded-xl"
            placeholder="搜索名称、类别、型号..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* 导入模板提示 */}
      <Card className="border-dashed border-2 border-slate-200 bg-slate-50/50">
        <CardContent className="flex items-center gap-4 py-4">
          <FileSpreadsheet className="h-8 w-8 text-slate-300" />
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-600">
              Excel/CSV 批量导入
            </p>
            <p className="mt-0.5 text-xs text-slate-400">
              {activeTab === "equipment"
                ? "表头格式：设备名称 | 设备类别 | 型号规格 | 生产厂家 | 额定功率(kW) | 适用掘进方式 | 适用最小断面(m²) | 适用最大断面(m²)"
                : "表头格式：材料名称 | 材料类别 | 规格型号 | 计量单位 | 单循环消耗量 | 适用支护方式 | 适用围岩级别"}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
          >
            <Upload className="h-3.5 w-3.5" />
            选择文件
          </Button>
        </CardContent>
      </Card>

      {/* 数据表格 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-sm">
            <span>
              {activeTab === "equipment" ? "设备目录" : "材料目录"}
              <span className="ml-2 text-xs font-normal text-slate-400">
                {activeTab === "equipment"
                  ? `共 ${filteredEquipment.length} 条`
                  : `共 ${filteredMaterials.length} 条`}
              </span>
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeTab === "equipment" ? (
            /* 设备表格 */
            loadingEq ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-slate-300" />
              </div>
            ) : filteredEquipment.length === 0 ? (
              <div className="py-12 text-center">
                <Wrench className="mx-auto mb-3 h-10 w-10 text-slate-200" />
                <p className="text-sm text-slate-400">
                  {equipment.length === 0
                    ? "暂无设备数据，请通过 Excel/CSV 导入"
                    : "无匹配结果"}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs text-slate-400">
                      <th className="pb-2 pr-4">#</th>
                      <th className="pb-2 pr-4">设备类别</th>
                      <th className="pb-2 pr-4">设备名称</th>
                      <th className="pb-2 pr-4">型号规格</th>
                      <th className="pb-2 pr-4">生产厂家</th>
                      <th className="pb-2 pr-4 text-right">功率(kW)</th>
                      <th className="pb-2 pr-4 text-right">重量(t)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEquipment.map((eq, i) => (
                      <tr
                        key={eq.id}
                        className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors"
                      >
                        <td className="py-2.5 pr-4 text-slate-400">{i + 1}</td>
                        <td className="py-2.5 pr-4">
                          <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                            {eq.category}
                          </span>
                        </td>
                        <td className="py-2.5 pr-4 font-medium">{eq.name}</td>
                        <td className="py-2.5 pr-4 text-slate-500">
                          {eq.model_spec || "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-slate-500">
                          {eq.manufacturer || "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-right">
                          {eq.power_kw ?? "—"}
                        </td>
                        <td className="py-2.5 pr-4 text-right">
                          {eq.weight_t ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : (
            /* 材料表格 */
            loadingMat ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-slate-300" />
              </div>
            ) : filteredMaterials.length === 0 ? (
              <div className="py-12 text-center">
                <Package className="mx-auto mb-3 h-10 w-10 text-slate-200" />
                <p className="text-sm text-slate-400">
                  {materials.length === 0
                    ? "暂无材料数据，请通过 Excel/CSV 导入"
                    : "无匹配结果"}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs text-slate-400">
                      <th className="pb-2 pr-4">#</th>
                      <th className="pb-2 pr-4">材料类别</th>
                      <th className="pb-2 pr-4">材料名称</th>
                      <th className="pb-2 pr-4">规格型号</th>
                      <th className="pb-2 pr-4">单位</th>
                      <th className="pb-2 pr-4 text-right">单循环消耗量</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMaterials.map((mat, i) => (
                      <tr
                        key={mat.id}
                        className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors"
                      >
                        <td className="py-2.5 pr-4 text-slate-400">{i + 1}</td>
                        <td className="py-2.5 pr-4">
                          <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                            {mat.category}
                          </span>
                        </td>
                        <td className="py-2.5 pr-4 font-medium">{mat.name}</td>
                        <td className="py-2.5 pr-4 text-slate-500">
                          {mat.model_spec || "—"}
                        </td>
                        <td className="py-2.5 pr-4">{mat.unit}</td>
                        <td className="py-2.5 pr-4 text-right">
                          {mat.consumption_per_cycle ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          )}
        </CardContent>
      </Card>
    </div>
  );
}
