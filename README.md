# Aegis — Personal AI-Assisted Quant Platform (Indian Equities)

Self-hosted, single-user. Live market data from **Yahoo Finance** (no market API key).

## Run (one command)

```bash
unzip aegis.zip && cd aegis
cp .env.example .env
# Optional: put your Gemini key in .env for the news panel
# GEMINI_API_KEY=your_key_here

docker compose up --build -d
```

Wait ~1–2 minutes on first boot, then open:

| Service        | URL |
|----------------|-----|
| **Dashboard**  | http://localhost:3000 |
| Backend API    | http://localhost:8080 |
| ML service     | http://localhost:8000/docs |
| Log analyzer   | http://localhost:8090/errors |

### Optional services

```bash
# Kafka streaming
docker compose --profile kafka up -d
# Then enable Kafka in backend (restart with):
# AEGIS_KAFKA_ENABLED=true
# SPRING_AUTOCONFIGURE_EXCLUDE=

# Airflow DAGs UI (admin / admin)
docker compose --profile airflow up -d
# → http://localhost:8081
```

### Stop

```bash
docker compose down
# Remove volumes too:
docker compose down -v
```

## Features

- **Watchlist** — add/remove any NSE symbol from the UI (`/watchlist`)
- **Yahoo Finance** — quotes, OHLCV, technical features (no API key)
- **Paper trading** — lot-size aware, capital-capped, direct Postgres TX
- **ML / quant** — features, baselines, walk-forward with purge/embargo, options Greeks, portfolio optimizer
- **Gemini news** — optional; degrades cleanly if key missing
- **Correctness** — point-in-time universe table, timestamp-locked news archive path, no Kafka for portfolio state

## Env (`.env`)

```
POSTGRES_DB=aegis
POSTGRES_USER=aegis
POSTGRES_PASSWORD=changeme
JWT_SECRET=changeme-jwt-secret-key-min-32-chars!!
GEMINI_API_KEY=          # optional
AIRFLOW_FERNET_KEY=dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGs=
```

## Quick API checks

```bash
curl -s http://localhost:8080/actuator/health
curl -s http://localhost:8000/health
curl -s http://localhost:8080/api/watchlist
curl -s -X POST http://localhost:8080/api/watchlist \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"WIPRO","name":"Wipro Ltd","sector":"IT"}'
curl -s http://localhost:8000/market/quote/RELIANCE
curl -s -X POST http://localhost:8000/news/analyze \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"RELIANCE","query":"Why is it moving?"}'
```

## Architecture (default profile)

```
React (Nginx :3000)
    → Spring Boot (:8080) → Postgres + Redis
    → FastAPI ML (:8000)  → Yahoo Finance + optional Gemini
log-analyzer (:8090)
```

Kafka and Airflow are **opt-in** profiles so the default `docker compose up --build` stays fast and reliable.
