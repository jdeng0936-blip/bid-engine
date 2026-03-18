"""
种子数据导入脚本 — 通过 HTTP API 批量导入标准库文档和规则库数据

用法:
    # 在 Docker 容器内执行
    docker exec excavation-api python scripts/seed_data.py

    # 或指定 API 地址
    API_BASE=http://localhost:8000/api/v1 python scripts/seed_data.py

特性:
    - 幂等设计：跳过已存在的同名数据
    - 自动登录获取 JWT
    - 详细日志输出
"""
import os
import sys
import json
import requests

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")
USERNAME = os.getenv("SEED_USER", "admin")
PASSWORD = os.getenv("SEED_PASS", "admin123")


def login() -> str:
    """登录获取 JWT Token"""
    r = requests.post(f"{API_BASE}/auth/login", json={
        "username": USERNAME, "password": PASSWORD,
    })
    r.raise_for_status()
    token = r.json()["data"]["access_token"]
    print(f"✅ 登录成功 (user={USERNAME})")
    return token


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# =============================================
# P3-A: 标准库数据 — 8 份文档 + 条款
# =============================================

DOCUMENTS = [
    {
        "title": "中华人民共和国煤矿安全规程（2022修订版）",
        "doc_type": "法律法规",
        "version": "2022",
        "clauses": [
            {"clause_no": "第95条", "title": "掘进工作面支护", "content": "采用锚杆（锚索）支护时，必须进行顶板离层监测。掘进工作面严禁空顶作业，靠近掘进工作面10m内的支护，在爆破前必须加固。", "level": 0},
            {"clause_no": "第96条", "title": "临时支护", "content": "掘进工作面严禁空顶作业。靠近掘进工作面10m内的支护，在爆破前必须加固。爆破崩倒、崩坏的支架必须先行修复，之后方可进入工作面作业。", "level": 0},
            {"clause_no": "第128条", "title": "掘进通风", "content": "掘进中的煤巷和半煤岩巷必须采用局部通风机通风。局部通风机必须实行专用变压器、专用开关、专用回路供电。", "level": 0},
            {"clause_no": "第135条", "title": "瓦斯检查", "content": "掘进工作面的瓦斯浓度达到1.0%时，必须停止用电钻打眼。爆破地点附近20m以内风流中瓦斯浓度达到1.0%时，严禁爆破。", "level": 0},
            {"clause_no": "第201条", "title": "防治水", "content": "矿井必须做好水害分析预报，坚持有疑必探、先探后掘的原则。采掘工作面遇到下列情况之一时，必须确定探水线进行探水。", "level": 0},
        ],
    },
    {
        "title": "煤矿防治水细则",
        "doc_type": "法律法规",
        "version": "2018",
        "clauses": [
            {"clause_no": "第3章", "title": "地面防治水", "content": "矿井应当查清矿区及其附近地面水流系统的汇水和渗漏情况，疏导或者堵截有害水源。", "level": 0},
            {"clause_no": "第5章", "title": "探放水", "content": "采掘工作面探水前，应当编制探放水设计，探放水设计应当包括探水钻孔布置图、封孔方法和安全措施等内容。", "level": 0},
            {"clause_no": "第7章", "title": "水害应急处置", "content": "矿井应当编制水害应急预案，明确各级人员的职责和水害事故的处置措施。", "level": 0},
        ],
    },
    {
        "title": "煤矿巷道锚杆支护技术规范 GB/T 35056-2018",
        "doc_type": "技术规范",
        "version": "GB/T 35056-2018",
        "clauses": [
            {"clause_no": "5.1", "title": "锚杆选型原则", "content": "锚杆的类型应根据围岩条件、巷道断面形状和尺寸、服务年限等因素综合确定。优先选用高强度锚杆，锚杆直径不宜小于20mm。", "level": 0},
            {"clause_no": "5.2", "title": "锚杆间排距设计", "content": "锚杆间排距应根据围岩分类和计算确定。I-II类围岩间距不大于1200mm，III类围岩间距不大于1000mm，IV-V类围岩间距不大于800mm。", "level": 0},
            {"clause_no": "5.3", "title": "锚索补强支护", "content": "IV类及以上围岩、大断面巷道（宽度≥5m）、交叉点等关键位置应采用锚索补强支护。锚索长度不应小于6m。", "level": 0},
            {"clause_no": "5.4", "title": "支护质量检测", "content": "锚杆安装后应进行锚固力检测，锚杆锚固力不应小于设计值的90%。每班应检测不少于30%的锚杆。", "level": 0},
        ],
    },
    {
        "title": "煤矿井巷工程质量验收规范 GB 50213-2018",
        "doc_type": "技术规范",
        "version": "GB 50213-2018",
        "clauses": [
            {"clause_no": "4.1", "title": "掘进质量标准", "content": "巷道净宽偏差不超过+150mm/-50mm，净高偏差不超过+100mm/-50mm。巷道中心线偏差不超过50mm/100m。", "level": 0},
            {"clause_no": "4.2", "title": "锚杆支护验收", "content": "锚杆外露长度为30~50mm，托盘应紧贴岩面，拧紧力矩不小于300N·m。锚杆角度偏差不超过±15°。", "level": 0},
            {"clause_no": "4.3", "title": "喷浆质量", "content": "喷层厚度偏差不超过设计厚度的-10%，强度不低于C20。喷层应密实、表面平整，不得有干斑、流淌和空鼓现象。", "level": 0},
        ],
    },
    {
        "title": "煤矿掘进工作面作业规程编制指南",
        "doc_type": "安全规程",
        "version": "2023",
        "clauses": [
            {"clause_no": "第1章", "title": "概况", "content": "作业规程应包括：工作面概况、地质情况、巷道断面及支护设计、掘进方式及装备配置、通风系统、安全技术措施等内容。", "level": 0},
            {"clause_no": "第4章", "title": "支护设计", "content": "支护设计应根据围岩分类结果，选择合理的支护形式和参数。支护参数应经过计算验证，必要时进行现场试验。", "level": 0},
            {"clause_no": "第6章", "title": "通风设计", "content": "通风设计应包括需风量计算、局扇选型、风筒布置方案。需风量应取瓦斯涌出法、人数法、炸药法三者最大值。", "level": 0},
            {"clause_no": "第8章", "title": "安全技术措施", "content": "安全技术措施应涵盖顶板管理、瓦斯防治、防治水、粉尘防治、防灭火、机电运输安全等方面。", "level": 0},
        ],
    },
    {
        "title": "煤矿通风安全质量标准化标准",
        "doc_type": "安全规程",
        "version": "2020",
        "clauses": [
            {"clause_no": "3.1", "title": "通风系统", "content": "矿井通风系统应合理、稳定、可靠。掘进工作面必须实行独立通风，风量满足需要。局部通风机安装位置距回风口不小于10m。", "level": 0},
            {"clause_no": "3.2", "title": "瓦斯管理", "content": "掘进工作面回风流中瓦斯浓度不超过1.0%，二氧化碳浓度不超过1.5%。瓦斯传感器应定期校准。", "level": 0},
            {"clause_no": "3.3", "title": "风筒管理", "content": "风筒吊挂应平直、逢环必挂，接头严密不漏风。风筒末端距工作面距离不大于5m（炮掘）或2m（综掘）。", "level": 0},
        ],
    },
    {
        "title": "华阳集团掘进工作面管理规定",
        "doc_type": "集团标准",
        "version": "2024",
        "clauses": [
            {"clause_no": "第3条", "title": "作业规程审批", "content": "作业规程由技术主管编制，矿总工程师审批。规程应在开工前15天完成编制，经会审通过后方可实施。", "level": 0},
            {"clause_no": "第5条", "title": "班前安全确认", "content": "班前安全确认包括：顶板完好状况、支护质量、通风瓦斯、机电设备、水害隐患五项内容。确认合格后方可开工。", "level": 0},
            {"clause_no": "第8条", "title": "质量验收", "content": "掘进工作面实行班检、日检、旬检制度。巷道质量不合格率不得超过5%，否则停工整改。", "level": 0},
        ],
    },
    {
        "title": "华阳集团煤巷锚杆支护技术标准",
        "doc_type": "集团标准",
        "version": "2024",
        "clauses": [
            {"clause_no": "4.1", "title": "锚杆材料", "content": "采用Φ22×2400mm左旋无纵筋螺纹钢锚杆，材质Q500，屈服强度≥500MPa。树脂锚固剂采用MSK2835型。", "level": 0},
            {"clause_no": "4.2", "title": "锚索规格", "content": "采用Φ21.6×7300mm预应力锚索(1×19结构)，破断力≥550kN。张拉预紧力不低于200kN。", "level": 0},
            {"clause_no": "4.3", "title": "施工工艺", "content": "锚杆安装工序：定位→钻孔→安装锚固剂→插入锚杆→搅拌→等待固化→安装托盘→预紧。预紧力矩不低于300N·m。", "level": 0},
        ],
    },
]


