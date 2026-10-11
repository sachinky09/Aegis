"""Log analyzer — tails structured JSON logs, clusters errors, serves report."""
from __future__ import annotations

import json
import re
import threading
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ERROR_CACHE: dict = defaultdict(lambda: {"count": 0, "first_seen": None, "last_seen": None, "example": None})
LOG_DIR = Path("/logs")
_seen_files: dict[str, int] = {}


def normalize_stack(stack: str) -> str:
    return re.sub(r":\d+", ":*", stack or "")[:300]


def process_line(line: str) -> None:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        if "ERROR" in line or "Exception" in line:
            key = ("unknown", "raw", normalize_stack(line[:200]))
            bucket = ERROR_CACHE[key]
            bucket["count"] += 1
            bucket["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            bucket["first_seen"] = bucket["first_seen"] or bucket["last_seen"]
            bucket["example"] = line[:300]
        return

    level = str(entry.get("level", "")).upper()
    if level not in ("ERROR", "CRITICAL", "FATAL"):
        return

    key = (
        entry.get("service", "unknown"),
        entry.get("error_type", entry.get("logger", "unknown")),
        normalize_stack(str(entry.get("stack", entry.get("message", "")))),
    )
    bucket = ERROR_CACHE[key]
    bucket["count"] += 1
    ts = entry.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    bucket["last_seen"] = ts
    bucket["first_seen"] = bucket["first_seen"] or ts
    bucket["example"] = entry.get("message") or entry.get("msg")


def scan_logs() -> None:
    if not LOG_DIR.exists():
        return
    for path in LOG_DIR.rglob("*.log"):
        try:
            key = str(path)
            offset = _seen_files.get(key, 0)
            with open(path, "r", errors="ignore") as f:
                f.seek(offset)
                for line in f:
                    process_line(line.strip())
                _seen_files[key] = f.tell()
        except Exception:
            pass


def background_scanner() -> None:
    while True:
        scan_logs()
        time.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()
    yield


app = FastAPI(title="Aegis Log Analyzer", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "log-analyzer"}


@app.get("/errors")
def top_errors(n: int = 20):
    items = sorted(ERROR_CACHE.items(), key=lambda kv: kv[1]["count"], reverse=True)[:n]
    return {
        "count": len(ERROR_CACHE),
        "errors": [
            {
                "service": k[0],
                "error_type": k[1],
                "stack_norm": k[2],
                **v,
            }
            for k, v in items
        ],
    }


@app.get("/")
def root():
    return {"service": "log-analyzer", "endpoints": ["/health", "/errors"]}
