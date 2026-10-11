"""IST wall-clock automation. No Airflow. 5 model retrain slots during NSE hours."""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("aegis.scheduler")
IST = ZoneInfo("Asia/Kolkata")

_scheduler = None
_job_log: list[dict] = []
_train_lock = threading.Lock()
_poll_lock = threading.Lock()

# Default stream universe: indices + liquid NSE names (top-20 style starter; rank can evolve)
DEFAULT_STREAM = [
    "^NSEI", "^BSESN",
    "RELIANCE", "TCS", "HDFCBANK", "BHARTIARTL", "ICICIBANK", "INFY", "SBIN", "HINDUNILVR",
    "ITC", "LT", "KOTAKBANK", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "TITAN", "WIPRO", "ULTRACEMCO", "NESTLEIND",
]


def _record(name: str, detail: str = "ok") -> None:
    _job_log.append({"job": name, "at": datetime.now(IST).isoformat(), "detail": detail})
    if len(_job_log) > 200:
        del _job_log[:100]
    logger.info("%s — %s", name, detail)


def job_live_poll() -> None:
    """Continuous live quotes for default universe. No synthetic."""
    if not _poll_lock.acquire(blocking=False):
        _record("live_poll", "skipped_overlap")
        return
    try:
        from features.live_data import live_quote
        ok, fail = 0, 0
        for s in DEFAULT_STREAM:
            q = live_quote(s)
            if q.get("ok"):
                ok += 1
            else:
                fail += 1
        _record("live_poll", f"ok={ok} fail={fail}")
    except Exception as e:
        _record("live_poll", f"error:{e}")
    finally:
        _poll_lock.release()


def job_model_retrain(slot: str) -> None:
    """One of 5 NSE-session retrain slots. Lock prevents overlap."""
    if not _train_lock.acquire(blocking=False):
        _record(f"retrain_{slot}", "skipped_overlap")
        return
    try:
        import numpy as np
        from models.baselines import train_direction_baseline, oof_stack
        rng = np.random.default_rng(int(datetime.now(IST).timestamp()) % 10000)
        # Prefer real feature rows when OHLCV available; else skip (no fake training set)
        from features.live_data import fetch_ohlcv_yahoo
        from features.technical import compute_features
        rows = []
        for sym in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"]:
            df = fetch_ohlcv_yahoo(sym, period="6mo")
            if df is None or len(df) < 40:
                continue
            feats = compute_features(df)
            if not feats:
                continue
            # build simple matrix from rolling closes
            closes = df["close"].astype(float).values
            for i in range(30, len(closes) - 1):
                window = closes[i - 8 : i]
                if len(window) < 8:
                    continue
                x = (window / window[-1] - 1.0).tolist()
                y = 1 if closes[i + 1] > closes[i] else 0
                rows.append((x, y))
        if len(rows) < 50:
            _record(f"retrain_{slot}", f"skipped_insufficient_real_data n={len(rows)}")
            return
        X = np.array([r[0] for r in rows], dtype=float)
        y = np.array([r[1] for r in rows], dtype=int)
        base = train_direction_baseline(X, y)
        oof = oof_stack(X, y) if len(X) >= 80 else {}
        _record(f"retrain_{slot}", f"base={base.get('model')} cv={base.get('cv_accuracy_mean')} oof={oof.get('oof_accuracy')}")
    except Exception as e:
        _record(f"retrain_{slot}", f"error:{e}")
    finally:
        _train_lock.release()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.warning("apscheduler missing")
        return

    sched = BackgroundScheduler(timezone=IST)
    # Continuous live stream poll during and around session
    sched.add_job(job_live_poll, IntervalTrigger(seconds=60), id="live_poll_60s", max_instances=1)

    # Five model retrain intervals during NSE open (approx 09:15–15:30 IST)
    # Slots: 09:30, 10:45, 12:00, 13:30, 15:00  Mon–Fri
    slots = [("0930", 9, 30), ("1045", 10, 45), ("1200", 12, 0), ("1330", 13, 30), ("1500", 15, 0)]
    for name, h, m in slots:
        sched.add_job(
            job_model_retrain,
            CronTrigger(day_of_week="mon-fri", hour=h, minute=m),
            id=f"retrain_{name}",
            args=[name],
            max_instances=1,
        )

    sched.add_job(job_live_poll, "date", id="boot_poll")
    sched.start()
    _scheduler = sched
    _record("scheduler", "started IST live_poll=60s retrains=5/session")


def scheduler_status() -> dict:
    jobs = []
    if _scheduler:
        for j in _scheduler.get_jobs():
            jobs.append({"id": j.id, "next_run": str(getattr(j, "next_run_time", None))})
    return {
        "running": _scheduler is not None,
        "retrain_slots_ist": ["09:30", "10:45", "12:00", "13:30", "15:00"],
        "live_poll_seconds": 60,
        "default_stream_size": len(DEFAULT_STREAM),
        "jobs": jobs,
        "recent": _job_log[-30:],
    }
