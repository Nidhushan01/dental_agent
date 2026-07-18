"""[DEPRECATED] Raw OpenRouter HTTP client — replaced by hermes_agent_wrapper.py.

This file is kept for reference only.  The project now uses the real
Hermes Agent Framework (NousResearch/hermes-agent) with the AIAgent class.

See hermes_agent_wrapper.py for the active implementation.
"""
# DEPRECATED — see hermes_agent_wrapper.py
"""Hermes LLM client with function-calling via OpenRouter API."""
import httpx
import json
from config import settings
from tools.appointments import (
    check_availability,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
)
from tools.faq import get_faq


# Tool definitions as JSON Schema for Hermes
TOOLS = [
    {
        "type": "function",
        "name": "check_availability",
        "description": "Check if appointment slots are available on a given date",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g., 2026-07-20)"
                }
            },
            "required": ["date"]
        }
    },
    {
        "type": "function",
        "name": "book_appointment",
        "description": "Book a new dental appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Patient's full name"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Time in HH:MM format (24-hour)"},
                "service": {"type": "string", "description": "Type of service (e.g., cleaning, checkup, root canal)"}
            },
            "required": ["name", "date", "time", "service"]
        }
    },
    {
        "type": "function",
        "name": "reschedule_appointment",
        "description": "Reschedule an existing appointment to a new date/time",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer", "description": "ID of the appointment to reschedule"},
                "new_date": {"type": "string", "description": "New date in YYYY-MM-DD format"},
                "new_time": {"type": "string", "description": "New time in HH:MM format"}
            },
            "required": ["appointment_id", "new_date", "new_time"]
        }
    },
    {
        "type": "function",
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer", "description": "ID of the appointment to cancel"}
            },
            "required": ["appointment_id"]
        }
    },
    {
        "type": "function",
        "name": "get_faq",
        "description": "Get an answer to a frequently asked question about dental care, hours, insurance, or costs",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic keyword (e.g., post-extraction, hours, insurance, cost)"}
            },
            "required": ["topic"]
        }
    }
]


