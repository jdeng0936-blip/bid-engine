"""
企业资料完整度检查 — 投标前准备度评估

检查企业信息、资质证书、图片资源的完整度，
给出百分比评分和缺失项清单。
"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import Enterprise
from app.models.credential import Credential
from app.models.image_asset import ImageAsset


# 必填字段权重
_REQUIRED_FIELDS = {
    "name": ("企业名称", 10),
    "credit_code": ("统一社会信用代码", 10),
    "legal_representative": ("法定代表人", 8),
    "food_license_no": ("食品经营许可证号", 10),
    "address": ("公司地址", 5),
    "contact_person": ("联系人", 5),
    "contact_phone": ("联系电话", 5),
    "description": ("企业简介", 8),
    "competitive_advantages": ("核心竞争优势", 8),
}

# 推荐资质类型
_RECOMMENDED_CREDS = {
    "business_license": ("营业执照", 10),
    "food_license": ("食品经营许可证", 10),
    "haccp": ("HACCP认证", 5),
    "iso22000": ("ISO22000认证", 5),
    "performance": ("业绩证明", 6),
}


class ReadinessCheckService:
    """企业资料完整度检查"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check(self, enterprise_id: int, tenant_id: int) -> dict:
        """检查企业资料完整度

        Returns:
            {
                "score": 85,  # 总分(满分100)
                "total_items": 14,
                "completed_items": 12,
                "missing": [{"field": "...", "label": "...", "weight": 10}],
                "sections": {...}
            }
        """
        result = await self.session.execute(
            select(Enterprise).where(
                Enterprise.id == enterprise_id,
                Enterprise.tenant_id == tenant_id,
            )
        )
        enterprise = result.scalar_one_or_none()
        if not enterprise:
            raise ValueError("企业不存在")

        # 加载资质
        cred_result = await self.session.execute(
            select(Credential).where(
                Credential.enterprise_id == enterprise_id,
                Credential.tenant_id == tenant_id,
            )
        )
        credentials = list(cred_result.scalars().all())
        cred_types = {c.cred_type for c in credentials}

        # 加载图片数量
        img_count_result = await self.session.execute(
            select(func.count(ImageAsset.id)).where(
                ImageAsset.enterprise_id == enterprise_id,
                ImageAsset.tenant_id == tenant_id,
            )
        )
        img_count = img_count_result.scalar() or 0

        # 检查企业基本信息
        missing = []
        field_score = 0
        field_max = 0
        for field, (label, weight) in _REQUIRED_FIELDS.items():
            field_max += weight
            value = getattr(enterprise, field, None)
            if value and str(value).strip():
                field_score += weight
            else:
                missing.append({"field": field, "label": label, "weight": weight})

        # 检查资质
        cred_score = 0
        cred_max = 0
        for cred_type, (label, weight) in _RECOMMENDED_CREDS.items():
            cred_max += weight
            if cred_type in cred_types:
                cred_score += weight
            else:
                missing.append({"field": f"cred:{cred_type}", "label": label, "weight": weight})

        # 图片加分
        img_max = 5
        img_score = min(img_count, 5)  # 最多5分

        total_max = field_max + cred_max + img_max
        total_score = field_score + cred_score + img_score
        pct = round(total_score / total_max * 100) if total_max > 0 else 0

        return {
            "score": pct,
            "total_items": len(_REQUIRED_FIELDS) + len(_RECOMMENDED_CREDS) + 1,
            "completed_items": len(_REQUIRED_FIELDS) + len(_RECOMMENDED_CREDS) + 1 - len(missing),
            "missing": missing,
            "sections": {
                "basic_info": {"score": field_score, "max": field_max},
                "credentials": {"score": cred_score, "max": cred_max},
                "images": {"score": img_score, "max": img_max, "count": img_count},
            },
        }
