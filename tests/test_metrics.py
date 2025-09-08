from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.schemas import Event
from api.services.metrics import avg_pr_interval, count_event_types
from api.services.storage import EventStore


def make_event(event_id: str, type_: str, repo: str, when: datetime) -> Event:
    return Event(id=event_id, type=type_, repo=repo, created_at=when)


def test_avg_pr_interval_less_than_two_prs():
    store = EventStore()
    base = datetime.now(timezone.utc)
    # Single PR event; should not compute an average
    store.add_events([
        make_event("1", "PullRequestEvent", "alice/repo", base),
        make_event("2", "IssuesEvent", "alice/repo", base + timedelta(hours=1)),
    ])

    response = avg_pr_interval(store, "alice/repo")
    assert response.count_pr == 1
    assert response.average_seconds_between_prs is None
    assert response.average_human_readable is None


def test_avg_pr_interval_multiple_prs():
    store = EventStore()
    base = datetime.now(timezone.utc)
    store.add_events([
        make_event("1", "PullRequestEvent", "alice/repo", base),
        make_event("2", "PullRequestEvent", "alice/repo", base + timedelta(hours=1)),
        make_event("3", "PullRequestEvent", "alice/repo", base + timedelta(hours=5)),
    ])

    response = avg_pr_interval(store, "alice/repo")
    assert response.count_pr == 3
    assert response.average_seconds_between_prs == 9000.0
    assert response.average_human_readable == "2h 30m"


def test_count_event_types_counts_and_zero_keys():
    store = EventStore()
    base = datetime.now(timezone.utc)
    events = [
        make_event("pr1", "PullRequestEvent", "alice/repo", base + timedelta(minutes=1)),
        make_event("iss1", "IssuesEvent", "alice/repo", base + timedelta(minutes=2)),
        make_event("pr2", "PullRequestEvent", "alice/repo", base + timedelta(minutes=3)),
        # Event before the cutoff that should not be counted
        make_event("watch0", "WatchEvent", "alice/repo", base - timedelta(days=1)),
    ]
    store.add_events(events)

    counts = count_event_types(base, store)
    assert counts["PullRequestEvent"] == 2
    assert counts["IssuesEvent"] == 1
    assert counts["WatchEvent"] == 0
