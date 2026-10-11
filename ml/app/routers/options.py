from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes(
    S: float, K: float, T: float, r: float, q: float, sigma: float, option_type: str = "call"
) -> dict[str, float]:
    """Dividend-adjusted Black-Scholes (European)."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(0.0, S - K) if option_type == "call" else max(0.0, K - S)
        return {"price": intrinsic, "delta": 1.0 if option_type == "call" and S > K else 0.0,
                "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "call":
        price = S * math.exp(-q * T) * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        delta = math.exp(-q * T) * norm_cdf(d1)
        rho = K * T * math.exp(-r * T) * norm_cdf(d2) / 100
    else:
        price = K * math.exp(-r * T) * norm_cdf(-d2) - S * math.exp(-q * T) * norm_cdf(-d1)
        delta = -math.exp(-q * T) * norm_cdf(-d1)
        rho = -K * T * math.exp(-r * T) * norm_cdf(-d2) / 100

    gamma = math.exp(-q * T) * math.exp(-0.5 * d1 ** 2) / (S * sigma * math.sqrt(2 * math.pi * T))
    vega = S * math.exp(-q * T) * math.exp(-0.5 * d1 ** 2) * math.sqrt(T) / math.sqrt(2 * math.pi) / 100
    theta = (
        -S * math.exp(-q * T) * math.exp(-0.5 * d1 ** 2) * sigma / (2 * math.sqrt(2 * math.pi * T))
        - r * K * math.exp(-r * T) * (norm_cdf(d2) if option_type == "call" else norm_cdf(-d2))
        + q * S * math.exp(-q * T) * (norm_cdf(d1) if option_type == "call" else norm_cdf(-d1))
    ) / 365

    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "rho": rho,
    }


def barone_adesi_whaley_approx(
    S: float, K: float, T: float, r: float, q: float, sigma: float, option_type: str = "call"
) -> dict[str, float]:
    """
    Simplified Barone-Adesi-Whaley style approximation for American options.
    For production use a full BAW implementation; here we blend BS with early-exercise premium.
    """
    euro = black_scholes(S, K, T, r, q, sigma, option_type)
    # Crude early-exercise premium for American puts / dividend calls
    intrinsic = max(0.0, S - K) if option_type == "call" else max(0.0, K - S)
    premium = 0.0
    if option_type == "put" and r > 0:
        premium = max(0.0, intrinsic - euro["price"]) * 0.15 * math.exp(-r * T)
    elif option_type == "call" and q > 0.02:
        premium = max(0.0, intrinsic - euro["price"]) * 0.1 * math.exp(-q * T)

    american_price = euro["price"] + premium
    out = dict(euro)
    out["price"] = max(american_price, intrinsic)
    out["model"] = "BAW-approx"
    out["european_price"] = euro["price"]
    return out


class GreeksRequest(BaseModel):
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    time_to_expiry_years: float = Field(..., ge=0)
    rate: float = 0.07
    dividend_yield: float = 0.01
    iv: float = Field(..., gt=0)
    option_type: str = "call"
    american: bool = True


@router.post("/greeks")
def greeks(req: GreeksRequest) -> dict[str, Any]:
    if req.american:
        result = barone_adesi_whaley_approx(
            req.spot, req.strike, req.time_to_expiry_years,
            req.rate, req.dividend_yield, req.iv, req.option_type.lower()
        )
    else:
        result = black_scholes(
            req.spot, req.strike, req.time_to_expiry_years,
            req.rate, req.dividend_yield, req.iv, req.option_type.lower()
        )
        result["model"] = "Black-Scholes-dividend"
    result["note"] = "Cross-check only; prefer NSE-published Greeks as source of truth"
    return result
