from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    phone = Column(String)
    appointment_time = Column(DateTime, nullable=False)
    status = Column(String, default="booked")
    created_at = Column(DateTime, server_default=func.now())


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_phone = Column(String)
    transcript = Column(String)
    intent = Column(String)
    summary = Column(String)
    sentiment = Column(String)
    created_at = Column(DateTime, server_default=func.now())