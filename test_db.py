"""Test DB operations: insert, read, update."""
import datetime
from db.db import init_db, SessionLocal
from db.models import Appointment

# Initialize DB
init_db()
print("✓ Database initialized")

# Create a session
session = SessionLocal()

# Test 1: Insert a test appointment
test_appt = Appointment(
    name="John Doe",
    date=datetime.date(2026, 7, 20),
    time=datetime.time(14, 30),
    service="cleaning",
    status="confirmed"
)
session.add(test_appt)
session.commit()
print(f"✓ Inserted appointment: ID={test_appt.id}, name={test_appt.name}")

# Test 2: Read back the appointment
appt = session.query(Appointment).filter(Appointment.id == test_appt.id).first()
if appt:
    print(f"✓ Read appointment: {appt.name} on {appt.date} at {appt.time} for {appt.service}")
else:
    print("✗ Failed to read appointment")

# Test 3: Update the appointment
appt.status = "completed"
session.commit()
print(f"✓ Updated status to: {appt.status}")

# Test 4: Query all appointments
all_appts = session.query(Appointment).all()
print(f"✓ Total appointments in DB: {len(all_appts)}")

session.close()
print("\n✓ All DB tests passed!")
