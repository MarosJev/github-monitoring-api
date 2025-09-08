from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Event(BaseModel):
    id: str
    type: str
    repo: str  # "owner/name"
    created_at: datetime  # timezone-aware UTC


class AvgPRIntervalResponse(BaseModel):
    repo: str
    count_pr: int
    average_seconds_between_prs: Optional[float]
    average_human_readable: Optional[str]


class CountsResponse(BaseModel):
    since_utc: datetime
    offset_minutes: int
    counts: dict[str, int]
