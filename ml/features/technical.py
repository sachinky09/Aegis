"""Technical feature engine — trend, momentum, volatility, volume, structure."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=1).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(window, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ef = ema(series, fast)
    es = ema(series, slow)
    line = ef - es
    sig = ema(line, signal)
    hist = line - sig
    return line, sig, hist


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(series, window)
    std = series.rolling(window, min_periods=1).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window, min_periods=1).mean()


def volume_zscore(volume: pd.Series, window: int = 20) -> pd.Series:
    mean = volume.rolling(window, min_periods=1).mean()
    std = volume.rolling(window, min_periods=1).std().replace(0, np.nan)
    return (volume - mean) / std


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical = (high + low + close) / 3
    return (typical * volume).cumsum() / volume.cumsum().replace(0, np.nan)


def compute_features(df: pd.DataFrame) -> dict:
    """
    Expect columns: open, high, low, close, volume.
    Returns latest feature vector as dict.
    """
    if df.empty or len(df) < 5:
        return {"error": "insufficient data"}

    c = df["close"]
    h = df["high"]
    l = df["low"]
    v = df["volume"]

    macd_line, macd_sig, macd_hist = macd(c)
    bb_u, bb_m, bb_l = bollinger(c)

    features = {
        "sma_10": float(sma(c, 10).iloc[-1]),
        "sma_20": float(sma(c, 20).iloc[-1]),
        "sma_50": float(sma(c, 50).iloc[-1]) if len(df) >= 50 else None,
        "ema_12": float(ema(c, 12).iloc[-1]),
        "ema_26": float(ema(c, 26).iloc[-1]),
        "rsi_14": float(rsi(c, 14).iloc[-1]),
        "macd": float(macd_line.iloc[-1]),
        "macd_signal": float(macd_sig.iloc[-1]),
        "macd_hist": float(macd_hist.iloc[-1]),
        "bb_upper": float(bb_u.iloc[-1]),
        "bb_mid": float(bb_m.iloc[-1]),
        "bb_lower": float(bb_l.iloc[-1]),
        "atr_14": float(atr(h, l, c, 14).iloc[-1]),
        "volume_zscore": float(volume_zscore(v, 20).iloc[-1]) if not np.isnan(volume_zscore(v, 20).iloc[-1]) else 0.0,
        "obv": float(obv(c, v).iloc[-1]),
        "vwap": float(vwap(h, l, c, v).iloc[-1]) if not np.isnan(vwap(h, l, c, v).iloc[-1]) else float(c.iloc[-1]),
        "roc_10": float(((c.iloc[-1] / c.iloc[-11]) - 1) * 100) if len(df) > 10 else 0.0,
        "close": float(c.iloc[-1]),
        "high": float(h.iloc[-1]),
        "low": float(l.iloc[-1]),
        "volume": float(v.iloc[-1]),
    }
    return {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in features.items()}