def _execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a tool function based on the tool name and arguments."""
    if tool_name == "check_availability":
        return check_availability(arguments["date"])
    elif tool_name == "book_appointment":
        return book_appointment(
            name=arguments["name"],
            date_str=arguments["date"],
            time_str=arguments["time"],
            service=arguments["service"]
        )
    elif tool_name == "reschedule_appointment":
        return reschedule_appointment(
            appointment_id=arguments["appointment_id"],
            new_date_str=arguments["new_date"],
            new_time_str=arguments["new_time"]
        )
    elif tool_name == "cancel_appointment":
        return cancel_appointment(appointment_id=arguments["appointment_id"])
    elif tool_name == "get_faq":
        return {"answer": get_faq(arguments["topic"])}
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def call_hermes(user_message: str, context: list = None) -> dict:
    """Call Hermes LLM via OpenRouter with function-calling.
    
    Args:
        user_message: User's input text
        context: Optional list of prior messages for multi-turn conversation
    
    Returns:
        dict with keys:
            - success: bool
            - tool_name: str (name of the tool called, or None if no tool was called)
            - tool_result: dict (result from executing the tool)
            - assistant_reply: str (assistant's response text)
            - error: str (if something went wrong)
    """
    if not settings.OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY not set in .env"
        }
    # Validate model is configured
    if not settings.OPENROUTER_MODEL:
        return {
            "success": False,
            "error": "OPENROUTER_MODEL not set in .env. Set OPENROUTER_MODEL to a valid OpenRouter model ID (example: gpt-4o-mini)."
        }
    
    # Build message history
    messages = context or []
    messages.append({"role": "user", "content": user_message})
    
    # Call OpenRouter API with tools
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Referer": "http://localhost:3000",
        "X-Title": "Dental Web Agent",
    }
    
    # Build tools array in OpenRouter format: each entry has a `type` and a `function` object
    tools_payload = [
        {
            "type": t.get("type", "function"),
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {}),
            },
        }
        for t in TOOLS
    ]

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        # OpenRouter prefers 'tools' + 'tool_choice'
        "tools": tools_payload,
        "tool_choice": "auto",
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    
    try:
        # Debug: print payload (only minimal info)
        # print('Calling OpenRouter with payload keys:', list(payload.keys()))
        with httpx.Client(timeout=30.0) as client:
            response = client.post(api_url, json=payload, headers=headers)

        # If the API returned an error status, include the body for diagnosis
        if response.status_code >= 400:
            body_text = response.text
            return {
                "success": False,
                "error": f"OpenRouter API returned status {response.status_code}: {body_text}"
            }

        data = response.json()

        # Extract message (OpenRouter may return 'tool_calls' while OpenAI-style returns 'function_call')
        choice = data.get("choices", [])[0]
        message = choice.get("message", {}) if isinstance(choice, dict) else {}

        # 1) OpenRouter-style tool call
        if "tool_calls" in message and len(message["tool_calls"]) > 0:
            tool_call = message["tool_calls"][0]
            # tool_call.function.arguments is expected as a JSON string
            tool_name = tool_call.get("function", {}).get("name")
            raw_args = tool_call.get("function", {}).get("arguments", "{}")
            try:
                tool_args = json.loads(raw_args)
            except json.JSONDecodeError:
                tool_args = {}

            tool_result = _execute_tool(tool_name, tool_args)

            # Add assistant content and the tool result as a proper tool-call pair.
            assistant_content = message.get("content") or ""
            messages.append({"role": "assistant", "content": assistant_content, "tool_calls": message.get("tool_calls", [])})
            messages.append({"role": "tool", "tool_call_id": tool_call.get("id"), "content": json.dumps(tool_result)})

            # Re-call model to get final response (without tools to avoid re-triggering tool selection)
            payload["messages"] = messages
            payload_second_call = {k: v for k, v in payload.items() if k not in ["tools", "tool_choice"]}
            with httpx.Client(timeout=30.0) as client:
                response = client.post(api_url, json=payload_second_call, headers=headers)

            if response.status_code >= 400:
                return {"success": False, "error": f"OpenRouter API returned status {response.status_code}: {response.text}"}

            final_data = response.json()
            final_choice = final_data.get("choices", [])[0]
            final_message = final_choice.get("message", {}).get("content", "")

            return {
                "success": True,
                "tool_name": tool_name,
                "tool_arguments": tool_args,
                "tool_result": tool_result,
                "assistant_reply": final_message
            }

        # 2) OpenAI-style function_call (fallback)
        function_call = message.get("function_call")
        if function_call:
            tool_name = function_call.get("name")
            try:
                tool_args = json.loads(function_call.get("arguments") or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            tool_result = _execute_tool(tool_name, tool_args)

            # Ensure content is never null
            assistant_content = message.get("content") or ""
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "function", "name": tool_name, "content": json.dumps(tool_result)})

            payload["messages"] = messages
            # Remove function-calling keys from second request
            payload_second_call = {k: v for k, v in payload.items() if k not in ["functions", "function_call"]}
            with httpx.Client(timeout=30.0) as client:
                response = client.post(api_url, json=payload_second_call, headers=headers)

            if response.status_code >= 400:
                return {"success": False, "error": f"OpenRouter API returned status {response.status_code}: {response.text}"}

            final_data = response.json()
            final_choice = final_data.get("choices", [])[0]
            final_message = final_choice.get("message", {}).get("content", "")

            return {
                "success": True,
                "tool_name": tool_name,
                "tool_arguments": tool_args,
                "tool_result": tool_result,
                "assistant_reply": final_message
            }

        # No tool/function call: simple assistant response
        return {
            "success": True,
            "tool_name": None,
            "tool_result": None,
            "assistant_reply": message.get("content", "No response from assistant")
        }
    
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}"
        }
    except (KeyError, json.JSONDecodeError) as e:
        return {
            "success": False,
            "error": f"Failed to parse response: {str(e)}"
        }




