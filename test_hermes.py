"""Test Hermes LLM client with function-calling.

Before running this, set your OPENROUTER_API_KEY in .env:
  OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

If you don't have an API key, visit: https://openrouter.ai/
"""
import json
from hermes_client import call_hermes, TOOLS

print("=" * 70)
print("Hermes LLM Client Test")
print("=" * 70)

# Print available tools
print("\nAvailable tools:")
for tool in TOOLS:
    print(f"  - {tool['name']}: {tool['description']}")

print("\n" + "-" * 70)

# Test cases
test_cases = [
    "Book a cleaning appointment for tomorrow at 2 PM under the name John Doe.",
    "What are your office hours?",
    "I need to reschedule appointment 3 to next week Friday at 3:30 PM.",
    "What should I do after a tooth extraction?"
]

for i, user_input in enumerate(test_cases, 1):
    print(f"\n[Test {i}] User: {user_input}")
    print("-" * 70)
    
    result = call_hermes(user_input)
    
    if not result["success"]:
        print(f"ERROR: {result.get('error', 'Unknown error')}")
        continue
    
    print(f"Tool Called: {result['tool_name']}")
    if result['tool_result']:
        print(f"Tool Result: {json.dumps(result['tool_result'], indent=2)}")
    print(f"\nAssistant Reply:\n{result['assistant_reply']}")
    print()

print("=" * 70)
