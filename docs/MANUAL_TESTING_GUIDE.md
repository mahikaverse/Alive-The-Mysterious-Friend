# Alive – Manual Testing & Deployment Guide

**Applies to:** Alive API (FastAPI) — `POST /chat/completions` (OpenAI-compatible) plus operational endpoints.
**Goal:** Manually verify the system works end-to-end with **Swagger UI**, **Postman**, **curl/HTTPie/REST Client**, and **k6**, then pass a **deployment-readiness checklist**.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Start the System](#2-start-the-system)
3. [Verify It Is Running](#3-verify-it-is-running)
4. [Test with Swagger UI](#4-test-with-swagger-ui)
5. [Test with Postman](#5-test-with-postman)
6. [Test with curl / HTTPie / VS Code REST Client](#6-test-with-curl--httpie--vs-code-rest-client)
7. [Test with k6 (Load Testing)](#7-test-with-k6-load-testing)
8. [Test the LLM Provider Failover Chain](#8-test-the-llm-provider-failover-chain)
9. [Run the Automated Test Suite](#9-run-the-automated-test-suite)
10. [Authentication Testing](#10-authentication-testing)
11. [Test Matrix (Checklist)](#11-test-matrix-checklist)
12. [Deployment Readiness Checklist](#12-deployment-readiness-checklist)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| **Docker Desktop** | Run PostgreSQL + API together | https://www.docker.com/products/docker-desktop |
| **Python 3.11+** | Run without Docker / run tests | https://www.python.org |
| **Postman** | Manual API testing | https://www.postman.com/downloads |
| **k6** (optional) | Load testing | https://k6.io/docs/getting-started/installation |
| **HTTPie** (optional) | CLI HTTP client | `pip install httpie` |
| **LLM API keys** | At least one for chat | DeepSeek / NVIDIA / OpenRouter / Grok / OpenAI / Gemini |

> **PowerShell note:** On Windows PowerShell 5.1, `curl` is an alias for `Invoke-WebRequest`. Always use `curl.exe` in PowerShell examples below, or use the `Invoke-RestMethod` variants provided.

---

## 2. Start the System

### Option A — Docker (recommended)

```bash
docker compose up --build
```

Wait for logs to show:

```
alive-1  | Memory subsystem initialized successfully   (or a warning — non-fatal)
alive-1  | Uvicorn running on http://0.0.0.0:8000
```

### Option B — Local (no Docker)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac / Linux

pip install -r requirements.txt
```

Make sure `.env` has `DATABASE_URL` pointing at a running PostgreSQL, then:

```bash
uvicorn backend.main:app --reload
```

### Configure the environment

Copy `.env.example` to `.env` if you have not already, and set:

```dotenv
LLM_PROVIDER=deepseek
LLM_FALLBACK_ORDER=nvidia,openrouter,grok
DEEPSEEK_API_KEY=sk-...
NVIDIA_API_KEY=nvapi-...
OPENROUTER_API_KEY=sk-or-...
GROK_API_KEY=xai-...
# OPENAI_API_KEY=sk-...   # required for the MEMORY (embeddings) subsystem
# API_KEY=my-secret       # optional; enables auth on protected endpoints
```

> `GROK_API_KEY` only enters the active provider chain once it is non-empty. Providers without a key are skipped automatically (`backend/core/llm_provider.py:286`).

---

## 3. Verify It Is Running

| URL | Expected |
|-----|----------|
| `http://localhost:8000/health` | `{"status":"ok","version":"1.1.0","uptime_seconds":N,"model":"alive-v1","environment":"development"}` |
| `http://localhost:8000/ready` | `{"status":"ready","version":"1.1.0","orchestrator":"initialised"}` |
| `http://localhost:8000/docs` | **Swagger UI** (interactive docs) |
| `http://localhost:8000/redoc` | ReDoc (alternative docs) |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3 schema |

> In production (`ENVIRONMENT=production`), `/docs` and `/redoc` are disabled (FastAPI mounts them only when `not settings.is_production` — `backend/app.py:52`).

---

## 4. Test with Swagger UI

1. Open `http://localhost:8000/docs`.
2. You will see six routes:
   - `GET /health`
   - `GET /ready`
   - `GET /metrics`
   - `GET /usage`
   - `GET /notifications`
   - `POST /chat/completions`
3. **Happy path:** expand `POST /chat/completions` → **Try it out** → paste the body below → **Execute**.

```json
{
  "model": "alive-v1",
  "messages": [
    { "role": "user", "content": "Hello! Who are you?" }
  ],
  "temperature": 0.7,
  "max_tokens": 300
}
```

**Expected 200 response (OpenAI-compatible):**

```json
{
  "id": "chatcmpl-<request-id>",
  "object": "chat.completion",
  "created": 1721800000,
  "model": "alive-v1",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "..." },
      "finish_reason": "stop"
    }
  ],
  "usage": { "prompt_tokens": N, "completion_tokens": N, "total_tokens": N }
}
```

4. **Negative tests:** repeat with each bad body below and confirm the HTTP status:

| Body change | Expected |
|---|---|
| `"messages": []` | 400 / 422 |
| `"role": "robot"` | 400 / 422 |
| omit `model` | 400 / 422 |
| `"temperature": 99` | 400 / 422 |
| `"max_tokens": -1` | 400 / 422 |
| `"content": ""` | 400 / 422 |

> **Swagger UI + auth:** when `API_KEY` is set, add the value to the **Authorize** button (top-right) so Swagger sends `Authorization: Bearer <key>`. The `/health`, `/ready`, `/metrics`, `/docs`, `/redoc`, `/openapi.json` paths are public; `/chat/completions`, `/usage`, `/notifications` are protected (`backend/api/middleware.py:21`).

---

## 5. Test with Postman

### 5.1 Import the collection

1. Open Postman → **Import** → select both files:
   - `docs/postman/Alive.postman_collection.json`
   - `docs/postman/Alive.postman_environment.json`
2. Select the **Alive - Local** environment (top-right dropdown).

### 5.2 Configure variables

| Variable | Default | When to change |
|----------|---------|----------------|
| `baseUrl` | `http://localhost:8000` | Different host/port |
| `apiKey` | *(empty)* | Set to your `API_KEY` when auth is enabled |
| `model` | `alive-v1` | — |
| `requestId` | `manual-test-001` | For `X-Request-ID` tests |

### 5.3 Run the folders in order

**Folder 0 — Operational / Health:** all five `GET` calls should return `200`.

**Folder 1 — Chat / Happy Path:** run in sequence.
- `Basic greeting`, `With system message`, `Multi-turn conversation` → `200`, non-empty `content`.
- `Memory: introduce yourself` then `Memory: recall` → the second response should reference the fact from the first (name/interest). **Requires `OPENAI_API_KEY`** for embeddings plus PostgreSQL/ChromaDB.
- `Zero temperature` → `200`.

**Folder 2 — Chat / Negative / Error Cases:** every request should return `400`/`422`/`404`/`405` as described in each request's description.

**Folder 3 — Auth:** only meaningful when `API_KEY` is set in `.env`.
- `Missing auth header` → `401`
- `Wrong auth header` → `401`
- `Valid auth header` → `200` (set the `apiKey` variable first)

### 5.4 Extra Postman tips

- **Request ID echo:** send any `POST /chat/completions` with header `X-Request-ID: my-test-123`. The response header `X-Request-ID` must echo `my-test-123` and the response `id` must be `chatcmpl-my-test-123`.
- **Usage before/after:** hit `GET /usage` before and after a chat request — the provider's `tokens.total` and `calls` counters should increase.
- **Automate:** use the Postman **Runner** to execute the whole collection in one pass and export a report.

---

## 6. Test with curl / HTTPie / VS Code REST Client

### curl.exe (Windows PowerShell)

```powershell
curl.exe -s http://localhost:8000/health

curl.exe -s -X POST http://localhost:8000/chat/completions `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"alive-v1\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'
```

### curl (bash / macOS / Linux)

```bash
curl -s http://localhost:8000/health

curl -s -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"alive-v1","messages":[{"role":"user","content":"Hello!"}]}'
```

### PowerShell native (Invoke-RestMethod)

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/health

$body = @{
  model    = "alive-v1"
  messages = @(@{ role = "user"; content = "Hello!" })
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://localhost:8000/chat/completions `
  -ContentType "application/json" -Body $body
```

### HTTPie

```bash
http :8000/health
http POST :8000/chat/completions model=alive-v1 messages:='[{"role":"user","content":"Hello!"}]'
```

### VS Code REST Client

Create a `.http` file:

```http
### Health
GET http://localhost:8000/health

### Chat
POST http://localhost:8000/chat/completions
Content-Type: application/json
Authorization: Bearer your-key-here        # only if API_KEY is set

{
  "model": "alive-v1",
  "messages": [
    { "role": "user", "content": "Hello! Who are you?" }
  ]
}
```

Install the **REST Client** extension and click **Send Request** above each block.

---

## 7. Test with k6 (Load Testing)

A ready-made script ships in `scripts/load_test.js`:

```bash
k6 run scripts/load_test.js
```

Customise load:

```bash
k6 run --vus 10 --duration 30s scripts/load_test.js
k6 run -e BASE_URL=http://localhost:8000 -e API_KEY=my-secret scripts/load_test.js
```

**Default thresholds** (failing them = performance problem):

- `p(95) < 2000ms` for request duration
- `< 1%` failed requests

Also watch for provider `429`/`402` responses in the output — those mean the LLM quota is exhausted, not a server fault.

---

## 8. Test the LLM Provider Failover Chain

```bash
python scripts/test_provider.py deepseek     # single provider
python scripts/test_provider.py nvidia
python scripts/test_provider.py openrouter
python scripts/test_provider.py grok
python scripts/test_provider.py all          # every provider in the active chain
```

Expected output per provider:

```
[OK] Response (N chars): ...
Usage: N tokens across N call(s)
```

- If a key is missing: `[SKIP] <Provider> API key is not configured...`
- If a key is invalid/out of credits: `[FAIL] <Provider> generation failed...`

**Verify fallback in real time:** temporarily set `LLM_PROVIDER=deepseek` with an invalid key, keep `LLM_FALLBACK_ORDER=nvidia,openrouter,grok`, then send a chat request. Alive should:

1. Try DeepSeek → exhaust (log: `provider 'deepseek' exhausted (401) — falling back`).
2. Fall back through NVIDIA → OpenRouter → Grok until a provider answers.
3. Record a notification — check `GET /notifications`.

---

## 9. Run the Automated Test Suite

```bash
python -m pytest -q                       # unit tests (no server needed)
python -m pytest tests/test_cost_saving.py -q   # failover + token-saving tests
```

### End-to-end tests (need a live server)

`tests/test_end_to_end.py` expects a server on **`127.0.0.1:8765`**:

```bash
uvicorn backend.main:app --port 8765     # in one terminal
python -m pytest tests/test_end_to_end.py -q -s   # in another
```

> The e2e suite covers health, ready, metrics, chat (basic/system/multi-turn), request-ID propagation, ~10 validation cases, 404/405, auth middleware (spawns its own server on 8766), long messages, zero temperature, response schema, and concurrency.

---

## 10. Authentication Testing

Auth is **disabled by default** (`API_KEY=` empty in `.env`). To test it:

1. Set `API_KEY=my-secret-key` in `.env` and restart.
2. Public endpoints — no token needed:
   - `GET /health`, `GET /ready`, `GET /metrics`, `GET /docs`, `GET /openapi.json`
3. Protected endpoints — require `Authorization: Bearer my-secret-key`:
   - `POST /chat/completions`, `GET /usage`, `GET /notifications`

| Scenario | Expected |
|----------|----------|
| No `Authorization` header on `/chat/completions` | `401 {"error":"Unauthorized."}` |
| `Authorization: Bearer wrong-key` | `401 {"error":"Unauthorized."}` |
| `Authorization: Bearer my-secret-key` | `200` |
| Public endpoint, no token | `200` |

---

## 11. Test Matrix (Checklist)

| # | Method & Path | Payload / Notes | Expected |
|---|---------------|-----------------|----------|
| 1 | `GET /health` | — | `200`, `status=ok`, `version=1.1.0` |
| 2 | `GET /ready` | — | `200`, `status=ready` |
| 3 | `GET /metrics` | — | `200`, keys: `total_requests`, `requests_by_path`, `requests_by_status`, `avg_latency_seconds` |
| 4 | `GET /usage` | — | `200`, `date`, `conversations_today`, `providers` |
| 5 | `GET /notifications` | `?limit=50&since=<epoch>` | `200`, `notifications` list |
| 6 | `POST /chat/completions` | 1 user message | `200`, OpenAI schema |
| 7 | `POST /chat/completions` | system + user | `200` |
| 8 | `POST /chat/completions` | 3-turn history | `200`, context-aware reply |
| 9 | `POST /chat/completions` | introduce fact, then recall | `200`, fact recalled (needs OpenAI key) |
| 10 | `POST /chat/completions` | `X-Request-ID: my-id` header | header echoed; `id=chatcmpl-my-id` |
| 11 | `POST /chat/completions` | `messages: []` | `400`/`422` |
| 12 | `POST /chat/completions` | `role: "robot"` | `400`/`422` |
| 13 | `POST /chat/completions` | missing `model` | `400`/`422` |
| 14 | `POST /chat/completions` | `temperature: 99` | `400`/`422` |
| 15 | `POST /chat/completions` | `max_tokens: -1` | `400`/`422` |
| 16 | `POST /chat/completions` | `content: ""` | `400`/`422` |
| 17 | `POST /chat/completions` | 101 messages | `400` (max 100) |
| 18 | `POST /chat/completions` | `temperature: 0.0` | `200` |
| 19 | `GET /nonexistent` | — | `404` |
| 20 | `PUT /chat/completions` | — | `405` |
| 21 | `POST /chat/completions` | no token (when `API_KEY` set) | `401` |
| 22 | `POST /chat/completions` | wrong token | `401` |
| 23 | `POST /chat/completions` | valid token | `200` |
| 24 | Load test | `k6 run scripts/load_test.js` | p95 < 2s, <1% errors |
| 25 | Providers | `python scripts/test_provider.py all` | all configured keys `[OK]` |

---

## 12. Deployment Readiness Checklist

Run through every item before shipping to staging/production:

### Environment & config
- [ ] `.env` uses **real** secrets and is **NOT** committed (`.gitignore` already excludes `.env`).
- [ ] `ENVIRONMENT=production` set.
- [ ] `DEBUG=false` (enforced in production by `settings.py` validator).
- [ ] `API_KEY` set → protected endpoints require auth. Verify `/chat/completions`, `/usage`, `/notifications` return `401` without it.
- [ ] At least one LLM key configured; ideally the full fallback chain (`nvidia,openrouter,grok`) is populated.
- [ ] `DATABASE_URL` set to the production PostgreSQL and reachable. `OPENAI_API_KEY` set if memory/embeddings are required.
- [ ] Docs check: in production `/docs` and `/redoc` return `404` (disabled by `backend/app.py:52`).

### Health & operations
- [ ] `GET /health` → `200 ok` (liveness).
- [ ] `GET /ready` → `200 ready, orchestrator=initialised` (readiness).
- [ ] Docker healthchecks configured (`docker-compose.yml` and `Dockerfile` both define `HEALTHCHECK` → `/health`).
- [ ] `GET /metrics` returns data after real traffic.
- [ ] `GET /usage` shows per-provider token usage; no provider permanently exhausted at start of day.
- [ ] `GET /notifications` empty or only benign events.

### Resilience & limits
- [ ] Verify failover: disable primary key temporarily → fallback chain answers and `GET /notifications` records the exhaustion event.
- [ ] Verify daily-limit reply: set `MAX_CONVERSATIONS_PER_DAY=1`, send 2 chats → second returns the graceful daily-limit reply and a notification.
- [ ] Load test passes k6 thresholds (`scripts/load_test.js`).
- [ ] Concurrency smoke test: 5 parallel requests all return `200` with unique `X-Request-ID` echoes.

### Runtime & process
- [ ] Run in production mode with gunicorn workers: `docker compose up` uses `scripts/entrypoint.sh`, which starts gunicorn + uvicorn workers when `ENVIRONMENT=production`.
- [ ] Logs: startup lines show environment, chain, and memory-subsystem status; no tracebacks.
- [ ] Graceful shutdown (`SHUTDOWN_TIMEOUT`) disconnects DB cleanly (log `shutting down`).

### Sign-off
- [ ] All rows **1–25** in the [Test Matrix](#11-test-matrix-checklist) pass.
- [ ] `python -m pytest -q` passes (unit + cost-saving).
- [ ] `python -m pytest tests/test_end_to_end.py -q -s` passes against a live server.

---

## 13. Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `POST /chat/completions` returns 500 with `Provider generation failed after N retries` | LLM key invalid or out of credits. Check `scripts/test_provider.py all`. |
| Response is the **daily-limit reply** | All providers exhausted (quota/rate-limit/balance) or `MAX_CONVERSATIONS_PER_DAY` reached. Check `GET /usage` and `GET /notifications`. |
| Chain only has one provider | Other keys are empty — providers without credentials are skipped. Set them in `.env` and restart. |
| Memory recall doesn't work | `OPENAI_API_KEY` missing (embeddings disabled). Check startup log: `Memory subsystem initialized successfully` vs a warning. |
| `/docs` returns 404 | Running with `ENVIRONMENT=production` — docs are intentionally disabled. |
| `401 Unauthorized` | `API_KEY` is set and you're missing/invalidating the `Authorization: Bearer <key>` header on protected routes. |
| e2e tests fail with `ConnectError` | The live server isn't running on `127.0.0.1:8765`. Start it, then re-run. |
| `curl` in PowerShell misbehaves | `curl` is aliased to `Invoke-WebRequest`; use `curl.exe`. |
| DB connection warning at startup | PostgreSQL not reachable; memory persistence will be unavailable until fixed. |
