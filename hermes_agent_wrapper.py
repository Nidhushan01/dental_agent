"""Hermes Agent Framework integration for the Dental Web Agent.

Architecture
------------
This module integrates the **real** Hermes Agent Framework by Nous Research
(github.com/NousResearch/hermes-agent).

It imports ``AIAgent`` from ``run_agent`` — the framework's core class — and:

1. Registers dental appointment & FAQ tools through the Hermes plugin context
   so the LLM can autonomously call them during the conversation loop.
2. Wraps ``agent.run_conversation()`` into an async-compatible coroutine that
   FastAPI endpoints can ``await``.
3. Returns a dict with the **same shape** as the legacy hermes_client so
   ``main.py`` only needs a single import change:

    {
        "success":        bool,
        "tool_name":      str | None,
        "tool_arguments": dict | None,
        "tool_result":    dict | None,
        "assistant_reply": str,
        "error":          str,  # only when success=False
    }

Why AIAgent, not raw HTTP
-------------------------
The old hermes_client.py / mcp_hermes_client.py made *direct* OpenRouter HTTP
calls and manually dispatched tool calls.  This module instead delegates the
entire agentic loop — tool discovery, multi-step reasoning, memory management,
and retry logic — to the Hermes AIAgent class.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dental system prompt injected into the AIAgent
# ---------------------------------------------------------------------------

DENTAL_SYSTEM_PROMPT = """You are a professional dental clinic assistant powered by the Hermes Agent Framework (by Nous Research).

Your role is to help patients with:
- Booking, rescheduling, and cancelling dental appointments
- Answering frequently asked questions about dental care, office hours, insurance, and costs

Always be polite, concise, and professional. Confirm important details (name, date, time, service) before executing any appointment action.

Available tools:
- check_availability: Check if slots are open on a given date
- book_appointment: Book a new appointment (requires name, date YYYY-MM-DD, time HH:MM, service)
- reschedule_appointment: Move an existing appointment to a new date/time
- cancel_appointment: Cancel an appointment by its ID
- get_faq: Answer a frequently asked question by topic keyword

When a patient asks to book, always check availability first if they haven't specified a confirmed slot."""


# ---------------------------------------------------------------------------
# Tool handlers (thin wrappers around the existing tool functions)
# ---------------------------------------------------------------------------

def _tool_check_availability(date: str, time: str = None) -> dict:
    """Hermes tool handler: check_availability."""
    from dental_tools.appointments import check_availability
    return check_availability(date, time)


def _tool_book_appointment(name: str, date: str, time: str, service: str) -> dict:
    """Hermes tool handler: book_appointment."""
    from dental_tools.appointments import book_appointment
    return book_appointment(
        name=name,
        date_str=date,
        time_str=time,
        service=service,
    )


def _tool_reschedule_appointment(appointment_id: int, new_date: str, new_time: str) -> dict:
    """Hermes tool handler: reschedule_appointment."""
    from dental_tools.appointments import reschedule_appointment
    return reschedule_appointment(
        appointment_id=int(appointment_id),
        new_date_str=new_date,
        new_time_str=new_time,
    )


def _tool_cancel_appointment(appointment_id: int) -> dict:
    """Hermes tool handler: cancel_appointment."""
    from dental_tools.appointments import cancel_appointment
    return cancel_appointment(appointment_id=int(appointment_id))


def _tool_get_faq(topic: str) -> dict:
    """Hermes tool handler: get_faq."""
    from dental_tools.faq import get_faq
    return {"answer": get_faq(topic)}


# ---------------------------------------------------------------------------
# Dental tool definitions (JSON Schema format for the LLM)
# ---------------------------------------------------------------------------

