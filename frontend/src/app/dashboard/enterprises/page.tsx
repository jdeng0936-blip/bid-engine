"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Building2,
  Plus,
  Loader2,
  ShieldCheck,
  Truck,
  AlertTriangle,
  CheckCircle2,
  Search,
} from "lucide-react";
import api from "@/lib/api";

interface EnterpriseListItem {
  id: number;
  name: string;
  short_name?: string;
  credit_code?: string;
  food_license_no?: string;
  food_license_expiry?: string;
  haccp_certified?: boolean;
  iso22000_certified?: boolean;
  sc_certified?: boolean;
  cold_chain_vehicles?: number;
  normal_vehicles?: number;
  contact_person?: string;
  contact_phone?: string;
}

export default function EnterprisesPage() {
  const router = useRouter();
  const [enterprises, setEnterprises] = useState<EnterpriseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchEnterprises = async () => {
    setLoading(true);
    try {
      const res = await api.get("/enterprises");
      setEnterprises(res.data?.data || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnterprises();
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const res = await api.post("/enterprises", { name: newName.trim() });
      const ent = res.data?.data;
      if (ent?.id) {
        router.push(`/dashboard/enterprises/${ent.id}`);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "创建失败");
    } finally {
      setCreating(false);
    }
  };

  const filtered = enterprises.filter(
    (e) =>
      !search ||
      e.name.includes(search) ||
      e.short_name?.includes(search) ||
      e.credit_code?.includes(search)
  );

  function isExpiringSoon(date?: string): boolean {
    if (!date) return false;
    const diff = (new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    return diff >= 0 && diff <= 90;
  }

  function isExpired(date?: string): boolean {
    if (!date) return false;
    return new Date(date) < new Date();
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">企业信息库</h1>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" />
          新建企业
        </Button>
      </div>

      {/* 新建企业 */}
      {showCreate && (
        <Card>
          <CardContent className="flex items-center gap-3 pt-4">
            <Input
              placeholder="输入企业名称"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              className="max-w-sm"
            />
            <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
              {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
              创建
            </Button>
            <Button variant="ghost" onClick={() => { setShowCreate(false); setNewName(""); }}>
              取消
            </Button>
          </CardContent>
        </Card>
      )}

      {/* 搜索 */}
      {enterprises.length > 0 && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="搜索企业名称、简称、信用代码..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      )}

      {/* 企业列表 */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Building2 className="h-10 w-10 text-slate-300" />
            <p className="mt-3 text-sm text-slate-400">
              {enterprises.length === 0 ? "暂无企业信息，点击「新建企业」开始录入" : "未找到匹配的企业"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((ent) => {
            const expired = isExpired(ent.food_license_expiry);
            const expiring = isExpiringSoon(ent.food_license_expiry);
            return (
              <Card
                key={ent.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => router.push(`/dashboard/enterprises/${ent.id}`)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Building2 className="h-4 w-4 text-slate-500" />
                    <span className="truncate">{ent.name}</span>
                  </CardTitle>
                  {ent.short_name && (
                    <p className="text-xs text-slate-400">{ent.short_name}</p>
                  )}
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* 资质状态 */}
                  <div className="flex flex-wrap gap-1.5">
                    {ent.food_license_no && (
                      <Badge
                        variant="secondary"
                        className={
                          expired ? "bg-red-100 text-red-700" :
                          expiring ? "bg-amber-100 text-amber-700" :
                          "bg-green-100 text-green-700"
                        }
                      >
                        {expired ? <AlertTriangle className="mr-1 h-3 w-3" /> :
                         expiring ? <AlertTriangle className="mr-1 h-3 w-3" /> :
                         <CheckCircle2 className="mr-1 h-3 w-3" />}
                        食品许可证
                      </Badge>
                    )}
                    {ent.haccp_certified && (
                      <Badge variant="secondary" className="bg-green-100 text-green-700">HACCP</Badge>
                    )}
                    {ent.iso22000_certified && (
                      <Badge variant="secondary" className="bg-green-100 text-green-700">ISO22000</Badge>
                    )}
                    {ent.sc_certified && (
                      <Badge variant="secondary" className="bg-green-100 text-green-700">SC</Badge>
                    )}
                  </div>

                  {/* 冷链信息 */}
                  {(ent.cold_chain_vehicles || ent.normal_vehicles) ? (
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <Truck className="h-3.5 w-3.5" />
                      {ent.cold_chain_vehicles ? `冷链车 ${ent.cold_chain_vehicles} 辆` : ""}
                      {ent.cold_chain_vehicles && ent.normal_vehicles ? " / " : ""}
                      {ent.normal_vehicles ? `常温车 ${ent.normal_vehicles} 辆` : ""}
                    </div>
                  ) : null}

                  {/* 联系人 */}
                  {ent.contact_person && (
                    <div className="text-xs text-slate-400">
                      联系人: {ent.contact_person}
                      {ent.contact_phone && ` · ${ent.contact_phone}`}
                    </div>
                  )}

                  {/* 信用代码 */}
                  {ent.credit_code && (
                    <div className="text-xs text-slate-400 truncate">
                      {ent.credit_code}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
