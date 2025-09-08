from fastapi import Request

from api.services.storage import EventStore


def get_store(request: Request) -> EventStore:
    store = getattr(request.app.state, "store", None)
    if store is None:
        raise RuntimeError("EventStore not configured on app.state")
    return store