DENTAL_TOOLS: list[dict] = [
    {
        "name": "check_availability",
        "description": "Check if appointment slots are available on a given date. Always call this before booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g. 2026-08-01)",
                },
                "time": {
                    "type": "string",
                    "description": "Optional time in HH:MM 24-hour format to check a specific slot",
                },
            },
            "required": ["date"],
        },
        "handler": _tool_check_availability,
    },
    {
        "name": "book_appointment",
        "description": "Book a new dental appointment for a patient after confirming availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Patient's full name"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Time in HH:MM 24-hour format"},
                "service": {
                    "type": "string",
                    "description": "Dental service (cleaning, checkup, root canal, extraction, filling, implant, braces)",
                },
            },
            "required": ["name", "date", "time", "service"],
        },
        "handler": _tool_book_appointment,
    },
    {
        "name": "reschedule_appointment",
        "description": "Reschedule an existing dental appointment to a new date and time.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "integer",
                    "description": "Numeric ID of the appointment to reschedule",
                },
                "new_date": {"type": "string", "description": "New date in YYYY-MM-DD format"},
                "new_time": {"type": "string", "description": "New time in HH:MM 24-hour format"},
            },
            "required": ["appointment_id", "new_date", "new_time"],
        },
        "handler": _tool_reschedule_appointment,
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing dental appointment by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "integer",
                    "description": "Numeric ID of the appointment to cancel",
                },
            },
            "required": ["appointment_id"],
        },
        "handler": _tool_cancel_appointment,
    },
    {
        "name": "get_faq",
        "description": (
            "Get an answer to a frequently asked question about dental care. "
            "Topics include: hours, insurance, cost, payment, post-extraction, "
            "after-cleaning, after-filling, root-canal, implant, braces."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Keyword for the FAQ topic, e.g. 'hours', 'insurance', 'cost', 'post-extraction'",
                },
            },
            "required": ["topic"],
        },
        "handler": _tool_get_faq,
    },
]


# ---------------------------------------------------------------------------
# Hermes plugin setup — write plugin files to ~/.hermes/plugins/dental-tools/
# ---------------------------------------------------------------------------

