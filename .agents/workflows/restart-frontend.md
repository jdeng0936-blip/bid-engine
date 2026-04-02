---
description: 重启前端服务（Docker Compose 容器重启）
---

# 重启前端

> ⚠️ 本项目通过 Docker Compose 部署，前端容器名: `fresh-bid-web`
> 统一入口：`http://localhost:8888`（Nginx 反代）

// turbo-all

## 场景一：仅重启前端容器

1. 重启前端容器
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose restart web
```

2. 等待启动并验证
```bash
sleep 5 && curl -s -o /dev/null -w "前端 HTTP 状态码: %{http_code}\n" http://localhost:8888/
```

## 场景二：修改了前端代码/依赖，需要重建镜像

1. 重建并重启前端
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose build --no-cache web && docker compose up -d web
```

2. 验证
```bash
sleep 5 && curl -s -o /dev/null -w "前端 HTTP 状态码: %{http_code}\n" http://localhost:8888/
```

3. 查看日志
```bash
cd /Users/hycdq2026/Desktop/shangxianshicai/- && docker compose logs --tail=20 web
```

**注意**: 前端是构建后部署（非 dev server），修改代码后必须重建镜像才能生效。
