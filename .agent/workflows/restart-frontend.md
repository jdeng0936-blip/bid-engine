---
description: 重启前端服务（自动清理端口占用和 lock 文件）
---

# 重启前端

// turbo-all

1. 杀掉占用 3000 端口的旧进程并清理 lock 文件
```bash
kill -9 $(lsof -t -i:3000) 2>/dev/null; rm -f /Users/mac111/Desktop/煤炭/frontend/.next/dev/lock; echo "port 3000 cleared, lock removed"
```

2. 启动前端 dev server
```bash
cd /Users/mac111/Desktop/煤炭/frontend && npm run dev
```

3. 确认输出包含 `✓ Ready` 即表示启动成功

**注意**: 如果 3000 被其他项目占用（非本项目进程），Next.js 会自动切换到可用端口（如 3001/3002），此时查看终端输出的实际端口号即可。
