"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, BookOpen, Settings2, Calculator, Loader2, ArrowUpRight, Zap } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

interface StatsData {
  projects: number;
  standards: number;
  rules: number;
  documents: number;
}

interface RecentProject {
  id: number;
  face_name: string;
  mine_name: string;
  status: string;
  created_at: string;
  params?: any;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  in_progress: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  in_progress: "进行中",
  completed: "已完成",
};

/** Dashboard 首页 — 工作台概览（对接真实 API） */
export default function DashboardPage() {
  const [stats, setStats] = useState<StatsData>({ projects: 0, standards: 0, rules: 0, documents: 0 });
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 并行请求各模块数据
        const [projRes, stdRes, rulesRes] = await Promise.allSettled([
          api.get("/projects", { params: { page: 1, page_size: 5 } }),
          api.get("/standards", { params: { page: 1, page_size: 1 } }),
          api.get("/rules/groups"),
        ]);

        const projData = projRes.status === "fulfilled" ? projRes.value.data?.data : null;
        const stdData = stdRes.status === "fulfilled" ? stdRes.value.data?.data : null;
        const rulesData = rulesRes.status === "fulfilled" ? rulesRes.value.data?.data : null;

        // 规则统计：累加每个规则组的 rule_count
        let totalRules = 0;
        if (Array.isArray(rulesData)) {
          totalRules = rulesData.reduce((sum: number, g: any) => sum + (g.rule_count || 0), 0);
        }

        setStats({
          projects: projData?.total ?? (Array.isArray(projData) ? projData.length : 0),
          standards: stdData?.total ?? (Array.isArray(stdData) ? stdData.length : 0),
          rules: totalRules,
          documents: 0, // 文档数后续可通过遍历项目统计
        });

        // 最近项目
        const items = projData?.items || (Array.isArray(projData) ? projData : []);
        setRecentProjects(items.slice(0, 5));
      } catch {
        // 使用默认值
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const cards = [
    { title: "规程项目", value: stats.projects, icon: FileText, desc: "已创建", href: "/dashboard/projects", color: "text-blue-600" },
    { title: "标准规范", value: stats.standards, icon: BookOpen, desc: "已录入", href: "/dashboard/standards", color: "text-emerald-600" },
    { title: "编制规则", value: stats.rules, icon: Settings2, desc: "条规则", href: "/dashboard/rules", color: "text-purple-600" },
    { title: "计算校验", value: "6 种", icon: Calculator, desc: "支护/通风/循环/锚索/合规/冲突", href: "/dashboard/calc", color: "text-orange-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white">工作台</h2>
        <Link href="/dashboard/projects/new">
          <span className="flex items-center gap-1 text-sm text-blue-600 hover:underline cursor-pointer">
            新建项目 <ArrowUpRight className="h-3.5 w-3.5" />
          </span>
        </Link>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((s) => (
          <Link key={s.title} href={s.href}>
            <Card className="cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-500">{s.title}</CardTitle>
                <s.icon className={`h-4 w-4 ${s.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {loading ? <Loader2 className="h-6 w-6 animate-spin text-slate-300" /> : s.value}
                </div>
                <p className="text-xs text-slate-500">{s.desc}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* 最近项目 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">最近项目</CardTitle>
          <Link href="/dashboard/projects">
            <span className="text-xs text-slate-400 hover:text-slate-600 cursor-pointer">查看全部 →</span>
          </Link>
        </CardHeader>
        <CardContent>
          {recentProjects.length > 0 ? (
            <div className="space-y-2.5">
              {recentProjects.map((p) => {
                const hasParams = p.params && Object.values(p.params).some((v: any) => v !== null && v !== "");
                return (
                  <Link key={p.id} href={`/dashboard/projects/${p.id}`}>
                    <div className="flex items-center justify-between rounded-lg border p-3.5 transition-all hover:bg-slate-50 hover:shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50">
                          <FileText className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{p.face_name}</p>
                          <p className="text-xs text-slate-400">{p.mine_name || "未关联矿井"}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {hasParams ? (
                          <span className="flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-600">
                            <Zap className="h-3 w-3" />可生成
                          </span>
                        ) : (
                          <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-600">
                            待填参数
                          </span>
                        )}
                        <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_COLORS[p.status] || "bg-slate-100 text-slate-500"}`}>
                          {STATUS_LABELS[p.status] || p.status}
                        </span>
                        <span className="text-xs text-slate-400">{p.created_at?.slice(0, 10)}</span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <p className="py-4 text-center text-sm text-slate-400">
              暂无项目，点击右上角&quot;新建项目&quot;开始创建。
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
