---
description: 重启后端服务（Docker Compose 容器重启）
---

# 重启后端

> ⚠️ 本项目通过 Docker Compose 部署，后端容器名: `fresh-bid-api`
> 统一入口：`http://localhost:8888`（Nginx 反代）

// turbo-all

## 场景一：仅重启后端（代码已挂载 or 镜像未变）

1. 重启后端容器
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose restart api
```

2. 等待启动并验证
```bash
sleep 4 && curl -s http://localhost:8888/api/v1/health
```

3. 查看日志确认无报错
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose logs --tail=20 api
```

## 场景二：修改了依赖/Dockerfile，需要重建镜像

1. 重建并重启后端
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose build --no-cache api && docker compose up -d api
```

2. 验证
```bash
sleep 5 && curl -s http://localhost:8888/api/v1/health
```

3. 查看日志
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose logs --tail=20 api
```