# =============================================
# P3-B: 规则库数据 — 3 组 12 条规则
# =============================================

RULE_GROUPS = [
    {
        "name": "支护规则组",
        "description": "根据围岩条件和断面参数自动匹配支护方案",
        "rules": [
            {
                "name": "IV/V类围岩锚索加强支护",
                "category": "支护",
                "priority": 10,
                "conditions": [{"field": "rock_class", "operator": "in", "value": "[\"IV\",\"V\"]"}],
                "actions": [{"target_chapter": "4.2", "params_override": {"bolt_spacing": 800, "cable_count": 5, "cable_length": 7.3}}],
            },
            {
                "name": "III类围岩标准锚杆支护",
                "category": "支护",
                "priority": 5,
                "conditions": [{"field": "rock_class", "operator": "eq", "value": "\"III\""}],
                "actions": [{"target_chapter": "4.2", "params_override": {"bolt_spacing": 1000, "cable_count": 3}}],
            },
            {
                "name": "拱形断面顶板特殊支护",
                "category": "支护",
                "priority": 8,
                "conditions": [{"field": "section_form", "operator": "eq", "value": "\"拱形\""}],
                "actions": [{"target_chapter": "4.3", "params_override": {"support_type": "拱形顶板锚网索"}}],
            },
            {
                "name": "大断面加强支护（宽≥5m）",
                "category": "支护",
                "priority": 9,
                "conditions": [{"field": "section_width", "operator": "gte", "value": "5.0"}],
                "actions": [{"target_chapter": "4.2", "params_override": {"bolt_spacing": 800, "extra_cable": True}}],
            },
            {
                "name": "煤巷锚网索联合支护",
                "category": "支护",
                "priority": 7,
                "conditions": [{"field": "excavation_type", "operator": "eq", "value": "\"煤巷\""}],
                "actions": [{"target_chapter": "4.4", "params_override": {"support_scheme": "锚网索联合支护"}}],
            },
        ],
    },
    {
        "name": "通风规则组",
        "description": "根据瓦斯等级和巷道参数自动匹配通风方案",
        "rules": [
            {
                "name": "高瓦斯/突出矿井双风机双电源",
                "category": "通风",
                "priority": 10,
                "conditions": [{"field": "gas_level", "operator": "in", "value": "[\"高瓦斯\",\"突出\"]"}],
                "actions": [{"target_chapter": "6.1", "params_override": {"fan_config": "双风机双电源", "backup_fan": True}}],
            },
            {
                "name": "低瓦斯矿井标准通风",
                "category": "通风",
                "priority": 5,
                "conditions": [{"field": "gas_level", "operator": "eq", "value": "\"低瓦斯\""}],
                "actions": [{"target_chapter": "6.1", "params_override": {"fan_config": "单风机", "backup_fan": False}}],
            },
            {
                "name": "长距离掘进加大风筒",
                "category": "通风",
                "priority": 8,
                "conditions": [{"field": "excavation_length", "operator": "gte", "value": "1000"}],
                "actions": [{"target_chapter": "6.2", "params_override": {"duct_diameter": 1000, "duct_material": "阻燃抗静电"}}],
            },
            {
                "name": "大断面风速校核",
                "category": "通风",
                "priority": 7,
                "conditions": [
                    {"field": "section_width", "operator": "gte", "value": "5.0"},
                    {"field": "section_height", "operator": "gte", "value": "4.0"},
                ],
                "actions": [{"target_chapter": "6.3", "params_override": {"min_wind_speed": 0.25, "max_wind_speed": 4.0}}],
            },
        ],
    },
    {
        "name": "安全规则组",
        "description": "根据地质和瓦斯条件自动匹配安全技术措施",
        "rules": [
            {
                "name": "突出矿井区域防突措施",
                "category": "安全",
                "priority": 10,
                "conditions": [{"field": "gas_level", "operator": "eq", "value": "\"突出\""}],
                "actions": [{"target_chapter": "8.1", "params_override": {"prevention_type": "区域防突", "measures": ["区域预抽", "区域效果检验", "工作面预测"]}}],
            },
            {
                "name": "复杂水文地质探放水",
                "category": "安全",
                "priority": 9,
                "conditions": [{"field": "hydro_type", "operator": "contains", "value": "\"复杂\""}],
                "actions": [{"target_chapter": "8.3", "params_override": {"water_control": "先探后掘", "drill_holes": 3}}],
            },
            {
                "name": "自燃煤层防灭火措施",
                "category": "安全",
                "priority": 8,
                "conditions": [{"field": "spontaneous_combustion", "operator": "in", "value": "[\"容易自燃\",\"自燃\"]"}],
                "actions": [{"target_chapter": "8.4", "params_override": {"fire_prevention": ["注氮", "喷浆封闭", "CO监测"]}}],
            },
        ],
    },
]


