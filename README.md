# 🦷 Dental Web Agent

A **voice-enabled agentic AI assistant** for dental clinics — delivered as a web chat widget.
Patients can type or speak naturally to book appointments, check availability, reschedule, cancel, and get answers to common dental questions.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Agentic AI** | Hermes LLM autonomously decides which action to take using function-calling |
| 📅 **Appointments** | Book, reschedule, cancel, and check slot availability |
| ❓ **FAQ** | Answers dental questions from a curated knowledge base |
| 🎙️ **Voice Input** | Speak into the browser mic — Whisper transcribes it to text |
| 🔊 **Voice Output** | FAQ answers are read aloud via Google TTS |
| 💬 **Multi-turn Chat** | Maintains conversation context across messages |
| 🐳 **Dockerised** | One command to build and run anywhere |
| ☁️ **Render-ready** | Includes `render.yaml` for one-click cloud deployment |

---

## 🏗️ Architecture

```
Browser (HTML + JS)
    │  text / voice
    ▼
FastAPI Backend (main.py)
    │
    ├── Voice? ──► Whisper STT ──► text
    │
    ├──► Hermes LLM (OpenRouter)
    │         │  decides which tool to call
    │    ┌────┴──────────────────────┐
    │    ▼                           ▼
    │  Appointment Tools          FAQ Tool
    │  (SQLite DB)                (dict lookup)
    │
    ├── FAQ reply? ──► gTTS ──► MP3 audio URL
    │
    └──► JSON response to browser
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn |
| AI / LLM | Hermes (NousResearch) via OpenRouter API |
| Speech-to-Text | OpenAI Whisper (`base` model) |
| Text-to-Speech | Google TTS (`gTTS`) |
| Database | SQLite + SQLAlchemy ORM |
| Audio Processing | FFmpeg + pydub |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Container | Docker (multi-stage build) |
| Cloud Hosting | Render.com |

---

## 📁 Project Structure

```
dental-web-agent/
├── main.py                  # FastAPI app — all API endpoints
├── hermes_client.py         # LLM client — function-calling logic
├── config.py                # Settings loaded from environment variables
├── requirements.txt         # Python dependencies
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Local development setup
├── render.yaml              # Render cloud deployment config
│
├── db/
│   ├── models.py            # SQLAlchemy Appointment model
│   └── db.py                # DB engine, session, init_db()
│
├── tools/
│   ├── appointments.py      # check_availability, book, reschedule, cancel
│   └── faq.py               # FAQ knowledge base + get_faq()
│
├── voice/
│   ├── stt.py               # Whisper speech-to-text wrapper
│   └── tts.py               # gTTS text-to-speech wrapper
│
└── static/
    ├── index.html           # Chat widget UI
    ├── app.js               # Frontend logic (mic, fetch, render)
    └── style.css            # Styling
```

---

## 🚀 Quick Start — Local

### Prerequisites
- Python 3.11+
- FFmpeg installed and on system PATH (`ffmpeg -version` to verify)
- An [OpenRouter](https://openrouter.ai/) account and API key

### 1. Clone the repo

```bash
git clone https://github.com/Nidhushan01/dental_agent.git
cd dental_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=gpt-4o-mini

# Optional (these are the defaults)
DATABASE_URL=sqlite:////tmp/dental.db
STT_MODEL=base
TTS_LANGUAGE=en
```

> Get your free API key at https://openrouter.ai/keys

### 5. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

---

## 🐳 Quick Start — Docker

```bash
# Build and run
docker compose up --build

# Open http://localhost:8000
```

The Docker setup pre-downloads the Whisper model at build time so there's no
delay on first voice request.

---

## ☁️ Deploy to Render

### Option A — Automatic (render.yaml)

1. Fork this repo to your GitHub account
2. Go to [render.com](https://render.com) → **New+ → Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` and configures everything

Then in the Render **Environment** tab, set:
```
OPENROUTER_API_KEY = sk-or-v1-your-key-here
```

### Option B — Manual

| Setting | Value |
|---------|-------|
| Runtime | Docker |
| Dockerfile Path | `./Dockerfile` |
| Health Check Path | `/health` |
| Plan | Free (or Starter for always-on) |

**Environment variables to set in dashboard:**

| Key | Value |
|-----|-------|
| `OPENROUTER_API_KEY` | your key |
| `OPENROUTER_MODEL` | `gpt-4o-mini` |
| `DATABASE_URL` | `sqlite:////tmp/dental.db` |
| `STT_MODEL` | `base` |
| `TTS_LANGUAGE` | `en` |

