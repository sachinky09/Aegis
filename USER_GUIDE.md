# Aegis — User Guide

Personal AI-assisted quant research platform for **Indian equities (NSE)**.  
Self-hosted: one machine, Docker Compose, your data.

---

## What Aegis is for

Aegis helps you:

- Track a **personal watchlist** of stocks  
- See **live-style quotes and technical indicators** (Yahoo Finance)  
- Understand **why a price may be moving** using **evidence first** (not AI guessing)  
- Run **paper trades** with lot-size and capital rules  
- Explore **backtests**, **options Greeks**, and **portfolio weights**  
- Optionally turn structured evidence into short prose with **Gemini**

It is a **research and paper-trading lab**, not a live broker.

---

## How to start

```bash
unzip aegis.zip && cd aegis
cp .env.example .env
# Optional: GEMINI_API_KEY=your_key
docker compose up --build -d
```

Open:

| What | URL |
|------|-----|
| Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8080 |
| ML API docs | http://localhost:8000/docs |
| Airflow | http://localhost:8081 (admin / admin) |
| Error report | http://localhost:8090/errors |

First boot can take a few minutes while images build and databases initialize.

---

## Main screens (what you do)

### Dashboard
- Service health (backend / ML)  
- Paper equity snapshot  
- Your **watchlist**  
- Click **View** on a symbol to load quote + technical features  
- Link to manage the watchlist  

### Watchlist
- **Add** any NSE-style symbol (e.g. `WIPRO`, `RELIANCE.NS` — suffix is stripped)  
- Optional name, sector, lot size, notes  
- **Remove** only unwatches; history and paper trades stay  
- Live last price when Yahoo responds  

### Paper Trading
- Starting cash is seeded (default ₹10,00,000)  
- Place **BUY/SELL** market-style paper orders  
- Quantity is rounded **down to lot size** and capped by **cash**  
- See positions, cash, equity, recent orders  

### Signals
- List stored signals  
- Create a demo technical signal for testing  

### Research
This is where diagnosis, backtests, options, and portfolio tools live.

#### Move diagnosis (why prices may be moving)

Four layers, in order:

1. **Numbers** — 1-day stock return, Nifty return, excess return, volume z-score (20d), overnight gap  
2. **Classification** — scores for **market**, **sector** (peers), **stock-specific**, **overnight gap**  
3. **Headlines** — placeholder until you wire NSE/news API; reports when nothing confirmed  
4. **Prose** — clear summary from those numbers; **Gemini only rewrites evidence** if `GEMINI_API_KEY` is set  

**Run diagnosis** → structured JSON + summary  
**Diagnosis + Gemini prose** → same evidence, optional LLM wording  

If Yahoo is unreachable, the system uses a **synthetic fallback** so the feature still runs offline (labeled in the response).

#### Other Research tools
- **Walk-forward backtest** with purge/embargo and a simple PBO-style metric  
- **Options Greeks** (dividend-adjusted Black–Scholes + American-style approximation)  
- **Portfolio optimize** (e.g. max Sharpe weights)  

---

## How “why is it moving?” works (user view)

Old pure-Gemini answers were weak because the model had no evidence.

Now:

```text
You click Diagnose
    → system measures the move vs Nifty and volume
    → ranks drivers (market / sector / stock / gap)
    → checks for matched headlines (when available)
    → writes a summary from that evidence only
    → optionally asks Gemini to rephrase the same evidence
```

Example of the kind of answer you should expect:

> RELIANCE: 1-day return +1.80%. Nifty +0.60% (excess +1.20%). Volume z-score 2.60.  
> Primary driver: stock_specific — elevated volume and excess vs Nifty.  
> No confirmed stock-specific headline in the linked sources for this window.  
> This is an evidence-based diagnosis, not a trade recommendation.

That is intentional: honest when a catalyst is unknown.

---

## Paper trading rules (what to expect)

- One default account  
- Buys require cash; sells require position  
- Lot size from the instrument master  
- Immediate fill at the price you supply (paper simulation)  
- State lives in Postgres only (not on a message queue)  

---

## External data & keys

| Need | Source |
|------|--------|
| Prices / OHLCV | Yahoo Finance (no key) |
| Move diagnosis peers / Nifty | Yahoo (`^NSEI`, peer tickers) |
| Gemini prose | `GEMINI_API_KEY` in `.env` (optional) |

Without Gemini, diagnosis and the whole app still work; only LLM prose is skipped.

---

## Services behind the UI (simple map)

- **Frontend** — screens you use  
- **Backend** — watchlist, paper trading, signals, health  
- **ML service** — Yahoo data, features, diagnosis, backtest, options, portfolio, Gemini  
- **Postgres** — durable storage  
- **Redis** — short-lived cache / dedupe  
- **Kafka** — event streams for ticks/signals (platform plumbing)  
- **Airflow** — scheduled historical/news/model jobs  
- **Log analyzer** — grouped errors  

---

## Typical first session

1. Open http://localhost:3000  
2. Go to **Watchlist** → add a few symbols  
3. **Dashboard** → View a symbol → check features  
4. **Research** → Run diagnosis on that symbol  
5. **Paper Trading** → place a small BUY and see position/cash update  
6. (Optional) set `GEMINI_API_KEY`, restart, use **Diagnosis + Gemini prose**  

---

## What Aegis is not

- Not a live broker or order gateway  
- Not guaranteed real-time exchange data (Yahoo can lag or fail)  
- Not investment advice  
- Gemini text is **interpretation of evidence**, not verified news  

---

## Stopping

```bash
docker compose down
# remove data volumes too:
docker compose down -v
```

---

*Built for personal research: measurable evidence first, optional language second.*
