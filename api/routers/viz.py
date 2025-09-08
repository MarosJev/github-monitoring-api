from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse

from api.config import RETENTION_MINUTES
from api.deps import get_store
from api.services.metrics import count_event_types
from api.services.storage import EventStore
from api.services.viz import generate_counts_graph

router = APIRouter(prefix="/viz", tags=["viz"])


@router.get("/counts.png")
def viz_count_events(offset: int = Query(60, ge=5, le=RETENTION_MINUTES, description="Look-back window in minutes"),
                     store: EventStore = Depends(get_store)):
    """
    Simple bar chart PNG: counts by event type in the recent window.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=offset)
    dict_counts = count_event_types(since=since, store=store)

    buf = generate_counts_graph(dict_counts=dict_counts, offset=offset)

    return StreamingResponse(buf, media_type="image/png")
