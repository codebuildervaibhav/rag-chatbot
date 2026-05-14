# AI Chatbot — Full-Stack Conversational AI with Hybrid Architecture

A full-stack AI chatbot with real-time conversation insight extraction (intent + sentiment), a persistent chat history sidebar, and a **switchable hybrid AI backend** — toggle between a fully local offline stack and a cloud-powered stack from within the chat interface.

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│  User Message  +  mode toggle (🐾 Local | ☁️ Cloud)              │
│                                                                   │
│   LOCAL MODE                        CLOUD MODE                    │
│   ──────────                        ──────────                    │
│   Ollama / Murphy (Gemma3)          OpenAI / Casper (GPT-4o-mini) │
│     → Conversational reply           → Conversational reply       │
│                                                                   │
│   NLP Service                       OpenAI JSON Mode              │
│   (NLTK + VADER)                    → Intent + Sentiment          │
│     → Intent + Sentiment                                          │
│                                                                   │
│   Keyword Rules (final fallback — always works offline)           │
│                                                                   │
│   SQLite  →  Chat history persisted per conversation              │
└───────────────────────────────────────────────────────────────────┘
```

### Why two modes?
| | 🐾 Local (Murphy) | ☁️ Cloud (Casper) |
|---|---|---|
| **Chat AI** | Ollama / Gemma3 | GPT-4o-mini |
| **Insight extraction** | NLTK POS + VADER | OpenAI JSON mode |
| **Cost** | Free | OpenAI tokens |
| **Speed** | Depends on hardware | ~500ms API |
| **Internet required** | ❌ No | ✅ Yes |
| **API key required** | ❌ No | ✅ Yes |

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.13+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| Ollama | Latest | Local LLM inference (for Local mode) |
| WSL2 | Any | Run Ollama on Windows (if using WSL) |

---

## Project Structure

```
AI_chatbot/
├── backend/
│   ├── main.py                     # FastAPI application entry point
│   ├── database.py                 # SQLite — conversation + message persistence
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables (create from .env.example)
│   ├── chat_history.db             # Auto-created on first startup
│   ├── routers/
│   │   ├── chat.py                 # POST /api/chat (mode-driven routing)
│   │   └── conversations.py        # GET/DELETE /api/conversations
│   └── services/
│       ├── ollama_service.py       # Ollama communication + Murphy persona
│       ├── openai_service.py       # OpenAI fallback + Casper persona + insight extraction
│       ├── insight_extractor.py    # Routes insights: NLP (local) or OpenAI (cloud)
│       └── nlp_service.py          # NLTK POS tagging + VADER sentiment (local mode)
│
└── frontend/
    ├── src/
    │   ├── App.tsx                 # Root layout (sidebar + chat)
    │   ├── hooks/
    │   │   └── useChatSocket.ts    # Core state: messages, mode, conversations
    │   └── components/
    │       ├── Header.tsx          # Mode-aware LED indicator
    │       ├── ChatInput.tsx       # Textarea + mode toggle pill
    │       ├── ChatView.tsx        # Message list with empty state
    │       ├── Message.tsx         # Bubble + InsightsBadge
    │       └── ConversationSidebar.tsx  # Chat history sidebar
    ├── .env                        # Frontend environment variables
    └── package.json
```

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd AI_chatbot
```

---

### 2. Backend Setup

#### 2a. Create and activate a virtual environment (recommended)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate
```

#### 2b. Install Python dependencies

```powershell
pip install -r requirements.txt
```

#### 2c. Download NLTK data (required for Local mode insight extraction)

```powershell
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"
```

> This downloads two small datasets (~3MB total) to your local NLTK data folder.
> Only needed once per machine.

#### 2d. Configure environment variables

Copy the example and fill in your values:

```powershell
copy .env.example .env
```

Then edit `backend/.env`:

```env
# ── Ollama (Local Mode) ────────────────────────────────────────────
# IP of your Ollama server. If running in WSL, find it with:
#   ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
OLLAMA_BASE_URL=http://172.26.18.7:11434

