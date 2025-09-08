from fastapi import Request
from fastapi.exceptions import HTTPException

from api.services.storage import EventStore


def get_store(request: Request) -> EventStore:
    store = getattr(request.app.state, "store", None)
    if store is None:
        raise HTTPException(status_code=500,
                            detail="EventStore not configured.")
    return store
