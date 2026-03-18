---
description: 重启后端服务（先杀旧进程再启动新实例）
---

## 重启后端 uvicorn 服务

每次需要启动或重启后端服务时，**必须**按以下步骤执行，避免多个旧进程同时监听 8000 端口导致新代码不生效。

// turbo-all

### 方式一：Docker 部署（推荐）

1. 重启后端容器：
```bash
cd /Users/imac2026/Desktop/掘进工作面规程智能生成平台
docker compose restart api
```

2. 查看后端日志确认启动成功：
```bash
docker compose logs -f --tail=20 api
```

3. 如需重建后端镜像（改了依赖/Dockerfile 时）：
```bash
docker compose build --no-cache api && docker compose up -d api
```

### 方式二：本地直接运行

1. 查找所有监听 8000 端口的进程：
```bash
lsof -ti :8000
```

2. 杀死所有监听 8000 端口的进程：
```bash
lsof -ti :8000 | xargs kill -9 2>/dev/null || echo "No old processes"
```

3. 等待 2 秒确保端口释放：
```bash
sleep 2
```

4. 启动新的 uvicorn 实例：
```bash
cd /Users/imac2026/Desktop/掘进工作面规程智能生成平台/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. 验证只有一个进程监听 8000：
```bash
lsof -i :8000 | grep LISTEN
```
预期结果：只有 1-2 行（主进程 + reload worker），不应超过 2 行。
