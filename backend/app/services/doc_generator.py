"""
文档生成引擎 — 编排全链路：参数→规则匹配→计算→模板填充→Word 输出

流程：
  1. 加载 ProjectParams + Project 基础信息
  2. 调用 RuleService.match_rules() → 命中规则+章节列表
  3. 调用 SupportCalcEngine + VentCalcEngine → 计算结果
  4. 按章节顺序组装内容
  5. python-docx 生成 .docx 文件
"""
import os
from datetime import datetime
from typing import Optional

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectParams
from app.schemas.calc import SupportCalcInput
from app.schemas.vent import VentCalcInput
from app.schemas.doc import ChapterContent, DocGenerateResult
from app.services.calc_engine import SupportCalcEngine
from app.services.vent_engine import VentCalcEngine
from app.services.rule_service import RuleService


# 参数字段中文映射
PARAM_LABELS: dict[str, str] = {
    "rock_class": "围岩级别", "coal_thickness": "煤层厚度(m)",
    "coal_dip_angle": "煤层倾角(°)", "gas_level": "瓦斯等级",
    "hydro_type": "水文地质类型", "geo_structure": "地质构造",
    "spontaneous_combustion": "自燃倾向性", "roadway_type": "巷道类型",
    "excavation_type": "掘进类型", "section_form": "断面形式",
    "section_width": "断面宽度(m)", "section_height": "断面高度(m)",
    "excavation_length": "掘进长度(m)", "service_years": "服务年限(年)",
    "dig_method": "掘进方式", "dig_equipment": "掘进设备",
    "transport_method": "运输方式",
}


