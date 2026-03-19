"""
知识库 API 测试 — 工程案例 / 文档模板 / 章节片段

利用 conftest.py 的 async_client + auth_headers fixture。
"""
import pytest


BASE = "/api/v1/knowledge"


# ==================== 工程案例 ====================

@pytest.mark.asyncio
async def test_create_case(async_client, auth_headers):
    """创建案例 → 200"""
    resp = await async_client.post(f"{BASE}/cases", json={
        "title": "3301 回风巷施工案例",
        "mine_name": "某某矿",
        "rock_class": "IV",
        "excavation_type": "煤巷",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "3301 回风巷施工案例"
    test_create_case._case_id = data["id"]


@pytest.mark.asyncio
async def test_list_cases(async_client, auth_headers):
    """案例列表 → 200"""
    resp = await async_client.get(f"{BASE}/cases", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_case(async_client, auth_headers):
    """更新案例 → 200"""
    case_id = getattr(test_create_case, "_case_id", None)
    if not case_id:
        pytest.skip("前置创建未执行")
    resp = await async_client.put(f"{BASE}/cases/{case_id}", json={
        "face_name": "3301 回风巷（更新）",
    }, headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_case(async_client, auth_headers):
    """删除案例 → 200"""
    case_id = getattr(test_create_case, "_case_id", None)
    if not case_id:
        pytest.skip("前置创建未执行")
    resp = await async_client.delete(f"{BASE}/cases/{case_id}", headers=auth_headers)
    assert resp.status_code == 200


# ==================== 章节片段 ====================

@pytest.mark.asyncio
async def test_create_snippet(async_client, auth_headers):
    """创建片段 → 200"""
    resp = await async_client.post(f"{BASE}/snippets", json={
        "chapter_no": "5.2",
        "chapter_name": "锚杆支护设计",
        "content": "锚杆间距 {{ bolt_spacing }}mm，排距 {{ bolt_row_spacing }}mm。",
        "sort_order": 50,
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["chapter_no"] == "5.2"
    test_create_snippet._snp_id = data["id"]


@pytest.mark.asyncio
async def test_list_snippets(async_client, auth_headers):
    """片段列表 → 200"""
    resp = await async_client.get(f"{BASE}/snippets", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_delete_snippet(async_client, auth_headers):
    """删除片段 → 200"""
    snp_id = getattr(test_create_snippet, "_snp_id", None)
    if not snp_id:
        pytest.skip("前置创建未执行")
    resp = await async_client.delete(f"{BASE}/snippets/{snp_id}", headers=auth_headers)
    assert resp.status_code == 200
