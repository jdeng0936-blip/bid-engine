"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, BookOpen, Settings2, Calculator, Loader2 } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

interface StatsData {
  projects: number;
  standards: number;
  rules: number;
  calcs: number;
}

interface RecentProject {
  id: number;
  face_name: string;
  mine_name: string;
  status: string;
  created_at: string;
}

/** Dashboard 首页 — 工作台概览（对接真实 API） */
export default function DashboardPage() {
  const [stats, setStats] = useState<StatsData>({ projects: 0, standards: 0, rules: 0, calcs: 0 });
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 并行请求各模块数据
        const [projRes, stdRes] = await Promise.allSettled([
          api.get("/projects", { params: { page: 1, page_size: 5 } }),
          api.get("/standards", { params: { page: 1, page_size: 1 } }),
        ]);

        const projData = projRes.status === "fulfilled" ? projRes.value.data?.data : null;
        const stdData = stdRes.status === "fulfilled" ? stdRes.value.data?.data : null;

        setStats({
          projects: projData?.total || 0,
          standards: stdData?.total || 0,
          rules: 0,
          calcs: 0,
        });

        if (projData?.items) {
          setRecentProjects(projData.items.slice(0, 5));
        }
      } catch {
        // 使用默认值
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const cards = [
    { title: "规程项目", value: stats.projects, icon: FileText, desc: "进行中", href: "/dashboard/projects" },
    { title: "标准规范", value: stats.standards, icon: BookOpen, desc: "已录入", href: "/dashboard/standards" },
    { title: "编制规则", value: stats.rules, icon: Settings2, desc: "已启用", href: "/dashboard/rules" },
    { title: "计算校验", value: stats.calcs, icon: Calculator, desc: "已完成", href: "/dashboard/calc" },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800 dark:text-white">工作台</h2>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((s) => (
          <Link key={s.title} href={s.href}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-500">{s.title}</CardTitle>
                <s.icon className="h-4 w-4 text-slate-400" />
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
        <CardHeader>
          <CardTitle className="text-base">最近项目</CardTitle>
        </CardHeader>
        <CardContent>
          {recentProjects.length > 0 ? (
            <div className="space-y-3">
              {recentProjects.map((p) => (
                <Link key={p.id} href={`/dashboard/projects/${p.id}`}>
                  <div className="flex items-center justify-between rounded-lg border p-3 transition hover:bg-slate-50">
                    <div>
                      <p className="text-sm font-medium">{p.face_name}</p>
                      <p className="text-xs text-slate-400">{p.mine_name}</p>
                    </div>
                    <span className="text-xs text-slate-400">{p.created_at?.slice(0, 10)}</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              暂无项目，点击&quot;规程项目&quot;开始创建第一个掘进工作面规程。
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
