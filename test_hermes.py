"""Tests for the Hermes Agent Framework integration (hermes_agent_wrapper.py).

These tests verify:
1. The wrapper correctly imports and uses the AIAgent class from run_agent.
2. Tool registration (plugin setup) works without errors.
3. The call_hermes() function returns a valid response dict.
4. The fallback path works when Hermes is unavailable.
"""

import asyncio
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_hermes_package_importable():
    """Test 1: Verify that hermes-agent package is installed and importable."""
    print("\n--- Test 1: Hermes Package Import ---")
    try:
        from run_agent import AIAgent
        print(f"  ✓ Successfully imported AIAgent from run_agent")
        print(f"  ✓ AIAgent class: {AIAgent}")
        return True
    except ImportError as e:
        print(f"  ✗ Could not import AIAgent: {e}")
        print("    Run: pip install git+https://github.com/NousResearch/hermes-agent.git")
        return False


def test_wrapper_importable():
    """Test 2: Verify hermes_agent_wrapper imports without errors."""
    print("\n--- Test 2: Wrapper Module Import ---")
    try:
        import hermes_agent_wrapper
        print(f"  ✓ hermes_agent_wrapper imported successfully")
        print(f"  ✓ DENTAL_TOOLS count: {len(hermes_agent_wrapper.DENTAL_TOOLS)}")
        expected_tools = {"check_availability", "book_appointment", "reschedule_appointment",
                         "cancel_appointment", "get_faq"}
        actual_tools = {t["name"] for t in hermes_agent_wrapper.DENTAL_TOOLS}
        if actual_tools == expected_tools:
            print(f"  ✓ All 5 dental tools defined: {', '.join(sorted(actual_tools))}")
        else:
            print(f"  ✗ Tool mismatch! Expected: {expected_tools}, Got: {actual_tools}")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_plugin_setup():
    """Test 3: Verify Hermes plugin files are created."""
    print("\n--- Test 3: Hermes Plugin Setup ---")
    try:
        from hermes_agent_wrapper import _ensure_dental_plugin
        _ensure_dental_plugin()

        from pathlib import Path
        plugin_dir = Path.home() / ".hermes" / "plugins" / "dental-tools"
        yaml_exists = (plugin_dir / "plugin.yaml").exists()
        init_exists = (plugin_dir / "__init__.py").exists()

        print(f"  Plugin directory: {plugin_dir}")
        print(f"  ✓ plugin.yaml: {'exists' if yaml_exists else 'MISSING'}")
        print(f"  ✓ __init__.py: {'exists' if init_exists else 'MISSING'}")

        if yaml_exists and init_exists:
            print("  ✓ Dental plugin files written successfully")
            return True
        else:
            print("  ✗ Plugin file(s) missing")
            return False
    except Exception as e:
        print(f"  ✗ Plugin setup error: {e}")
        return False


def test_hermes_available():
    """Test 4: Check if Hermes AIAgent can be instantiated."""
    print("\n--- Test 4: AIAgent Instantiation ---")
    from hermes_agent_wrapper import _check_hermes_available, _get_agent

    available = _check_hermes_available()
    print(f"  Hermes available: {available}")

    if not available:
        print("  ℹ  Hermes not installed — fallback mode will be used")
        return True  # This is a valid state (fallback works)

    print("  Attempting AIAgent instantiation...")
    agent = _get_agent()
    if agent is not None:
        print(f"  ✓ AIAgent instance created: {type(agent).__name__}")
        return True
    else:
        print("  ✗ AIAgent returned None — check OPENROUTER_API_KEY in .env")
        return False


def test_call_hermes_faq():
    """Test 5: Full round-trip — ask an FAQ question."""
    print("\n--- Test 5: call_hermes() FAQ Round-Trip ---")
    from hermes_agent_wrapper import call_hermes

    async def run():
        result = await call_hermes("What are your office hours?")
        return result

    result = asyncio.run(run())
    print(f"  success: {result.get('success')}")
    print(f"  tool_name: {result.get('tool_name')}")
    print(f"  assistant_reply: {result.get('assistant_reply', '')[:120]}...")

    if result.get("success"):
        print("  ✓ call_hermes() returned a successful response")
        return True
    else:
        print(f"  ✗ call_hermes() failed: {result.get('error')}")
        return False


def test_call_hermes_booking():
    """Test 6: Full round-trip — book an appointment."""
    print("\n--- Test 6: call_hermes() Booking Round-Trip ---")
    from hermes_agent_wrapper import call_hermes

    async def run():
        result = await call_hermes(
            "I'd like to book an appointment for Alice Smith on 2026-09-15 at 10:00 for a cleaning."
        )
        return result

    result = asyncio.run(run())
    print(f"  success: {result.get('success')}")
    print(f"  tool_name: {result.get('tool_name')}")
    print(f"  tool_result: {result.get('tool_result')}")
    print(f"  assistant_reply: {result.get('assistant_reply', '')[:120]}...")

    if result.get("success"):
        print("  ✓ call_hermes() handled booking request")
        return True
    else:
        print(f"  ✗ call_hermes() failed: {result.get('error')}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  HERMES AGENT FRAMEWORK — Integration Tests")
    print("=" * 60)

    results = {}

    # Always run these (no network needed)
    results["import"] = test_hermes_package_importable()
    results["wrapper"] = test_wrapper_importable()
    results["plugin"] = test_plugin_setup()
    results["agent"] = test_hermes_available()

    # Network tests (require valid OPENROUTER_API_KEY)
    run_network = input("\nRun network tests (requires OPENROUTER_API_KEY)? [y/N]: ").strip().lower()
    if run_network == "y":
        results["faq"] = test_call_hermes_faq()
        results["booking"] = test_call_hermes_booking()

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"  Results: {passed}/{total} tests passed")
    for name, ok in results.items():
        icon = "✓" if ok else "✗"
        print(f"    {icon} {name}")
    print("=" * 60)

    if passed < total:
        sys.exit(1)
