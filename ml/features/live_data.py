"""Live market data — NSE first, Yahoo second. NO synthetic prices."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, build_opener, urlopen
from http.cookiejar import CookieJar

import pandas as pd

_nse_opener = None
_nse_last_init = 0.0


def _ua() -> str:
    return (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )


def _nse():
    global _nse_opener, _nse_last_init
    now = time.time()
    if _nse_opener is None or now - _nse_last_init > 600:
        cj = CookieJar()
        from urllib.request import HTTPCookieProcessor
        _nse_opener = build_opener(HTTPCookieProcessor(cj))
        _nse_opener.addheaders = [
            ("User-Agent", _ua()),
            ("Accept", "application/json,text/plain,*/*"),
            ("Accept-Language", "en-IN,en;q=0.9"),
        ]
        try:
            _nse_opener.open("https://www.nseindia.com", timeout=12)
        except Exception:
            pass
        _nse_last_init = now
    return _nse_opener


def nse_quote(symbol: str) -> dict[str, Any]:
    sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    try:
        op = _nse()
        url = f"https://www.nseindia.com/api/quote-equity?symbol={sym}"
        req = Request(url, headers={"Referer": "https://www.nseindia.com/", "User-Agent": _ua()})
        with op.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
        price = data.get("priceInfo") or {}
        info = data.get("info") or {}
        last = price.get("lastPrice")
        if last is None:
            return {"ok": False, "source": "nse", "symbol": sym, "error": "no lastPrice in NSE payload"}
        return {
            "ok": True,
            "symbol": sym,
            "source": "nse",
            "delayed": False,
            "last": float(last),
            "open": float(price.get("open") or last),
            "high": float(price.get("intraDayHighLow", {}).get("max") or price.get("high") or last),
            "low": float(price.get("intraDayHighLow", {}).get("min") or price.get("low") or last),
            "prev_close": float(price.get("previousClose") or last),
            "change": float(price.get("change") or 0),
            "change_pct": float(price.get("pChange") or 0),
            "volume": int((data.get("securityWiseDP") or {}).get("quantityTraded") or 0),
            "company": info.get("companyName"),
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"ok": False, "source": "nse", "symbol": symbol, "error": str(e)}


def yahoo_quote(symbol: str) -> dict[str, Any]:
    sym = symbol.upper().strip()
    if sym in ("^NSEI", "^BSESN", "NIFTY", "SENSEX"):
        ysym = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "^NSEI": "^NSEI", "^BSESN": "^BSESN"}.get(sym, sym)
    elif not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        ysym = f"{sym}.NS"
    else:
        ysym = sym
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ysym}?interval=1m&range=1d"
        req = Request(url, headers={"User-Agent": _ua()})
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
        result = (data.get("chart") or {}).get("result") or []
        if not result:
            return {"ok": False, "source": "yahoo", "symbol": symbol, "error": "empty chart result"}
        meta = result[0].get("meta") or {}
        last = meta.get("regularMarketPrice") or meta.get("previousClose")
        if last is None:
            return {"ok": False, "source": "yahoo", "symbol": symbol, "error": "no price in meta"}
        prev = float(meta.get("previousClose") or last)
        last_f = float(last)
        return {
            "ok": True,
            "symbol": symbol.upper().replace(".NS", "").replace(".BO", ""),
            "source": "yahoo",
            "delayed": True,
            "last": last_f,
            "open": float(meta.get("regularMarketOpen") or last_f),
            "high": float(meta.get("regularMarketDayHigh") or last_f),
            "low": float(meta.get("regularMarketDayLow") or last_f),
            "prev_close": prev,
            "change": last_f - prev,
            "change_pct": ((last_f / prev - 1) * 100) if prev else 0.0,
            "volume": int(meta.get("regularMarketVolume") or 0),
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"ok": False, "source": "yahoo", "symbol": symbol, "error": str(e)}


def live_quote(symbol: str) -> dict[str, Any]:
    """NSE → Yahoo → structured error. Never synthetic."""
    nse = nse_quote(symbol)
    if nse.get("ok"):
        return nse
    y = yahoo_quote(symbol)
    if y.get("ok"):
        y["nse_error"] = nse.get("error")
        return y
    return {
        "ok": False,
        "symbol": symbol.upper().replace(".NS", "").replace(".BO", ""),
        "source": None,
        "error": "All live sources failed",
        "attempts": [
            {"source": "nse", "error": nse.get("error")},
            {"source": "yahoo", "error": y.get("error")},
        ],
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def fetch_ohlcv_yahoo(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    try:
        import yfinance as yf
        sym = symbol
        if symbol.upper() in ("NIFTY", "^NSEI"):
            sym = "^NSEI"
        elif symbol.upper() in ("SENSEX", "^BSESN"):
            sym = "^BSESN"
        elif not symbol.startswith("^") and "." not in symbol:
            sym = f"{symbol}.NS"
        df = yf.Ticker(sym).history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.rename(columns={c: c.lower() for c in df.columns})
        return df[["open", "high", "low", "close", "volume"]].dropna()
    except Exception:
        return pd.DataFrame()


def search_indian_stocks(query: str, limit: int = 15) -> list[dict[str, Any]]:
    """Yahoo finance search filtered to NSE/BSE."""
    q = (query or "").strip()
    if len(q) < 1:
        return []
    try:
        from urllib.parse import quote_plus
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={quote_plus(q)}&quotesCount={limit}&newsCount=0"
        req = Request(url, headers={"User-Agent": _ua()})
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
        out = []
        for item in data.get("quotes") or []:
            symbol = item.get("symbol") or ""
            exch = (item.get("exchange") or item.get("exchDisp") or "").upper()
            if not (symbol.endswith(".NS") or symbol.endswith(".BO") or "NSE" in exch or "BSE" in exch or "NSI" in exch):
                # still allow if name looks Indian equity and type equity
                if item.get("quoteType") not in ("EQUITY", "INDEX", None):
                    continue
            base = symbol.replace(".NS", "").replace(".BO", "")
            out.append({
                "symbol": base,
                "yahoo_symbol": symbol,
                "name": item.get("shortname") or item.get("longname") or base,
                "exchange": "NSE" if symbol.endswith(".NS") or "NSE" in exch or "NSI" in exch else (
                    "BSE" if symbol.endswith(".BO") or "BSE" in exch else (item.get("exchDisp") or "IND")
                ),
                "type": item.get("quoteType") or "EQUITY",
            })
        return out[:limit]
    except Exception as e:
        return [{"error": str(e), "symbol": None, "name": f"Search failed: {e}"}]
