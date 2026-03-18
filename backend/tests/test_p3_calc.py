"""
test_p3_calc.py — P3 计算增强测试

测试:
  1. 锚索受力计算 API
  2. 批量合规校验 API
  3. 规则冲突检测 API
"""
import pytest


@pytest.mark.asyncio
async def test_calc_cable(async_client, auth_headers):
    """锚索受力计算"""
    r = await async_client.post("/api/v1/calc/cable", headers=auth_headers, json={
        "rock_class": "IV",
        "section_form": "拱形",
        "section_width": 5.0,
        "section_height": 3.6,
        "cable_count": 2,       # 故意偏少，触发校核
        "pretension": 50.0,     # 故意偏低
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["loosening_height"] > 0
    assert data["min_cable_count"] >= 1
    assert data["min_pretension"] > 0
    # IV 类围岩，2 根锚索大概率不够
    assert data["is_compliant"] is False
    assert len(data["warnings"]) >= 1


@pytest.mark.asyncio
async def test_calc_cable_compliant(async_client, auth_headers):
    """锚索受力计算 — 合规场景"""
    r = await async_client.post("/api/v1/calc/cable", headers=auth_headers, json={
        "rock_class": "II",
        "section_form": "矩形",
        "section_width": 4.0,
        "section_height": 3.0,
        "cable_count": 5,       # 足够
        "pretension": 200.0,    # 足够
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["is_compliant"] is True


@pytest.mark.asyncio
async def test_batch_compliance(async_client, auth_headers):
    """批量合规校验 — 多维度"""
    r = await async_client.post("/api/v1/calc/compliance", headers=auth_headers, json={
        "rock_class": "IV",
        "gas_level": "高瓦斯",
        "section_form": "矩形",
        "section_width": 5.0,
        "section_height": 3.6,
        "excavation_length": 800,
        "bolt_spacing": 800,
        "bolt_row_spacing": 800,
        "cable_count": 3,
        "spontaneous_combustion": "容易自燃",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_checks"] >= 5  # 至少 5 项检查
    assert "items" in data
    # 应有安全类 warning（高瓦斯 + 容易自燃）
    categories = [i["category"] for i in data["items"]]
    assert "安全" in categories


@pytest.mark.asyncio
async def test_rule_conflicts(async_client, auth_headers):
    """规则冲突检测 — 基础调用"""
    r = await async_client.get("/api/v1/calc/rule-conflicts", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert "total_rules" in data
    assert "total_conflicts" in data
    assert isinstance(data["conflicts"], list)
