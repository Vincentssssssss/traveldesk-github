# Architecture Deep Dive

This document covers the internal design decisions, data flow, and extension points for TravelDesk AI.

---

## LangGraph State Machine

### State Object

Every node in the graph reads from and writes to a single `TravelDeskState` TypedDict. No agent communicates directly with another — all coordination happens through shared state.

```python
class TravelDeskState(TypedDict):
    messages: Annotated[list, add_messages]   # Full conversation history
    conversation_id: str
    customer_name: str

    intent: Optional[str]          # Classified intent from supervisor
    sub_intent: Optional[str]
    confidence: float              # Classification confidence (0.0–1.0)

    search_results: Optional[List[Dict]]    # Flights or hotels from booking agent
    knowledge_results: Optional[List[Dict]] # FAQs/policies from knowledge agent
    policy_result: Optional[Dict]

    escalated: bool
    escalation_id: Optional[str]
    escalation_reason: Optional[str]

    final_response: Optional[str]  # Customer-facing text set by any agent
    response_type: Optional[str]   # text | flights | hotels | policy | escalation
```

### Routing Logic

```
supervisor
    ├── intent in {flight_search, hotel_search, cab_request}  → booking
    ├── intent in {policy_query, general_faq, expense_query,  → knowledge
    │             visa_inquiry, cancellation, refund_inquiry,
    │             itinerary_query}
    ├── intent in {complaint, emergency} OR escalated=True    → escalation
    └── fallback                                              → customer_interaction

booking
    ├── final_response already set (cab text)  → END
    └── flights or hotels found                → customer_interaction

knowledge  → customer_interaction
escalation → END                  (response fully set by escalation agent)
customer_interaction → END
```

---

## Demo Mode

When `ANTHROPIC_API_KEY` is absent or is the placeholder value, each agent's `_get_llm()` factory returns a `MockLLM` instance instead of `ChatAnthropic`. The `MockLLM` implements the same `.invoke(messages)` interface, so the agent code is unchanged.

```
Real mode:  agent → ChatAnthropic.invoke() → Claude API → response
Demo mode:  agent → MockLLM.invoke()       → keyword logic → response
```

The full LangGraph graph executes identically in both modes — routing, state management, and agent sequencing are not affected.

---

## Knowledge Retrieval (MVP)

The MVP uses lightweight keyword search. The production path (Phase 3) replaces this with a Pinecone RAG pipeline.

### MVP flow
```
user query
    → search_faqs(query)      # Keyword score across question + answer + keywords fields
    → search_policies(query)  # Keyword score across title + description + category
    → top-3 results assembled as context
    → LLM synthesises answer from context only
```

### Production RAG flow (Phase 3 target)
```
user query
    → Query expansion (Claude)
    → Dense retrieval (Pinecone text-embedding-3-large)
    → Sparse retrieval (Elasticsearch BM25)
    → Hybrid reranking (Cohere Rerank v3)
    → Top-5 chunks with citations
    → Hallucination gate (confidence check)
    → LLM response grounded in retrieved chunks
```

---

## Mock GDS Data

`backend/data/mock_flights.json` and `mock_hotels.json` serve as stand-ins for Amadeus/Sabre GDS responses. Each record includes a `policy_compliant` flag and optional `policy_note` that the UI renders as warning badges.

### Adding real GDS integration (Phase 2)

1. Create `backend/tools/amadeus_client.py` wrapping the Amadeus REST SDK
2. Replace `search_flights()` in `tools/flight_search.py` with an Amadeus call
3. Map the GDS response schema to the existing `search_results` dict structure
4. Set `policy_compliant` by calling `policy_agent_node()` inline on each result

---

## Escalation Priority Matrix

| Intent | Priority | ETA | Assigned Team |
|---|---|---|---|
| `emergency` | P0 | 15 minutes | Emergency Response Team |
| `complaint` | P1 | 30 minutes | Senior Travel Specialist |
| `refund_inquiry` | P2 | 1 hour | Billing Specialist |
| `visa_inquiry` | P2 | 2 hours | Visa & Documentation Specialist |
| Any other | P3 | 4 hours | Travel Specialist |

---

## Conversation Continuity

LangGraph's `MemorySaver` checkpointer stores the full graph state keyed by `thread_id` (= `conversation_id`). Each `/api/chat` call passes the same `conversation_id` in the config, so the graph resumes from exactly where it left off — including all previous messages and state fields.

For production, swap `MemorySaver` for `AsyncPostgresSaver`:

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

checkpointer = AsyncPostgresSaver.from_conn_string(os.environ["DATABASE_URL"])
graph = build_graph().compile(checkpointer=checkpointer)
```

---

## Adding a New Agent

1. Create `backend/agents/my_agent.py` with a `my_agent_node(state) -> dict` function
2. Register the node in `graph/travel_graph.py`:
   ```python
   builder.add_node("my_agent", my_agent_node)
   ```
3. Add routing logic in `route_from_supervisor()` or add a new edge from an existing node
4. Export from `agents/__init__.py`

No changes to `main.py` or the frontend are needed for backend-only agents.

---

## Extending the Frontend

The frontend is a single `frontend/index.html` file using Tailwind CSS (CDN) and vanilla JavaScript. To add a new card type:

1. Add a new `response_type` value in the backend response
2. Add a `buildMyCard(data)` function in `index.html`
3. Call it in `appendAIMessage()` alongside the existing `buildFlightCards` / `buildHotelCards` checks

---

## Environment Variables

| Variable | Used by | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | All agents | Empty = Demo Mode |
| `ENVIRONMENT` | `main.py` | `development` enables auto-reload |
| `LOG_LEVEL` | `main.py` | Python logging level |
| `DATABASE_URL` | _(Phase 2)_ | PostgreSQL for persistent checkpointing |
| `PINECONE_API_KEY` | _(Phase 3)_ | Vector store for production RAG |
