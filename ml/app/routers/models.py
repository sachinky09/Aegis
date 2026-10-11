from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from models.baselines import (
    train_direction_baseline,
    garch_vol,
    ewma_vol,
    oof_stack,
    shap_importance,
    hmm_regimes,
    lstm_direction,
)

router = APIRouter()


class PredictRequest(BaseModel):
    symbol: str = "RELIANCE"
    features: list[float] = Field(default_factory=lambda: [0.1] * 8)
    target: str = "direction"


class TrainDemoRequest(BaseModel):
    symbol: str = "RELIANCE"
    n_samples: int = 150
    n_features: int = 8


@router.post("/predict")
def predict(req: PredictRequest) -> dict[str, Any]:
    """Demo prediction using a simple heuristic + noise (no trained model required at boot)."""
    x = np.array(req.features, dtype=float)
    score = float(np.tanh(x.mean() + 0.1 * x.std()))
    direction = "UP" if score >= 0 else "DOWN"
    return {
        "symbol": req.symbol,
        "target": req.target,
        "prediction": direction,
        "score": score,
        "probability": float(0.5 + 0.5 * abs(score)),
        "model": "heuristic-demo",
    }


@router.post("/train-demo")
def train_demo(req: TrainDemoRequest) -> dict[str, Any]:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(req.n_samples, req.n_features))
    y = (X[:, 0] + 0.5 * X[:, 1] + rng.normal(scale=0.5, size=req.n_samples) > 0).astype(int)
    result = train_direction_baseline(X, y)
    result["symbol"] = req.symbol
    return result


@router.post("/oof-stack")
def oof(req: TrainDemoRequest) -> dict[str, Any]:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(max(req.n_samples, 80), req.n_features))
    y = (X[:, 0] + 0.3 * X[:, 1] + rng.normal(scale=0.4, size=len(X)) > 0).astype(int)
    out = oof_stack(X, y)
    out["symbol"] = req.symbol
    return out


@router.post("/shap")
def shap(req: TrainDemoRequest) -> dict[str, Any]:
    rng = np.random.default_rng(1)
    X = rng.normal(size=(max(req.n_samples, 80), req.n_features))
    y = (X[:, 0] + 0.4 * X[:, 2] + rng.normal(scale=0.5, size=len(X)) > 0).astype(int)
    names = [f"f{i}" for i in range(req.n_features)]
    out = shap_importance(X, y, names)
    out["symbol"] = req.symbol
    return out


class RegimesRequest(BaseModel):
    returns: list[float] | None = None


@router.post("/regimes")
def regimes(req: RegimesRequest | None = None) -> dict[str, Any]:
    returns = (req.returns if req else None) or []
    if len(returns) < 30:
        rng = np.random.default_rng(2)
        returns = rng.normal(0.0005, 0.012, 120).tolist()
    return hmm_regimes(np.array(returns, dtype=float))


@router.post("/lstm")
def lstm(req: TrainDemoRequest) -> dict[str, Any]:
    rng = np.random.default_rng(3)
    X = rng.normal(size=(max(req.n_samples, 100), req.n_features))
    y = (X[:, 0] + rng.normal(scale=0.5, size=len(X)) > 0).astype(int)
    out = lstm_direction(X, y)
    out["symbol"] = req.symbol
    return out


@router.post("/volatility")
def volatility(returns: list[float]) -> dict[str, Any]:
    arr = np.array(returns, dtype=float)
    return {"ewma": ewma_vol(arr), "garch": garch_vol(arr)}
