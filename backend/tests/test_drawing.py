"""
图纸管理 API 测试 — 图纸 CRUD / 分类统计

利用 conftest.py 的 async_client + auth_headers fixture。
注意：上传接口使用 multipart/form-data，单独测试。
"""
import pytest


BASE = "/api/v1/drawings"


@pytest.mark.asyncio
async def test_list_drawings_empty(async_client, auth_headers):
    """图纸列表（可能为空）→ 200 + 分页结构"""
    resp = await async_client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_category_counts(async_client, auth_headers):
    """分类统计 → 200"""
    resp = await async_client.get(f"{BASE}/categories", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_upload_drawing(async_client, auth_headers):
    """上传图纸（multipart）→ 201"""
    # 构造一个假的 DWG/PNG 文件
    fake_file = b"%PDF-1.4 fake drawing content"
    resp = await async_client.post(
        f"{BASE}/upload",
        files={"file": ("testdrawing.pdf", fake_file, "application/pdf")},
        data={
            "name": "测试断面图",
            "category": "section",
            "description": "pytest 上传测试",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "测试断面图"
    assert data["category"] == "section"
    test_upload_drawing._drawing_id = data["id"]


@pytest.mark.asyncio
async def test_get_drawing_detail(async_client, auth_headers):
    """图纸详情 → 200"""
    drawing_id = getattr(test_upload_drawing, "_drawing_id", None)
    if not drawing_id:
        pytest.skip("前置上传测试未执行")
    resp = await async_client.get(f"{BASE}/{drawing_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "测试断面图"


@pytest.mark.asyncio
async def test_update_drawing(async_client, auth_headers):
    """更新图纸元信息 → 200"""
    drawing_id = getattr(test_upload_drawing, "_drawing_id", None)
    if not drawing_id:
        pytest.skip("前置上传测试未执行")
    resp = await async_client.put(f"{BASE}/{drawing_id}", json={
        "name": "测试断面图（已更新）",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "测试断面图（已更新）"


@pytest.mark.asyncio
async def test_get_nonexistent_drawing(async_client, auth_headers):
    """不存在的图纸 → 404"""
    resp = await async_client.get(f"{BASE}/999999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_match_drawings(async_client, auth_headers):
    """匹配推荐 → 200"""
    resp = await async_client.post(f"{BASE}/match", json={
        "rock_class": "IV",
        "section_form": "矩形",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_drawing(async_client, auth_headers):
    """删除图纸 → 200"""
    drawing_id = getattr(test_upload_drawing, "_drawing_id", None)
    if not drawing_id:
        pytest.skip("前置上传测试未执行")
    resp = await async_client.delete(f"{BASE}/{drawing_id}", headers=auth_headers)
    assert resp.status_code == 200
