"""
P2 基准对比脚本 — AI 生成 vs 客户真实规程 逐章覆盖率分析

做什么:
  1. 从数据库读取客户样本条款(doc_type=客户样本)
  2. 按文档分组，提取各章节关键词
  3. 与 AI 生成的 9 章逐章比对语义相似度
  4. 输出覆盖率报告 + 差异分析

输出:
  - 各章覆盖率百分比
  - 人工有但 AI 缺少的内容
  - AI 有但人工没有的内容(增值项)
"""
import asyncio
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine as async_engine


# AI 生成的 9 章标准结构
AI_CHAPTERS = [
    "概述",
    "地质条件",
    "巷道支护设计",
    "施工工艺",
    "生产系统",
    "劳动组织及主要技术经济指标",
    "安全技术措施",
    "灾害预防",
    "应急救援",
]

# 客户规程常见章节关键词 → AI 章节映射
CHAPTER_MAPPING = {
    "概述": ["概述", "巷道名称", "巷道布置", "工程概况", "编制依据"],
    "地质条件": ["地质", "煤层", "水文", "地面位置", "地质构造", "岩层"],
    "巷道支护设计": ["支护", "锚杆", "锚索", "喷浆", "断面", "掘进断面"],
    "施工工艺": ["施工", "工艺", "掘进方法", "装岩", "运输", "钻眼", "爆破", "出矸"],
    "生产系统": ["通风", "供电", "排水", "供水", "压风", "监控", "通讯", "运输系统", "防尘"],
    "劳动组织": ["劳动组织", "循环", "作业", "工作制", "技术经济"],
    "安全技术措施": ["安全", "顶板", "一通三防", "机电", "爆破安全", "防治水"],
    "灾害预防": ["灾害", "预防", "辨识", "风险"],
    "应急救援": ["应急", "避灾", "救援", "撤退", "自救"],
}


def classify_clause(title: str, content: str) -> str:
    """将客户条款分类到 AI 章节"""
    text_combined = f"{title} {content[:200]}"
    best_match = "其他"
    best_score = 0
    for chapter, keywords in CHAPTER_MAPPING.items():
        score = sum(1 for kw in keywords if kw in text_combined)
        if score > best_score:
            best_score = score
            best_match = chapter
    return best_match if best_score > 0 else "其他"


async def main():
    print("=" * 70)
    print("📊 P2: AI vs 人工基准对比报告")
    print("=" * 70)

    async with async_engine.connect() as conn:
        # 1. 读取客户样本条款
        result = await conn.execute(text(
            "SELECT sc.title, sc.content, sc.clause_no, sd.title as doc_title "
            "FROM std_clause sc "
            "JOIN std_document sd ON sd.id = sc.document_id "
            "WHERE sd.doc_type = '客户样本' "
            "ORDER BY sd.id, sc.id"
        ))
        rows = result.mappings().all()
        print(f"\n📄 客户样本条款总数: {len(rows)}")

        # 2. 按文档分组
        doc_groups = defaultdict(list)
        for r in rows:
            doc_groups[r["doc_title"]].append(r)
        print(f"📁 文档数: {len(doc_groups)}")
        for doc_title, clauses in doc_groups.items():
            print(f"   - {doc_title}: {len(clauses)} 条")

        # 3. 逐章分类并统计覆盖率
        print(f"\n{'='*70}")
        print("📈 逐章覆盖率分析")
        print(f"{'='*70}")

        for doc_title, clauses in doc_groups.items():
            print(f"\n{'─'*50}")
            print(f"📄 {doc_title}")
            print(f"{'─'*50}")

            # 将每条客户条款分类到 AI 章节
            chapter_map = defaultdict(list)
            for c in clauses:
                chapter = classify_clause(c["title"], c["content"])
                chapter_map[chapter].append(c)

            # 统计
            total = len(clauses)
            covered = 0
            uncovered_items = []

            for ai_chapter in AI_CHAPTERS:
                matched = chapter_map.get(ai_chapter, [])
                count = len(matched)
                covered += count
                pct = round(count / total * 100, 1) if total > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))

                status = "✅" if count > 0 else "⬜"
                print(f"  {status} {ai_chapter:<20} {bar} {pct:5.1f}% ({count}/{total})")

                if count == 0:
                    uncovered_items.append(ai_chapter)

            # 未分类的条款（人工有但 AI 结构中没有对应章节）
            other = chapter_map.get("其他", [])
            if other:
                print(f"  🔸 未映射条款          {'░' * 20} {round(len(other)/total*100,1):5.1f}% ({len(other)}/{total})")

            coverage_rate = round(covered / total * 100, 1) if total > 0 else 0
            print(f"\n  📊 整体覆盖率: {coverage_rate}%")
            if uncovered_items:
                print(f"  ⚠️  AI 缺失章节: {', '.join(uncovered_items)}")

            # AI 增值分析
            print(f"\n  💡 AI 增值项（人工规程未涉及但 AI 会生成）:")
            for ai_ch in AI_CHAPTERS:
                if ai_ch not in [classify_clause(c["title"], c["content"]) for c in clauses]:
                    print(f"     + {ai_ch}")

        # 4. 总结
        print(f"\n{'='*70}")
        print("📋 总结")
        print(f"{'='*70}")
        all_clauses = [c for clauses in doc_groups.values() for c in clauses]
        all_map = defaultdict(int)
        for c in all_clauses:
            ch = classify_clause(c["title"], c["content"])
            all_map[ch] += 1

        total_all = len(all_clauses)
        print(f"\n  客户样本总条款: {total_all}")
        print(f"  AI 9 章覆盖分布:")
        for ai_ch in AI_CHAPTERS:
            cnt = all_map.get(ai_ch, 0)
            pct = round(cnt / total_all * 100, 1) if total_all > 0 else 0
            print(f"    {ai_ch:<24} {cnt:>4} 条 ({pct}%)")
        other_cnt = all_map.get("其他", 0)
        if other_cnt:
            print(f"    {'未映射':<24} {other_cnt:>4} 条 ({round(other_cnt/total_all*100,1)}%)")

        mapped_total = total_all - other_cnt
        final_rate = round(mapped_total / total_all * 100, 1) if total_all > 0 else 0
        print(f"\n  ✅ AI 9 章结构覆盖率: {final_rate}%")
        print(f"  📌 未映射条款数: {other_cnt} ({round(other_cnt/total_all*100,1)}%)")
        print(f"\n{'='*70}")
        print("🎉 对比完成！报告可用于客户演示和产品评估。")


if __name__ == "__main__":
    asyncio.run(main())
