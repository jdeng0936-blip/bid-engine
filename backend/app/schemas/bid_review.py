"""
投标复盘 Schema — Pydantic V2
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BidCompetitorCreate(BaseModel):
    competitor_name: str = Field(min_length=1, max_length=200)
    competitor_price: Optional[float] = None
    competitor_result: Optional[str] = Field(None, pattern="^(won|lost|disqualified)$")
    competitor_strengths: Optional[str] = None
    notes: Optional[str] = None


class BidCompetitorOut(BaseModel):
    id: int
    competitor_name: str
    competitor_price: Optional[float] = None
    competitor_result: Optional[str] = None
    competitor_strengths: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class BidReviewCreate(BaseModel):
    result: str = Field(pattern="^(won|lost|disqualified|abandoned)$")
    result_reason: Optional[str] = None
    our_bid_price: Optional[float] = None
    winning_price: Optional[float] = None
    official_feedback: Optional[str] = None
    personal_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    improvement_actions: Optional[str] = None
    competitors: list[BidCompetitorCreate] = Field(default_factory=list)


class BidReviewUpdate(BaseModel):
    result: Optional[str] = Field(None, pattern="^(won|lost|disqualified|abandoned)$")
    result_reason: Optional[str] = None
    our_bid_price: Optional[float] = None
    winning_price: Optional[float] = None
    official_feedback: Optional[str] = None
    personal_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    improvement_actions: Optional[str] = None
    competitors: Optional[list[BidCompetitorCreate]] = None


class BidReviewOut(BaseModel):
    id: int
    project_id: int
    result: str
    result_reason: Optional[str] = None
    our_bid_price: Optional[float] = None
    winning_price: Optional[float] = None
    official_feedback: Optional[str] = None
    personal_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    improvement_actions: Optional[str] = None
    competitors: list[BidCompetitorOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
