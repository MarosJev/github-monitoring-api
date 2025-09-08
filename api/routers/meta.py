from collections import defaultdict

from fastapi import APIRouter, Depends, FastAPI, Query
from fastapi.routing import APIRoute

from api.deps import get_store
from api.services.storage import EventStore

router = APIRouter(prefix="/meta", tags=["meta"])


def build_route_index(app: FastAPI) -> dict:
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


@router.get("/repos", summary="List repos with PullRequestEvents above a threshold")
def repos(
        store: EventStore = Depends(get_store),
        min_prs: int = Query(2, ge=2, description="Minimum number of PullRequestEvents required"),
):
    events = store.snapshot()
    counts: dict[str, int] = {}
    for e in events:
        if e.type == "PullRequestEvent" and e.repo:
            counts[e.repo] = counts.get(e.repo, 0) + 1

    l_repos = sorted([repo for repo, c in counts.items() if c >= min_prs])
    return {"min_prs": min_prs, "repos": l_repos}


@router.get("/health")
def health(store=Depends(get_store)):
    return {"status": "ok", "stored_events": len(store.snapshot())}


@router.get("/all-events")
def display_all_events(store=Depends(get_store)):
    return {"all_events": store.snapshot()}
