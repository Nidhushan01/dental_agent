"""Dental MCP Server — exposes dental tools via the Model Context Protocol (MCP).

This module defines the FastMCP server that wraps the existing dental tool
functions as MCP-compliant tools.  It is designed to run **in-process**
alongside the FastAPI application: no extra port or subprocess is required.

Usage (in-process):
    from mcp_server import dental_mcp
    from fastmcp import Client

    async with Client(dental_mcp) as client:
        tools = await client.list_tools()
        result = await client.call_tool("check_availability", {"date": "2026-07-25"})
"""

from fastmcp import FastMCP

from tools.appointments import (
    check_availability as _check_availability,
    book_appointment as _book_appointment,
    reschedule_appointment as _reschedule_appointment,
    cancel_appointment as _cancel_appointment,
)
from tools.faq import get_faq as _get_faq

# ---------------------------------------------------------------------------
# Create the FastMCP server instance
# ---------------------------------------------------------------------------

dental_mcp = FastMCP(
    name="DentalWebAgent",
    instructions=(
        "You are a helpful dental clinic assistant. "
        "Use the provided tools to manage appointments and answer FAQs. "
        "Always confirm details with the patient before booking."
    ),
)


# ---------------------------------------------------------------------------
# Tool: check_availability
# ---------------------------------------------------------------------------

@dental_mcp.tool()
def check_availability(date: str, time: str = None) -> dict:
    """Check if appointment slots are available on a given date.

    Args:
        date: Date in YYYY-MM-DD format (e.g., 2026-07-20).
        time: Optional time in HH:MM 24-hour format. If omitted, returns
              availability for the whole day.

    Returns:
        dict with keys:
            available (bool): Whether a slot exists.
            slots_available (int): Number of free slots (when available=True).
            date (str): The queried date.
            reason (str): Why unavailable (when available=False).
    """
    return _check_availability(date, time)


# ---------------------------------------------------------------------------
# Tool: book_appointment
# ---------------------------------------------------------------------------

@dental_mcp.tool()
def book_appointment(name: str, date: str, time: str, service: str) -> dict:
    """Book a new dental appointment for a patient.

    Args:
        name: Patient's full name.
        date: Appointment date in YYYY-MM-DD format.
        time: Appointment time in HH:MM 24-hour format.
        service: Type of dental service (e.g., 'cleaning', 'checkup',
                 'root canal', 'extraction', 'filling', 'implant').

    Returns:
        dict with keys:
            success (bool): Whether the booking succeeded.
            message (str): Confirmation or error message.
            appointment_id (int): ID of the new appointment (on success).
            details (dict): Booking details (on success).
            error (str): Reason for failure (on failure).
    """
    return _book_appointment(
        name=name,
        date_str=date,
        time_str=time,
        service=service,
    )


# ---------------------------------------------------------------------------
# Tool: reschedule_appointment
# ---------------------------------------------------------------------------

@dental_mcp.tool()
def reschedule_appointment(
    appointment_id: int,
    new_date: str,
    new_time: str,
) -> dict:
    """Reschedule an existing appointment to a new date and time.

    Args:
        appointment_id: Numeric ID of the appointment to reschedule.
        new_date: New date in YYYY-MM-DD format.
        new_time: New time in HH:MM 24-hour format.

    Returns:
        dict with keys:
            success (bool): Whether the reschedule succeeded.
            message (str): Confirmation or error message.
            appointment_id (int): The rescheduled appointment ID.
            error (str): Reason for failure (on failure).
    """
    return _reschedule_appointment(
        appointment_id=appointment_id,
        new_date_str=new_date,
        new_time_str=new_time,
    )


# ---------------------------------------------------------------------------
# Tool: cancel_appointment
# ---------------------------------------------------------------------------

@dental_mcp.tool()
def cancel_appointment(appointment_id: int) -> dict:
    """Cancel an existing dental appointment.

    Args:
        appointment_id: Numeric ID of the appointment to cancel.

    Returns:
        dict with keys:
            success (bool): Whether the cancellation succeeded.
            message (str): Confirmation or error message.
            appointment_id (int): The cancelled appointment ID.
            error (str): Reason for failure (on failure).
    """
    return _cancel_appointment(appointment_id=appointment_id)


# ---------------------------------------------------------------------------
# Tool: get_faq
# ---------------------------------------------------------------------------

@dental_mcp.tool()
def get_faq(topic: str) -> dict:
    """Get an answer to a frequently asked question about dental care.

    Covers topics such as post-operative care, office hours, insurance,
    payment options, costs, and common procedures.

    Args:
        topic: Keyword describing the topic. Examples: 'post-extraction',
               'hours', 'insurance', 'cost', 'root-canal', 'implant',
               'braces', 'after-filling', 'after-cleaning'.

    Returns:
        dict with key:
            answer (str): The FAQ answer text.
    """
    return {"answer": _get_faq(topic)}
