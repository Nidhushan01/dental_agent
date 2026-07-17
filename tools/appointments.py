"""Appointment management tools: check availability, book, reschedule, cancel."""
import datetime
from db.db import SessionLocal
from db.models import Appointment


def check_availability(date_str: str, time_str: str = None) -> dict:
    """Check if a slot is available on a given date (and optionally time).
    
    Args:
        date_str: Date in YYYY-MM-DD format
        time_str: Time in HH:MM format (optional; if not provided, return all slots for that day)
    
    Returns:
        dict with availability info
    """
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"available": False, "reason": f"Invalid date format: {date_str}"}
    
    session = SessionLocal()
    
    # Check for conflicts on that date
    existing = session.query(Appointment).filter(
        Appointment.date == date,
        Appointment.status != "cancelled"
    ).all()
    
    session.close()
    
    # Simple logic: if less than 3 appointments on that day, it's available
    if len(existing) < 3:
        return {"available": True, "date": date_str, "slots_available": 3 - len(existing)}
    else:
        return {"available": False, "date": date_str, "reason": "No slots available on this date"}


def book_appointment(name: str, date_str: str, time_str: str, service: str) -> dict:
    """Book a new appointment.
    
    Args:
        name: Patient name
        date_str: Date in YYYY-MM-DD format
        time_str: Time in HH:MM format
        service: Service type (e.g., "cleaning", "root canal")
    
    Returns:
        dict with confirmation or error
    """
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        time = datetime.datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return {"success": False, "error": "Invalid date or time format"}
    
    # Check availability first
    avail = check_availability(date_str, time_str)
    if not avail["available"]:
        return {"success": False, "error": avail.get("reason", "Date/time not available")}
    
    session = SessionLocal()
    
    # Create the appointment
    appointment = Appointment(
        name=name,
        date=date,
        time=time,
        service=service,
        status="confirmed"
    )
    session.add(appointment)
    session.commit()
    appt_id = appointment.id
    session.close()
    
    return {
        "success": True,
        "message": f"Appointment confirmed for {name} on {date_str} at {time_str}",
        "appointment_id": appt_id,
        "details": {"name": name, "date": date_str, "time": time_str, "service": service}
    }


def reschedule_appointment(appointment_id: int, new_date_str: str, new_time_str: str) -> dict:
    """Reschedule an existing appointment to a new date/time.
    
    Args:
        appointment_id: ID of the appointment to reschedule
        new_date_str: New date in YYYY-MM-DD format
        new_time_str: New time in HH:MM format
    
    Returns:
        dict with result
    """
    try:
        new_date = datetime.datetime.strptime(new_date_str, "%Y-%m-%d").date()
        new_time = datetime.datetime.strptime(new_time_str, "%H:%M").time()
    except ValueError:
        return {"success": False, "error": "Invalid date or time format"}
    
    session = SessionLocal()
    
    appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        session.close()
        return {"success": False, "error": f"Appointment {appointment_id} not found"}
    
    # Check availability at new time
    avail = check_availability(new_date_str, new_time_str)
    if not avail["available"]:
        session.close()
        return {"success": False, "error": "New date/time not available"}
    
    # Update
    old_date = appointment.date
    old_time = appointment.time
    appointment.date = new_date
    appointment.time = new_time
    session.commit()
    session.close()
    
    return {
        "success": True,
        "message": f"Rescheduled from {old_date} {old_time} to {new_date_str} {new_time_str}",
        "appointment_id": appointment_id
    }


def cancel_appointment(appointment_id: int) -> dict:
    """Cancel an appointment.
    
    Args:
        appointment_id: ID of the appointment to cancel
    
    Returns:
        dict with result
    """
    session = SessionLocal()
    
    appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        session.close()
        return {"success": False, "error": f"Appointment {appointment_id} not found"}
    
    appointment.status = "cancelled"
    session.commit()
    session.close()
    
    return {
        "success": True,
        "message": f"Appointment {appointment_id} has been cancelled",
        "appointment_id": appointment_id
    }

