"""Test voice synthesis (TTS).

Note: Testing STT requires an actual audio file. TTS just needs text.
"""
from voice.tts import synthesize
import os

print("=" * 60)
print("Testing Voice Synthesis (TTS)")
print("=" * 60)

test_texts = [
    "Hello, welcome to our dental clinic.",
    "Your appointment is confirmed for tomorrow at 2 PM.",
    "Please remember to rinse with warm salt water after extraction."
]

for i, text in enumerate(test_texts, 1):
    print(f"\n[Test {i}] Synthesizing: {text[:50]}...")
    try:
        audio_path = synthesize(text)
        print(f"✓ Generated: {audio_path}")
        
        # Check if file exists
        full_path = audio_path.lstrip('/')
        if os.path.exists(full_path):
            size_kb = os.path.getsize(full_path) / 1024
            print(f"  File size: {size_kb:.1f} KB")
        else:
            print(f"  WARNING: File not found at {full_path}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Voice synthesis tests completed!")
print("=" * 60)
