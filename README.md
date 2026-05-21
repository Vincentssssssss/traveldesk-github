# TravelDesk AI — Corporate Travel Support Platform

> An AI-powered customer support system for corporate travel desks, built on **LangGraph** multi-agent orchestration and **Anthropic Claude**.

---

## Overview

TravelDesk AI automates corporate travel support through a team of specialized AI agents that collaborate to handle flight bookings, hotel search, travel policy queries, visa assistance, cancellations, and escalations — all from a single chat interface.

The system runs fully in **Demo Mode** without an API key, using deterministic mock responses and realistic mock GDS data. Add an Anthropic API key to switch to live Claude AI responses instantly.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LANGGRAPH GRAPH                       │
│                                                         │
│  User Message                                           │
│       │                                                 │
│       ▼                                                 │
│  ┌─────────────┐                                        │
│  │  Supervisor  │  ← Intent classification + routing    │
│  └──────┬──────┘                                        │
│         │                                               │
│    ┌────┴────┬──────────┬────────────┐                  │
│    ▼         ▼          ▼            ▼                  │
│  ┌───────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Booking│ │Knowledge│ │Escalation│ │   Customer   │  │
│  │ Agent │ │  Agent  │ │  Agent   │ │  Interaction │  │
│  └───┬───┘ └────┬────┘ └────┬─────┘ │    Agent     │  │
│      │          │           │        └──────────────┘  │
│      └──────────┴───────────┘                          │
│                      │                                  │
│                      ▼                                  │
│             Customer Interaction Agent                  │
│             (final response formatting)                 │
└─────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Model | Responsibility |
|---|---|---|
| **Supervisor** | Claude Haiku | Intent classification, entity extraction, routing |
| **Booking Agent** | _(no LLM)_ | Flight & hotel search against GDS mock data |
| **Knowledge Agent** | Claude Haiku | FAQ & policy retrieval + RAG synthesis |
| **Escalation Agent** | Claude Haiku | Ticket creation, human handoff, priority routing |
| **Customer Interaction** | Claude Sonnet | Final response formatting and tone calibration |

### Graph Routing

```
supervisor → booking           → customer_interaction → END
supervisor → knowledge         → customer_interaction → END
supervisor → escalation                              → END
supervisor → customer_interaction                    → END
```

---

## Project Structure

```
traveldesk/
├── backend/
│   ├── main.py                    # FastAPI application, /api/chat endpoint
│   ├── requirements.txt           # Python dependencies
│   ├── graph/
│   │   └── travel_graph.py        # LangGraph state machine (compile + run)
│   ├── agents/
│   │   ├── supervisor.py          # Intent classifier and router
│   │   ├── booking.py             # Flight and hotel search
│   │   ├── knowledge.py           # FAQ and policy retrieval
│   │   ├── escalation.py          # Escalation ticket creation
│   │   ├── customer_interaction.py# Final response generation
│   │   └── mock_llm.py            # Demo mode: keyword-based mock responses
│   ├── tools/
│   │   ├── flight_search.py       # Mock GDS flight search
│   │   ├── hotel_search.py        # Mock GDS hotel search
│   │   └── knowledge_base.py      # FAQ + policy keyword retrieval
│   ├── models/
│   │   └── state.py               # LangGraph TypedDict state definition
│   └── data/
│       ├── policies.json          # 8 corporate travel policy rules
│       ├── faqs.json              # 10 travel desk FAQs
│       ├── mock_flights.json      # 7 sample flight records
│       └── mock_hotels.json       # 6 sample hotel records
└── frontend/
    └── index.html                 # Chat UI (Tailwind CSS, vanilla JS)
```

---

## Quickstart

### Prerequisites

- Python 3.9+
- An Anthropic API key _(optional — runs in Demo Mode without one)_

### 1. Clone and set up

```bash
git clone https://github.com/writersrinivasan/traveldesk.git
cd traveldesk

python3 -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

**macOS note:** If you see a `UnicodeDecodeError` on the venv activation, delete the macOS AppleDouble artifact and retry:

```bash
rm venv/lib/python3.9/site-packages/._distutils-precedence.pth
source venv/bin/activate
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Leave the placeholder value to run in **Demo Mode** (no API calls, mock responses).

### 3. Start the server

