"""Yahoo Finance market data — no API key required."""
from __future__ import annotations

from typing import Any

import pandas as pd

NSE_SUFFIX = ".NS"


def to_yahoo_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.endswith(".NS") or s.endswith(".BO"):
        return s
    return f"{s}{NSE_SUFFIX}"


def fetch_ohlcv(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV from Yahoo Finance for an Indian equity.
    Returns DataFrame with columns: open, high, low, close, volume.
    Empty DataFrame on failure (never raises for network/data issues).
    """
    empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    try:
        import yfinance as yf
    except ImportError:
        return empty

    ysym = to_yahoo_symbol(symbol)
    try:
        ticker = yf.Ticker(ysym)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return empty
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        out = df[cols].copy()
        out.index = pd.to_datetime(out.index).tz_localize(None)
        return out.dropna(how="all")
    except Exception:
        return empty


def fetch_quote(symbol: str) -> dict[str, Any]:
    """Latest price / basic quote from Yahoo Finance."""
    ysym = to_yahoo_symbol(symbol)
    try:
        import yfinance as yf
    except ImportError:
        return {"symbol": symbol.upper(), "yahoo_symbol": ysym, "error": "yfinance not installed"}

    try:
        ticker = yf.Ticker(ysym)
        try:
            fast = ticker.fast_info
            last = getattr(fast, "last_price", None) or getattr(fast, "lastPrice", None)
            prev = getattr(fast, "previous_close", None) or getattr(fast, "previousClose", None)
            if last is not None:
                return {
                    "symbol": symbol.upper(),
                    "yahoo_symbol": ysym,
                    "last_price": float(last) if last is not None else None,
                    "previous_close": float(prev) if prev is not None else None,
                    "currency": getattr(fast, "currency", None) or "INR",
                    "exchange": getattr(fast, "exchange", None) or "NSI",
                }
        except Exception:
            pass

        hist = ticker.history(period="5d", interval="1d")
        if hist is not None and not hist.empty:
            last_row = hist.iloc[-1]
            prev_close = float(hist.iloc[-2]["Close"]) if len(hist) > 1 else float(last_row["Close"])
            return {
                "symbol": symbol.upper(),
                "yahoo_symbol": ysym,
                "last_price": float(last_row["Close"]),
                "previous_close": prev_close,
                "currency": "INR",
                "exchange": "NSI",
            }
        return {"symbol": symbol.upper(), "yahoo_symbol": ysym, "error": "no data"}
    except Exception as e:
        return {"symbol": symbol.upper(), "yahoo_symbol": ysym, "error": str(e)}


def fetch_multiple_quotes(symbols: list[str]) -> list[dict[str, Any]]:
    return [fetch_quote(s) for s in symbols]
