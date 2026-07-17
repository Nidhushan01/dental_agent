"""
DENTAL WEB AGENT - DEPLOYMENT CHECKLIST

Step-by-step guide to deploying the voice-enabled dental assistant to Render.
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║ DENTAL WEB AGENT - RENDER DEPLOYMENT CHECKLIST ║
╚════════════════════════════════════════════════════════════════════════════╝

BEFORE DEPLOYMENT:

□ [1] Test Locally
├─ Run: python test_integration.py
├─ Verify: http://localhost:8000 opens in browser
├─ Test text chat: "Book a cleaning for tomorrow"
├─ Test FAQ: "What are your hours?"
└─ Test voice: Click mic, speak, listen for response

□ [2] Verify Requirements
├─ Check requirements.txt has all dependencies:
│ fastapi, uvicorn, sqlalchemy, gtts, pydantic, pydantic-settings,
│ python-multipart, openai, requests, python-dotenv,
│ openai-whisper, pydub, jinja2, httpx
└─ Run: pip install -r requirements.txt

□ [3] Prepare Environment Variables
├─ Get OpenRouter API key from: https://openrouter.ai/
│ (Create free account, go to Dashboard → API Keys)
├─ Note your key: sk-or-v1-xxxxxxxxxxxxxxxx
├─ Choose model (default: meta-llama/llama-2-7b-chat)
└─ Keep these ready for Render setup

□ [4] Commit to Git
├─ Run: git add .
├─ Run: git commit -m "Dental web agent - ready for deployment"
├─ Run: git push origin main
└─ Verify code is on GitHub/GitLab/etc.

════════════════════════════════════════════════════════════════════════════════

RENDER DEPLOYMENT (10 minutes):

□ [5] Create Render Account
├─ Go to: https://render.com
├─ Click "Sign Up"
├─ Use GitHub/GitLab account or email
└─ Verify email if needed

□ [6] Create Web Service
├─ Click "New +" button (top right)
├─ Select "Web Service"
├─ Click "Connect" next to your repository
│ (If repo not listed, click "Connect account" first)
└─ Select: dental-web-agent repository

□ [7] Configure Service
├─ Name: dental-web-agent (or your choice)
├─ Environment: Python 3.11
├─ Build Command: pip install -r requirements.txt
├─ Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
├─ Plan: Free (or select paid for always-on)
└─ Click "Advanced" to expand more options

□ [8] Add Environment Variables
In the "Advanced" section, click "Add Environment Variable":

├─ OPENROUTER_API_KEY = sk-or-v1-xxxxxxx (your API key)
├─ OPENROUTER_MODEL = meta-llama/llama-2-7b-chat
├─ DATABASE_URL = sqlite:///./dental.db
├─ STT_MODEL = base
├─ TTS_LANGUAGE = en
└─ Click "Add" for each variable

□ [9] Deploy
├─ Review all settings one more time
├─ Click "Create Web Service"
├─ Wait 3-5 minutes for build to complete
├─ You'll see: "Your service is live!"
└─ Note your URL: https://dental-web-agent-xxx.onrender.com

════════════════════════════════════════════════════════════════════════════════

POST-DEPLOYMENT VERIFICATION:

□ [10] Test Live Service
├─ Open: https://your-app-url.onrender.com
├─ Test endpoints:
│ ├─ GET /health (should return {"status": "ok"})
│ ├─ GET /api/config (check features enabled)
│ ├─ POST /api/chat (test with text)
│ └─ Test UI: Text chat, voice (if HTTPS)
├─ First request may take 30 seconds (normal - Render is spinning up)
└─ Subsequent requests should be <5 seconds

□ [11] Monitor Logs
├─ In Render dashboard, click your service
├─ Click "Logs" tab (top)
├─ Watch for any errors
├─ Look for: "Application startup complete"
└─ If errors, check environment variables match .env

□ [12] Test Each Feature
├─ Appointments:
│ - "Book a cleaning for July 25 at 2 PM"
│ - "Reschedule appointment 5 to August 1"
│ - "Cancel appointment 3"
│
├─ FAQ:
│ - "What are your office hours?"
│ - "What care after extraction?"
│ - "Do you take insurance?"
│
├─ Voice (on mobile or desktop with HTTPS):
│ - Click mic, speak, listen for response
└─ Check all work correctly

════════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING:

Issue: Build fails with "ModuleNotFoundError"
└─ Fix: Check requirements.txt has all imports used in code
Run locally: pip install -r requirements.txt

Issue: "OPENROUTER_API_KEY not set"
└─ Fix: Verify env var added in Render dashboard
Value should be: sk-or-v1-xxxxxxx (not empty)
Test: curl https://your-url/health

Issue: First request very slow (30 seconds)
└─ Normal! Render free tier spins down after 15 min inactivity
Subsequent requests are fast (~2-5s)

Issue: Mic not working
└─ Only works on HTTPS (not HTTP)
Render URLs are HTTPS by default ✓
Test on localhost: http://localhost:8000 (no mic)
Test on Render: https://your-url (with mic)

Issue: No audio response for FAQ
└─ Whisper model loads on first request (~20s)
Wait for first STT request to complete
Subsequent requests should have audio

Issue: "503 Service Unavailable"
└─ Render is restarting service
Wait 1-2 minutes and retry
Check logs for errors

════════════════════════════════════════════════════════════════════════════════

SUCCESS CHECKLIST:

□ Service deployed and live at: https://your-url
□ /health endpoint returns OK
□ Text chat works
□ Voice recording works (on HTTPS)
□ Appointments can be booked/rescheduled/cancelled
□ FAQ questions return with voice responses
□ No errors in Render logs

════════════════════════════════════════════════════════════════════════════════

NEXT STEPS:

1. Share public URL with dental clinic staff
2. Test in production with real users
3. Monitor Render logs for errors
4. Set up error notifications (Render → Settings)
5. Upgrade to paid plan for always-on (optional)
6. Add user authentication for privacy
7. Configure email/SMS confirmations for bookings
8. Integrate with actual dental scheduling system

════════════════════════════════════════════════════════════════════════════════

USEFUL LINKS:

- OpenRouter Dashboard: https://openrouter.ai/
- Render Dashboard: https://dashboard.render.com
- View Logs: Your service → Logs
- Environment Variables: Your service → Environment
- Restart Service: Your service → More → Restart

════════════════════════════════════════════════════════════════════════════════
""")
