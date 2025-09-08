from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
from api.services.viz import generate_counts_graph
from api.services.storage import EventStore
from api.deps import get_store
from api.services.metrics import count_event_types

router = APIRouter(prefix="/viz", tags=["viz"])

@router.get("/counts.png", summary="Bar chart: counts by event type in window")
def viz_count_events(offset: int = Query(60, ge=5, le=24 * 60, description="Look-back window in minutes"),
                     store: EventStore = Depends(get_store)):
    """
    Simple bar chart PNG: counts by event type in the recent window.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=offset)
    dict_counts = count_event_types(since=since, store=store)

    buf = generate_counts_graph(dict_counts=dict_counts, offset=offset)

    return StreamingResponse(buf, media_type="image/png")