> ⚠️ **Never** commit your API key to GitHub. Always set secrets via the dashboard.

---

## 📖 API Documentation

The full interactive API docs are available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Endpoints Summary

---

#### `GET /`
Serves the chat widget HTML page.

**Response:** HTML page

---

#### `GET /health`
Health check endpoint (used by Render to confirm the service is alive).

**Response:**
```json
{
  "status": "ok",
  "service": "Dental Web Agent"
}
```

---

#### `POST /api/chat`
Main text chat endpoint. The LLM reads the message, picks a tool, executes it, and returns a human-friendly reply.

**Request Body:**
```json
{
  "text": "I'd like to book an appointment for next Monday at 10am",
  "mode": "appointments",
  "context": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | User's message |
| `mode` | string | ❌ | `"appointments"` (default) or `"faq"` |
| `context` | array | ❌ | Previous messages for multi-turn conversation |

**Response:**
```json
{
  "reply_text": "Your appointment has been booked for Monday July 21st at 10:00 AM!",
  "tool_used": "book_appointment",
  "tool_result": {
    "success": true,
    "appointment_id": 7,
    "message": "Appointment confirmed for John on 2026-07-21 at 10:00"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reply_text` | string | Human-readable response from the LLM |
| `tool_used` | string \| null | Name of the tool the LLM called |
| `tool_result` | object \| null | Raw result from the tool |
| `voice_url` | string | *(FAQ mode only)* URL to the generated MP3 audio |

---

#### `POST /api/chat/voice`
Voice chat endpoint. Accepts an audio file, transcribes it with Whisper, then processes it the same as `/api/chat`.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | audio file | Browser recording (`.webm`, `.mp3`, `.wav`) |
| `mode` | string | `"appointments"` or `"faq"` |

**Response:**
```json
{
  "transcribed_text": "Book me an appointment for tomorrow",
  "reply_text": "I've booked your appointment for tomorrow at 10:00 AM.",
  "tool_used": "book_appointment",
  "tool_result": { ... }
}
```

---

#### `POST /api/appointments/check`
Check slot availability for a specific date.

**Request Body:**
```json
{
  "date": "2026-07-25",
  "time": "10:00"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "available": true,
    "date": "2026-07-25",
    "slots_available": 2
  }
}
```

> Each day has a maximum of **3 appointment slots**.

---

#### `POST /api/appointments/book`
Book a new appointment directly (bypasses LLM).

**Request Body:**
```json
{
  "name": "John Smith",
  "date": "2026-07-25",
  "time": "10:00",
  "service": "cleaning"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "appointment_id": 12,
    "message": "Appointment confirmed for John Smith on 2026-07-25 at 10:00",
    "details": {
      "name": "John Smith",
      "date": "2026-07-25",
      "time": "10:00",
      "service": "cleaning"
    }
  }
}
```

---

#### `POST /api/appointments/reschedule`
Reschedule an existing appointment.

**Request Body:**
```json
{
  "appointment_id": 12,
  "new_date": "2026-07-28",
  "new_time": "14:00"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "message": "Rescheduled from 2026-07-25 10:00:00 to 2026-07-28 14:00",
    "appointment_id": 12
  }
}
```

---

#### `POST /api/appointments/cancel`
Cancel an appointment by ID.

**Request Body:**
```json
{
  "appointment_id": 12
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "message": "Appointment 12 has been cancelled",
    "appointment_id": 12
  }
}
```

---

#### `GET /api/appointments/scheduled`
List all confirmed (non-cancelled) appointments ordered by date and time.

**Response:**
```json
{
  "success": true,
  "count": 2,
  "appointments": [
    {
      "id": 5,
      "name": "Alice",
      "date": "2026-07-21",
      "time": "09:00",
      "service": "checkup",
      "status": "confirmed"
    }
  ]
}
```

---

## 💬 Usage Examples

### Booking an Appointment (Text)
```
User: "I need a checkup appointment for Alice on July 25th at 2pm"

Agent: "I've booked a checkup appointment for Alice on July 25th at 2:00 PM.
        Your appointment ID is 8. See you then! 😊"
```

### Checking Availability (Text)
```
User: "Are there any slots available this Friday?"

Agent: "Yes! Friday July 19th has 2 slots remaining. 
        Would you like me to book one for you?"
