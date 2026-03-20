from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RawSourceItem(BaseModel):
    raw_item_id: str
    source_tier: str
    source_name: str
    source_url: str | None = None
    fetched_at: datetime | None = None
    published_at: datetime | None = None
    raw_text: str
    raw_payload: str | None = None
