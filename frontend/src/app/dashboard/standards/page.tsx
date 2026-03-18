"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Search,
  Plus,
  Eye,
  Trash2,
  BookOpen,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";

/** 文档类型选项 */
const DOC_TYPES = ["全部", "法律法规", "技术规范", "集团标准", "安全规程"];

interface StdDoc {
  id: number;
  title: string;
  doc_type: string;
  version?: string;
  publish_date?: string;
  is_current?: boolean;
  clause_count?: number;
}

/** 标准库管理页面 — 对接真实 API */
export default function StandardsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeType, setActiveType] = useState("全部");
  const [docs, setDocs] = useState<StdDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: "", doc_type: "技术规范", version: "" });

  // 加载文档列表
  const fetchDocs = useCallback(async () => {
    try {
      const params: any = { page: 1, page_size: 100 };
      if (activeType !== "全部") params.doc_type = activeType;
      if (searchTerm) params.title = searchTerm;
      const res = await api.get("/standards", { params });
      setDocs(res.data?.data?.items || []);
    } catch {
      // 静默处理
    } finally {
      setLoading(false);
    }
  }, [activeType, searchTerm]);

  useEffect(() => {
    setLoading(true);
    fetchDocs();
  }, [fetchDocs]);

  // 创建文档
  const handleCreate = async () => {
    if (!form.title) return;
    setCreating(true);
    try {
      await api.post("/standards", form);
      setShowCreate(false);
      setForm({ title: "", doc_type: "技术规范", version: "" });
      fetchDocs();
    } catch (err: any) {
      alert("创建失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  // 删除文档
  const handleDelete = async (id: number) => {
    if (!confirm("确认删除？")) return;
    try {
      await api.delete(`/standards/${id}`);
      fetchDocs();
    } catch {
      alert("删除失败");
    }
  };

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white">标准库</h2>
          <p className="mt-1 text-sm text-slate-500">
            管理法律法规、技术规范、集团标准等基础规范文档
          </p>
        </div>
        <Button className="gap-2" onClick={() => setShowCreate(!showCreate)}>
          <Plus className="h-4 w-4" />新增文档
        </Button>
      </div>

      {/* 新建表单 */}
      {showCreate && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="space-y-3 pt-4">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium">文档名称 *</label>
                <Input
                  placeholder="如：煤矿安全规程"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">类型</label>
                <select
                  className="h-10 w-full rounded-md border px-3 text-sm"
                  value={form.doc_type}
                  onChange={(e) => setForm({ ...form, doc_type: e.target.value })}
                >
                  {DOC_TYPES.filter((t) => t !== "全部").map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">版本</label>
                <Input
                  placeholder="如：2022版"
                  value={form.version}
                  onChange={(e) => setForm({ ...form, version: e.target.value })}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowCreate(false)}>取消</Button>
              <Button size="sm" onClick={handleCreate} disabled={creating}>
                {creating && <Loader2 className="mr-1 h-4 w-4 animate-spin" />}创建
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 搜索与筛选 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="搜索规范名称..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              {DOC_TYPES.map((type) => (
                <Button
                  key={type}
                  variant={activeType === type ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveType(type)}
                >
                  {type}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 文档列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BookOpen className="h-4 w-4" />
            规范文档列表
            <span className="ml-2 text-sm font-normal text-slate-400">
              共 {docs.length} 条
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>规范名称</TableHead>
                  <TableHead className="w-24">类型</TableHead>
                  <TableHead className="w-20">版本</TableHead>
                  <TableHead className="w-16 text-center">状态</TableHead>
                  <TableHead className="w-28 text-center">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {docs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-12 text-center text-slate-400">
                      暂无数据，点击&quot;新增文档&quot;开始录入规范
                    </TableCell>
                  </TableRow>
                ) : (
                  docs.map((doc, idx) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-mono text-slate-400">{idx + 1}</TableCell>
                      <TableCell className="font-medium">{doc.title}</TableCell>
                      <TableCell>
                        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                          {doc.doc_type}
                        </span>
                      </TableCell>
                      <TableCell className="text-slate-500">{doc.version || "—"}</TableCell>
                      <TableCell className="text-center">
                        {doc.is_current !== false ? (
                          <span className="text-green-600">现行</span>
                        ) : (
                          <span className="text-slate-400">废止</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-center gap-1">
                          <Link href={`/dashboard/standards/${doc.id}`}>
                            <Button variant="ghost" size="icon" title="查看">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="删除"
                            className="text-red-500 hover:text-red-700"
                            onClick={() => handleDelete(doc.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