```bash
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open the app

Navigate to **[http://localhost:8000](http://localhost:8000)**

---

## Usage

### Chat Interface

Enter your name in the welcome dialog, then type naturally:

| What to ask | Intent handled |
|---|---|
| `I need a flight from New York to Los Angeles next week` | Flight search → booking cards |
| `Find me a hotel in Los Angeles for 3 nights` | Hotel search → hotel cards with policy badges |
| `What is the business class travel policy?` | Policy query → knowledge retrieval |
| `How do I claim travel expenses?` | FAQ → expense guidance |
| `I need a visa for India` | Visa inquiry → requirements + timeline |
| `I want to cancel my trip and get a refund` | Cancellation → refund process |
| `My flight was cancelled, I'm stranded!` | Emergency → escalation ticket (ESC-XXXXXXXX) |

### Agent Pipeline Sidebar

The left sidebar visualises which agents ran for each request. Green dots indicate active nodes. The header shows the routing path (e.g., `supervisor → booking → customer_interaction`).

### Demo Mode Banner

When running without an API key, an amber banner appears at the top. All agents run through the full LangGraph graph — only the LLM calls are replaced with keyword-based mock logic.

---

## API Reference

### `POST /api/chat`

Send a message and receive a structured response.

**Request body:**
```json
{
  "message": "I need a flight from New York to Los Angeles",
  "conversation_id": "optional-uuid-for-continuity",
  "customer_name": "Sarah Johnson"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "response": "I found 3 flight options for you...",
  "response_type": "flights",
  "intent": "flight_search",
  "confidence": 0.85,
  "escalated": false,
  "escalation_id": null,
  "search_results": [...],
  "knowledge_results": null,
  "agent_path": ["supervisor", "booking", "customer_interaction"]
}
```

**Response types:**

| `response_type` | UI behaviour |
|---|---|
| `text` | Plain text message bubble |
| `flights` | Flight result cards rendered below the message |
| `hotels` | Hotel result cards rendered below the message |
| `policy` | Text response sourced from policy knowledge base |
| `escalation` | Escalation ticket card with priority, team, ETA |

### `GET /health`

```json
{ "status": "ok", "service": "TravelDesk AI MVP", "demo_mode": true }
```

### `GET /api/demo-status`

```json
{ "demo_mode": true }
```

### `GET /api/conversations/{conversation_id}`

Returns full conversation history for a given session.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) 0.6+ |
| LLM Provider | [Anthropic Claude](https://www.anthropic.com) (Haiku 4.5 + Sonnet 4.6) |
| Backend Framework | [FastAPI](https://fastapi.tiangolo.com) |
| ASGI Server | [Uvicorn](https://www.uvicorn.org) |
| Frontend | Vanilla JS + [Tailwind CSS](https://tailwindcss.com) (CDN) |
| State Checkpointing | LangGraph `MemorySaver` (in-memory; swap for `PostgresSaver` in production) |

---

## Demo Mode vs. Live Mode

| Feature | Demo Mode | Live Mode |
|---|---|---|
| API key required | No | Yes |
| Intent classification | Keyword matching | Claude Haiku |
| Knowledge answers | Pre-written responses | Claude Haiku + retrieved context |
| Escalation messages | Template-based | Claude Haiku |
| Customer-facing response | Template | Claude Sonnet |
| Flight / hotel data | Mock JSON | Mock JSON (Phase 1) |
| Full LangGraph execution | Yes | Yes |
| Agent pipeline visualization | Yes | Yes |

---

## Roadmap

### Phase 1 — MVP (current)
- [x] LangGraph 5-agent orchestration
- [x] Demo mode (no API key required)
- [x] Flight and hotel search (mock GDS)
- [x] Policy and FAQ knowledge retrieval
- [x] Escalation ticket creation
- [x] Web chat UI with agent pipeline visualizer
- [x] Multi-intent routing with confidence scoring

### Phase 2 — Core Platform
- [ ] Real GDS integration (Amadeus REST API)
- [ ] PostgreSQL state persistence (swap MemorySaver)
- [ ] Itinerary Management Agent
- [ ] Billing & Refund Agent
- [ ] Manager approval workflow (interrupt/resume)
- [ ] Multi-language support
- [ ] WhatsApp and email channel adapters

### Phase 3 — Intelligence Layer
- [ ] Sentiment analysis and proactive escalation
- [ ] Real-time disruption handling (airline webhook → re-book)
- [ ] RAG pipeline with Pinecone (replace keyword search)
- [ ] Voice channel (Whisper + ElevenLabs)
- [ ] Analytics & Reporting Agent

### Phase 4 — Enterprise Scale
- [ ] Multi-tenant support
- [ ] Concur / SAP Travel deep integration
- [ ] Duty of care (real-time traveler location)
- [ ] SOC 2 Type II compliance
- [ ] GDPR right-to-erasure automation

---

## Configuration Reference

| Environment Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic API key. Leave empty for Demo Mode. |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.
