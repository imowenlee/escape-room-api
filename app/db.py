from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./escape_room.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import models here to create tables
    from app.models import User, Room, TimeSlot, Hold
    Base.metadata.create_all(bind=engine)

    # Seed minimal data if empty
    from sqlalchemy.orm import Session
    db: Session = SessionLocal()
    try:
        # Create a demo user, room and slots if none
        if not db.query(User).first():
            u = User(id="u-demo", name="Demo User", email="demo@example.com")
            db.add(u)
        if not db.query(Room).first():
            r = Room(id="r-101", name="Mystery Cave", capacity=6)
            db.add(r)
            db.flush()
        else:
            r = db.query(Room).first()
        if not db.query(TimeSlot).first():
            from datetime import datetime, timedelta
            now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            slots = []
            for i in range(3):
                start = now + timedelta(hours=i+1)
                end = start + timedelta(hours=1)
                slots.append(TimeSlot(id=f"s-{i+1}", room_id=r.id, start_time=start, end_time=end, is_booked=False))
            db.add_all(slots)
        db.commit()
    finally:
        db.close()
