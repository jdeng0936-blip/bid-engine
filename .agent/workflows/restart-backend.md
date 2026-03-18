---
description: 重启后端服务（先杀旧进程再启动新实例）
---

# 重启后端

// turbo-all

1. 杀掉占用 8000 端口的旧进程
```bash
kill -9 $(lsof -t -i:8000) 2>/dev/null; echo "port 8000 cleared"
```

2. 启动后端服务
```bash
source /Users/mac111/Desktop/煤炭/backend/venv/bin/activate && cd /Users/mac111/Desktop/煤炭/backend && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 4
curl -s http://localhost:8000/api/v1/health
```

3. 确认 health check 返回 `{"status":"ok"}`