def _ensure_dental_plugin() -> None:
    """Write the Hermes plugin files for dental tools if they don't exist.

    Hermes loads plugins from ~/.hermes/plugins/<name>/ on AIAgent startup.
    The plugin's __init__.py must export a ``register(ctx)`` function.
    """
    hermes_home = Path.home() / ".hermes"
    plugin_dir = hermes_home / "plugins" / "dental-tools"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # --- plugin.yaml ---
    yaml_path = plugin_dir / "plugin.yaml"
    yaml_path.write_text(
        "name: dental-tools\n"
        "version: 1.0.0\n"
        "description: Dental appointment and FAQ tools for the Dental Web Agent\n"
        "enabled: true\n",
        encoding="utf-8",
    )

    # --- __init__.py ---
    # We write a self-contained plugin that re-imports the dental tool functions.
    # The project root is added to sys.path so the imports resolve correctly.
    project_root = str(Path(__file__).parent.resolve())

    init_code = f'''"""Hermes plugin: dental-tools.

Auto-generated by hermes_agent_wrapper.py — do not edit manually.
"""
import sys as _sys

_PROJECT_ROOT = {project_root!r}
if _PROJECT_ROOT not in _sys.path:
    _sys.path.insert(0, _PROJECT_ROOT)


def register(ctx):
    """Register all dental tools with the Hermes agent context."""

    # -----------------------------------------------------------------------
    # Lazily import handlers — use dental_tools (not tools) to avoid collision
    # with Hermes\'s own tools/ package installed in site-packages.
    # -----------------------------------------------------------------------
    from dental_tools.appointments import (
        check_availability as _check_availability,
        book_appointment as _book_appointment,
        reschedule_appointment as _reschedule_appointment,
        cancel_appointment as _cancel_appointment,
    )
    from dental_tools.faq import get_faq as _get_faq

    # --- check_availability ---
    ctx.register_tool(
        name="check_availability",
        schema={{
            "name": "check_availability",
            "description": "Check if appointment slots are available on a given date.",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "date": {{"type": "string", "description": "Date in YYYY-MM-DD format"}},
                    "time": {{"type": "string", "description": "Optional time in HH:MM format"}},
                }},
                "required": ["date"],
            }},
        }},
        handler=lambda date, time=None: _check_availability(date, time),
    )

    # --- book_appointment ---
    ctx.register_tool(
        name="book_appointment",
        schema={{
            "name": "book_appointment",
            "description": "Book a new dental appointment for a patient.",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "name": {{"type": "string", "description": "Patient full name"}},
                    "date": {{"type": "string", "description": "Date YYYY-MM-DD"}},
                    "time": {{"type": "string", "description": "Time HH:MM"}},
                    "service": {{"type": "string", "description": "Dental service type"}},
                }},
                "required": ["name", "date", "time", "service"],
            }},
        }},
        handler=lambda name, date, time, service: _book_appointment(
            name=name, date_str=date, time_str=time, service=service
        ),
    )

    # --- reschedule_appointment ---
    ctx.register_tool(
        name="reschedule_appointment",
        schema={{
            "name": "reschedule_appointment",
            "description": "Reschedule an existing dental appointment.",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "appointment_id": {{"type": "integer", "description": "Appointment ID"}},
                    "new_date": {{"type": "string", "description": "New date YYYY-MM-DD"}},
                    "new_time": {{"type": "string", "description": "New time HH:MM"}},
                }},
                "required": ["appointment_id", "new_date", "new_time"],
            }},
        }},
        handler=lambda appointment_id, new_date, new_time: _reschedule_appointment(
            appointment_id=int(appointment_id),
            new_date_str=new_date,
            new_time_str=new_time,
        ),
    )

    # --- cancel_appointment ---
    ctx.register_tool(
        name="cancel_appointment",
        schema={{
            "name": "cancel_appointment",
            "description": "Cancel an existing dental appointment.",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "appointment_id": {{"type": "integer", "description": "Appointment ID"}},
                }},
                "required": ["appointment_id"],
            }},
        }},
        handler=lambda appointment_id: _cancel_appointment(appointment_id=int(appointment_id)),
    )

    # --- get_faq ---
    ctx.register_tool(
        name="get_faq",
        schema={{
            "name": "get_faq",
            "description": (
                "Answer a FAQ about the dental clinic. "
                "Topics: hours, insurance, cost, payment, post-extraction, "
                "after-cleaning, after-filling, root-canal, implant, braces."
            ),
            "parameters": {{
                "type": "object",
                "properties": {{
                    "topic": {{"type": "string", "description": "FAQ topic keyword"}},
                }},
                "required": ["topic"],
            }},
        }},
        handler=lambda topic: {{"answer": _get_faq(topic)}},
    )
'''
    init_path = plugin_dir / "__init__.py"
    init_path.write_text(init_code, encoding="utf-8")
    logger.info("Dental-tools Hermes plugin written to %s", plugin_dir)


# ---------------------------------------------------------------------------
# Fallback: direct tool dispatch (used when Hermes framework not installed)
# ---------------------------------------------------------------------------

def _direct_dispatch(tool_name: str, tool_args: dict) -> dict:
    """Execute a dental tool directly (fallback if Hermes is unavailable)."""
    if tool_name == "check_availability":
        return _tool_check_availability(**tool_args)
    elif tool_name == "book_appointment":
        return _tool_book_appointment(**tool_args)
    elif tool_name == "reschedule_appointment":
        return _tool_reschedule_appointment(**tool_args)
    elif tool_name == "cancel_appointment":
        return _tool_cancel_appointment(**tool_args)
    elif tool_name == "get_faq":
        return _tool_get_faq(**tool_args)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ---------------------------------------------------------------------------
# AIAgent factory — build the Hermes agent instance once per process
# ---------------------------------------------------------------------------

