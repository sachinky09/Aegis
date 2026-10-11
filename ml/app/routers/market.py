"""Market data endpoints — NSE live first, Yahoo second."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from features.live_data import live_quote, search_indian_stocks
from features.market_data import fetch_ohlcv, fetch_quote, fetch_multiple_quotes, to_yahoo_symbol
from features.technical import compute_features
from features.move_diagnosis import run_diagnosis

router = APIRouter()


@router.get("/quote/{symbol}")
def quote(symbol: str) -> dict[str, Any]:
    """Prefer live NSE/Yahoo quote; fall back to legacy fetch_quote."""
    live = live_quote(symbol)
    if live.get("last") is not None:
        return live
    data = fetch_quote(symbol)
    if not data:
        return {"symbol": symbol, "error": "quote unavailable", "source": None}
    return data


@router.get("/live/{symbol}")
def live(symbol: str) -> dict[str, Any]:
    """Near-real-time quote: NSE first, Yahoo second, synthetic last (labeled)."""
    return live_quote(symbol)


@router.get("/ohlcv/{symbol}")
def ohlcv(
    symbol: str,
    period: str = Query("3mo"),
    interval: str = Query("1d"),
) -> dict[str, Any]:
    df = fetch_ohlcv(symbol, period=period, interval=interval)
    if df is None or df.empty:
        return {"symbol": symbol, "bars": [], "count": 0}
    records = []
    for idx, row in df.tail(500).iterrows():
        records.append({
            "time": str(idx),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        })
    return {"symbol": symbol, "yahoo": to_yahoo_symbol(symbol), "count": len(records), "bars": records}


@router.get("/features/{symbol}")
def features(symbol: str, period: str = "3mo") -> dict[str, Any]:
    df = fetch_ohlcv(symbol, period=period)
    if df is None or df.empty:
        return {"symbol": symbol, "error": "no bars", "features": {}}
    feats = compute_features(df)
    return {"symbol": symbol, "features": feats}


@router.get("/move-diagnosis/{symbol}")
def move_diagnosis(symbol: str, period: str = "3mo") -> dict[str, Any]:
    """
    Four-layer move diagnosis (always on):
    1) Numbers  2) Driver classification  3) Headlines  4) Prose (+ Gemini in /news/analyze)
    """
    return run_diagnosis(symbol, period=period)


@router.post("/quotes")
def quotes(symbols: list[str]) -> dict[str, Any]:
    return {"quotes": fetch_multiple_quotes(symbols)}


@router.get("/search")
def search(q: str = Query("", min_length=1), limit: int = Query(15, ge=1, le=30)) -> dict[str, Any]:
    """Search Indian equities (Yahoo), any name — not limited to a fixed list."""
    results = search_indian_stocks(q, limit=limit)
    err = next((r for r in results if r.get("error") and not r.get("symbol")), None)
    return {"query": q, "count": len([r for r in results if r.get("symbol")]), "results": results, "error": (err or {}).get("error")}
