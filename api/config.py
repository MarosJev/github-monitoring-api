import json
import os
from pathlib import Path

GITHUB_EVENTS_URL = "https://api.github.com/events"
ALLOWED_TYPES = {"WatchEvent", "PullRequestEvent", "IssuesEvent"}
LOAD_AVG_METRICS_TESTING_EVENTS = True

# How often to poll GitHub (seconds). For unauthenticated usage there is a limit of 60 requests per hour.
# Visit https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28 for more information about limits
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
# How long to retain events in memory (minutes)
RETENTION_MINUTES = int(os.getenv("RETENTION_MINUTES", "14400"))  # default 10 days
# Maximum 100. Visit https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28 for more information.
EVENTS_PER_POLL = int(os.getenv("EVENTS_PER_POLL", "100"))

if LOAD_AVG_METRICS_TESTING_EVENTS:
    project_root = Path(__file__).resolve().parent.parent
    test_file = project_root / "demo-data" / "demo_avg_prs_interval_events.json"
    with test_file.open('r') as f:
        TESTING_DATA = json.load(f)
else:
    TESTING_DATA = []
