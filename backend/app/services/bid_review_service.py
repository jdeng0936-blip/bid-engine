"""
投标复盘 Service
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bid_review import BidProjectReview, BidCompetitor
from app.schemas.bid_review import BidReviewCreate, BidReviewUpdate


class BidReviewService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_project(self, project_id: int, tenant_id: int) -> Optional[BidProjectReview]:
        result = await self.session.execute(
            select(BidProjectReview)
            .where(BidProjectReview.project_id == project_id, BidProjectReview.tenant_id == tenant_id)
            .options(selectinload(BidProjectReview.competitors))
        )
        return result.scalar_one_or_none()

    async def create(self, project_id: int, tenant_id: int, data: BidReviewCreate) -> BidProjectReview:
        review = BidProjectReview(
            project_id=project_id,
            tenant_id=tenant_id,
            result=data.result,
            result_reason=data.result_reason,
            our_bid_price=data.our_bid_price,
            winning_price=data.winning_price,
            official_feedback=data.official_feedback,
            personal_summary=data.personal_summary,
            lessons_learned=data.lessons_learned,
            improvement_actions=data.improvement_actions,
        )
        for comp in data.competitors:
            review.competitors.append(BidCompetitor(
                tenant_id=tenant_id,
                **comp.model_dump(),
            ))
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review, attribute_names=["competitors"])
        return review

    async def update(self, project_id: int, tenant_id: int, data: BidReviewUpdate) -> Optional[BidProjectReview]:
        review = await self.get_by_project(project_id, tenant_id)
        if not review:
            return None
        for k, v in data.model_dump(exclude_none=True, exclude={"competitors"}).items():
            setattr(review, k, v)
        # 如果提供了 competitors，替换全部
        if data.competitors is not None:
            # 删除旧的
            for old in list(review.competitors):
                await self.session.delete(old)
            await self.session.flush()
            # 添加新的
            for comp in data.competitors:
                review.competitors.append(BidCompetitor(
                    tenant_id=tenant_id,
                    **comp.model_dump(),
                ))
        await self.session.commit()
        await self.session.refresh(review, attribute_names=["competitors"])
        return review

    async def delete(self, project_id: int, tenant_id: int) -> bool:
        review = await self.get_by_project(project_id, tenant_id)
        if not review:
            return False
        await self.session.delete(review)
        await self.session.commit()
        return True
