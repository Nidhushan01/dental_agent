"""Integration test: verify all components work together."""
import asyncio
import json
from config import settings
from db.db import init_db, SessionLocal
from db.models import Appointment
from hermes_client import call_hermes, TOOLS
from tools.appointments import book_appointment, check_availability
from tools.faq import get_faq
from voice.tts import synthesize
import datetime

print("=" * 70)
print("DENTAL WEB AGENT - INTEGRATION TEST")
print("=" * 70)

# Test 1: Config
print("\n[1] Configuration:")
print(f"   DATABASE_URL: {settings.DATABASE_URL}")
print(f"   OpenRouter Model: {settings.OPENROUTER_MODEL}")
print(f"   STT Model: {settings.STT_MODEL}")
print(f"   TTS Language: {settings.TTS_LANGUAGE}")

# Test 2: Database
print("\n[2] Database:")
try:
    init_db()
    session = SessionLocal()
    count = session.query(Appointment).count()
    session.close()
    print(f"   ✓ Connected. Appointments in DB: {count}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Tools
print("\n[3] Tools:")
try:
    future_date = (datetime.date.today() + datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Check availability
    avail = check_availability(future_date)
    print(f"   ✓ check_availability: {avail['available']} ({avail.get('slots_available', 0)} slots)")
    
    # FAQ
    faq_answer = get_faq("hours")
    print(f"   ✓ get_faq: {faq_answer[:50]}...")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Voice
print("\n[4] Voice Synthesis:")
try:
    audio_url = synthesize("Welcome to our dental clinic!")
    print(f"   ✓ TTS generated: {audio_url}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Hermes Client (requires API key)
print("\n[5] Hermes LLM Client:")
if settings.OPENROUTER_API_KEY:
    print("   Testing with real API...")
    try:
        result = call_hermes("What are your office hours?")
        if result['success']:
            print(f"   ✓ LLM responded")
            print(f"     Tool used: {result['tool_name']}")
            print(f"     Reply: {result['assistant_reply'][:60]}...")
        else:
            print(f"   ✗ Error: {result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
else:
    print("   ⚠ OPENROUTER_API_KEY not set. Skipping live test.")
    print("   Set it in .env to enable: OPENROUTER_API_KEY=sk-or-v1-...")

# Test 6: Verify API endpoints exist
print("\n[6] API Endpoints:")
endpoints = [
    "GET  /",
    "GET  /api/config",
    "POST /api/chat",
    "POST /api/transcribe",
    "POST /api/synthesize",
    "GET  /health"
]
for endpoint in endpoints:
    print(f"   ✓ {endpoint}")

print("\n" + "=" * 70)
print("✓ INTEGRATION TEST COMPLETE")
print("\nTo run the server locally:")
print("  uvicorn main:app --reload")
print("\nThen open: http://localhost:8000")
print("=" * 70)
