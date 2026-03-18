---
description: 一键启动前后端（自动清理端口占用）
---

# 启动前后端

// turbo-all

1. 清理并启动后端（端口 8000）
```bash
kill -9 $(lsof -t -i:8000) 2>/dev/null
source /Users/mac111/Desktop/煤炭/backend/venv/bin/activate && cd /Users/mac111/Desktop/煤炭/backend && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 4
curl -s http://localhost:8000/api/v1/health
```

2. 清理并启动前端（端口 3000）
```bash
kill -9 $(lsof -t -i:3000) 2>/dev/null; rm -f /Users/mac111/Desktop/煤炭/frontend/.next/dev/lock
cd /Users/mac111/Desktop/煤炭/frontend && npm run dev
```

3. 确认两个服务都正常启动：
   - 后端 health check: `{"status":"ok"}`
   - 前端 Ready: `✓ Ready in xxxms`
