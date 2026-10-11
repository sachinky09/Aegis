#!/usr/bin/env bash
set -u
PASS=0; FAIL=0
green() { printf 'PASS  %s\n' "$1"; PASS=$((PASS+1)); }
red()   { printf 'FAIL  %s — %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

check_http() {
  local name="$1" url="$2" expect="${3:-200}"
  local code body
  body=$(curl -sS -m 45 -w '\n%{http_code}' "$url" 2>&1) || true
  code=$(echo "$body" | tail -n1)
  body=$(echo "$body" | sed '$d')
  if [[ "$code" == "$expect" ]]; then green "$name ($code)"; else red "$name" "HTTP $code body=${body:0:120}"; fi
}

check_post() {
  local name="$1" url="$2" json="$3"
  local code body
  body=$(curl -sS -m 60 -w '\n%{http_code}' -X POST "$url" -H 'Content-Type: application/json' -d "$json" 2>&1) || true
  code=$(echo "$body" | tail -n1)
  body=$(echo "$body" | sed '$d')
  if [[ "$code" == "200" ]]; then green "$name ($code)"; else red "$name" "HTTP $code body=${body:0:120}"; fi
}

echo "=== Aegis test.sh $(date -u) ==="
docker compose ps 2>/dev/null || true

check_http "backend_health" "http://127.0.0.1:8080/actuator/health"
check_http "ml_health" "http://127.0.0.1:8000/health"
check_http "frontend" "http://127.0.0.1:3000/"
check_http "proxy_api" "http://127.0.0.1:3000/api/instruments"
check_http "search" "http://127.0.0.1:8000/market/search?q=indusind"
check_http "live_reliance" "http://127.0.0.1:8000/market/live/RELIANCE"
check_http "diagnosis" "http://127.0.0.1:8000/market/move-diagnosis/RELIANCE"
check_http "automation" "http://127.0.0.1:8000/automation/status"
check_http "watchlist" "http://127.0.0.1:8080/api/watchlist"
check_post "add_watch" "http://127.0.0.1:8080/api/watchlist" '{"symbol":"INDUSINDBK","name":"IndusInd Bank"}'
check_post "paper_order" "http://127.0.0.1:8080/api/paper/orders" '{"symbol":"INDUSINDBK","side":"BUY","orderType":"MARKET","quantity":1,"marketPrice":1000}'
check_post "predict" "http://127.0.0.1:8000/models/predict" '{"features":[0.1,0.2,0,0,0,0,0,0]}'
check_post "news" "http://127.0.0.1:8000/news/analyze" '{"symbol":"RELIANCE"}'

echo "=== RESULT PASS=$PASS FAIL=$FAIL ==="
[[ "$FAIL" -eq 0 ]]
