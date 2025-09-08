from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query, Depends

from api.config import RETENTION_MINUTES
from api.deps import get_store
from api.schemas import AvgPRIntervalResponse, CountsResponse
from api.services.metrics import count_event_types, avg_pr_interval
from api.services.storage import EventStore

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/avg-pr-interval", response_model=AvgPRIntervalResponse)
def avg_pr_interval_handler(repo: str = Query(..., description='Repository in "owner/name" format'),
                            store: EventStore = Depends(get_store)):
    """
    Average time between *opened* PullRequestEvent occurrences for the given repo.
    Requires at least two PR openings observed in the retained window.
    """
    return avg_pr_interval(store=store, repo=repo)


@router.get("/counts", response_model=CountsResponse)
def counts(offset: int = Query(10, ge=1, le=RETENTION_MINUTES, description="Look-back window in minutes"),
           store: EventStore = Depends(get_store)):
    """
    Return total number of events grouped by type within the last `offset` minutes.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=offset)
    dict_counts = count_event_types(since=since, store=store)
    return CountsResponse(since_utc=since, offset_minutes=offset, counts=dict(dict_counts))
