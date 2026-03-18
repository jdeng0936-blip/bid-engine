"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Plus,
  Search,
  FileText,
  Clock,
  ArrowRight,
  Pickaxe,
  Loader2,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  进行中: "bg-blue-100 text-blue-700",
  已完成: "bg-green-100 text-green-700",
  草稿: "bg-slate-200 text-slate-600",
};

interface Mine {
  id: number;
  name: string;
}

interface Project {
  id: number;
  face_name: string;
  mine_name: string;
  mine_id: number;
  status: string;
  rock_class?: string;
  gas_level?: string;
  section_form?: string;
  section_width?: number;
  section_height?: number;
  dig_method?: string;
  created_at?: string;
}

/** 项目列表页 — 对接后端真实 API */
export default function ProjectsPage() {
  const [search, setSearch] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [mines, setMines] = useState<Mine[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    face_name: "",
    mine_id: 0,
    dig_method: "综掘",
    rock_class: "III",
    gas_level: "低瓦斯",
    section_width: "4.5",
    section_height: "3.2",
  });

  // 加载矿井列表（用于下拉选择器）
  const fetchMines = useCallback(async () => {
    try {
      const res = await api.get("/system/mines", { params: { page: 1, page_size: 100 } });
      const data = res.data?.data;
      // 兼容分页格式 { items: [...] } 和直接数组格式
      const list = Array.isArray(data) ? data : (data?.items || []);
      setMines(list);
      // 默认选第一个矿井
      if (list.length > 0 && form.mine_id === 0) {
        setForm(prev => ({ ...prev, mine_id: list[0].id }));
      }
    } catch {
      // 静默处理
    }
  }, []);

  // 加载项目列表
  const fetchProjects = useCallback(async () => {
    try {
      const res = await api.get("/projects", {
        params: { page: 1, page_size: 50 },
      });
      // 兼容分页格式和直接数组格式
      const data = res.data?.data;
      setProjects(Array.isArray(data) ? data : (data?.items || []));
    } catch {
      // 发生错误使用空列表
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMines();
    fetchProjects();
  }, [fetchMines, fetchProjects]);

  // 创建项目
  const handleCreate = async () => {
    if (!form.face_name || !form.mine_id) {
      alert("请填写项目名称并选择矿井");
      return;
    }
    setCreating(true);
    try {
      await api.post("/projects", {
        face_name: form.face_name,
        mine_id: form.mine_id,
        dig_method: form.dig_method,
      });
      setShowCreate(false);
      setForm({ face_name: "", mine_id: mines[0]?.id || 0, dig_method: "综掘", rock_class: "III", gas_level: "低瓦斯", section_width: "4.5", section_height: "3.2" });
      fetchProjects();
    } catch (err: any) {
      alert("创建失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  // 删除项目
  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("确认删除该项目？")) return;
    try {
      await api.delete(`/projects/${id}`);
      fetchProjects();
    } catch {
      alert("删除失败");
    }
  };

  const filtered = projects.filter(
    (p) =>
      (p.face_name || "").includes(search) ||
      (p.mine_name || "").includes(search)
  );

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white">项目管理</h2>
          <p className="mt-1 text-sm text-slate-500">
            共 {projects.length} 个项目
          </p>
        </div>
        <Button className="gap-2" onClick={() => setShowCreate(!showCreate)}>
          <Plus className="h-4 w-4" />新建项目
        </Button>
      </div>

      {/* 搜索 */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            className="pl-10"
            placeholder="搜索项目名称或矿井..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* 新建项目表单 */}
      {showCreate && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="space-y-3 pt-4">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium">项目名称 *</label>
                <Input
                  placeholder="如：3301回风巷"
                  value={form.face_name}
                  onChange={(e) => setForm({ ...form, face_name: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">选择矿井 *</label>
                <select
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  value={form.mine_id}
                  onChange={(e) => setForm({ ...form, mine_id: Number(e.target.value) })}
                >
                  {mines.length === 0 && (
                    <option value={0}>暂无矿井，请先在系统管理中添加</option>
                  )}
                  {mines.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">掘进方式</label>
                <Input
                  placeholder="综掘 / 钻爆法"
                  value={form.dig_method}
                  onChange={(e) => setForm({ ...form, dig_method: e.target.value })}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowCreate(false)}>
                取消
              </Button>
              <Button size="sm" onClick={handleCreate} disabled={creating}>
                {creating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : null}
                创建项目
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 项目卡片列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <Pickaxe className="h-12 w-12 text-slate-300" />
            <p className="mt-3 text-sm text-slate-400">暂无项目，点击「新建项目」开始</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <Link key={p.id} href={`/dashboard/projects/${p.id}`}>
              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Pickaxe className="h-4 w-4 text-amber-600" />
                        {p.face_name}
                      </CardTitle>
                      <p className="mt-0.5 text-xs text-slate-500">{p.mine_name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLE[p.status] || STATUS_STYLE["草稿"]}`}>
                        {p.status || "草稿"}
                      </span>
                      <button
                        onClick={(e) => handleDelete(p.id, e)}
                        className="rounded p-1 text-slate-300 hover:bg-red-50 hover:text-red-500"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                    <div>围岩：<span className="font-medium">{p.rock_class || "—"}类</span></div>
                    <div>瓦斯：<span className="font-medium">{p.gas_level || "—"}</span></div>
                    <div>
                      断面：<span className="font-medium">
                        {p.section_width && p.section_height
                          ? `${p.section_form || ""} ${p.section_width}×${p.section_height}m`
                          : "—"}
                      </span>
                    </div>
                    <div>方式：<span className="font-medium">{p.dig_method || "—"}</span></div>
                  </div>
                  <div className="flex items-center justify-between border-t pt-2 text-xs text-slate-400">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />{p.created_at?.slice(0, 10) || "—"}
                    </div>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
