"""Test appointment tools directly."""
import datetime
from tools.appointments import check_availability, book_appointment, reschedule_appointment, cancel_appointment

print("=" * 60)
print("Testing Appointment Tools")
print("=" * 60)

# Test 1: Check availability
print("\n[1] Testing check_availability()...")
future_date = (datetime.date.today() + datetime.timedelta(days=5)).strftime("%Y-%m-%d")
result = check_availability(future_date)
print(f"  Result: {result}")
assert result["available"], "Should have availability"

# Test 2: Book an appointment
print("\n[2] Testing book_appointment()...")
book_result = book_appointment(
    name="Alice Smith",
    date_str=future_date,
    time_str="10:00",
    service="cleaning"
)
print(f"  Result: {book_result}")
assert book_result["success"], "Booking should succeed"
appt_id = book_result["appointment_id"]

# Test 3: Check availability again (should be reduced)
print("\n[3] Checking availability after booking...")
result = check_availability(future_date)
print(f"  Result: {result}")
assert result["available"], "Should still have availability"

# Test 4: Book another appointment on the same day
print("\n[4] Booking another appointment on the same day...")
book_result2 = book_appointment(
    name="Bob Johnson",
    date_str=future_date,
    time_str="11:00",
    service="checkup"
)
print(f"  Result: {book_result2}")
assert book_result2["success"], "Second booking should succeed"

# Test 5: Reschedule the first appointment
print("\n[5] Testing reschedule_appointment()...")
new_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
reschedule_result = reschedule_appointment(appt_id, new_date, "14:30")
print(f"  Result: {reschedule_result}")
assert reschedule_result["success"], "Reschedule should succeed"

# Test 6: Cancel an appointment
print("\n[6] Testing cancel_appointment()...")
cancel_result = cancel_appointment(appt_id)
print(f"  Result: {cancel_result}")
assert cancel_result["success"], "Cancel should succeed"

print("\n" + "=" * 60)
print("✓ All appointment tool tests passed!")
print("=" * 60)
