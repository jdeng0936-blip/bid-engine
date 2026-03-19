"""
系统管理 API 测试 — 用户/角色/矿井/日志/字典 五个子模块

利用 conftest.py 的 async_client + auth_headers fixture。
"""
import pytest
import time


# ==================== 矿井管理 ====================

@pytest.mark.asyncio
async def test_create_mine(async_client, auth_headers):
    """创建矿井 → 201"""
    ts = int(time.time() * 1000)
    resp = await async_client.post("/api/v1/system/mines", json={
        "name": f"测试矿井-系统测试_{ts}",
        "design_capacity": 2.4,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "测试矿井" in data["name"]
    assert data["id"] > 0
    test_create_mine._mine_id = data["id"]


@pytest.mark.asyncio
async def test_list_mines(async_client, auth_headers):
    """矿井列表 → 200 + 分页结构"""
    resp = await async_client.get("/api/v1/system/mines", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_update_mine(async_client, auth_headers):
    """更新矿井 → 200"""
    mine_id = getattr(test_create_mine, "_mine_id", None)
    if not mine_id:
        pytest.skip("前置创建测试未执行")
    resp = await async_client.put(
        f"/api/v1/system/mines/{mine_id}",
        json={"name": "测试矿井-已更新"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "测试矿井-已更新"


# ==================== 角色管理 ====================

@pytest.mark.asyncio
async def test_create_role(async_client, auth_headers):
    """创建角色 → 201"""
    ts = int(time.time() * 1000)
    resp = await async_client.post("/api/v1/system/roles", json={
        "name": f"测试审核人_{ts}",
        "description": "pytest 创建的测试角色",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "测试审核人" in data["name"]
    test_create_role._role_id = data["id"]


@pytest.mark.asyncio
async def test_list_roles(async_client, auth_headers):
    """角色列表 → 200"""
    resp = await async_client.get("/api/v1/system/roles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1


# ==================== 用户管理 ====================

@pytest.mark.asyncio
async def test_create_user(async_client, auth_headers):
    """创建用户 → 201"""
    role_id = getattr(test_create_role, "_role_id", None)
    if not role_id:
        pytest.skip("前置角色创建未执行")
    ts = int(time.time() * 1000)
    resp = await async_client.post("/api/v1/system/users", json={
        "username": f"pytest_user_{ts}",
        "password": "Test@123456",
        "real_name": "测试用户",
        "role_id": role_id,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "pytest_user" in data["username"]
    test_create_user._user_id = data["id"]


@pytest.mark.asyncio
async def test_list_users(async_client, auth_headers):
    """用户列表 → 200 + 分页结构"""
    resp = await async_client.get("/api/v1/system/users", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data


# ==================== 数据字典 ====================

@pytest.mark.asyncio
async def test_create_dict_item(async_client, auth_headers):
    """创建字典项 → 201"""
    resp = await async_client.post("/api/v1/system/dicts", json={
        "dict_type": "gas_level",
        "dict_key": "low",
        "dict_value": "低瓦斯",
        "sort_order": 1,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["dict_type"] == "gas_level"
    test_create_dict_item._dict_id = data["id"]


@pytest.mark.asyncio
async def test_list_dicts(async_client, auth_headers):
    """字典列表 → 200"""
    resp = await async_client.get(
        "/api/v1/system/dicts", params={"dict_type": "gas_level"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_dict_types(async_client, auth_headers):
    """字典类型列表 → 200"""
    resp = await async_client.get("/api/v1/system/dicts/types", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


# ==================== 操作日志 ====================

@pytest.mark.asyncio
async def test_list_logs(async_client, auth_headers):
    """操作日志 → 200 + 分页"""
    resp = await async_client.get("/api/v1/system/logs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data
