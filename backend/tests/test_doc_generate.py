"""
test_doc_generate.py — 文档生成端到端测试

验证链路: 创建矿井 → 创建项目 → 填写参数 → 一键生成 Word → 列出文档 → 下载
"""
import pytest


@pytest.mark.asyncio
async def test_generate_document_e2e(async_client, auth_headers):
    """端到端: 创建项目 → 填参数 → 生成 Word → 列出 → 下载"""
    # 1. 创建矿井
    r = await async_client.post("/api/v1/system/mines", headers=auth_headers,
        json={"name": "测试矿-生成", "company": "测试", "gas_level": "低瓦斯", "address": "测试地址"})
    assert r.status_code in (200, 201), f"创建矿井失败: {r.text}"
    mine_id = r.json()["data"]["id"]

    # 2. 创建项目
    r = await async_client.post("/api/v1/projects", headers=auth_headers,
        json={"face_name": "测试-生成验证工作面", "mine_id": mine_id})
    assert r.status_code in (200, 201), f"创建项目失败: {r.text}"
    project_id = r.json()["data"]["id"]

    # 3. 填写参数
    params = {
        "rock_class": "III", "coal_thickness": 3.5, "coal_dip_angle": 8,
        "gas_level": "低瓦斯", "hydro_type": "中等",
        "geo_structure": "无断层", "spontaneous_combustion": "不易自燃",
        "roadway_type": "进风巷", "excavation_type": "煤巷",
        "section_form": "矩形", "section_width": 4.5, "section_height": 3.2,
        "excavation_length": 600, "service_years": 5,
        "dig_method": "综掘", "dig_equipment": "EBZ200", "transport_method": "皮带运输",
    }
    r = await async_client.put(f"/api/v1/projects/{project_id}/params",
        headers=auth_headers, json=params)
    assert r.json()["code"] == 0, f"参数保存失败: {r.text}"

    # 4. 一键生成
    r = await async_client.post(f"/api/v1/projects/{project_id}/generate",
        headers=auth_headers)
    assert r.status_code == 200, f"生成失败: {r.text}"
    data = r.json()["data"]
    assert data["total_chapters"] >= 3, "章节数不足"
    assert data["file_path"].endswith(".docx"), "未生成 docx 文件"

    # 5. 列出文档（验证路径一致性）
    r = await async_client.get(f"/api/v1/projects/{project_id}/documents",
        headers=auth_headers)
    assert r.status_code == 200
    docs = r.json()["data"]
    assert len(docs) >= 1, "文档列表为空，路径可能不一致"

    # 6. 下载
    filename = docs[0]["filename"]
    r = await async_client.get(f"/api/v1/projects/{project_id}/documents/download",
        headers=auth_headers, params={"filename": filename})
    assert r.status_code == 200, f"下载失败: {r.status_code}"
    assert len(r.content) > 1000, "下载文件太小，可能不是有效 docx"


@pytest.mark.asyncio
async def test_generate_without_params(async_client, auth_headers):
    """无参数时生成也不应崩溃"""
    # 创建矿井
    r = await async_client.post("/api/v1/system/mines", headers=auth_headers,
        json={"name": "空参数矿", "company": "T", "gas_level": "低瓦斯", "address": "T"})
    mine_id = r.json()["data"]["id"]

    # 创建项目（不填参数）
    r = await async_client.post("/api/v1/projects", headers=auth_headers,
        json={"face_name": "空参数测试面", "mine_id": mine_id})
    project_id = r.json()["data"]["id"]

    # 生成（应成功但章节可能较少）
    r = await async_client.post(f"/api/v1/projects/{project_id}/generate",
        headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["code"] == 0
