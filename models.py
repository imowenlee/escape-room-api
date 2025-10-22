from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    created_at = Column(DateTime)

class Room(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime)

class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(String, primary_key=True)
    room_id = Column(String, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint("strftime('%s', end_time) > strftime('%s', start_time)", name="slot_time_valid"),
        UniqueConstraint("room_id", "start_time", "end_time", name="uniq_room_slot_window"),
    )

class Hold(Base):
    __tablename__ = "holds"
    id = Column(String, primary_key=True)
    slot_id = Column(String, ForeignKey("time_slots.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # HOLD|CONFIRMED|RELEASED|EXPIRED
    created_at = Column(DateTime)
    expires_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint("status in ('HOLD','CONFIRMED','RELEASED','EXPIRED')", name="hold_status_valid"),
    )