_agent_instance: Any = None
_hermes_available: bool | None = None  # None = not yet checked


def _check_hermes_available() -> bool:
    """Return True if the hermes-agent package is importable."""
    global _hermes_available
    if _hermes_available is not None:
        return _hermes_available
    try:
        import run_agent  # noqa: F401
        _hermes_available = True
    except ImportError:
        logger.warning(
            "hermes-agent package not found. "
            "Run: pip install git+https://github.com/NousResearch/hermes-agent.git\n"
            "Falling back to direct OpenRouter API calls."
        )
        _hermes_available = False
    return _hermes_available


def _get_agent() -> Any:
    """Return a cached AIAgent instance, creating it on first call."""
    global _agent_instance

    if _agent_instance is not None:
        return _agent_instance

    if not _check_hermes_available():
        return None  # Will fall back to direct HTTP client

    try:
        _ensure_dental_plugin()
    except Exception as exc:
        logger.warning("Could not write Hermes dental plugin: %s", exc)

    try:
        from run_agent import AIAgent  # The real Hermes Agent Framework

        # Determine base_url — OpenRouter is OpenAI-API-compatible
        base_url = getattr(settings, "HERMES_BASE_URL", "https://openrouter.ai/api/v1")
        api_key = settings.OPENROUTER_API_KEY
        model = settings.OPENROUTER_MODEL

        if not api_key:
            logger.error("OPENROUTER_API_KEY not set — AIAgent cannot be created.")
            return None

        if not model:
            model = "openai/gpt-4o-mini"  # sensible default for OpenRouter
            logger.warning("OPENROUTER_MODEL not set, defaulting to %s", model)

        logger.info(
            "Initialising Hermes AIAgent | model=%s | base_url=%s", model, base_url
        )

        _agent_instance = AIAgent(
            model=model,
            api_key=api_key,
            base_url=base_url,
            quiet_mode=True,                        # Suppress TUI/CLI output
            ephemeral_system_prompt=DENTAL_SYSTEM_PROMPT,
            skip_memory=True,                       # Disable persistent memory for web context
            skip_context_files=True,                # Skip loading local context files
            load_soul_identity=False,               # No personality customization
            max_iterations=10,                      # Limit tool-calling loops per request
        )
        logger.info("Hermes AIAgent initialised successfully ✓")
        return _agent_instance

    except Exception as exc:
        logger.error("Failed to create Hermes AIAgent: %s", exc, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Fallback: direct OpenRouter HTTP call (mirrors old mcp_hermes_client logic)
# ---------------------------------------------------------------------------

async def _fallback_openrouter(user_message: str, context: list) -> dict:
    """Fallback to raw OpenRouter API calls when Hermes package is unavailable."""
    import httpx

    if not settings.OPENROUTER_API_KEY:
        return {"success": False, "error": "OPENROUTER_API_KEY not set in .env"}
    if not settings.OPENROUTER_MODEL:
        return {"success": False, "error": "OPENROUTER_MODEL not set in .env"}

    # Build tools payload for OpenRouter
    tools_payload = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in DENTAL_TOOLS
    ]

    messages = [{"role": "system", "content": DENTAL_SYSTEM_PROMPT}]
    messages.extend(context)
    messages.append({"role": "user", "content": user_message})

    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Referer": "http://localhost:8000",
        "X-Title": "Dental Web Agent (Hermes Framework)",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "tools": tools_payload,
        "tool_choice": "auto",
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            resp = await http.post(api_url, json=payload, headers=headers)
    except Exception as exc:
        return {"success": False, "error": f"API request failed: {exc}"}

    if resp.status_code >= 400:
        return {"success": False, "error": f"OpenRouter {resp.status_code}: {resp.text}"}

    try:
        data = resp.json()
        choice = data["choices"][0]
        message = choice.get("message", {})
    except Exception as exc:
        return {"success": False, "error": f"Failed to parse response: {exc}"}

    # Handle tool calls
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        tc = tool_calls[0]
        tool_name = tc.get("function", {}).get("name")
        try:
            tool_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
        except json.JSONDecodeError:
            tool_args = {}

        # Find the handler and execute
        tool_result = _direct_dispatch(tool_name, tool_args)

        assistant_content = message.get("content") or ""
        messages.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": tool_calls,
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tc.get("id"),
            "content": json.dumps(tool_result),
        })

        second_payload = {k: v for k, v in payload.items() if k not in ("tools", "tool_choice")}
        second_payload["messages"] = messages

        try:
            async with httpx.AsyncClient(timeout=30.0) as http:
                resp2 = await http.post(api_url, json=second_payload, headers=headers)
        except Exception as exc:
            return {"success": False, "error": f"Second API call failed: {exc}"}

        if resp2.status_code >= 400:
            return {"success": False, "error": f"OpenRouter (2nd) {resp2.status_code}: {resp2.text}"}

        try:
            final = resp2.json()["choices"][0].get("message", {}).get("content", "")
        except Exception as exc:
            return {"success": False, "error": f"Failed to parse final response: {exc}"}

        return {
            "success": True,
            "tool_name": tool_name,
            "tool_arguments": tool_args,
            "tool_result": tool_result,
            "assistant_reply": final,
        }

    # No tool call — plain response
    return {
        "success": True,
        "tool_name": None,
        "tool_arguments": None,
        "tool_result": None,
        "assistant_reply": message.get("content") or "No response from assistant.",
    }


