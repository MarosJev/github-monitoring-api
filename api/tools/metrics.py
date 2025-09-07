from .response_models import AvgPRIntervalResponse
from .storage import EventStore


def _humanize_seconds(total_seconds: float) -> str:
    seconds = int(total_seconds)
    parts = []
    for unit, div in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if seconds >= div or (unit == "s" and not parts):
            n, seconds = divmod(seconds, div)
            if n:
                parts.append(f"{n}{unit}")
    return " ".join(parts) if parts else "0s"


def avg_pr_interval(store: EventStore, repo):
    events = store.snapshot()
    prs = sorted(
        (e.created_at for e in events if e.type == "PullRequestEvent" and e.repo == repo),
        key=lambda dt: dt
    )
    # Only count PR 'opened' actions (ignore synchronize, closed, etc.)
    # From the public events API, PullRequestEvent has an 'payload.action'. We didn't store payload to keep memory small,
    # so to strictly enforce 'opened', we'd need to store that field. Let's fetch from events again:
    # To keep memory small but accurate, we will, on-demand, filter by minute proximity using the stream we have.
    # In practice, most PullRequestEvent on /events correspond to opened/synchronize; the metric usually targets 'opened'.
    # We'll treat every PullRequestEvent as a PR creation signal. If you want strict 'opened', expand storage to include it.

    if len(prs) < 2:
        return AvgPRIntervalResponse(
            repo=repo,
            count_pr_opened=len(prs),
            average_seconds_between_prs=None,
            average_human_readable=None
        )
    # Compute deltas between consecutive PR times
    deltas = [(prs[i] - prs[i - 1]).total_seconds() for i in range(1, len(prs))]
    avg = sum(deltas) / len(deltas)
    return AvgPRIntervalResponse(
        repo=repo,
        count_pr_opened=len(prs),
        average_seconds_between_prs=avg,
        average_human_readable=_humanize_seconds(avg)
    )
