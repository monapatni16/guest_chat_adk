# main.py
import os
import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from db import SessionLocal, init_db, GuestSession, Message
from agent_def import build_agent
from dotenv import load_dotenv

load_dotenv()

init_db()
app = FastAPI(title="ADK Guest Chat")

app.mount("/static", StaticFiles(directory="static"), name="static")

agent, runner, session_service = build_agent()

class StartResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.post("/guest/start", response_model=StartResponse)
async def start_guest():
    db = SessionLocal()
    try:
        session_id = str(uuid.uuid4())
        guest = GuestSession(session_id=session_id)
        db.add(guest)
        db.commit()
        db.refresh(guest)

        # Create ADK session for this guest
        # API for session_service may vary by ADK version; adapt if needed.
        await session_service.create_session(app_name=runner.app_name, user_id=session_id, session_id=session_id)

        return {"session_id": session_id}
    finally:
        db.close()

@app.post("/guest/{session_id}/message", response_model=ChatResponse)
async def chat(session_id: str, payload: ChatRequest):
    db = SessionLocal()
    try:
        guest = db.query(GuestSession).filter(GuestSession.session_id == session_id).first()
        if not guest:
            raise HTTPException(status_code=404, detail="session not found")

        user_msg = Message(guest_id=guest.id, role="user", content=payload.message)
        db.add(user_msg)
        db.commit()

        try:
            from google.genai import types as genai_types
        except Exception:
            genai_types = None

        if genai_types:
            content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=payload.message)]
            )
        else:
            content = payload.message

        # Ensure session exists
        adk_session = await session_service.get_session(app_name=runner.app_name, user_id=session_id, session_id=session_id)
        if adk_session is None:
            adk_session = await session_service.create_session(app_name=runner.app_name, user_id=session_id, session_id=session_id)

        events = runner.run_async(user_id=session_id, session_id=adk_session.id, new_message=content)

        assistant_text = None
        async for ev in events:
            try:
                if hasattr(ev, 'content') and getattr(ev, 'content'):
                    if hasattr(ev.content, "parts") and ev.content.parts:
                        assistant_text = ev.content.parts[0].text
                payload = getattr(ev, 'payload', None)
                if payload:
                    assistant_text = getattr(payload, 'text', assistant_text) or assistant_text
                assistant_text = getattr(ev, 'response', assistant_text) or assistant_text
            except Exception:
                pass

        if assistant_text is None:
            assistant_text = "(no response from agent)"

        agent_msg = Message(guest_id=guest.id, role="agent", content=assistant_text)
        db.add(agent_msg)
        db.commit()

        return {"reply": assistant_text, "session_id": session_id}
    finally:
        db.close()

@app.get("/guest/{session_id}/history")
def history(session_id: str):
    db = SessionLocal()
    try:
        guest = db.query(GuestSession).filter(GuestSession.session_id == session_id).first()
        if not guest:
            raise HTTPException(status_code=404, detail="session not found")
        msgs = [
            {"role": m.role, "content": m.content, "ts": m.created_at.isoformat()}
            for m in guest.messages
        ]
        return {"session_id": session_id, "messages": msgs}
    finally:
        db.close()

@app.delete("/guest/{session_id}/clear")
def clear_chat(session_id: str):
    db = SessionLocal()
    try:
        guest = db.query(GuestSession).filter(GuestSession.session_id == session_id).first()
        if not guest:
            raise HTTPException(status_code=404, detail="session not found")
        
        # Delete all messages for this guest
        deleted_count = db.query(Message).filter(Message.guest_id == guest.id).delete()
        db.commit()
        
        return {
            "session_id": session_id,
            "deleted_messages": deleted_count,
            "detail": "Chat history cleared"
        }
    finally:
        db.close()
