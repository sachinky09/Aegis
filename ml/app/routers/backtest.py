from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from backtesting.walk_forward import walk_forward, probability_of_backtest_overfitting

router = APIRouter()


class BacktestRequest(BaseModel):
    symbol: str = "DEMO"
    n_samples: int = Field(200, ge=50, le=5000)
    n_features: int = Field(8, ge=2, le=50)
    n_splits: int = Field(5, ge=2, le=10)
    embargo: int = Field(5, ge=0, le=30)
    transaction_cost_bps: float = 5.0


@router.post("/run")
def run_backtest(req: BacktestRequest) -> dict[str, Any]:
    rng = np.random.default_rng(abs(hash(req.symbol)) % (2**32))
    X = rng.normal(size=(req.n_samples, req.n_features))
    # Label with some signal + noise
    latent = X[:, 0] * 0.4 + X[:, 1] * 0.2 + rng.normal(scale=0.8, size=req.n_samples)
    y = (latent > 0).astype(int)
    returns = rng.normal(0.0003, 0.012, req.n_samples)

    result = walk_forward(X, y, returns, n_splits=req.n_splits, embargo=req.embargo)

    # Simulate multiple trials for PBO
    is_sharpes = [r["sharpe"] + rng.normal(0, 0.2) for r in result.get("folds", [])]
    oos_sharpes = [r["sharpe"] for r in result.get("folds", [])]
    pbo = probability_of_backtest_overfitting(is_sharpes, oos_sharpes)

    result["symbol"] = req.symbol
    result["transaction_cost_bps"] = req.transaction_cost_bps
    result["pbo"] = pbo
    result["note"] = "Synthetic walk-forward with purge+embargo; replace with real data via historical_ingest_dag"
    return result
