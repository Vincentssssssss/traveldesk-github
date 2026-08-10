import os
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from graph.travel_graph import get_compiled_graph
from agents.llm_provider import is_demo_mode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    logger.info("Compiling LangGraph travel desk graph...")
    _graph = get_compiled_graph()
    logger.info("Graph ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="TravelDesk AI",
    description="AI-powered corporate travel desk support platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    customer_name: str = "Traveler"
    language: str = "zh"


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    language: str
    response_type: str
    intent: Optional[str]
    confidence: float
    escalated: bool
    escalation_id: Optional[str]
    search_results: Optional[List[Dict[str, Any]]]
    knowledge_results: Optional[List[Dict[str, Any]]]
    agent_path: List[str]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok", "service": "TravelDesk AI v1.0", "demo_mode": is_demo_mode()}


@app.get("/api/demo-status")
async def demo_status():
    return {"demo_mode": is_demo_mode()}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not _graph:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    conversation_id = req.conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": conversation_id}}

    # Current product mode is Chinese-first; all sessions run in zh.
    language = "zh"

    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "conversation_id": conversation_id,
        "customer_name": req.customer_name,
        "language": language,
        "intent": None,
        "sub_intent": None,
        "confidence": 0.0,
        "search_results": None,
        "knowledge_results": None,
        "policy_result": None,
        "escalated": False,
        "escalation_id": None,
        "escalation_reason": None,
        "final_response": None,
        "response_type": "text",
    }

    try:
        # Track which nodes were visited
        agent_path = []
        final_state = None

        async for event in _graph.astream_events(initial_state, config=config, version="v2"):
            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in (
                "supervisor", "booking", "knowledge", "escalation", "customer_interaction"
            ):
                agent_path.append(name)

            if kind == "on_chain_end" and name == "LangGraph":
                final_state = event.get("data", {}).get("output", {})

        if final_state is None:
            # Fallback: run synchronously
            final_state = _graph.invoke(initial_state, config=config)

    except Exception as e:
        logger.exception(f"Graph execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    response_text = final_state.get("final_response") or "I'm here to help with your travel needs."
    if language == "zh" and not final_state.get("final_response"):
        response_text = "我可以帮您处理差旅相关问题。"
    escalation_data = None
    if final_state.get("response_type") == "escalation" and final_state.get("knowledge_results"):
        escalation_data = final_state["knowledge_results"]

    return ChatResponse(
        conversation_id=conversation_id,
        response=response_text,
        language=final_state.get("language", language),
        response_type=final_state.get("response_type", "text"),
        intent=final_state.get("intent"),
        confidence=final_state.get("confidence", 0.0),
        escalated=final_state.get("escalated", False),
        escalation_id=final_state.get("escalation_id"),
        search_results=final_state.get("search_results"),
        knowledge_results=escalation_data or final_state.get("knowledge_results"),
        agent_path=agent_path or ["supervisor"],
    )


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history from in-memory checkpointer."""
    config = {"configurable": {"thread_id": conversation_id}}
    try:
        state = _graph.get_state(config)
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = state.values.get("messages", [])
        history = [
            {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
            for m in messages
        ]
        return {"conversation_id": conversation_id, "messages": history}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))
