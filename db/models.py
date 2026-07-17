from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)  # YYYY-MM-DD
    time = Column(Time, nullable=False)  # HH:MM:SS
    service = Column(String, nullable=False)  # e.g., "cleaning", "root canal"
    status = Column(String, default="confirmed")  # "confirmed", "completed", "cancelled"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