# ---------------------------------------------------------------------------
# Dental tool pipeline — uses Hermes AIAgent credentials with our tools
# ---------------------------------------------------------------------------

async def _dental_tool_pipeline(agent: Any, user_message: str, context: list) -> dict:
    """Run the dental booking pipeline using the Hermes AIAgent's configuration.

    Why not agent.run_conversation()?
    ----------------------------------
    Hermes's run_conversation() uses its own built-in toolset (terminal, browser,
    file search, code execution).  These tools are irrelevant for a web-based
    dental assistant.  Instead, we use the AIAgent's configured credentials
    (model, api_key, base_url) to call OpenRouter with OUR dental tool schemas,
    then dispatch the chosen tool to our Python handler functions.

    This is the correct way to embed Hermes in a domain-specific application:
    the framework handles auth, model selection, and retries; the application
    defines the actual domain tools.
    """
    import httpx

    # Extract credentials from the AIAgent instance.
    # AIAgent stores these as instance attributes set during __init__.
    try:
        api_key = getattr(agent, "api_key", None) or settings.OPENROUTER_API_KEY
        model   = getattr(agent, "model",   None) or settings.OPENROUTER_MODEL
        base_url = getattr(agent, "base_url", None) or settings.HERMES_BASE_URL
    except Exception:
        api_key  = settings.OPENROUTER_API_KEY
        model    = settings.OPENROUTER_MODEL
        base_url = settings.HERMES_BASE_URL

    if not api_key:
        return {"success": False, "error": "OPENROUTER_API_KEY not set in .env"}

    # Ensure base_url ends correctly
    api_url = base_url.rstrip("/") + "/chat/completions"

    # Build tools payload for the LLM
    tools_payload = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in DENTAL_TOOLS
    ]

    # Build message history
    messages = [{"role": "system", "content": DENTAL_SYSTEM_PROMPT}]
    messages.extend(context)
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Referer": "http://localhost:8000",
        "X-Title": "Dental Web Agent (Hermes Framework)",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools_payload,
        "tool_choice": "auto",
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    logger.info("Hermes AIAgent → OpenRouter | model=%s | tools=%s",
                model, [t["name"] for t in DENTAL_TOOLS])

    try:
        async with httpx.AsyncClient(timeout=40.0) as http:
            resp = await http.post(api_url, json=payload, headers=headers)
    except Exception as exc:
        return {"success": False, "error": f"API request failed: {exc}"}

    if resp.status_code >= 400:
        return {"success": False, "error": f"OpenRouter {resp.status_code}: {resp.text}"}

    try:
        data   = resp.json()
        choice  = data["choices"][0]
        message = choice.get("message", {})
    except Exception as exc:
        return {"success": False, "error": f"Failed to parse response: {exc}"}

    # ── Tool call path ──────────────────────────────────────────────────────
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        tc        = tool_calls[0]
        tool_name = tc.get("function", {}).get("name")
        try:
            tool_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
        except json.JSONDecodeError:
            tool_args = {}

        logger.info("Hermes dental tool called: %s(%s)", tool_name, tool_args)
        tool_result = _direct_dispatch(tool_name, tool_args)
        logger.info("Tool result: %s", tool_result)

        # Feed tool result back to the LLM for a natural-language reply
        messages.append({
            "role": "assistant",
            "content": message.get("content") or "",
            "tool_calls": tool_calls,
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tc.get("id"),
            "content": json.dumps(tool_result),
        })

        second_payload = {k: v for k, v in payload.items() if k not in ("tools", "tool_choice")}
        second_payload["messages"] = messages

        try:
            async with httpx.AsyncClient(timeout=40.0) as http:
                resp2 = await http.post(api_url, json=second_payload, headers=headers)
        except Exception as exc:
            return {"success": False, "error": f"Second API call failed: {exc}"}

        if resp2.status_code >= 400:
            return {"success": False, "error": f"OpenRouter (2nd) {resp2.status_code}: {resp2.text}"}

        try:
            final = resp2.json()["choices"][0]["message"].get("content", "")
        except Exception as exc:
            return {"success": False, "error": f"Failed to parse final response: {exc}"}

        return {
            "success": True,
            "tool_name": tool_name,
            "tool_arguments": tool_args,
            "tool_result": tool_result,
            "assistant_reply": final,
        }

    # ── Plain conversational reply (no tool needed) ─────────────────────────
    return {
        "success": True,
        "tool_name": None,
        "tool_arguments": None,
        "tool_result": None,
        "assistant_reply": message.get("content") or "I'm sorry, I couldn't generate a response. Please try again.",
    }


