# 前后端全栈部署及常见故障排查记录

本文档记录了项目开发部署过程中遇到的技术难点、踩坑点及最终解决方案，以便日后查阅。

---

## 1. 前端代码未推送到远程仓库（Git 孤儿子模块问题）

### 🤒 现象：做什么？
在 GitHub 仓库中看到的 `frontend` 目录是一个无法点击的空壳（类似 `@commit-hash`），使用 `git status` 时前端文件被忽略，导致团队其他人克隆代码时没有前端源码。

### 🔍 诊断：为什么？
在使用 `create-next-app` 初始化前端项目时，脚手架会在 `frontend/` 目录内部自动生成一个独立的 `.git` 仓库。
此时根目录的 Git 会自动将其识别为 **Git Submodule（子模块）**的指针（类型为 `160000`），从而只记录了一个 commit 引用，而直接丢弃/忽略了实际的目录内容。因此，前端所有源代码始终处于 untracked 状态。

### ✅ 修复方案：怎么做？
将 `frontend` 从子模块状态恢复为普通目录，并重新提交：
```bash
# 1. 从 Git 索引中强制移除被误认的子模块
git rm --cached frontend

# 2. 如果 frontend 内部还有 .git 文件夹，也需要删除（按需）
# rm -rf frontend/.git

# 3. 重新将 frontend 作为普通文件夹追踪
git add frontend/

# 4. 提交并推送到远端
git commit -m "fix: 将 frontend 从孤儿子模块转为普通目录，提交前端源码"
git push
```

---

## 2. AI 助手页面对话报 Network Error（SSE 传输中断）

### 🤒 现象：做什么？
在部署完整的全栈 Docker 环境后，访问 AI 助手发送问题时，页面短暂停顿并直接报错 `⚠️ 请求失败: network error`。
同时，控制台出现 `net::ERR_INCOMPLETE_CHUNKED_ENCODING` 报错。

### 🔍 诊断：为什么？
1. **表面现象（前端）**：该报错表面上由于 Server-Sent Events (SSE) 流式传输被中间代理（如 Nginx）缓冲导致异常中断。
2. **根本原因（后端）**：查阅 `excavation-api` 服务后端的日志发现，实际在路由层面抛出了 404 错误：
   `openai.NotFoundError: Error code: 404 - models/gemini-2.5-flash-preview-04-17 is not found`
   这说明系统中配置的基座大模型（`gemini-2.5-flash-preview-04-17`）已经被 Google 官方下线或废弃，API 请求失败。LLM 服务直接抛出异常切断连接，Nginx 的流被强行关闭，从而在前端表现为 `network error`。

### ✅ 修复方案：怎么做？
更新失效的模型环境变量并重启容器：
```bash
# 1. 修改后端环境变量文件
# 编辑 backend/.env 文件：
- AI_MODEL="gemini-2.5-flash-preview-04-17"
+ AI_MODEL="gemini-2.5-flash"

# 2. 强制使用新配置重新创建后台 Docker 容器 
# （注：Docker Compose 中单纯使用 restart 不会重新加载外挂的 .env 变更）
docker compose up -d api --force-recreate

# 3. 验证网络畅通
# 重新刷新前端页面发送问题，观察流式文字是否平滑输出，问题解决。
```
