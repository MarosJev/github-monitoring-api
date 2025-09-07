import os

GITHUB_EVENTS_URL = "https://api.github.com/events"
# How often to poll GitHub (seconds). Keep conservative for unauthenticated usage.
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
# How long to retain events in memory (minutes)
RETENTION_MINUTES = int(os.getenv("RETENTION_MINUTES", "4320"))  # default 3 days
# Only these event types are stored
ALLOWED_TYPES = {"WatchEvent", "PullRequestEvent", "IssuesEvent"}

EVENTS_PER_POLL = int(os.getenv("EVENTS_PER_POLL", "100"))