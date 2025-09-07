import os

GITHUB_EVENTS_URL = "https://api.github.com/events"
ALLOWED_TYPES = {"WatchEvent", "PullRequestEvent", "IssuesEvent"}

# How often to poll GitHub (seconds). For unauthenticated usage there is a limit of 60 requests per hour.
# Visit https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28 for more information about limits
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
# How long to retain events in memory (minutes)
RETENTION_MINUTES = int(os.getenv("RETENTION_MINUTES", "4320"))  # default 3 days
# Maximum 100. Visit https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28 for more information.
EVENTS_PER_POLL = int(os.getenv("EVENTS_PER_POLL", "100"))