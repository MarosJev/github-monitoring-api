from datetime import datetime
import os
import threading
from typing import Optional

import requests

from .storage import EventStore, Event
from .config import ALLOWED_TYPES, GITHUB_EVENTS_URL, EVENTS_PER_POLL


class GitHubIngestor:
    def __init__(self, store: EventStore, poll_interval: int = 60, url: str = GITHUB_EVENTS_URL):
        self.url = url
        self.store = store
        self.poll_interval = poll_interval
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._etag: Optional[str] = None

        self._session = requests.Session()
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self._session.headers.update({"Authorization": f"Bearer {token}"})
        self._session.headers.update({"Accept": "application/vnd.github+json",
                                      "X-GitHub-Api-Version": "2022-11-28"})

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="github-ingestor", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        while not self._stop.is_set():
            try:
                headers = {}
                if self._etag:
                    headers["If-None-Match"] = self._etag
                r = self._session.get(
                    self.url,
                    headers=headers,
                    params={"per_page": EVENTS_PER_POLL},
                    timeout=20,
                )
                # Record ETag for conditional requests
                if "ETag" in r.headers:
                    self._etag = r.headers["ETag"]

                if r.status_code == 304:
                    # No changes
                    pass
                elif r.ok:
                    payload = r.json()
                    batch = []
                    for item in payload:
                        etype = item.get("type")
                        if etype not in ALLOWED_TYPES:
                            continue
                        repo = (item.get("repo") or {}).get("name") or ""
                        created_raw = item.get("created_at")
                        try:
                            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                        except Exception:
                            continue
                        ev = Event(
                            id=item.get("id"),
                            type=etype,
                            repo=repo,
                            created_at=created_at
                        )
                        batch.append(ev)
                    added = self.store.add_events(batch)
                    # Optional: print minimal heartbeat
                    # print(f"[ingestor] fetched={len(payload)} added={added} total={len(self.store.snapshot())}")
                else:
                    # print(f"[ingestor] error {r.status_code}: {r.text[:200]}")
                    pass
            except Exception:
                # swallow and continue
                pass
            finally:
                self._stop.wait(self.poll_interval)
