-- ======================================================
-- 鲜标智投 — PostgreSQL 初始化脚本
-- 容器首次启动时自动执行（挂载到 /docker-entrypoint-initdb.d/）
-- ======================================================

-- 启用 pgvector 向量扩展（语义检索核心依赖）
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 pg_trgm 扩展（模糊搜索优化，可选）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
