import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import agent_tools
from copilot_agent import CopilotEngine

app = FastAPI(title="Asset Intelligence Copilot", version="1.0.0")

engine = CopilotEngine()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    answer: str
    visual_type: Optional[str] = None
    visual_data: Optional[Any] = None
    citations: List[str] = []
    a2ui: Optional[Dict[str, Any]] = None
    context_meta: Optional[Dict[str, Any]] = None

@app.get("/api/users")
def get_users():
    users = agent_tools.execute_query("SELECT user_id, name, role, team_id FROM users ORDER BY name")
    return {"users": users}

@app.get("/api/areas")
def get_areas():
    areas = agent_tools.execute_query("SELECT area_id, name, team_id, center_lat, center_lon FROM areas ORDER BY name")
    return {"areas": areas}

@app.get("/api/stats")
def get_field_stats():
    wells_count = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM wells")[0]["cnt"]
    insp_count = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM inspections")[0]["cnt"]
    maint_count = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM maintenance")[0]["cnt"]
    reports_count = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM maintenance_reports")[0]["cnt"]
    spill_count = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM inspections WHERE spill_detected = 1")[0]["cnt"]
    
    return {
        "wells": wells_count,
        "inspections": insp_count,
        "maintenance_jobs": maint_count,
        "reports": reports_count,
        "spills_detected": spill_count,
        "current_date": "16 Oct 2026"
    }

@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    
    # Retrieve conversation context (either passed from client or fetched from DB before saving new message)
    history = req.history
    if history is None:
        raw_hist = agent_tools.get_user_chat_history(req.user_id, limit=8)
        history = [{"role": h["role"], "content": h["content"]} for h in raw_hist]

    # Save user message to chat history
    agent_tools.save_chat_message(user_id=req.user_id, role="user", content=req.message)

    # Process query with copilot engine with conversation context
    res = engine.handle_query(user_id=req.user_id, question=req.message, history=history)

    # Save copilot response to chat history
    agent_tools.save_chat_message(
        user_id=req.user_id,
        role="assistant",
        content=res["answer"],
        visual_type=res.get("visual_type"),
        visual_data=res.get("visual_data")
    )

    return ChatResponse(
        answer=res["answer"],
        visual_type=res.get("visual_type"),
        visual_data=res.get("visual_data"),
        citations=res.get("citations") or [],
        a2ui=res.get("a2ui"),
        context_meta=res.get("context_meta")
    )

@app.get("/api/history")
def get_history(user_id: str):
    history = agent_tools.get_user_chat_history(user_id, limit=20)
    for h in history:
        if h.get("visual_data_json"):
            try:
                h["visual_data"] = json.loads(h["visual_data_json"])
            except Exception:
                h["visual_data"] = None
    return {"history": history}

# Serve static frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
