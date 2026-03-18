"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileText,
  Download,
  Search,
  Loader2,
  Calendar,
  HardDrive,
  RefreshCw,
} from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

/** 文档列表项类型 */
type DocItem = {
  filename: string;
  size: number;
  size_kb: number;
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [downloading, setDownloading] = useState<string | null>(null);

  // 加载所有项目的文档
  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      // 获取所有项目
      const projRes = await api.get("/projects");
      const projects = projRes.data?.data || [];

      // 并发获取每个项目的文档
      const allDocs: DocItem[] = [];
      await Promise.allSettled(
        projects.map(async (proj: any) => {
          try {
            const docRes = await api.get(`/projects/${proj.id}/documents`);
            const docs = docRes.data?.data || [];
            allDocs.push(...docs);
          } catch { /* 静默 */ }
        })
      );

      // 按文件名降序排列（最新的在前）
      allDocs.sort((a, b) => b.filename.localeCompare(a.filename));
      setDocuments(allDocs);
    } catch (e: any) {
      console.error("加载文档失败:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  // 下载文档 — 需要知道 project_id
  const handleDownload = async (filename: string) => {
    setDownloading(filename);
    try {
      // 从文件名推断 project_id（遍历项目查找）
      const projRes = await api.get("/projects");
      const projects = projRes.data?.data || [];

      for (const proj of projects) {
        try {
          const res = await api.get(`/projects/${proj.id}/documents/download`, {
            params: { filename },
            responseType: "blob",
          });
          if (res.status === 200) {
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
            break;
          }
        } catch { continue; }
      }
    } catch {
      alert("下载失败");
    } finally {
      setDownloading(null);
    }
  };

  // 过滤
  const filtered = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // 统计
  const totalSize = documents.reduce((s, d) => s + d.size_kb, 0);

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white">
            文档中心
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            查看和下载所有已生成的掘进作业规程文档
          </p>
        </div>
        <Button variant="outline" className="gap-2" onClick={fetchDocuments}>
          <RefreshCw className="h-4 w-4" />
          刷新
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="flex items-center gap-4 py-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
              <FileText className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{documents.length}</p>
              <p className="text-xs text-slate-500">总文档数</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 py-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
              <HardDrive className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalSize.toFixed(1)}</p>
              <p className="text-xs text-slate-500">总大小 (KB)</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 py-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
              <Calendar className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {documents.length > 0
                  ? documents[0].filename.match(/_(\d{8})_/)?.[1]?.replace(
                      /(\d{4})(\d{2})(\d{2})/,
                      "$1-$2-$3"
                    ) || "—"
                  : "—"}
              </p>
              <p className="text-xs text-slate-500">最近生成</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索 */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          placeholder="搜索文档名称..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="h-9 pl-10"
        />
      </div>

      {/* 文档列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
        </div>
      ) : filtered.length === 0 ? (
        <Card className="flex h-48 items-center justify-center">
          <div className="text-center text-slate-400">
            <FileText className="mx-auto mb-3 h-12 w-12 opacity-30" />
            <p>暂无文档</p>
            <p className="mt-1 text-xs">
              前往{" "}
              <Link
                href="/dashboard/projects"
                className="text-blue-500 hover:underline"
              >
                规程项目
              </Link>{" "}
              创建并生成规程文档
            </p>
          </div>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              文档列表（{filtered.length} 个）
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {filtered.map((doc, i) => {
              // 从文件名提取日期和工作面名称
              const dateMatch = doc.filename.match(
                /_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/
              );
              const dateStr = dateMatch
                ? `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]} ${dateMatch[4]}:${dateMatch[5]}`
                : "";
              const faceName = doc.filename
                .replace(/_作业规程_\d+_\d+\.docx$/, "")
                .replaceAll("_", " ");

              return (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border px-4 py-3 transition-colors hover:bg-slate-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded bg-blue-50">
                      <FileText className="h-4 w-4 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{faceName}</p>
                      <div className="flex items-center gap-3 text-xs text-slate-400">
                        <span>{dateStr}</span>
                        <span>{doc.size_kb} KB</span>
                      </div>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="gap-1.5"
                    disabled={downloading === doc.filename}
                    onClick={() => handleDownload(doc.filename)}
                  >
                    {downloading === doc.filename ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Download className="h-3.5 w-3.5" />
                    )}
                    下载
                  </Button>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
