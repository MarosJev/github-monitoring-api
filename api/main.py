import logging
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # non-GUI backend for servers
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
# import matplotlib.pyplot as plt
import uvicorn
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.routing import APIRoute

from tools import avg_pr_interval, EventStore, GitHubIngestor, AvgPRIntervalResponse, CountsResponse
from tools.config import POLL_INTERVAL_SECONDS, RETENTION_MINUTES, ALLOWED_TYPES

if logging.getLogger().hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.getLogger("__main__")

load_dotenv(find_dotenv(), override=True)

STORE = EventStore(retention_minutes=RETENTION_MINUTES)
INGESTOR = GitHubIngestor(store=STORE, poll_interval=POLL_INTERVAL_SECONDS)


def _build_route_index(app: FastAPI) -> dict:
    groups = defaultdict(list)
    for route in app.routes:
        if isinstance(route, APIRoute) and route.include_in_schema:
            item = {
                "path": route.path,
                "methods": sorted(m for m in route.methods if m in {"GET", "POST", "PUT", "PATCH", "DELETE"}),
                "name": route.name,
                "summary": route.summary or route.description or route.name,
            }
            tags = route.tags or ["untagged"]
            for t in tags:
                groups[t].append(item)
    # stable sort
    return {k: sorted(v, key=lambda x: (x["path"], x["methods"])) for k, v in sorted(groups.items())}


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    INGESTOR.start()
    # build once after routes are registered
    app.state.landing = {
        "service": "GitHub Events Monitor",
        "status": "ok",
        # relative paths so we don't need a Request to compute absolute URLs
        "docs": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": _build_route_index(app),
    }

    yield
    # Shutdown
    INGESTOR.stop()


app = FastAPI(title="GitHub Events Monitor",
              description="Streams selected GitHub events and serves metrics.",
              version="1.0.0",
              lifespan=lifespan)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "favicon.ico"))


@app.get("/", include_in_schema=False)
def root():
    return app.state.landing


@app.get("/health")
def health():
    return {"status": "ok", "stored_events": len(STORE.snapshot())}


@app.get("/all-events")
def display_all_events():
    return {"all_events": STORE.snapshot()}


@app.get("/metrics/avg-pr-interval", tags=['metric'], response_model=AvgPRIntervalResponse)
def avg_pr_interval_handler(repo: str = Query(..., description='Repository in "owner/name" format')):
    """
    Average time between *opened* PullRequestEvent occurrences for the given repo.
    Requires at least two PR openings observed in the retained window.
    """
    return avg_pr_interval(store=STORE, repo=repo)


@app.get("/metrics/counts", tags=['metric'], response_model=CountsResponse)
def counts(offset: int = Query(10, ge=1, le=24 * 60, description="Look-back window in minutes")):
    """
    Return total number of events grouped by type within the last `offset` minutes.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=offset)
    events = STORE.recent_since(since)
    dict_counts: dict[str, int] = defaultdict(int)
    for e in events:
        dict_counts[e.type] += 1
    # Ensure all allowed types appear with at least 0
    for t in ALLOWED_TYPES:
        dict_counts.setdefault(t, 0)
    return CountsResponse(since_utc=since, offset_minutes=offset, counts=dict(dict_counts))


@app.get("/viz/counts.png", tags=['Visualisation'])
def viz_count_events(offset: int = Query(60, ge=5, le=24 * 60, description="Look-back window in minutes")):
    """
    Simple bar chart PNG: counts by event type in the recent window.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=offset)
    events = STORE.recent_since(since)
    dict_counts: dict[str, int] = defaultdict(int)
    for e in events:
        dict_counts[e.type] += 1
    # Sort bars by count desc
    labels = sorted(dict_counts.keys(), key=lambda k: dict_counts[k], reverse=True)
    values = [dict_counts[k] for k in labels]

    fig = Figure(figsize=(6, 3.5), dpi=140)
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(labels, values)
    ax.set_title(f"GitHub events in last {offset} min")
    ax.set_xlabel("Event type")
    ax.set_ylabel("Count")
    fig.tight_layout()

    buf = BytesIO()
    FigureCanvasAgg(fig).print_png(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# Optional: expose what repos are currently seen (useful for discovery)
@app.get("/repos")
def repos():
    events = STORE.snapshot()
    reps = sorted({e.repo for e in events if e.repo})
    return {"repos": reps}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
