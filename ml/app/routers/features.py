from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, Field

from features.technical import compute_features

router = APIRouter()


class OHLCVBar(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class FeatureRequest(BaseModel):
    symbol: str
    bars: list[OHLCVBar] = Field(..., min_length=5)


@router.post("/compute")
def compute(req: FeatureRequest) -> dict[str, Any]:
    df = pd.DataFrame([b.model_dump() for b in req.bars])
    feats = compute_features(df)
    return {"symbol": req.symbol, "features": feats}


@router.get("/demo/{symbol}")
def demo_features(symbol: str) -> dict[str, Any]:
    """Generate synthetic OHLCV and compute features (no external data needed)."""
    rng = np.random.default_rng(abs(hash(symbol)) % (2**32))
    n = 120
    returns = rng.normal(0.0005, 0.015, n)
    close = 1000 * np.cumprod(1 + returns)
    high = close * (1 + rng.uniform(0, 0.01, n))
    low = close * (1 - rng.uniform(0, 0.01, n))
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    volume = rng.integers(100000, 2000000, n).astype(float)
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})
    feats = compute_features(df)
    return {"symbol": symbol.upper(), "features": feats, "bars_used": n}