def seed_standards(token: str):
    """导入标准库文档和条款"""
    h = headers(token)
    print("\n📚 === 导入标准库 ===")

    # 获取已有文档列表
    existing = requests.get(f"{API_BASE}/standards", params={"page": 1, "page_size": 100}, headers=h)
    existing_titles = set()
    if existing.status_code == 200:
        data = existing.json().get("data", {})
        items = data.get("items", []) if isinstance(data, dict) else data
        existing_titles = {d["title"] for d in items}

    created_count = 0
    skipped_count = 0

    for doc in DOCUMENTS:
        if doc["title"] in existing_titles:
            print(f"  ⏭️  跳过（已存在）: {doc['title']}")
            skipped_count += 1
            continue

        # 创建文档
        payload = {
            "title": doc["title"],
            "doc_type": doc["doc_type"],
            "version": doc.get("version"),
        }
        r = requests.post(f"{API_BASE}/standards", json=payload, headers=h)
        if r.status_code in (200, 201):
            doc_id = r.json()["data"]["id"]
            print(f"  ✅ 创建文档 [{doc_id}]: {doc['title']}")

            # 创建条款
            for clause in doc.get("clauses", []):
                cr = requests.post(
                    f"{API_BASE}/standards/{doc_id}/clauses",
                    json=clause, headers=h,
                )
                if cr.status_code in (200, 201):
                    print(f"      📎 条款: {clause['clause_no']} {clause['title']}")
                else:
                    print(f"      ❌ 条款失败: {cr.status_code} {cr.text[:80]}")

            created_count += 1
        else:
            print(f"  ❌ 创建失败: {r.status_code} {r.text[:100]}")

    print(f"\n  📊 标准库: 新建 {created_count} / 跳过 {skipped_count} / 总计 {len(DOCUMENTS)}")


