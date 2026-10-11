
"""4-layer move diagnosis — always on, nothing optional."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from features.live_data import live_quote, fetch_ohlcv_yahoo
from features.headlines import fetch_headlines
from features.market_data import to_yahoo_symbol

NIFTY = "NIFTY 50"
NIFTY_YAHOO = "^NSEI"
SECTOR_PEERS: dict[str, list[str]] = {
    "RELIANCE": ["ONGC", "BPCL", "IOC"],
    "TCS": ["INFY", "WIPRO", "HCLTECH"],
    "INFY": ["TCS", "WIPRO", "HCLTECH"],
    "HDFCBANK": ["ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "ICICIBANK": ["HDFCBANK", "SBIN", "AXISBANK"],
    "SBIN": ["HDFCBANK", "ICICIBANK", "AXISBANK"],
    "ITC": ["HINDUNILVR", "NESTLEIND"],
    "LT": ["ADANIENT"],
    "AXISBANK": ["HDFCBANK", "ICICIBANK", "SBIN"],
    "WIPRO": ["TCS", "INFY", "HCLTECH"],
    "BHARTIARTL": ["IDEA"],
}


def _bars(symbol: str, period: str = "3mo") -> pd.DataFrame:
    """Real Yahoo/NSE-derived bars only. Empty = caller must error."""
    df = fetch_ohlcv_yahoo(symbol, period=period)
    if df is not None and not df.empty and len(df) >= 5:
        return df
    return pd.DataFrame()


def _ret(df: pd.DataFrame, days: int = 1) -> float | None:
    if df is None or len(df) < days + 1:
        return None
    c = df["close"].astype(float)
    prev, last = float(c.iloc[-(days + 1)]), float(c.iloc[-1])
    return None if prev == 0 else (last / prev - 1.0) * 100.0


def _gap(df: pd.DataFrame) -> float | None:
    if df is None or len(df) < 2:
        return None
    prev_close, open_ = float(df["close"].iloc[-2]), float(df["open"].iloc[-1])
    return None if prev_close == 0 else (open_ / prev_close - 1.0) * 100.0


def _vol_z(df: pd.DataFrame, window: int = 20) -> float | None:
    if df is None or len(df) < 5:
        return None
    v = df["volume"].astype(float)
    w = min(window, len(v) - 1)
    hist, last = v.iloc[-(w + 1):-1], float(v.iloc[-1])
    mean, std = float(hist.mean()), float(hist.std())
    return 0.0 if std < 1e-9 else (last - mean) / std


def classify_drivers(stock_ret, nifty_ret, peer_rets, volume_z, gap) -> list[dict[str, Any]]:
    drivers = []
    sr = stock_ret or 0.0
    nr = nifty_ret or 0.0
    excess = sr - nr
    vz = volume_z or 0.0
    peer_avg = float(np.mean(peer_rets)) if peer_rets else 0.0

    market_score = 0.0
    if abs(nr) > 0.3 and abs(sr) > 0.2 and ((sr > 0 and nr > 0) or (sr < 0 and nr < 0)):
        market_score = float(np.clip(abs(nr) / (abs(sr) + 1e-6) * 0.9, 0, 1))
    drivers.append({"type": "market", "score": round(market_score, 3), "evidence": f"Nifty {nr:+.2f}% vs stock {sr:+.2f}%"})

    sector_score = 0.0
    if peer_rets and abs(peer_avg) > 0.25 and ((sr > 0 and peer_avg > 0) or (sr < 0 and peer_avg < 0)):
        sector_score = float(np.clip(abs(peer_avg) / (abs(sr) + 1e-6) * 0.85, 0, 1))
    drivers.append({"type": "sector", "score": round(sector_score, 3), "evidence": f"Peer avg {peer_avg:+.2f}% (n={len(peer_rets)})"})

    stock_score = 0.0
    if abs(excess) > 0.8:
        stock_score += 0.45
    if abs(vz) >= 1.5:
        stock_score += 0.35
    if abs(excess) > 1.5 and abs(vz) >= 2.0:
        stock_score += 0.2
    stock_score = float(np.clip(stock_score, 0, 1))
    drivers.append({"type": "stock_specific", "score": round(stock_score, 3), "evidence": f"Excess vs Nifty {excess:+.2f}%, volume z={vz:.2f}"})

    g = gap or 0.0
    gap_score = float(np.clip(abs(g) / 3.0, 0, 1)) if abs(g) > 0.8 else 0.0
    drivers.append({"type": "overnight_gap", "score": round(gap_score, 3), "evidence": f"Open vs prior close gap {g:+.2f}%"})
    drivers.sort(key=lambda d: d["score"], reverse=True)
    return drivers


def prose_from_evidence(diagnosis: dict[str, Any]) -> str:
    sym = diagnosis.get("symbol", "?")
    nums = diagnosis.get("numbers") or {}
    drivers = diagnosis.get("drivers") or []
    headlines = diagnosis.get("headlines") or []
    live = diagnosis.get("live_quote") or {}
    sr, nr, vz = nums.get("stock_return_pct"), nums.get("nifty_return_pct"), nums.get("volume_z_20d")
    top = drivers[0] if drivers else None
    lines = [f"{sym}: 1-day return {sr:+.2f}%" if sr is not None else f"{sym}: return n/a"]
    if live.get("last") is not None:
        lines.append(f"Live last {live['last']:.2f} ({live.get('source')}, change {live.get('change_pct', 0):+.2f}%).")
    if nr is not None:
        lines.append(f"Nifty 1-day {nr:+.2f}% (excess {nums.get('excess_return_pct'):+.2f}%).")
    if vz is not None:
        lines.append(f"Volume z-score (20d): {vz:.2f}.")
    if top:
        lines.append(f"Primary driver: {top['type']} (score {top['score']}) — {top['evidence']}.")
    matched = [h for h in headlines if h.get("matched")]
    if matched:
        lines.append("Headlines: " + "; ".join(h["title"][:90] for h in matched[:3]))
    else:
        lines.append("No confirmed stock-specific headline matched in the free feed window.")
    lines.append("Evidence-based diagnosis only — not a trade recommendation.")
    return " ".join(lines)


def run_diagnosis(symbol: str, period: str = "3mo") -> dict[str, Any]:
    sym = symbol.upper().strip().replace(".NS", "").replace(".BO", "")

    # Layer inputs
    live = live_quote(sym)
    stock_df = _bars(sym, period)
    if not live.get("ok") and (stock_df is None or stock_df.empty):
        return {
            "ok": False,
            "symbol": sym,
            "error": "No live quote and no historical bars",
            "live_quote": live,
            "layers": {
                "1_numbers": {"error": "unavailable"},
                "2_classification": {"error": "unavailable"},
                "3_headlines": {"error": "unavailable"},
                "4_prose": {"error": "unavailable"},
            },
            "summary": None,
        }
    nifty_df = _bars(NIFTY_YAHOO, period)

    # Prefer live change_pct when feed is real
    stock_ret = _ret(stock_df, 1)
    if live.get("source") in ("nse", "yahoo") and live.get("change_pct") is not None:
        stock_ret = float(live["change_pct"])

    nifty_live = live_quote("^NSEI") if False else None  # Nifty via yahoo bars
    nifty_ret = _ret(nifty_df, 1)

    peers = SECTOR_PEERS.get(sym, [])
    peer_rets, peer_detail = [], []
    for p in peers[:5]:
        pr = _ret(_bars(p, period), 1)
        pq = live_quote(p)
        if pq.get("source") in ("nse", "yahoo") and pq.get("change_pct") is not None:
            pr = float(pq["change_pct"])
        if pr is not None:
            peer_rets.append(pr)
            peer_detail.append({"symbol": p, "return_pct": round(pr, 3), "source": pq.get("source")})

    excess = (stock_ret - nifty_ret) if stock_ret is not None and nifty_ret is not None else None
    vol_z = _vol_z(stock_df, 20)
    gap = _gap(stock_df)

    numbers = {
        "stock_return_pct": round(stock_ret, 3) if stock_ret is not None else None,
        "nifty_return_pct": round(nifty_ret, 3) if nifty_ret is not None else None,
        "excess_return_pct": round(excess, 3) if excess is not None else None,
        "volume_z_20d": round(vol_z, 3) if vol_z is not None else None,
        "gap_pct": round(gap, 3) if gap is not None else None,
        "last_price": live.get("last") or float(stock_df["close"].iloc[-1]),
        "bars_used": len(stock_df),
        "live_source": live.get("source"),
        "live_delayed": live.get("delayed"),
    }
    drivers = classify_drivers(stock_ret, nifty_ret, peer_rets, vol_z, gap)

    company = live.get("company") or sym
    headlines = fetch_headlines(sym, company_name=company if isinstance(company, str) else sym)

    diagnosis: dict[str, Any] = {
        "symbol": sym,
        "yahoo_symbol": to_yahoo_symbol(sym),
        "as_of": datetime.now(timezone.utc).isoformat(),
        "window": "1d",
        "data_source": live.get("source") or "unknown",
        "live_quote": {k: v for k, v in live.items() if not str(k).startswith("_")},
        "numbers": numbers,
        "peers": peer_detail,
        "drivers": drivers,
        "headlines": headlines,
        "primary_driver": drivers[0]["type"] if drivers else None,
    }
    summary = prose_from_evidence(diagnosis)
    diagnosis["summary"] = summary
    diagnosis["layers"] = {
        "1_numbers": {"name": "Measure the move", "data": numbers},
        "2_classification": {
            "name": "Rank drivers (market / sector / stock-specific / gap)",
            "data": drivers,
            "primary": diagnosis["primary_driver"],
        },
        "3_headlines": {
            "name": "Time-matched headlines (Google News RSS, free)",
            "data": headlines,
            "count": len([h for h in headlines if h.get("matched")]),
        },
        "4_prose": {
            "name": "Evidence-only summary; Gemini rewrites same evidence when key set",
            "deterministic_summary": summary,
            "gemini": "applied_in_/news/analyze_when_key_present",
        },
    }
    return diagnosis
