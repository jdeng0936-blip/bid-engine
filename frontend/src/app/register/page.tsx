"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff, Sparkles, Loader2, UserPlus } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth-store";

/** 注册页 — 新用户注册同时创建租户 */
export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [realName, setRealName] = useState("");
  const [enterpriseName, setEnterpriseName] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("请输入用户名和密码");
      return;
    }
    if (password !== confirmPassword) {
      setError("两次密码输入不一致");
      return;
    }
    if (password.length < 6) {
      setError("密码长度不能少于6位");
      return;
    }
    setError("");
    setLoading(true);

    try {
      // 调用注册接口
      const res = await api.post("/auth/register", {
        username,
        password,
        confirm_password: confirmPassword,
        real_name: realName,
        enterprise_name: enterpriseName,
      });
      const token = res.data?.data?.access_token;
      if (!token) throw new Error("注册成功但未返回 Token");

      // 存储认证信息（注册即登录）
      setAuth(token, { id: 0, username, tenant_id: 0 });
      localStorage.setItem("access_token", token);

      // 获取用户 profile
      try {
        const profileRes = await api.get("/auth/profile", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const profile = profileRes.data?.data;
        if (profile) {
          setAuth(token, profile);
        }
      } catch {
        // profile 获取失败不阻塞
      }

      router.push("/dashboard");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail || "注册失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800">
      <div className="w-full max-w-md space-y-6 rounded-2xl bg-slate-800/60 p-8 shadow-2xl backdrop-blur-xl">
        {/* Logo */}
        <div className="flex flex-col items-center gap-2">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-blue-600 shadow-lg">
            <Sparkles className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">鲜标智投</h1>
          <p className="text-sm text-slate-400">创建账号，开始智能投标</p>
        </div>

        {/* 注册表单 */}
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm text-slate-300">用户名 *</label>
            <Input
              placeholder="请输入用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="bg-slate-700/50 text-white placeholder:text-slate-500"
              autoFocus
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-slate-300">密码 *</label>
            <div className="relative">
              <Input
                type={showPwd ? "text" : "password"}
                placeholder="至少6位密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-slate-700/50 pr-10 text-white placeholder:text-slate-500"
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-slate-300">确认密码 *</label>
            <Input
              type="password"
              placeholder="再次输入密码"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="bg-slate-700/50 text-white placeholder:text-slate-500"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-slate-300">姓名</label>
            <Input
              placeholder="您的真实姓名（选填）"
              value={realName}
              onChange={(e) => setRealName(e.target.value)}
              className="bg-slate-700/50 text-white placeholder:text-slate-500"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-slate-300">企业名称</label>
            <Input
              placeholder="如：XX食品配送有限公司（选填）"
              value={enterpriseName}
              onChange={(e) => setEnterpriseName(e.target.value)}
              className="bg-slate-700/50 text-white placeholder:text-slate-500"
            />
          </div>

          {error && (
            <p className="rounded-md bg-red-900/30 px-3 py-2 text-sm text-red-400">{error}</p>
          )}

          <Button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700"
            disabled={loading}
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <UserPlus className="mr-2 h-4 w-4" />
            注册并开始使用
          </Button>
        </form>

        {/* 已有账号入口 */}
        <div className="text-center">
          <span className="text-sm text-slate-400">已有账号？</span>
          <Link
            href="/login"
            className="ml-1 text-sm text-blue-400 hover:text-blue-300 transition"
          >
            立即登录
          </Link>
        </div>
      </div>
    </div>
  );
}