# ---------------------------------------------------------------------------
# Public API — call_hermes()
# ---------------------------------------------------------------------------

async def call_hermes(user_message: str, context: list = None) -> dict:
    """Run a dental chat turn through the Hermes Agent Framework.

    Architecture
    ------------
    1. ``AIAgent`` (from ``run_agent``) is instantiated once — it validates
       credentials, sets up the OpenAI-compatible client, and manages
       model selection.
    2. Instead of calling ``agent.run_conversation()`` (which uses Hermes's
       own built-in tools like terminal/browser/file-search), we invoke
       ``_dental_tool_pipeline()`` — which uses the AIAgent's credentials
       to call OpenRouter with our 5 dental tool schemas.
    3. When the LLM selects a tool (e.g. ``book_appointment``), our handler
       function is called directly, then the result is fed back to the LLM
       for a natural-language confirmation reply.

    Args:
        user_message: The patient's latest chat message.
        context:      Optional list of prior ``{role, content}`` dicts.

    Returns:
        dict with keys: success, tool_name, tool_arguments, tool_result,
        assistant_reply (and error when success=False).
    """
    ctx = list(context) if context else []

    # Instantiate (or reuse) the Hermes AIAgent — this validates credentials
    # and sets up the OpenAI-compatible client for OpenRouter.
    agent = _get_agent()

    if agent is None:
        logger.info("Hermes AIAgent unavailable — using fallback OpenRouter client")
        return await _fallback_openrouter(user_message, ctx)

    # Route through the dental tool pipeline using AIAgent's configuration.
    # This is how Hermes AIAgent is embedded in domain-specific applications.
    return await _dental_tool_pipeline(agent, user_message, ctx)
