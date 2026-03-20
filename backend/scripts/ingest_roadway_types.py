"""
巷道类型专项知识入库 — 补充高抽巷/低抽巷/切巷的专业技术条款

目的: 补强知识库中高抽巷(6条)、低抽巷(5条)、切巷(33条)的覆盖深度，
      使AI在生成不同巷道类型的规程时有足够的专业知识支撑。

知识来源:
  - 《煤矿安全规程》(2022版) 瓦斯抽采章节
  - 《煤矿瓦斯抽采达标暂行规定》
  - 《防治煤与瓦斯突出细则》
  - 华阳集团《采掘运技术管理规定》巷道支护章节
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine as async_engine

# 巷道类型专项知识条款
ROADWAY_KNOWLEDGE = [
    # ===== 高抽巷 =====
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "GAO-01",
        "title": "高抽巷定义与用途",
        "content": (
            "高抽巷（高位瓦斯抽放巷）是布置在煤层上方裂隙带范围内的专用瓦斯抽采巷道。"
            "主要用于抽采采空区和邻近层涌出的瓦斯，是高瓦斯和突出矿井回采工作面瓦斯治理的重要手段。"
            "高抽巷层位一般距煤层顶板15~35m，须通过钻孔验证确保处于裂隙带内。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "GAO-02",
        "title": "高抽巷布置参数要求",
        "content": (
            "高抽巷布置要求：（1）走向与回采工作面推进方向平行；"
            "（2）距回风巷水平距离一般20~50m；"
            "（3）巷道断面不小于4.5m²(矩形)或5.0m²(拱形)；"
            "（4）服务期间须保持畅通，严禁堆放杂物；"
            "（5）抽采管路直径不小于200mm，接头密封可靠。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "GAO-03",
        "title": "高抽巷安全监控要求",
        "content": (
            "高抽巷安全监控要求：（1）巷道内须安设甲烷传感器，报警浓度≥1.0%，断电浓度≥1.5%；"
            "（2）抽采管路出口须安设CO传感器；"
            "（3）密闭墙内外须安设温度传感器，实时监测自燃征兆；"
            "（4）须接入矿井安全监控系统，实现远程监测和声光报警；"
            "（5）突出矿井高抽巷须配备压力和流量监测装置。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "GAO-04",
        "title": "高抽巷施工安全措施",
        "content": (
            "高抽巷施工安全措施：（1）掘进通风须满足《煤矿安全规程》要求，局扇双风机双电源；"
            "（2）掘进期间须进行超前地质预测预报，防止误揭煤层或含水层；"
            "（3）岩巷掘进须执行打眼定爆方案，控制单次装药量；"
            "（4）距煤层20m以内须执行防突措施；"
            "（5）巷道贯通前须编制专项贯通安全技术措施。"
        ),
    },
    # ===== 低抽巷 =====
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "DI-01",
        "title": "低抽巷定义与用途",
        "content": (
            "低抽巷（底板瓦斯抽放巷/底板岩巷）是布置在煤层底板岩层中的瓦斯预抽巷道。"
            "主要通过底板穿层钻孔预抽煤层瓦斯和邻近层瓦斯，是突出矿井区域防突措施的核心手段。"
            "低抽巷距煤层底板一般10~25m，须在稳定岩层中施工。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "DI-02",
        "title": "低抽巷钻孔布置参数",
        "content": (
            "低抽巷穿层钻孔布置要求：（1）钻孔间距根据煤层透气性系数确定，突出煤层一般≤5m；"
            "（2）钻孔终孔位置须进入煤层顶板0.5m以上；"
            "（3）封孔深度不小于8m，突出煤层封孔深度不小于12m；"
            "（4）单孔抽采浓度低于10%时须补打钻孔；"
            "（5）预抽时间不少于6个月（突出煤层）或3个月（高瓦斯煤层）。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "DI-03",
        "title": "低抽巷施工与支护要求",
        "content": (
            "低抽巷施工要求：（1）采用全岩巷施工方式，严禁沿煤层掘进；"
            "（2）根据围岩条件选择锚网喷或锚网索支护，服务年限一般3~5年；"
            "（3）巷道净断面不小于6.0m²；"
            "（4）须配备专用运料和排矸系统；"
            "（5）掘进期间须进行超前探测，防止误揭含水层和地质异常体。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "DI-04",
        "title": "低抽巷抽采达标要求",
        "content": (
            "低抽巷瓦斯抽采达标指标：（1）煤层残余瓦斯含量≤8m³/t（突出煤层）；"
            "（2）煤层残余瓦斯压力≤0.74MPa（突出煤层）；"
            "（3）抽采率不低于25%（高瓦斯矿井）或30%（突出矿井）；"
            "（4）工作面日均抽采纯量不低于设计值的80%；"
            "（5）连续监测30天指标合格后方可进入下一道工序。"
        ),
    },
    # ===== 切巷 =====
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "QIE-01",
        "title": "切巷（切眼）定义与分类",
        "content": (
            "切巷（开切眼）是连接进风巷和回风巷、作为回采工作面初始开采位置的巷道。"
            "按用途分为：（1）沿走向布置的标准切巷；（2）沿倾斜方向布置的斜切巷。"
            "切巷断面一般大于回采巷道断面，宽度通常为回采工作面采高的1.5~2倍。"
            "切巷长度即为工作面长度，一般150~300m。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "QIE-02",
        "title": "切巷贯通安全技术措施",
        "content": (
            "切巷贯通安全要求：（1）相向掘进贯通，距贯通点20m时，须停止一个工作面作业；"
            "（2）须事先做好通风系统调整方案，防止贯通后风流短路；"
            "（3）瓦斯检查员须在贯通前对两端进行瓦斯检查；"
            "（4）贯通后须及时调整通风系统，确保风量满足要求；"
            "（5）高瓦斯和突出矿井贯通须编制专项防突安全技术措施。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "QIE-03",
        "title": "切巷支护与初次放顶",
        "content": (
            "切巷支护要求：（1）切巷断面宽度较大，须采用加强支护；"
            "（2）常采用锚网索+单体液压支柱联合支护；"
            "（3）初次放顶前须编制专项安全技术措施，明确：放顶步距、切顶线位置、人员撤离路线；"
            "（4）初采期间须加强矿压监测，及时掌握顶板活动规律；"
            "（5）参照集团《退锚放顶管理规定》执行。"
        ),
    },
    # ===== 进风巷 / 回风巷 补充 =====
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "JH-01",
        "title": "进风巷与回风巷通风功能对比",
        "content": (
            "进风巷：输送新鲜风流至掘进工作面，保证工作面所需新鲜空气。"
            "进风巷瓦斯浓度不得超过0.5%，CO浓度不得超过0.0024%。"
            "回风巷：排出工作面污浊风流，将有害气体和粉尘排至地面。"
            "回风巷瓦斯浓度不得超过1.0%，回风流中瓦斯浓度超过1.0%时须停止作业。"
            "高瓦斯和突出矿井的回风巷不得设电气设备（密闭墙以外除外）。"
        ),
    },
    {
        "doc_title": "巷道类型专项知识库",
        "doc_type": "巷道专项",
        "clause_no": "JH-02",
        "title": "回风巷反风能力要求",
        "content": (
            "回风巷反风要求：（1）矿井主要通风机须具备反风能力；"
            "（2）反风量不得低于正常风量的40%；"
            "（3）每年至少进行1次反风演习；"
            "（4）反风后进入回风巷的风流温度须满足安全规程要求；"
            "（5）突出矿井反风时须加强瓦斯监测，防止瓦斯逆流引发事故。"
        ),
    },
]


async def main():
    print("=" * 60)
    print("📦 巷道类型专项知识入库")
    print("=" * 60)

    async with async_engine.begin() as conn:
        # 检查是否已入库
        r = await conn.execute(text(
            "SELECT COUNT(*) FROM std_document WHERE doc_type = '巷道专项'"
        ))
        existing = r.scalar()
        if existing:
            print(f"⚠️ 已存在 {existing} 条巷道专项文档，清理后重新入库...")
            # 清理残留数据
            r2 = await conn.execute(text(
                "SELECT id FROM std_document WHERE doc_type = '巷道专项'"
            ))
            old_ids = [row[0] for row in r2.fetchall()]
            for oid in old_ids:
                await conn.execute(text("DELETE FROM std_clause WHERE document_id = :did"), {"did": oid})
                await conn.execute(text("DELETE FROM std_document WHERE id = :did"), {"did": oid})
            print(f"  清理完成: {len(old_ids)} 个文档")

        # 创建文档记录
        r = await conn.execute(text(
            "INSERT INTO std_document (title, doc_type, tenant_id, is_current) "
            "VALUES (:title, :doc_type, 1, true) RETURNING id"
        ), {
            "title": "巷道类型专项知识库",
            "doc_type": "巷道专项",
        })
        doc_id = r.scalar()
        print(f"✅ 创建文档 ID={doc_id}")

        # 插入条款
        count = 0
        for clause in ROADWAY_KNOWLEDGE:
            title = clause["title"][:60]  # 截断避免超长
            await conn.execute(text(
                "INSERT INTO std_clause (document_id, clause_no, title, content, level) "
                "VALUES (:doc_id, :clause_no, :title, :content, 1)"
            ), {
                "doc_id": doc_id,
                "clause_no": clause["clause_no"],
                "title": title,
                "content": clause["content"],
            })
            count += 1
            print(f"  ✅ [{clause['clause_no']}] {title}")

        print(f"\n🎉 入库完成: {count} 条巷道专项知识")
        print(f"   高抽巷: 4 条 (GAO-01~04)")
        print(f"   低抽巷: 4 条 (DI-01~04)")
        print(f"   切巷: 3 条 (QIE-01~03)")
        print(f"   进风/回风: 2 条 (JH-01~02)")

    # 向量化
    print("\n🔄 向量化中...")
    from app.services.embedding_service import EmbeddingService
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        svc = EmbeddingService(session)
        vec_count = await svc.vectorize_standards(tenant_id=1)
        print(f"✅ 向量化完成: {vec_count} 条")


if __name__ == "__main__":
    asyncio.run(main())
