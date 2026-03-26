"""
设备材料智能配置引擎

功能说明：
  1. match_equipment() — 根据巷道类型、掘进方式、断面参数匹配推荐设备
  2. match_materials() — 根据支护方式、围岩条件匹配支护材料
  3. generate_bom() — 结合循环进尺/月进尺生成分级工程量清单
  4. run_full_match() — 完整匹配流程（设备+材料+BOM），保存到数据库

所有匹配均强制注入 tenant_id 过滤条件，严禁全域检索（安全红线）。
"""
import math
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import (
    EquipmentCatalog,
    MaterialCatalog,
    ProjectEquipmentList,
    ProjectMaterialBom,
)
from app.models.project import Project, ProjectParams
from app.schemas.equipment import (
    ProjectEquipmentItem,
    ProjectMaterialBomItem,
    EquipmentMatchResult,
)


class EquipmentMaterialEngine:
    """设备材料智能配置引擎"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_full_match(
        self, project_id: int, tenant_id: int
    ) -> EquipmentMatchResult:
        """
        完整匹配流程：
          1. 加载项目参数
          2. 匹配推荐设备
          3. 匹配推荐材料 + 生成 BOM
          4. 保存到数据库
          5. 返回匹配结果
        """
        # 加载项目参数
        params = await self._load_project_params(project_id, tenant_id)
        if not params:
            raise ValueError("项目不存在或参数未填写")

        params_dict = self._params_to_dict(params)

        # 清除旧的匹配结果
        await self._clear_old_results(project_id)

        # 匹配设备
        equipment_list = await self._match_equipment(
            project_id, tenant_id, params_dict
        )

        # 匹配材料 + 生成 BOM
        material_bom = await self._match_materials_and_generate_bom(
            project_id, tenant_id, params_dict
        )

        # 保存到数据库
        await self._save_results(
            project_id, tenant_id, equipment_list, material_bom
        )

        return EquipmentMatchResult(
            project_id=project_id,
            equipment_list=equipment_list,
            material_bom=material_bom,
            total_equipment_count=len(equipment_list),
            total_material_types=len(material_bom),
        )

    async def _load_project_params(
        self, project_id: int, tenant_id: int
    ) -> Optional[ProjectParams]:
        """加载项目参数（强制 tenant_id 隔离）"""
        result = await self.session.execute(
            select(ProjectParams)
            .join(Project, Project.id == ProjectParams.project_id)
            .where(
                and_(
                    ProjectParams.project_id == project_id,
                    Project.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _params_to_dict(params: ProjectParams) -> dict:
        """参数模型转字典"""
        return {
            c.key: getattr(params, c.key)
            for c in params.__table__.columns
            if c.key not in ("id", "project_id")
        }

    async def _clear_old_results(self, project_id: int) -> None:
        """清除项目已有的设备材料匹配结果"""
        from sqlalchemy import delete

        await self.session.execute(
            delete(ProjectEquipmentList).where(
                ProjectEquipmentList.project_id == project_id
            )
        )
        await self.session.execute(
            delete(ProjectMaterialBom).where(
                ProjectMaterialBom.project_id == project_id
            )
        )

    async def _match_equipment(
        self, project_id: int, tenant_id: int, params: dict
    ) -> list[ProjectEquipmentItem]:
        """
        根据项目参数匹配推荐设备

        匹配逻辑：
          1. 根据掘进方式筛选适用设备（如综掘→掘进机、转载机、锚杆机等）
          2. 根据断面面积过滤设备规格范围
          3. 按设备类别分组确保每类至少推荐一台
          4. 补充通用设备（通风/排水/电气/安全设备）
        """
        dig_method = params.get("dig_method", "综掘")
        excavation_type = params.get("excavation_type", "煤巷")
        section_width = float(params.get("section_width", 4.5) or 4.5)
        section_height = float(params.get("section_height", 3.2) or 3.2)
        section_area = section_width * section_height

        # 查询目录中适配的设备
        query = select(EquipmentCatalog).where(
            and_(
                EquipmentCatalog.tenant_id == tenant_id,
                EquipmentCatalog.is_active == 1,
            )
        )
        result = await self.session.execute(query)
        all_equipment = result.scalars().all()

        matched = []
        for eq in all_equipment:
            # 掘进方式匹配
            if eq.match_dig_methods:
                methods = [m.strip() for m in eq.match_dig_methods.split(",")]
                if dig_method and dig_method not in methods:
                    continue

            # 掘进类型匹配
            if eq.match_excavation_types:
                types = [t.strip() for t in eq.match_excavation_types.split(",")]
                if excavation_type and excavation_type not in types:
                    continue

            # 断面面积范围匹配
            if eq.match_min_section_area and section_area < eq.match_min_section_area:
                continue
            if eq.match_max_section_area and section_area > eq.match_max_section_area:
                continue

            # 通过所有过滤条件 → 推荐
            matched.append(eq)

        # 如果目录中没有匹配数据，使用默认推荐方案
        if not matched:
            matched = self._generate_default_equipment(dig_method, params)
            return matched

        # 转换为 Schema
        items = []
        for eq in matched:
            items.append(ProjectEquipmentItem(
                id=0,  # 数据库保存后会更新
                project_id=project_id,
                name=eq.name,
                category=eq.category,
                model_spec=eq.model_spec,
                quantity=1,
                power_kw=eq.power_kw,
                tech_params_summary=eq.applicable_conditions,
                match_source="auto",
            ))

        return items

    @staticmethod
    def _generate_default_equipment(
        dig_method: str, params: dict
    ) -> list[ProjectEquipmentItem]:
        """
        默认设备推荐方案（当设备目录为空时的降级策略）

        基于掘进方式生成标准设备清单，确保规程中不会出现空白设备章节。
        """
        project_id = 0  # 占位符，保存时会更新

        if dig_method == "综掘":
            items = [
                ("掘进设备", "掘进机", "EBZ200型", 200),
                ("掘进设备", "锚杆钻机", "MQT-130/3.2型", 7.5),
                ("运输设备", "刮板输送机", "SGZ630/220型", 220),
                ("运输设备", "皮带输送机", "DSJ-800型", 110),
                ("运输设备", "转载机", "SZZ730/200型", 200),
                ("通风设备", "局部通风机", "FBD№6.0/2×15型", 30),
                ("支护设备", "锚索张拉机具", "MQ18-200/60型", 18),
                ("排水设备", "水泵", "BQS25-15-3型", 3),
                ("电气设备", "矿用隔爆型真空馈电开关", "KBZ-400型", None),
                ("电气设备", "矿用隔爆型真空电磁起动器", "QJZ-200型", None),
                ("安全设备", "甲烷传感器", "GJC4型", None),
                ("安全设备", "一氧化碳传感器", "GTH1000型", None),
                ("安全设备", "风速传感器", "GFY15型", None),
            ]
        elif dig_method == "炮掘":
            items = [
                ("掘进设备", "凿岩机", "YT-28型", 4),
                ("掘进设备", "装岩机", "Z-17型", 11),
                ("运输设备", "矿车", "MGC1.1-6型", None),
                ("运输设备", "刮板输送机", "SGB420/30型", 30),
                ("通风设备", "局部通风机", "FBD№5.0/2×11型", 22),
                ("支护设备", "锚杆钻机", "MQT-130/3.2型", 7.5),
                ("排水设备", "水泵", "BQS15-10-2型", 2),
                ("电气设备", "矿用隔爆型真空馈电开关", "KBZ-200型", None),
                ("安全设备", "甲烷传感器", "GJC4型", None),
                ("安全设备", "一氧化碳传感器", "GTH1000型", None),
            ]
        else:
            items = [
                ("掘进设备", "凿岩机", "YT-28型", 4),
                ("通风设备", "局部通风机", "FBD№5.0/2×11型", 22),
                ("支护设备", "锚杆钻机", "MQT-130/3.2型", 7.5),
                ("排水设备", "水泵", "BQS15-10-2型", 2),
                ("安全设备", "甲烷传感器", "GJC4型", None),
            ]

        return [
            ProjectEquipmentItem(
                id=0,
                project_id=project_id,
                name=name,
                category=cat,
                model_spec=spec,
                quantity=1,
                power_kw=power,
                match_source="default",
            )
            for cat, name, spec, power in items
        ]

    async def _match_materials_and_generate_bom(
        self, project_id: int, tenant_id: int, params: dict
    ) -> list[ProjectMaterialBomItem]:
        """
        匹配支护材料并生成分级工程量清单

        计算逻辑：
          1. 根据围岩级别和支护方式匹配材料目录
          2. 根据断面、间排距计算单循环用量
          3. 结合循环进尺/月进尺推算月用量和工程总量
        """
        rock_class = params.get("rock_class", "III")
        section_width = float(params.get("section_width", 4.5) or 4.5)
        section_height = float(params.get("section_height", 3.2) or 3.2)
        excavation_length = float(params.get("excavation_length", 600) or 600)
        dig_method = params.get("dig_method", "综掘")

        # 单循环进尺（假定：综掘 0.8m/循环，炮掘 1.6m/循环）
        cycle_advance = 0.8 if dig_method == "综掘" else 1.6
        # 月进尺估算（每天 3 循环 × 25 天）
        monthly_advance = cycle_advance * 3 * 25
        # 总循环数
        total_cycles = math.ceil(excavation_length / cycle_advance)
        total_months = math.ceil(excavation_length / monthly_advance)

        # 查询材料目录
        query = select(MaterialCatalog).where(
            and_(
                MaterialCatalog.tenant_id == tenant_id,
                MaterialCatalog.is_active == 1,
            )
        )
        result = await self.session.execute(query)
        all_materials = result.scalars().all()

        matched_materials = []
        for mat in all_materials:
            # 围岩级别匹配
            if mat.match_rock_classes:
                classes = [c.strip() for c in mat.match_rock_classes.split(",")]
                if rock_class and rock_class not in classes:
                    continue
            matched_materials.append(mat)

        # 如果目录为空，使用默认推荐
        if not matched_materials:
            return self._generate_default_bom(
                project_id, params, cycle_advance, monthly_advance, total_cycles
            )

        # 生成 BOM
        bom_items = []
        for mat in matched_materials:
            # 计算单循环用量
            qty_cycle = mat.consumption_per_cycle or 0
            if qty_cycle == 0:
                # 根据材料类别和断面参数估算
                qty_cycle = self._estimate_cycle_consumption(
                    mat.category, section_width, section_height, cycle_advance
                )

            qty_month = qty_cycle * 3 * 25  # 日 3 循环 × 月 25 天
            qty_total = qty_cycle * total_cycles

            bom_items.append(ProjectMaterialBomItem(
                id=0,
                project_id=project_id,
                name=mat.name,
                category=mat.category,
                model_spec=mat.model_spec,
                unit=mat.unit,
                qty_per_cycle=round(qty_cycle, 1),
                qty_per_month=round(qty_month, 1),
                qty_total=round(qty_total, 1),
                calc_basis=(
                    f"单循环进尺{cycle_advance}m, "
                    f"月进尺{monthly_advance}m, "
                    f"总长{excavation_length}m, "
                    f"共{total_cycles}循环"
                ),
                match_source="auto",
            ))

        return bom_items

    @staticmethod
    def _estimate_cycle_consumption(
        category: str,
        width: float,
        height: float,
        advance: float,
    ) -> float:
        """
        根据材料类别和断面参数估算单循环消耗量

        基于常用煤矿掘进支护参数经验公式。
        """
        perimeter = 2 * (width + height)  # 周长（矩形简化）

        if category == "锚杆":
            # 顶板锚杆：间距 800mm，排距 = advance(m)
            # 每排顶部锚杆数 ≈ 断面宽度 / 0.8
            top_bolts = math.ceil(width / 0.8)
            # 两帮锚杆：每帮 (height - 0.3) / 0.8 根
            side_bolts = math.ceil((height - 0.3) / 0.8) * 2
            return top_bolts + side_bolts

        elif category == "锚索":
            # 每排锚索数 ≈ 2-3 根（宽度 > 5m 取 3 根）
            return 3 if width >= 5.0 else 2

        elif category == "树脂药卷":
            # 每根锚杆 2 卷，每根锚索 3 卷
            bolts = math.ceil(width / 0.8) + math.ceil((height - 0.3) / 0.8) * 2
            cables = 3 if width >= 5.0 else 2
            return bolts * 2 + cables * 3

        elif category == "金属网":
            # 顶板 + 两帮面积 / 单片面积 (1m×2m)
            area = (width + 2 * height) * advance
            return math.ceil(area / 2.0)

        elif category == "W钢带":
            # 顶板每排 1-2 条
            return 2 if width >= 5.0 else 1

        elif category == "托盘":
            # 每根锚杆/锚索各配 1 个托盘
            bolts = math.ceil(width / 0.8) + math.ceil((height - 0.3) / 0.8) * 2
            cables = 3 if width >= 5.0 else 2
            return bolts + cables

        elif category == "喷射混凝土":
            # 喷层厚度 50-100mm，单位 m³
            spray_area = (width + 2 * height) * advance
            return round(spray_area * 0.07, 2)  # 70mm 平均喷层厚度

        return 1.0  # 其他材料默认 1

    @staticmethod
    def _generate_default_bom(
        project_id: int,
        params: dict,
        cycle_advance: float,
        monthly_advance: float,
        total_cycles: int,
    ) -> list[ProjectMaterialBomItem]:
        """
        默认材料 BOM 推荐方案（当材料目录为空时的降级策略）

        基于标准支护参数生成典型材料清单。
        """
        width = float(params.get("section_width", 4.5) or 4.5)
        height = float(params.get("section_height", 3.2) or 3.2)
        length = float(params.get("excavation_length", 600) or 600)

        # 每循环用量估算
        top_bolts = math.ceil(width / 0.8)
        side_bolts = math.ceil((height - 0.3) / 0.8) * 2
        total_bolts = top_bolts + side_bolts
        cables = 3 if width >= 5.0 else 2
        resin = total_bolts * 2 + cables * 3
        mesh = math.ceil((width + 2 * height) * cycle_advance / 2.0)
        trays = total_bolts + cables

        items = [
            ("锚杆", "左旋无纵筋螺纹钢锚杆", "φ20×2000mm", "根", total_bolts),
            ("锚索", "预应力钢绞线锚索", "φ17.8×6300mm", "根", cables),
            ("树脂药卷", "CK2335型树脂药卷", "φ23×350mm", "卷", resin),
            ("金属网", "菱形金属网", "1000×2000mm", "片", mesh),
            ("W钢带", "W型钢带", "BHW280×3.75mm", "根", 2 if width >= 5.0 else 1),
            ("托盘", "高强度拱形托盘", "150×150×10mm", "个", trays),
            ("喷射混凝土", "喷射混凝土", "C20", "m³", round((width + 2 * height) * cycle_advance * 0.07, 2)),
        ]

        return [
            ProjectMaterialBomItem(
                id=0,
                project_id=project_id,
                name=name,
                category=cat,
                model_spec=spec,
                unit=unit,
                qty_per_cycle=round(qty, 1),
                qty_per_month=round(qty * 3 * 25, 1),
                qty_total=round(qty * total_cycles, 1),
                calc_basis=(
                    f"循环进尺{cycle_advance}m, "
                    f"月进尺{monthly_advance}m, "
                    f"总长{length}m, 共{total_cycles}循环"
                ),
                match_source="default",
            )
            for cat, name, spec, unit, qty in items
        ]

    async def _save_results(
        self,
        project_id: int,
        tenant_id: int,
        equipment_list: list[ProjectEquipmentItem],
        material_bom: list[ProjectMaterialBomItem],
    ) -> None:
        """保存匹配结果到数据库"""
        # 保存设备清单
        for eq in equipment_list:
            db_item = ProjectEquipmentList(
                project_id=project_id,
                name=eq.name,
                category=eq.category,
                model_spec=eq.model_spec,
                quantity=eq.quantity,
                power_kw=eq.power_kw,
                tech_params_summary=eq.tech_params_summary,
                match_source=eq.match_source,
                tenant_id=tenant_id,
                created_by=0,
            )
            self.session.add(db_item)

        # 保存材料 BOM
        for mat in material_bom:
            db_item = ProjectMaterialBom(
                project_id=project_id,
                name=mat.name,
                category=mat.category,
                model_spec=mat.model_spec,
                unit=mat.unit,
                qty_per_cycle=mat.qty_per_cycle,
                qty_per_month=mat.qty_per_month,
                qty_total=mat.qty_total,
                calc_basis=mat.calc_basis,
                match_source=mat.match_source,
                tenant_id=tenant_id,
                created_by=0,
            )
            self.session.add(db_item)

        await self.session.commit()

    async def get_equipment_list(
        self, project_id: int, tenant_id: int
    ) -> list[ProjectEquipmentItem]:
        """查询项目设备清单"""
        result = await self.session.execute(
            select(ProjectEquipmentList).where(
                and_(
                    ProjectEquipmentList.project_id == project_id,
                    ProjectEquipmentList.tenant_id == tenant_id,
                )
            )
        )
        items = result.scalars().all()
        return [ProjectEquipmentItem.model_validate(item) for item in items]

    async def get_material_bom(
        self, project_id: int, tenant_id: int
    ) -> list[ProjectMaterialBomItem]:
        """查询项目材料工程量清单"""
        result = await self.session.execute(
            select(ProjectMaterialBom).where(
                and_(
                    ProjectMaterialBom.project_id == project_id,
                    ProjectMaterialBom.tenant_id == tenant_id,
                )
            )
        )
        items = result.scalars().all()
        return [ProjectMaterialBomItem.model_validate(item) for item in items]
