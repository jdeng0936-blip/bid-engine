---
description: 一键启动前后端（Docker Compose 部署）
---

# 启动前后端

> ⚠️ 本项目通过 Docker Compose 全栈部署，**不要**尝试本地 `python -m uvicorn` 或 `npm run dev`。
> 访问入口：`http://localhost:8888`（Nginx 反代）

// turbo-all

1. 检查 Docker 容器状态
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose ps
```

2. 如果容器未运行，启动全栈服务
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose up -d
```

3. 等待服务就绪并验证后端 Health Check
```bash
sleep 5 && curl -s http://localhost:8888/api/v1/health
```

4. 验证前端可访问
```bash
curl -s -o /dev/null -w "前端 HTTP 状态码: %{http_code}\n" http://localhost:8888/
```

5. 确认启动成功：
   - 后端 health: `{"status":"ok","service":"fresh-food-bidding-api"}`
   - 前端 HTTP 状态码: `200` 或 `307`（正常重定向到登录页）
   - 统一入口: **http://localhost:8888**