```

### FAQ via Voice
```
User speaks: "What are your opening hours?"

Agent replies (text + audio): "We are open Monday to Friday, 9:00 AM to 5:00 PM,
                               and Saturday 10:00 AM to 2:00 PM."
```

### FAQ Topics Supported

| Topic | Example Question |
|-------|-----------------|
| `hours` | "What time do you open?" |
| `insurance` | "Do you accept Delta Dental?" |
| `cost` | "How much is a cleaning?" |
| `post-extraction` | "What should I do after tooth removal?" |
| `root-canal` | "What is a root canal?" |
| `implant` | "How long do implants take?" |
| `braces` | "What braces options do you have?" |

---

## 🔧 Configuration Reference

All configuration is via environment variables (or `.env` file locally):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | *(required)* | Your OpenRouter API key |
| `OPENROUTER_MODEL` | *(required)* | Model ID e.g. `gpt-4o-mini` |
| `DATABASE_URL` | `sqlite:////tmp/dental.db` | SQLAlchemy database URL |
| `STT_MODEL` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium` |
| `TTS_LANGUAGE` | `en` | Language code for gTTS |

---

## 🧪 Running Tests

```bash
# All tests
python test_integration.py
python test_db.py
python test_appointments.py
python test_voice.py
python test_hermes.py
```

---

## 🍴 How to Fork & Customise

### 1. Fork the repo
Click **Fork** on GitHub → clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/dental_agent.git
cd dental_agent
```

### 2. Add your own FAQ answers
Edit `tools/faq.py` — add entries to `FAQ_DATABASE`:
```python
FAQ_DATABASE = {
    "parking": "Free parking is available in our car park on the east side.",
    "emergency": "For dental emergencies call us at 0117894561, we have same-day slots.",
    # ... existing entries
}
```

### 3. Change the LLM model
In `.env` or Render dashboard:
```env
OPENROUTER_MODEL=anthropic/claude-3-haiku   # cheaper, faster
OPENROUTER_MODEL=openai/gpt-4o              # more capable
```
Browse all models at https://openrouter.ai/models

### 4. Change the Whisper model size

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 39 MB | ⚡⚡⚡ | Good |
| `base` | 74 MB | ⚡⚡ | Better ← default |
| `small` | 244 MB | ⚡ | Great |
| `medium` | 769 MB | 🐢 | Excellent |

Update in `.env`:
```env
STT_MODEL=small
```
Also update the Whisper model download URL in `Dockerfile` if deploying via Docker.

### 5. Add a new tool (Extend the Agent)

**Step 1** — Write the function in `tools/`:
```python
# tools/reminders.py
def send_reminder(appointment_id: int, phone: str) -> dict:
    # ... your logic
    return {"success": True, "message": "Reminder sent"}
```

**Step 2** — Register it in `hermes_client.py`:
```python
TOOLS = [
    # ... existing tools ...
    {
        "type": "function",
        "name": "send_reminder",
        "description": "Send an SMS reminder for an upcoming appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer"},
                "phone": {"type": "string"}
            },
            "required": ["appointment_id", "phone"]
        }
    }
]
```

**Step 3** — Handle it in `_execute_tool()`:
```python
elif tool_name == "send_reminder":
    return send_reminder(arguments["appointment_id"], arguments["phone"])
```

The LLM will now automatically call this tool when appropriate.

---

## 🐛 Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `OPENROUTER_API_KEY not set` | Missing env var | Add to `.env` or Render dashboard |
| `unable to open database file` | DB directory not writable | Set `DATABASE_URL=sqlite:////tmp/dental.db` |
| `Transcription failed` | FFmpeg not found | Install FFmpeg: `apt install ffmpeg` / `brew install ffmpeg` |
| Mic not working | Browser security | Must be on `https://` in production (not `http://`) |
| Slow first request | Render free tier cold start | Wait ~30s or upgrade to Starter plan |
| `SHA256 mismatch` on Whisper | Model file corrupted | Delete `~/.cache/whisper/` and re-download |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Credits

- [OpenRouter](https://openrouter.ai/) — LLM API gateway
- [NousResearch Hermes](https://huggingface.co/NousResearch) — Open-source LLM
- [OpenAI Whisper](https://github.com/openai/whisper) — Speech recognition
- [gTTS](https://github.com/pndurette/gTTS) — Text to speech
- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