def seed_rules(token: str):
    """导入规则组和规则"""
    h = headers(token)
    print("\n📐 === 导入规则库 ===")

    # 获取已有规则组
    existing = requests.get(f"{API_BASE}/rules/groups", params={"page": 1, "page_size": 100}, headers=h)
    existing_names = set()
    if existing.status_code == 200:
        data = existing.json().get("data", {})
        items = data.get("items", []) if isinstance(data, dict) else data
        existing_names = {g["name"] for g in items}

    created_groups = 0
    created_rules = 0
    skipped_groups = 0

    for group in RULE_GROUPS:
        if group["name"] in existing_names:
            print(f"  ⏭️  跳过（已存在）: {group['name']}")
            skipped_groups += 1
            continue

        # 创建规则组
        gr = requests.post(f"{API_BASE}/rules/groups", json={
            "name": group["name"],
            "description": group["description"],
        }, headers=h)

        if gr.status_code not in (200, 201):
            print(f"  ❌ 规则组创建失败: {gr.status_code} {gr.text[:100]}")
            continue

        group_id = gr.json()["data"]["id"]
        print(f"  ✅ 规则组 [{group_id}]: {group['name']}")
        created_groups += 1

        # 创建规则
        for rule in group.get("rules", []):
            rr = requests.post(f"{API_BASE}/rules", json={
                "group_id": group_id,
                "name": rule["name"],
                "category": rule["category"],
                "priority": rule["priority"],
                "conditions": rule["conditions"],
                "actions": rule["actions"],
            }, headers=h)

            if rr.status_code in (200, 201):
                rule_id = rr.json()["data"]["id"]
                cond_count = len(rule["conditions"])
                act_count = len(rule["actions"])
                print(f"      📌 规则 [{rule_id}]: {rule['name']} ({cond_count}条件/{act_count}结论)")
                created_rules += 1
            else:
                print(f"      ❌ 规则失败: {rr.status_code} {rr.text[:80]}")

    print(f"\n  📊 规则库: 新建 {created_groups} 组 + {created_rules} 规则 / 跳过 {skipped_groups} 组")


def main():
    print("=" * 60)
    print("🏗️  掘进工作面规程智能生成平台 — 种子数据导入")
    print("=" * 60)
    print(f"API: {API_BASE}")

    token = login()
    seed_standards(token)
    seed_rules(token)

    print("\n" + "=" * 60)
    print("✅ 种子数据导入完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

