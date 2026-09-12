from fastapi import FastAPI

from app.api.routes import router
from app.error_log import install as install_error_log

install_error_log()

app = FastAPI(
    title="Betting Aggregator API",
    version="0.1.0",
    description="Canonical NFL and NBA odds comparison API.",
)
app.include_router(router)
