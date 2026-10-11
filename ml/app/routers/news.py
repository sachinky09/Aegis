"""News intelligence — evidence-first move explanation; Gemini only formats evidence."""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from features.move_diagnosis import run_diagnosis, prose_from_evidence

router = APIRouter()


class AnalyzeRequest(BaseModel):
    symbol: str
    query: str | None = None
    context: str | None = None


class AnalyzeMoveRequest(BaseModel):
    symbol: str
    use_gemini: bool = True


def _gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or "").strip()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai

    key = _gemini_key()
    genai.configure(api_key=key)
    model_names = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro",
    ]
    last_err: Exception | None = None
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 512},
            )
            text = getattr(resp, "text", None)
            if text and text.strip():
                return text.strip()
            try:
                parts = resp.candidates[0].content.parts
                text = "".join(getattr(p, "text", "") or "" for p in parts)
                if text.strip():
                    return text.strip()
            except Exception:
                pass
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    return ""


def _gemini_prose_from_diagnosis(diagnosis: dict[str, Any]) -> str:
    prompt = (
        "You are a market research assistant for Indian equities (NSE).\n"
        "Rewrite the following STRUCTURED EVIDENCE into 5-8 clear sentences.\n"
        "Rules:\n"
        "- Use ONLY facts present in the evidence. Do not invent headlines, filings, or numbers.\n"
        "- If headlines are empty or matched=false, say no confirmed stock-specific headline was linked.\n"
        "- Do not give trade recommendations or price targets.\n"
        "- Label uncertainty.\n\n"
        f"EVIDENCE JSON:\n{diagnosis}\n"
    )
    return _call_gemini(prompt)


@router.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    """
    Evidence-first 'why is it moving':
    always runs move diagnosis; Gemini optional for prose only.
    """
    diagnosis = run_diagnosis(req.symbol)
    base_summary = diagnosis.get("summary") or prose_from_evidence(diagnosis)

    result: dict[str, Any] = {
        "symbol": diagnosis["symbol"],
        "status": "ok",
        "label": "interpretation",
        "diagnosis": diagnosis,
        "interpretation": base_summary,
        "source": "move-diagnosis",
    }

    if not _gemini_key():
        result["gemini"] = "skipped_no_key"
        result["message"] = "Structured diagnosis ready; set GEMINI_API_KEY for LLM prose"
        return result

    try:
        text = _gemini_prose_from_diagnosis(diagnosis)
        if text:
            result["interpretation"] = text
            result["source"] = "move-diagnosis+gemini"
            result["gemini"] = "ok"
        else:
            result["gemini"] = "empty_response"
    except Exception as e:
        result["gemini"] = "error"
        result["gemini_error"] = str(e)
        result["message"] = "Diagnosis OK; Gemini prose failed — showing deterministic summary"

    return result


@router.post("/analyze-move")
def analyze_move(req: AnalyzeMoveRequest) -> dict[str, Any]:
    """Same as /analyze with explicit use_gemini flag."""
    diagnosis = run_diagnosis(req.symbol)
    summary = diagnosis.get("summary") or prose_from_evidence(diagnosis)
    out: dict[str, Any] = {
        "symbol": diagnosis["symbol"],
        "status": "ok",
        "diagnosis": diagnosis,
        "interpretation": summary,
        "source": "move-diagnosis",
        "label": "interpretation",
    }
    if not req.use_gemini:
        out["gemini"] = "disabled_by_request"
        return out
    if not _gemini_key():
        out["gemini"] = "skipped_no_key"
        return out
    try:
        text = _gemini_prose_from_diagnosis(diagnosis)
        if text:
            out["interpretation"] = text
            out["source"] = "move-diagnosis+gemini"
            out["gemini"] = "ok"
    except Exception as e:
        out["gemini"] = "error"
        out["gemini_error"] = str(e)
    return out


@router.get("/archive")
def archive(symbol: str | None = None, limit: int = 20) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "count": 0,
        "articles": [],
        "note": "Timestamp-locked archive — populated by news_archive_dag. Never uses live Gemini.",
    }


@router.get("/status")
def news_status() -> dict[str, Any]:
    key = _gemini_key()
    return {
        "gemini_configured": bool(key),
        "key_prefix": (key[:6] + "…") if len(key) > 6 else ("set" if key else "missing"),
        "mode": "evidence-first move diagnosis; Gemini optional prose only",
    }
