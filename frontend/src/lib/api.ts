"use client";

import axios from "axios";

/** Axios 实例 — 自动注入 JWT Token */
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 600000, // 10分钟 — 规程生成等长耗时操作需要充足时间
  headers: { "Content-Type": "application/json" },
});

// 请求拦截器：注入 Token
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
