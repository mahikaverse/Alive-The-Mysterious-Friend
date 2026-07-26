# How to Run — Alive: The Mysterious Friend

A step-by-step guide to get the project running on your machine.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Docker Desktop** | Latest | https://www.docker.com/products/docker-desktop |
| **Git** | Any | https://git-scm.com |
| **OpenAI API Key** | — | https://platform.openai.com/api-keys |

> Docker is the easiest way. No need to install Python, PostgreSQL, or ChromaDB separately.

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/mahikaverse/Alive-The-Mysterious-Friend.git
cd Alive-The-Mysterious-Friend
```

---

## Step 2: Set Up Environment Variables

Copy the example env file:

```bash
cp .env.example .env
```

Open `.env` and fill in your **OpenAI API key**:

```
OPENAI_API_KEY=sk-your-key-here
```

> You need an OpenAI account with credits. Get a key at https://platform.openai.com/api-keys

---

## Step 3: Run with Docker (Recommended)

```bash
docker compose up --build
```

This starts **two containers**:
- **Alive API** → http://localhost:8000
- **PostgreSQL** → localhost:5432

Wait for the logs to show:
```
alive-1  | Memory subsystem initialized successfully
alive-1  | Uvicorn running on http://0.0.0.0:8000
```

---

## Step 4: Verify It's Running

Open your browser and go to:

| URL | What it shows |
|-----|---------------|
| http://localhost:8000/health | Health check — should show `"status": "ok"` |
| http://localhost:8000/ready | Readiness check — should show `"status": "ready"` |
| http://localhost:8000/docs | **Swagger UI** — interactive API docs |
| http://localhost:8000/metrics | Request metrics and latency stats |

---

## Step 5: Test the Chat Endpoint

### Option A: Use Swagger UI (Easiest)

1. Go to http://localhost:8000/docs
2. Click on `POST /chat/completions`
3. Click **Try it out**
4. Paste this body:

```json
{
    "model": "alive-v1",
    "messages": [
        {"role": "user", "content": "Hello! Who are you?"}
    ]
}
```

5. Click **Execute**
6. You should get a response from Alive with personality!

### Option B: Use curl

```bash
curl -X POST http://localhost:8000/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"alive-v1\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}"
```

### Option C: Use Python

```python
import requests

response = requests.post(
    "http://localhost:8000/chat/completions",
    json={
        "model": "alive-v1",
        "messages": [
            {"role": "user", "content": "Hey, what's your name?"}
        ]
    }
)

print(response.json())
```

---

## Step 6: Test Memory (The Cool Part!)

Send multiple messages and Alive will **remember** things:

```json
{"model": "alive-v1", "messages": [
    {"role": "user", "content": "My name is Rahul and I love cricket"}
]}
```

Then in a new request:

```json
{"model": "alive-v1", "messages": [
    {"role": "user", "content": "What do you remember about me?"}
]}
```

Alive should recall your name and interest!

---

## Stopping the Server

```bash
docker compose down
```

To also delete the database data:

```bash
docker compose down -v
```

---

## Running Locally (Without Docker)

If you prefer to run without Docker:

### 1. Install Python 3.11+

### 2. Create virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install chromadb
```

### 4. Set up PostgreSQL

You need a running PostgreSQL instance with:
- Database: `alive`
- User: `alive`
- Password: `alive`
- Port: `5432`

Update `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://alive:alive@localhost:5432/alive
```

### 5. Run the server

```bash
uvicorn backend.main:app --reload
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `insufficient_quota` error | Your OpenAI API key has no credits. Add credits at https://platform.openai.com/billing |
| `ModuleNotFoundError: chromadb` | Run `pip install chromadb` |
| Port 8000 already in use | Stop the other process or change `PORT` in `.env` |
| Database connection failed | Make sure PostgreSQL is running (Docker or local) |
| Docker build fails | Run `docker compose down` first, then `docker compose up --build` |

---

## Project Structure

```
Alive-The-Mysterious-Friend/
├── backend/
│   ├── api/            # FastAPI routes and middleware
│   ├── config/         # Settings and logging
│   ├── controllers/    # Orchestrator pipeline
│   ├── core/           # LLM, prompts, identity
│   ├── behaviour/      # Emotion, relationships, life sim
│   ├── memory/         # Memory system (Person 3)
│   ├── database/       # PostgreSQL ORM
│   ├── models/         # Pydantic schemas
│   ├── prompts/        # AI prompt templates
│   └── utils/          # Logging, metrics
├── alembic/            # Database migrations
├── tests/              # Test suite
├── docker-compose.yml  # Docker setup
├── Dockerfile          # Container build
└── .env                # Your config (DO NOT COMMIT)
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/ready` | Readiness check |
| `GET` | `/metrics` | Request metrics |
| `POST` | `/chat/completions` | Chat with Alive (OpenAI-compatible) |

---

## Need Help?

Contact the team or open an issue at:
https://github.com/mahikaverse/Alive-The-Mysterious-Friend/issues
