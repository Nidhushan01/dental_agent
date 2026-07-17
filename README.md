# Dental Web Agent - Complete Setup & Deployment Guide

## Overview

A **voice-enabled agentic AI assistant** for dental clinics, delivered as a web chat widget. Built with:

- **Backend:** FastAPI (Python)
- **AI:** Hermes LLM via OpenRouter (function-calling/tool-use)
- **Voice:** Whisper (STT) + gTTS (TTS)
- **Database:** SQLite
- **Frontend:** Plain HTML/CSS/JS with mic recording
- **Hosting:** Render.com

---

## Key Features

1. **Agentic AI**: Hermes LLM with function-calling decides which tool to use
2. **Two Flows**:
   - **Appointments**: book, reschedule, cancel dental appointments
   - **FAQ**: answer dental questions with voice replies
3. **Voice Input**: Browser microphone recording + Whisper transcription
4. **Voice Output**: FAQ answers read aloud via gTTS
5. **Conversation Memory**: Multi-turn chat with context preservation
6. **Real Tools**: Actual database queries, not just template responses

---

## Quick Start (Local)

### 1. Setup

```bash
cd dental-web-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
# Get API key from https://openrouter.ai/
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> .env
```

### 3. Run

```bash
uvicorn main:app --reload
# Open http://localhost:8000
```

---

## API Endpoints

### `POST /api/chat`

Main chat endpoint with Hermes LLM function-calling.

### `POST /api/transcribe`

Transcribe audio file to text.

### `POST /api/synthesize`

Synthesize text to speech (gTTS).

### `GET /api/config`

Get frontend configuration.

### `GET /health`

Health check endpoint.

---

## Deployment on Render

1. Push code to GitHub
2. Sign up at https://render.com
3. Click "New +" → "Web Service"
4. Connect your repo and configure:

**Start Command:**

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**

```
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=meta-llama/llama-2-7b-chat
DATABASE_URL=sqlite:///./dental.db
```

---

## Testing

```bash
python test_integration.py
python test_db.py
python test_appointments.py
python test_voice.py
```

---

## Project Structure

```
dental-web-agent/
├── main.py                      # FastAPI server
├── config.py                    # Environment config
├── hermes_client.py             # LLM + function-calling
├── db/
│   ├── models.py                # SQLAlchemy models
│   └── db.py                    # Connection helpers
├── tools/
│   ├── appointments.py          # Appointment functions
│   └── faq.py                   # FAQ database
├── voice/
│   ├── stt.py                   # Whisper wrapper
│   └── tts.py                   # gTTS wrapper
├── static/
│   ├── index.html               # Chat widget
│   ├── app.js                   # Frontend logic
│   └── style.css                # Styling
├── requirements.txt
├── Procfile
├── .env                         # Environment variables
└── README.md
```

---

## Troubleshooting

- **"OPENROUTER_API_KEY not set"**: Check `.env` file exists
- **"No microphone support"**: Use Chrome/Firefox, ensure HTTPS (production)
- **"Transcription failed"**: Install FFmpeg
- **Slow first request**: Render free tier spins down after inactivity (normal)
