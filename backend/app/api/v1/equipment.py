"""
设备材料配置 API 路由

提供设备/材料目录管理和项目设备材料匹配接口。
所有接口强制 JWT 鉴权 + tenant_id 隔离。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload
from app.schemas.common import ApiResponse
from app.schemas.equipment import (
    EquipmentCatalogItem,
    EquipmentCatalogCreate,
    MaterialCatalogItem,
    MaterialCatalogCreate,
    ProjectEquipmentItem,
    ProjectMaterialBomItem,
    EquipmentMatchResult,
)
from app.models.equipment import EquipmentCatalog, MaterialCatalog
from app.services.equipment_material_engine import EquipmentMaterialEngine


router = APIRouter(prefix="/equipment", tags=["设备材料配置"])


# ===================== 设备匹配 =====================

@router.post(
    "/projects/{project_id}/match",
    response_model=ApiResponse[EquipmentMatchResult],
)
async def match_equipment_for_project(
    project_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """
    触发项目设备材料匹配

    根据项目参数（掘进方式、断面、围岩等）自动匹配推荐设备和材料，
    并生成按循环/月/总量分级的工程量清单。
    """
    tenant_id = int(payload.get("tenant_id", 0))
    engine = EquipmentMaterialEngine(session)
    try:
        result = await engine.run_full_match(project_id, tenant_id)
        return ApiResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/projects/{project_id}/equipment-list",
    response_model=ApiResponse[list[ProjectEquipmentItem]],
)
async def get_project_equipment_list(
    project_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取项目推荐设备清单"""
    tenant_id = int(payload.get("tenant_id", 0))
    engine = EquipmentMaterialEngine(session)
    items = await engine.get_equipment_list(project_id, tenant_id)
    return ApiResponse(data=items)


