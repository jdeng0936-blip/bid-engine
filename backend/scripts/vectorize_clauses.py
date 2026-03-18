"""
批量向量化脚本 — 对 std_clause 表中的条款生成 1536 维嵌入向量

用法: python scripts/vectorize_clauses.py

功能:
  1. 读取所有 embedding IS NULL 的条款
  2. 拼接 document_title + clause_no + content 作为文本
  3. 调用 Gemini text-embedding-004 批量生成向量
  4. 更新到数据库 embedding 列

依赖: google-genai, sqlalchemy, asyncpg, pgvector
"""
import asyncio
import os
import sys
import time

# 让脚本能 import app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from google import genai

# ========== 配置 ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBED_MODEL = "gemini-embedding-001"
BATCH_SIZE = 20  # 每批处理条数
DIMENSION = 1536

if not GEMINI_API_KEY:
    print("❌ 未配置 GEMINI_API_KEY，请在 .env 中设置")
    sys.exit(1)

# 初始化 Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
print("✅ Gemini API 已初始化")


async def main():
    from sqlalchemy import text
    from app.core.database import engine

    async with engine.connect() as conn:
        # 查询未向量化的条款（JOIN 获取文档标题）
        rows = (await conn.execute(text("""
            SELECT c.id, d.title AS doc_title, c.clause_no, c.content
            FROM std_clause c
            JOIN std_document d ON c.document_id = d.id
            WHERE c.embedding IS NULL
            ORDER BY c.id
        """))).fetchall()

        total = len(rows)
        if total == 0:
            print("✅ 所有条款已向量化，无需操作")
            return

        print(f"📊 待处理条款: {total} 条")
        done = 0

        # 分批处理
        for i in range(0, total, BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            batch_texts = []
            batch_ids = []

            for row in batch:
                # 拼接文本：文档标题 + 条款编号 + 内容
                parts = [row.doc_title or ""]
                if row.clause_no:
                    parts.append(f"第{row.clause_no}条")
                parts.append(row.content or "")
                text_input = " ".join(p for p in parts if p)
                batch_texts.append(text_input)
                batch_ids.append(row.id)

            # 调用 Gemini Embedding API（新 SDK）
            try:
                result = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=batch_texts,
                    config={"output_dimensionality": DIMENSION},
                )
                embeddings = [e.values for e in result.embeddings]
            except Exception as e:
                print(f"⚠️ 批次 {i//BATCH_SIZE + 1} 调用失败: {e}")
                time.sleep(2)
                continue

            # 写入数据库
            for clause_id, emb in zip(batch_ids, embeddings):
                emb_str = "[" + ",".join(str(v) for v in emb) + "]"
                await conn.execute(
                    text("UPDATE std_clause SET embedding = :emb WHERE id = :id"),
                    {"emb": emb_str, "id": clause_id},
                )

            await conn.commit()
            done += len(batch)
            print(f"  ✅ 批次 {i//BATCH_SIZE + 1}: {len(batch)} 条已更新 ({done}/{total})")

            # 控制速率（避免触发 API 限流）
            if i + BATCH_SIZE < total:
                time.sleep(1)

        print(f"\n🎉 向量化完成: {done}/{total} 条")


if __name__ == "__main__":
    asyncio.run(main())