# The Ollama model to use for chat responses
OLLAMA_MODEL=gemma3:270m

# ── OpenAI (Cloud Mode) ────────────────────────────────────────────
# Your OpenAI API key — required for Cloud mode chat AND insight extraction
# Leave blank to disable Cloud mode (Local mode will still work)
OPENAI_API_KEY=sk-proj-...

# OpenAI model for chat responses and insight extraction
OPENAI_MODEL=gpt-4o-mini
```

#### 2e. Start the backend

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running:
```
http://localhost:8000/api/health  → { "status": "ok" }
http://localhost:8000/docs        → Swagger UI
```

---

### 3. Ollama Setup (for Local Mode)

#### In WSL:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull gemma3:270m

# Start the server (accessible from Windows)
OLLAMA_HOST=0.0.0.0 ollama serve
```

#### Find your WSL IP (update OLLAMA_BASE_URL in .env):

```bash
ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
```

---

### 4. Frontend Setup

```powershell
cd ../frontend
npm install
```

Configure `frontend/.env`:

```env
# URL of the FastAPI backend
VITE_API_BASE_URL=http://localhost:8000
```

Start the dev server:

```powershell
npm run dev
```

The app will be available at: **http://localhost:5173**

---

## Running the Full Stack

Open two terminals:

**Terminal 1 — Backend:**
```powershell
cd backend
.\venv\Scripts\Activate     # if using venv
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

---

## Features

- **🐾 Local Mode** — Fully offline AI chat (Ollama/Gemma3) with NLTK+VADER insight extraction
- **☁️ Cloud Mode** — GPT-4o-mini chat with OpenAI JSON-mode insight extraction
- **Mode Toggle** — Switch between Local and Cloud in real-time from the input bar
- **Mode-aware LED** — Header indicator glows green (local) or blue (cloud)
- **Conversation Insights** — Intent (complaint/query/request/greeting) + Sentiment (positive/neutral/negative) displayed as badges on every AI response
- **Chat History Sidebar** — All conversations persisted to SQLite, grouped by Today/Yesterday/Older
- **Resumable Conversations** — Click any past conversation to reload and continue it
- **Markdown Rendering** — Code blocks with syntax highlighting in AI responses
- **Shift+Enter** — Multiline input support

---

## Environment Variables Reference

### `backend/.env`

| Variable | Required | Default | Description |
|---|---|---|---|
| `OLLAMA_BASE_URL` | For Local mode | `http://172.26.18.7:11434` | Ollama server URL (WSL or local) |
| `OLLAMA_MODEL` | For Local mode | `gemma3:270m` | Ollama model name |
| `OPENAI_API_KEY` | For Cloud mode | _(empty)_ | Your OpenAI API key |
| `OPENAI_MODEL` | For Cloud mode | `gpt-4o-mini` | OpenAI model name |

### `frontend/.env`

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | FastAPI backend URL |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check |
| `POST` | `/api/chat` | Send message, get reply + insights |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get messages for a conversation |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation |

### POST `/api/chat` — Request body

```json
{
  "message": "Hello!",
  "history": [{ "role": "user", "content": "..." }],
  "conversation_id": "uuid-or-null",
  "mode": "local"
}
```

### POST `/api/chat` — Response

```json
{
  "reply": "Hey there! I'm Murphy...",
  "insights": {
    "intent": "greeting",
    "sentiment": "positive"
  },
  "conversation_id": "550e8400-e29b-41d4-...",
  "mode": "local"
}
```

---

## Built With

**Backend:** Python · FastAPI · SQLite · Ollama · OpenAI API · NLTK · VADER

**Frontend:** React · TypeScript · Vite · TailwindCSS · ReactMarkdown

**AI Models:** Gemma3:270m (local) · GPT-4o-mini (cloud)

---

*Built by Vaibhav Singh Rana — AI Developer*