@router.get(
    "/projects/{project_id}/material-bom",
    response_model=ApiResponse[list[ProjectMaterialBomItem]],
)
async def get_project_material_bom(
    project_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取项目材料工程量清单（按循环/月/总量分级）"""
    tenant_id = int(payload.get("tenant_id", 0))
    engine = EquipmentMaterialEngine(session)
    items = await engine.get_material_bom(project_id, tenant_id)
    return ApiResponse(data=items)


# ===================== 设备目录管理 =====================

@router.get("/catalog/equipment", response_model=ApiResponse[list[EquipmentCatalogItem]])
async def list_equipment_catalog(
    category: Optional[str] = Query(None, description="按设备类别筛选"),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取设备目录列表"""
    tenant_id = int(payload.get("tenant_id", 0))
    query = select(EquipmentCatalog).where(
        and_(
            EquipmentCatalog.tenant_id == tenant_id,
            EquipmentCatalog.is_active == 1,
        )
    )
    if category:
        query = query.where(EquipmentCatalog.category == category)
    query = query.order_by(EquipmentCatalog.category, EquipmentCatalog.name)

    result = await session.execute(query)
    items = result.scalars().all()
    return ApiResponse(data=[EquipmentCatalogItem.model_validate(i) for i in items])


@router.post("/catalog/equipment", response_model=ApiResponse[EquipmentCatalogItem])
async def create_equipment_catalog(
    body: EquipmentCatalogCreate,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """新增设备目录条目"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))
    db_item = EquipmentCatalog(
        **body.model_dump(),
        tenant_id=tenant_id,
        created_by=user_id,
    )
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return ApiResponse(data=EquipmentCatalogItem.model_validate(db_item))


# ===================== 材料目录管理 =====================

@router.get("/catalog/materials", response_model=ApiResponse[list[MaterialCatalogItem]])
async def list_material_catalog(
    category: Optional[str] = Query(None, description="按材料类别筛选"),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取材料目录列表"""
    tenant_id = int(payload.get("tenant_id", 0))
    query = select(MaterialCatalog).where(
        and_(
            MaterialCatalog.tenant_id == tenant_id,
            MaterialCatalog.is_active == 1,
        )
    )
    if category:
        query = query.where(MaterialCatalog.category == category)
    query = query.order_by(MaterialCatalog.category, MaterialCatalog.name)

    result = await session.execute(query)
    items = result.scalars().all()
    return ApiResponse(data=[MaterialCatalogItem.model_validate(i) for i in items])


@router.post("/catalog/materials", response_model=ApiResponse[MaterialCatalogItem])
async def create_material_catalog(
    body: MaterialCatalogCreate,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """新增材料目录条目"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))
    db_item = MaterialCatalog(
        **body.model_dump(),
        tenant_id=tenant_id,
        created_by=user_id,
    )
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return ApiResponse(data=MaterialCatalogItem.model_validate(db_item))


# ===================== 批量导入（客户提供基础数据） =====================

@router.post("/catalog/equipment/import", response_model=ApiResponse)
async def import_equipment_catalog(
    file: "UploadFile",
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """
    批量导入设备目录（Excel/CSV）

    文件格式要求（表头列名）：
      设备名称(必填) | 设备类别(必填) | 型号规格 | 生产厂家 | 额定功率(kW) |
      设备重量(t) | 适用条件 | 适用掘进方式 | 适用掘进类型 |
      适用最小断面(m²) | 适用最大断面(m²)
    """
    import io

    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    # 读取文件内容
    content = await file.read()
    filename = file.filename or ""

    # 解析为 DataFrame
    rows = _parse_upload_file(content, filename)
    if not rows:
        raise HTTPException(400, "文件解析失败或内容为空，请检查文件格式")

    # 列名映射（中文→字段名）
    COL_MAP = {
        "设备名称": "name", "名称": "name",
        "设备类别": "category", "类别": "category",
        "型号规格": "model_spec", "型号": "model_spec",
        "生产厂家": "manufacturer", "厂家": "manufacturer",
        "额定功率": "power_kw", "功率": "power_kw", "额定功率(kW)": "power_kw",
        "设备重量": "weight_t", "重量": "weight_t", "设备重量(t)": "weight_t",
        "适用条件": "applicable_conditions",
        "适用掘进方式": "match_dig_methods",
        "适用掘进类型": "match_excavation_types",
        "适用最小断面": "match_min_section_area", "适用最小断面(m²)": "match_min_section_area",
        "适用最大断面": "match_max_section_area", "适用最大断面(m²)": "match_max_section_area",
    }

    success, failed, errors = 0, 0, []
    for i, row in enumerate(rows, 1):
        mapped = _map_row(row, COL_MAP)
        if not mapped.get("name") or not mapped.get("category"):
            failed += 1
            errors.append(f"第{i}行: 缺少必填字段(设备名称/设备类别)")
            continue

        try:
            db_item = EquipmentCatalog(
                name=str(mapped["name"]),
                category=str(mapped["category"]),
                model_spec=str(mapped.get("model_spec", "")) or None,
                manufacturer=str(mapped.get("manufacturer", "")) or None,
                power_kw=_safe_float(mapped.get("power_kw")),
                weight_t=_safe_float(mapped.get("weight_t")),
                applicable_conditions=str(mapped.get("applicable_conditions", "")) or None,
                match_dig_methods=str(mapped.get("match_dig_methods", "")) or None,
                match_excavation_types=str(mapped.get("match_excavation_types", "")) or None,
                match_min_section_area=_safe_float(mapped.get("match_min_section_area")),
                match_max_section_area=_safe_float(mapped.get("match_max_section_area")),
                tenant_id=tenant_id,
                created_by=user_id,
            )
            session.add(db_item)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"第{i}行: {str(e)}")

    await session.commit()
    return ApiResponse(data={
        "success": success, "failed": failed,
        "errors": errors[:20],  # 最多返回前 20 条错误
    })


@router.post("/catalog/materials/import", response_model=ApiResponse)
async def import_material_catalog(
    file: "UploadFile",
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """
    批量导入材料目录（Excel/CSV）

    文件格式要求（表头列名）：
      材料名称(必填) | 材料类别(必填) | 规格型号 | 计量单位 |
      单循环消耗量 | 适用支护方式 | 适用围岩级别
    """
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    content = await file.read()
    filename = file.filename or ""

    rows = _parse_upload_file(content, filename)
    if not rows:
        raise HTTPException(400, "文件解析失败或内容为空")

    COL_MAP = {
        "材料名称": "name", "名称": "name",
        "材料类别": "category", "类别": "category",
        "规格型号": "model_spec", "型号": "model_spec",
        "计量单位": "unit", "单位": "unit",
        "单循环消耗量": "consumption_per_cycle", "单循环用量": "consumption_per_cycle",
        "适用支护方式": "match_support_types",
        "适用围岩级别": "match_rock_classes",
    }

    success, failed, errors = 0, 0, []
    for i, row in enumerate(rows, 1):
        mapped = _map_row(row, COL_MAP)
        if not mapped.get("name") or not mapped.get("category"):
            failed += 1
            errors.append(f"第{i}行: 缺少必填字段(材料名称/材料类别)")
            continue

        try:
            db_item = MaterialCatalog(
                name=str(mapped["name"]),
                category=str(mapped["category"]),
                model_spec=str(mapped.get("model_spec", "")) or None,
                unit=str(mapped.get("unit", "根")) or "根",
                consumption_per_cycle=_safe_float(mapped.get("consumption_per_cycle")),
                match_support_types=str(mapped.get("match_support_types", "")) or None,
                match_rock_classes=str(mapped.get("match_rock_classes", "")) or None,
                tenant_id=tenant_id,
                created_by=user_id,
            )
            session.add(db_item)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"第{i}行: {str(e)}")

    await session.commit()
    return ApiResponse(data={
        "success": success, "failed": failed,
        "errors": errors[:20],
    })


# ===================== 导入辅助函数 =====================

def _parse_upload_file(content: bytes, filename: str) -> list[dict]:
    """解析上传的 Excel 或 CSV 文件为字典列表"""
    import io

    if filename.lower().endswith((".xlsx", ".xls")):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            headers = [str(h).strip() if h else "" for h in next(rows_iter, [])]
            if not headers:
                return []
            result = []
            for row in rows_iter:
                row_dict = {}
                for j, val in enumerate(row):
                    if j < len(headers) and headers[j]:
                        row_dict[headers[j]] = val
                if any(v for v in row_dict.values()):  # 跳过全空行
                    result.append(row_dict)
            return result
        except ImportError:
            # openpyxl 未安装时降级为 CSV 解析
            pass
        except Exception:
            return []

    # CSV 解析
    import csv
    try:
        text = content.decode("utf-8-sig")  # 兼容 BOM
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader if any(row.values())]
    except Exception:
        try:
            text = content.decode("gbk")  # 兼容 GBK 编码
            reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in reader if any(row.values())]
        except Exception:
            return []


def _map_row(row: dict, col_map: dict) -> dict:
    """将原始行数据按列名映射转换为标准字段名"""
    mapped = {}
    for col_name, val in row.items():
        clean_name = str(col_name).strip()
        field_name = col_map.get(clean_name)
        if field_name and val is not None:
            mapped[field_name] = val
    return mapped


def _safe_float(val) -> float | None:
    """安全转换为 float，无效值返回 None"""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None  # NaN 检查
    except (ValueError, TypeError):
        return None



