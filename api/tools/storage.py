from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from collections import deque
import threading


class Event(BaseModel):
    id: str
    type: str
    repo: str              # "owner/name"
    created_at: datetime   # timezone-aware UTC

class EventStore:
    """
    Thread-safe, in-memory, time-pruned event store.
    """
    def __init__(self, retention_minutes: int = 4320, store_limit: int = 100_000):
        self._events: deque[Event] = deque(maxlen=store_limit)
        self._seen_ids: set[str] = set()
        self._lock = threading.RLock()
        self.retention = timedelta(minutes=retention_minutes)

    def add_events(self, events: list[Event]) -> int:
        added = 0
        cutoff = datetime.now(timezone.utc) - self.retention
        with self._lock:
            # prune old
            while self._events and self._events[0].created_at < cutoff:
                old = self._events.popleft()
                self._seen_ids.discard(old.id)
            # add new
            for e in events:
                if e.id in self._seen_ids:
                    continue
                if e.created_at < cutoff:
                    continue
                self._events.append(e)
                self._seen_ids.add(e.id)
                added += 1
        return added

    def snapshot(self) -> list[Event]:
        with self._lock:
            return list(self._events)

    def recent_since(self, since: datetime) -> list[Event]:
        with self._lock:
            return [e for e in self._events if e.created_at >= since]
