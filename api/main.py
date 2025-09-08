import logging
import os
from contextlib import asynccontextmanager

import matplotlib

matplotlib.use("Agg")  # non-GUI backend for servers
import uvicorn
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse

from api.config import POLL_INTERVAL_SECONDS, RETENTION_MINUTES
from api.services.storage import EventStore
from api.services.github_ingestor import GitHubIngestor
from api.routers.meta import build_route_index
from api.routers import meta, metrics, viz

logging.getLogger("__main__")

load_dotenv(find_dotenv(), override=True)

INGESTOR = GitHubIngestor(poll_interval=POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    app.state.store = EventStore(retention_minutes=RETENTION_MINUTES)
    INGESTOR.configure(store=app.state.store)
    # Startup
    INGESTOR.start()
    # build once after routes are registered
    app.state.landing = {
        "service": "GitHub Events Monitor",
        "status": "ok",
        # relative paths so we don't need a Request to compute absolute URLs
        "docs": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": build_route_index(app),
    }

    yield
    # Shutdown
    INGESTOR.stop()


app = FastAPI(title="GitHub Events Monitor",
              description="Streams selected GitHub events and serves metrics.",
              version="1.0.0",
              lifespan=lifespan)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "favicon.ico"))


# Routers
app.include_router(meta.router)
app.include_router(metrics.router)
app.include_router(viz.router)


@app.get("/", include_in_schema=False)
def root():
    return app.state.landing


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
