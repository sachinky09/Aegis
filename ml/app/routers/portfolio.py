from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class OptimizeRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=2)
    expected_returns: list[float]
    cov_matrix: list[list[float]] | None = None
    risk_free: float = 0.07
    objective: str = "max_sharpe"  # max_sharpe | min_vol | risk_parity


def _max_sharpe(mu: np.ndarray, cov: np.ndarray, rf: float) -> np.ndarray:
    n = len(mu)
    inv = np.linalg.pinv(cov)
    excess = mu - rf
    w = inv @ excess
    w = np.maximum(w, 0)
    s = w.sum()
    return w / s if s > 0 else np.ones(n) / n


def _min_vol(cov: np.ndarray) -> np.ndarray:
    n = cov.shape[0]
    inv = np.linalg.pinv(cov)
    ones = np.ones(n)
    w = inv @ ones
    w = np.maximum(w, 0)
    s = w.sum()
    return w / s if s > 0 else ones / n


@router.post("/optimize")
def optimize(req: OptimizeRequest) -> dict[str, Any]:
    n = len(req.symbols)
    if len(req.expected_returns) != n:
        return {"error": "expected_returns length must match symbols"}

    mu = np.array(req.expected_returns, dtype=float)
    if req.cov_matrix is not None:
        cov = np.array(req.cov_matrix, dtype=float)
        if cov.shape != (n, n):
            return {"error": "cov_matrix shape mismatch"}
    else:
        # synthetic diagonal + mild correlation
        cov = np.eye(n) * 0.04 + 0.01

    if req.objective == "min_vol":
        weights = _min_vol(cov)
    else:
        weights = _max_sharpe(mu, cov, req.risk_free)

    port_ret = float(weights @ mu)
    port_vol = float(np.sqrt(weights @ cov @ weights))
    sharpe = (port_ret - req.risk_free) / port_vol if port_vol > 0 else 0.0

    return {
        "symbols": req.symbols,
        "weights": {s: float(w) for s, w in zip(req.symbols, weights)},
        "expected_return": port_ret,
        "volatility": port_vol,
        "sharpe": sharpe,
        "objective": req.objective,
    }
