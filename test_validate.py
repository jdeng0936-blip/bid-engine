import asyncio
from app.schemas.tender_notice import TenderNoticeListOut
from pydantic import ValidationError

try:
    data = {
        "id": 1,
        "title": "test",
        "status": "analyzed",
        "match_score": 80.5,
        "created_at": None,
        # missing recommendation?
    }
    TenderNoticeListOut.model_validate(data)
    print("Success dict")
except Exception as e:
    print("Dict Exception:", e)

