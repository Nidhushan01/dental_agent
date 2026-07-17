"""FastAPI backend for dental web agent.

Endpoints:
    GET  /                 - Serve chat widget
    POST /api/chat         - Text chat pipeline
    POST /api/chat/voice   - Voice chat pipeline (upload audio, transcribe, then process)
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Literal
import os
import tempfile
import uvicorn

from db.db import init_db, SessionLocal
from db.models import Appointment
from hermes_client import call_hermes
from tools.appointments import (
    check_availability,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
)
from voice.stt import transcribe as transcribe_audio
from voice.tts import synthesize

# Initialize database
init_db()

app = FastAPI(title="Dental Web Agent")

# Serve static files (widget UI, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# Data Models
# ============================================================================

class ChatRequest(BaseModel):
    """User chat message."""
    text: str
    mode: Literal["appointments", "faq"] = "appointments"
    context: list = None  # Optional conversation history


APPOINTMENT_TOOLS = {
    "check_availability",
    "book_appointment",
    "reschedule_appointment",
    "cancel_appointment",
}


def _compose_reply(mode: str, llm_result: dict) -> tuple[str, str | None]:
    """Build final text + optional voice URL based on mode and selected tool."""
    tool_name = llm_result.get("tool_name")
    tool_result = llm_result.get("tool_result") or {}
    assistant_reply = llm_result.get("assistant_reply", "")

    reply_text = assistant_reply or "I couldn't generate a response."

    if tool_name in APPOINTMENT_TOOLS:
        if isinstance(tool_result, dict) and tool_result.get("message"):
            reply_text = str(tool_result["message"])

    voice_url = None
    if mode == "faq" or tool_name == "get_faq":
        try:
            voice_url = synthesize(reply_text)
        except Exception as exc:
            print(f"Warning: TTS generation failed: {exc}")

    return reply_text, voice_url


# ============================================================================
# Routes
# ============================================================================

@app.get("/")
async def serve_widget():
    """Serve the main chat widget HTML."""
    return FileResponse("static/index.html")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Text chat endpoint: Hermes decides tool-use, backend executes and returns response."""
    try:
        user_text = request.text.strip()
        if not user_text:
            return JSONResponse(status_code=400, content={"error": "Message cannot be empty"})

        result = call_hermes(user_text, context=request.context or [])
        if not result["success"]:
            return JSONResponse(status_code=500, content={"error": result.get("error", "LLM error")})

        reply_text, voice_url = _compose_reply(request.mode, result)
        payload = {
            "reply_text": reply_text,
            "tool_used": result.get("tool_name"),
            "tool_result": result.get("tool_result"),
        }
        if voice_url:
            payload["voice_url"] = voice_url

        return JSONResponse(content=payload)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/chat/voice")
async def chat_voice(file: UploadFile = File(...), mode: str = Form("appointments")):
    """Voice chat endpoint: audio upload -> Whisper STT -> Hermes/tool pipeline."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
            contents = await file.read()
            f.write(contents)
            temp_path = f.name

        transcribed_text = transcribe_audio(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        request_mode = "faq" if str(mode).lower() == "faq" else "appointments"
        result = call_hermes(transcribed_text, context=[])
        if not result["success"]:
            return JSONResponse(status_code=500, content={"error": result.get("error", "LLM error")})

        reply_text, voice_url = _compose_reply(request_mode, result)
        payload = {
            "transcribed_text": transcribed_text,
            "reply_text": reply_text,
            "tool_used": result.get("tool_name"),
            "tool_result": result.get("tool_result"),
        }
        if voice_url:
            payload["voice_url"] = voice_url

        return JSONResponse(content=payload)
    except Exception as e:
        print(f"Voice chat error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ---------------------------------------------------------------------------
# Direct appointment endpoints (called from the Appointments UI)
# ---------------------------------------------------------------------------


@app.post("/api/appointments/check")
async def api_check_availability(payload: dict):
    """Check availability for a date (and optional time).

    Expected JSON: { "date": "YYYY-MM-DD", "time": "HH:MM" } (time optional)
    """
    date = payload.get("date")
    time = payload.get("time")
    if not date:
        return JSONResponse(status_code=400, content={"error": "Missing 'date' in request"})
    try:
        result = check_availability(date, time)
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/appointments/book")
async def api_book_appointment(payload: dict):
    """Book a new appointment.

    Expected JSON: { "name": "Alice", "date": "YYYY-MM-DD", "time": "HH:MM", "service": "cleaning" }
    """
    name = payload.get("name")
    date = payload.get("date")
    time = payload.get("time")
    service = payload.get("service")
    if not all([name, date, time, service]):
        return JSONResponse(status_code=400, content={"error": "Missing required fields: name, date, time, service"})
    try:
        result = book_appointment(name, date, time, service)
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/appointments/reschedule")
async def api_reschedule_appointment(payload: dict):
    """Reschedule an existing appointment.

    Expected JSON: { "appointment_id": 1, "new_date": "YYYY-MM-DD", "new_time": "HH:MM" }
    """
    appt_id = payload.get("appointment_id")
    new_date = payload.get("new_date")
    new_time = payload.get("new_time")
    if not all([appt_id, new_date, new_time]):
        return JSONResponse(status_code=400, content={"error": "Missing required fields: appointment_id, new_date, new_time"})
    try:
        result = reschedule_appointment(int(appt_id), new_date, new_time)
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/appointments/cancel")
async def api_cancel_appointment(payload: dict):
    """Cancel an appointment.

    Expected JSON: { "appointment_id": 1 }
    """
    appt_id = payload.get("appointment_id")
    if not appt_id:
        return JSONResponse(status_code=400, content={"error": "Missing 'appointment_id'"})
    try:
        result = cancel_appointment(int(appt_id))
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/appointments/scheduled")
async def api_scheduled_appointments():
    """Return all scheduled appointments ordered by date and time."""
    session = SessionLocal()
    try:
        appointments = (
            session.query(Appointment)
            .filter(Appointment.status == "confirmed")
            .order_by(Appointment.date.asc(), Appointment.time.asc())
            .all()
        )

        result = [
            {
                "id": appt.id,
                "name": appt.name,
                "date": appt.date.isoformat() if appt.date else None,
                "time": appt.time.strftime("%H:%M") if appt.time else None,
                "service": appt.service,
                "status": appt.status,
            }
            for appt in appointments
        ]

        return JSONResponse(content={"success": True, "count": len(result), "appointments": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "Dental Web Agent"}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
