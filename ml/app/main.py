"""Aegis ML / Quant service — FastAPI entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import features, models, backtest, news, options, portfolio, health, market


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print("scheduler start failed:", e)
    yield


app = FastAPI(
    title="Aegis ML Service",
    description="Live market data, 4-layer diagnosis, ML models, time-based automation",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(features.router, prefix="/features", tags=["features"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(options.router, prefix="/options", tags=["options"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "aegis-ml",
        "status": "ok",
        "docs": "/docs",
        "live_data": "NSE → Yahoo → synthetic",
        "automation": "/automation/status",
    }


@app.get("/automation/status")
def automation_status():
    from app.scheduler import scheduler_status
    return scheduler_status()