class DocGenerator:
    """文档生成引擎"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate(
        self, project_id: int, tenant_id: int, include_calc: bool = True
    ) -> DocGenerateResult:
        """
        端到端文档生成

        Returns:
            DocGenerateResult 包含文件路径和章节列表
        """
        # 1. 加载项目信息
        project = await self._load_project(project_id, tenant_id)
        if not project:
            raise ValueError("项目不存在或无权访问")

        params = await self._load_params(project_id)
        params_dict = self._params_to_dict(params) if params else {}

        # 2. 规则匹配
        rule_svc = RuleService(self.session)
        match_result = None
        try:
            match_result = await rule_svc.match_rules(project_id, tenant_id)
        except ValueError:
            pass  # 参数未填写时跳过匹配

        # 3. 计算引擎
        calc_result = None
        vent_result = None
        if include_calc and params:
            calc_result = self._run_support_calc(params_dict)
            vent_result = self._run_vent_calc(params_dict)

        # 4. 组装章节
        chapters = self._assemble_chapters(
            project, params_dict, match_result, calc_result, vent_result
        )

        # 4.5 智能深度润色（AI赋能）
        chapters = await self._ai_polish_content(chapters, params_dict)

        # 5. 生成 Word
        file_path = self._render_docx(project, chapters, calc_result, vent_result)

        total_warnings = 0
        if calc_result:
            total_warnings += len(calc_result.warnings)
        if vent_result:
            total_warnings += len(vent_result.warnings)

        return DocGenerateResult(
            project_id=project_id,
            project_name=project.face_name,
            file_path=file_path,
            total_chapters=len(chapters),
            total_warnings=total_warnings,
            chapters=chapters,
        )

    # ========== 加载数据 ==========

    async def _load_project(self, pid: int, tid: int) -> Optional[Project]:
        result = await self.session.execute(
            select(Project).where(Project.id == pid, Project.tenant_id == tid)
        )
        return result.scalar_one_or_none()

    async def _load_params(self, pid: int) -> Optional[ProjectParams]:
        result = await self.session.execute(
            select(ProjectParams).where(ProjectParams.project_id == pid)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _params_to_dict(params: ProjectParams) -> dict:
        return {
            c.key: getattr(params, c.key)
            for c in params.__table__.columns
            if c.key not in ("id", "project_id")
        }

    # ========== 计算引擎调用 ==========

    @staticmethod
    def _run_support_calc(p: dict):
        try:
            inp = SupportCalcInput(
                rock_class=p.get("rock_class", "III"),
                section_form=p.get("section_form", "矩形"),
                section_width=float(p.get("section_width", 4.5)),
                section_height=float(p.get("section_height", 3.2)),
            )
            return SupportCalcEngine.calculate(inp)
        except Exception:
            return None

    @staticmethod
    def _run_vent_calc(p: dict):
        try:
            inp = VentCalcInput(
                gas_emission=float(p.get("gas_emission", 2.0) or 2.0),
                gas_level=p.get("gas_level", "低瓦斯"),
                section_area=float(p.get("section_width", 4.5)) * float(p.get("section_height", 3.2)),
                excavation_length=float(p.get("excavation_length", 300)),
            )
            return VentCalcEngine.calculate(inp)
        except Exception:
            return None

    # ========== 章节组装 ==========

    def _assemble_chapters(self, project, params_dict, match_result, calc_result, vent_result):
        """按华阳集团《采掘运技术管理规定》9章结构组装规程内容"""
        chapters: list[ChapterContent] = []

        # ========== 第一章 地质概况 ==========
        geo_lines = [
            f"项目名称：{project.face_name}",
            f"矿井名称：{getattr(project, 'mine_name', '—')}",
            "",
            "一、煤层赋存",
        ]
        geo_fields = {
            "coal_thickness": "煤层厚度(m)", "coal_dip_angle": "煤层倾角(°)",
            "gas_level": "瓦斯等级", "spontaneous_combustion": "自燃倾向性",
        }
        for field, label in geo_fields.items():
            val = params_dict.get(field, "—")
            if val is not None:
                geo_lines.append(f"  {label}：{val}")

        geo_lines.extend([
            "",
            "二、顶底板岩性",
            f"  围岩级别：{params_dict.get('rock_class', '—')}",
            "",
            "三、地质构造",
            f"  地质构造类型：{params_dict.get('geo_structure', '—')}",
            "",
            "四、水文地质",
            f"  水文地质类型：{params_dict.get('hydro_type', '—')}",
        ])

        chapters.append(ChapterContent(
            chapter_no="第一章", title="地质概况",
            content="\n".join(geo_lines), source="template",
        ))

        # ========== 第二章 巷道布置与断面设计 ==========
        layout_lines = [
            "一、巷道布置",
            f"  巷道类型：{params_dict.get('roadway_type', '—')}",
            f"  掘进长度：{params_dict.get('excavation_length', '—')} m",
            f"  服务年限：{params_dict.get('service_years', '—')} 年",
            "",
            "二、断面设计",
            f"  断面形式：{params_dict.get('section_form', '—')}",
            f"  断面宽度：{params_dict.get('section_width', '—')} m",
            f"  断面高度：{params_dict.get('section_height', '—')} m",
        ]
        section_w = float(params_dict.get("section_width", 0) or 0)
        section_h = float(params_dict.get("section_height", 0) or 0)
        if section_w > 0 and section_h > 0:
            area = round(section_w * section_h, 2)
            layout_lines.append(f"  断面净面积：{area} m²")

        layout_lines.extend([
            "",
            "三、煤柱留设",
            "  按照集团《采掘运技术管理规定》及采区设计确定的煤柱尺寸执行，",
            "  严禁在施工过程中任意扩大或缩小设计确定的煤柱。",
        ])

        chapters.append(ChapterContent(
            chapter_no="第二章", title="巷道布置与断面设计",
            content="\n".join(layout_lines), source="template",
        ))

        # ========== 第三章 巷道支护设计 ==========
        if calc_result:
            support_lines = [
                "一、正常段支护参数",
                f"  断面净面积：{calc_result.section_area} m²",
                f"  单根锚杆锚固力：{calc_result.bolt_force} kN",
                f"  最大允许锚杆间距：{calc_result.max_bolt_spacing} mm",
                f"  最大允许排距：{calc_result.max_bolt_row_spacing} mm",
                f"  推荐每排锚杆数：{calc_result.recommended_bolt_count_per_row} 根",
                f"  最少锚索数量：{calc_result.min_cable_count} 根",
                f"  支护密度：{calc_result.support_density} 根/m²",
                f"  安全系数：{calc_result.safety_factor}",
                "",
                "二、构造影响段加强支护",
                "  过断层、陷落柱等地质构造期间，须根据变化情况及时优化支护设计。",
                "  冒落高度＜3m时：采用\"锚索+金属网\"超前维护后架棚通过；",
                "  冒落高度≥3m时：直接采用架棚支护，棚距不大于规定值。",
                "  锚索预紧力必须逐根检查，确保预应力全部达标。",
                "",
                "三、支护工艺",
                "  煤巷综掘、大断面岩巷综掘必须使用机载式临时支护装置。",
                "  使用液压锚杆台车时要保证临时支护装置完好可靠。",
            ]
            if calc_result.warnings:
                support_lines.append("")
                support_lines.append("【合规预警】")
                for w in calc_result.warnings:
                    support_lines.append(f"  ⚠ {w.message}")

            chapters.append(ChapterContent(
                chapter_no="第三章", title="巷道支护设计",
                content="\n".join(support_lines), source="calc_engine",
                has_warning=not calc_result.is_compliant,
            ))

        # ========== 第四章 施工工艺 ==========
        craft_lines = [
            "一、掘进方式",
            f"  掘进方式：{params_dict.get('dig_method', '—')}",
            f"  掘进类型：{params_dict.get('excavation_type', '—')}",
            f"  掘进设备：{params_dict.get('dig_equipment', '—')}",
            "",
            "二、爆破作业",
            "  严格执行\"一炮三检\"和\"三人连锁放炮\"制度。",
            "  炮孔内发现异状、温度骤高骤低、有显著瓦斯涌出、煤岩松软时，",
            "  必须停止装药，并采取安全措施。",
            "",
            "三、装载与运输",
            f"  运输方式：{params_dict.get('transport_method', '—')}",
            "",
            "四、管线及轨道敷设",
            "  风、水管路要同侧敷设，不得与瓦斯抽采管路同侧布置。",
        ]

        chapters.append(ChapterContent(
            chapter_no="第四章", title="施工工艺",
            content="\n".join(craft_lines), source="template",
        ))

        # ========== 第五章 生产系统 ==========
        system_lines = []

        # 5.1 通风（含计算结果）
        system_lines.append("一、通风系统")
        if vent_result:
            system_lines.extend([
                f"  瓦斯涌出法需风量：{vent_result.q_gas} m³/min",
                f"  人数法需风量：{vent_result.q_people} m³/min",
                f"  炸药法需风量：{vent_result.q_explosive} m³/min",
                f"  最终配风量：{vent_result.q_required} m³/min",
                f"  推荐局扇：{vent_result.recommended_fan}（{vent_result.fan_power} kW）",
            ])
            if vent_result.warnings:
                system_lines.append("  【合规预警】")
                for w in vent_result.warnings:
                    system_lines.append(f"    ⚠ {w.message}")

        system_lines.extend([
            "",
            "二、综合防尘",
            "  采用湿式打眼、喷雾降尘、通风除尘等综合防尘措施。",
            "  掘进工作面应安设净化水幕、转载点喷雾装置。",
            "",
            "三、防灭火",
            "  巷道布置及通风设施设置须符合防灭火要求。",
            "  厚煤层工作面进、回风巷开口须按规定设置防灭火设施。",
            "",
            "四、供电",
            "  掘进工作面供电须采用三专线路（专用变压器、开关、电缆）。",
            "",
            "五、供排水",
            "  掘进工作面须配备排水设备，排水能力须满足最大涌水量要求。",
            "",
            "六、压风系统",
            "  压风自救装置安设间距不超过200米。",
            "",
            "七、监控与通讯",
            "  掘进工作面须安设甲烷传感器、一氧化碳传感器、风速传感器。",
            "  高瓦斯矿井使用量程上限不低于10%的甲烷传感器；",
            "  突出煤层使用量程上限不低于40%的甲烷传感器。",
        ])

        chapters.append(ChapterContent(
            chapter_no="第五章", title="生产系统",
            content="\n".join(system_lines), source="calc_engine" if vent_result else "template",
            has_warning=bool(vent_result and not vent_result.is_compliant),
        ))

        # ========== 第六章 劳动组织 ==========
        labor_lines = [
            "一、劳动组织",
            "  实行\"三八\"作业制，两班生产、一班检修。",
            "",
            "二、循环作业",
            "  按照\"正规循环作业\"要求组织生产，正规循环率不低于80%。",
            "",
            "三、主要技术经济指标",
            f"  巷道掘进长度：{params_dict.get('excavation_length', '—')} m",
        ]

        chapters.append(ChapterContent(
            chapter_no="第六章", title="劳动组织及主要技术经济指标",
            content="\n".join(labor_lines), source="template",
        ))

        # ========== 第七章 安全技术措施（8专项） ==========
        safety_lines = [
            "一、顶板管理",
            "  掘进工作面应当严格执行敲帮问顶制度，开工前必须全面检查。",
            "  空顶距离不得超过规定值，掘开面附近必须设临时支护。",
            "",
            "二、一通三防",
            "  严格执行瓦斯检查制度，瓦斯超限必须停止作业。",
            f"  本工作面瓦斯等级：{params_dict.get('gas_level', '—')}",
            "",
            "三、爆破安全",
            "  严格执行\"一炮三检\"制度，瓦斯浓度达到0.5%时严禁放炮。",
            "",
            "四、防治水",
            "  坚持\"有疑必探、先探后掘\"的原则。",
            f"  水文地质类型：{params_dict.get('hydro_type', '—')}",
            "",
            "五、机电安全",
            "  井下电气设备必须取得煤矿矿用产品安全标志。",
            "  各部位绝缘电阻值应不低于0.5MΩ。",
            "",
            "六、运输安全",
            "  运输设备运行前必须发出警报信号。",
            "",
            "七、监控与通讯",
            "  掘进工作面必须安装甲烷传感器并实现瓦斯电闭锁。",
            "",
            "八、其它安全措施",
            "  掘进面进入构造影响区域前，须提前制定专项安全技术措施。",
        ]

        chapters.append(ChapterContent(
            chapter_no="第七章", title="安全技术措施",
            content="\n".join(safety_lines), source="template",
        ))

        # ========== 第八章 灾害预防 ==========
        disaster_lines = [
            "一、主要灾害类型辨识",
            f"  瓦斯等级：{params_dict.get('gas_level', '—')}",
            f"  自燃倾向性：{params_dict.get('spontaneous_combustion', '—')}",
            f"  水文地质类型：{params_dict.get('hydro_type', '—')}",
            "",
            "二、灾害预防措施",
            "  根据辨识出的灾害类型，逐项制定针对性预防措施。",
            "  瓦斯灾害：加强瓦斯抽采和监测，确保通风可靠。",
            "  水害：坚持先探后掘，配备专用排水系统。",
            "  火灾：合理设置防灭火设施，配备灭火器材。",
            "  顶板灾害：严格支护管理，加强矿压观测。",
        ]

        chapters.append(ChapterContent(
            chapter_no="第八章", title="灾害预防",
            content="\n".join(disaster_lines), source="template",
        ))

        # ========== 第九章 应急避险 ==========
        emergency_lines = [
            "一、应急预案",
            "  按照集团《采掘运技术管理规定》要求，制定掘进工作面专项应急预案。",
            "",
            "二、避灾路线",
            "  根据掘进工作面位置和灾害类型，明确相应避灾路线。",
            "  避灾路线须标注在作业规程附图中，并在井下设置明显标识。",
            "",
            "三、自救器及避险设施",
            "  掘进工作面所有作业人员必须随身携带自救器。",
            "  压风自救装置安设间距不超过200米。",
        ]

        chapters.append(ChapterContent(
            chapter_no="第九章", title="安全风险管控及应急避险",
            content="\n".join(emergency_lines), source="template",
        ))

        # ========== 附录：编制依据与规则命中 ==========
        if match_result and match_result.matched_rules:
            rule_lines = []
            for mr in match_result.matched_rules:
                rule_lines.append(f"• {mr.rule_name}（{mr.category}，优先级 {mr.priority}）")
                for a in mr.actions:
                    rule_lines.append(f"  → 关联章节：{a.target_chapter}")

            chapters.append(ChapterContent(
                chapter_no="附录", title="编制依据与规则命中",
                content="\n".join(rule_lines), source="rule_match",
            ))

        return chapters


    async def _ai_polish_content(self, chapters: list[ChapterContent], params: dict) -> list[ChapterContent]:
        """
        AI 深度润色长尾章节 — RAG 增强版

        流程:
          1. 对每个须润色的章节，用章节标题检索标准库 + 知识库
          2. 将检索到的规程片段注入 LLM System Prompt
          3. LLM 基于客户真实规程生成更贴合实际的内容
        """
        from app.core.config import settings
        from openai import AsyncOpenAI
        from app.services.embedding_service import EmbeddingService

        api_key = settings.OPENAI_API_KEY or settings.GEMINI_API_KEY
        base_url = settings.OPENAI_BASE_URL or None
        model = settings.AI_MODEL

        if not api_key:
            return chapters  # 降级：无大模型配置时原样返回

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = AsyncOpenAI(**client_kwargs)

        # RAG 检索服务
        emb_svc = EmbeddingService(self.session)

        for ch in chapters:
            if any(kw in ch.title for kw in [
                "安全技术措施", "灾害预防", "支护", "应急", "施工工艺",
                "生产系统", "防尘", "防灭火"
            ]):
                # ===== RAG 检索：标准库 + 知识库 =====
                rag_context_parts = []

                # L1a: 标准库条款
                std_results = await emb_svc.search_similar(
                    query=ch.title, tenant_id=1, top_k=3, threshold=0.4
                )
                if std_results:
                    rag_context_parts.append("【标准库参考条款】")
                    for r in std_results:
                        rag_context_parts.append(
                            f"- [{r['doc_title']}] {r['clause_no']}: {r['content'][:300]}"
                        )

                # L1b: 知识库（客户规程片段）
                snippet_results = await emb_svc.search_snippets(
                    query=ch.title, tenant_id=1, top_k=5, threshold=0.4
                )
                if snippet_results:
                    rag_context_parts.append("\n【客户规程参考内容】")
                    for r in snippet_results:
                        rag_context_parts.append(
                            f"- [{r['chapter_name']}]: {r['content'][:300]}"
                        )

                rag_context = "\n".join(rag_context_parts)
                rag_note = ""
                if rag_context:
                    rag_note = (
                        f"\n\n以下是从客户已有规程和国家标准中检索到的相关内容，"
                        f"请务必参考并融入你的输出中，确保与客户实际情况一致：\n{rag_context}\n"
                    )

                prompt = (
                    f"请作为顶尖煤矿安全专家，根据以下参数对作业规程的【{ch.title}】章节进行扩充、润色，"
                    f"使其更符合现场实际，具备可操作性，避免生硬的模板拼接感。\n"
                    f"地质条件与参数: {params}\n"
                    f"原始内容框架:\n{ch.content}"
                    f"{rag_note}\n\n"
                    "要求：\n"
                    "1. 直接输出润色后的篇章正式内容，不要包含任何前言后语和分析推理过程。\n"
                    "2. 分条列出，层级清晰，重点突出。\n"
                    "3. 如引用了参考资料中的具体数值标准，请在文中自然融入。"
                )
                try:
                    resp = await client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    polished = resp.choices[0].message.content
                    if polished:
                        ch.content = polished
                        ch.source = "ai_polished"
                except Exception as e:
                    print(f"⚠️ AI 润色失败: {e}")

        return chapters

    # ========== Word 渲染 ==========

    def _render_docx(self, project, chapters, calc_result, vent_result) -> str:
        """用 python-docx 生成 .docx 文件"""
        doc = Document()

        # 文档样式
        style = doc.styles["Normal"]
        style.font.name = "宋体"
        style.font.size = Pt(12)

        # --- 封面 ---
        for _ in range(4):
            doc.add_paragraph()

        title = doc.add_paragraph()
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = title.add_run(f"{project.face_name}")
        run.font.size = Pt(22)
        run.font.bold = True

        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run2 = subtitle.add_run("掘进工作面作业规程")
        run2.font.size = Pt(18)

        doc.add_paragraph()

        meta_items = [
            f"矿井名称：{getattr(project, 'mine_name', '—')}",
            f"编制日期：{datetime.now().strftime('%Y年%m月%d日')}",
            f"编制单位：生产技术科",
        ]
        for item in meta_items:
            p = doc.add_paragraph()
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            p.add_run(item).font.size = Pt(14)

        doc.add_page_break()

        # --- 正文章节 ---
        for ch in chapters:
            # 章节标题
            heading = doc.add_heading(f"{ch.chapter_no}  {ch.title}", level=1)

            # 预警标记
            if ch.has_warning:
                warn_p = doc.add_paragraph()
                warn_run = warn_p.add_run("⚠ 本章节存在合规预警，请重点审查")
                warn_run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                warn_run.font.bold = True

            # 章节内容
            for line in ch.content.split("\n"):
                if line.startswith("  ⚠"):
                    p = doc.add_paragraph()
                    run = p.add_run(line)
                    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                elif line.startswith("【"):
                    p = doc.add_paragraph()
                    run = p.add_run(line)
                    run.font.bold = True
                else:
                    doc.add_paragraph(line)

        # --- 保存 ---
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "storage", "outputs"
        )
        os.makedirs(output_dir, exist_ok=True)

        safe_name = project.face_name.replace("/", "_").replace(" ", "_")
        filename = f"{safe_name}_作业规程_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        file_path = os.path.join(output_dir, filename)

        doc.save(file_path)
        return file_path
