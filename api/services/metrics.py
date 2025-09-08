from datetime import datetime
from collections import defaultdict

from api.config import ALLOWED_TYPES
from api.schemas import AvgPRIntervalResponse
from api.services.storage import EventStore


def _humanize_seconds(total_seconds: float) -> str:
    """
    :param total_seconds: number of seconds
    :return: number of days, hours, minutes and seconds
    """
    seconds = int(total_seconds)
    parts = []
    for unit, div in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if seconds >= div or (unit == "s" and not parts):
            n, seconds = divmod(seconds, div)
            if n:
                parts.append(f"{n}{unit}")
    return " ".join(parts) if parts else "0s"


def avg_pr_interval(store: EventStore, repo: str):
    """
    :param store: EventStore containing events
    :param repo: name of the GitHub repository
    :return: average interval between pull requests for provided repository
    """
    events = store.snapshot()
    prs = sorted(
        (e.created_at for e in events if e.type == "PullRequestEvent" and e.repo == repo),
        key=lambda dt: dt
    )

    if len(prs) < 2:
        return AvgPRIntervalResponse(
            repo=repo,
            count_pr=len(prs),
            average_seconds_between_prs=None,
            average_human_readable=None
        )
    # Compute deltas between consecutive PR times
    deltas = [(prs[i] - prs[i - 1]).total_seconds() for i in range(1, len(prs))]
    avg = sum(deltas) / len(deltas)
    return AvgPRIntervalResponse(
        repo=repo,
        count_pr=len(prs),
        average_seconds_between_prs=avg,
        average_human_readable=_humanize_seconds(avg)
    )


def count_event_types(since: datetime, store: EventStore, allowed_types=ALLOWED_TYPES):
    """

    :param since: datetime since which we need to count event types
    :param store: Eventstore
    :param allowed_types: allowed types to count
    :return: dictionary with event types and their counts
    """
    events = store.recent_since(since)
    dict_counts: dict[str, int] = defaultdict(int)
    for e in events:
        dict_counts[e.type] += 1
    # Ensure all allowed types appear with at least 0
    for t in allowed_types:
        dict_counts.setdefault(t, 0)
    return dict_counts
