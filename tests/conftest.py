# tests/conftest.py
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.models import Base, User, Room, TimeSlot
from app.main import app

@pytest.fixture(scope="function")
def test_db_session():
    os.environ["SKIP_DB_INIT"] = "1"

    # temp DB
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_url = f"sqlite:///{tmp.name}"

    # test engine / Session
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(test_db_session):
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

# —— Factories ——
@pytest.fixture
def make_user(test_db_session):
    def _make_user(user_id="u-1", name="User1", email="u1@example.com"):
        u = User(id=user_id, name=name, email=email)
        test_db_session.add(u)
        test_db_session.commit()
        return u
    return _make_user

@pytest.fixture
def make_room(test_db_session):
    def _make_room(room_id="r-1", name="Room 1", capacity=6):
        r = Room(id=room_id, name=name, capacity=capacity)
        test_db_session.add(r)
        test_db_session.commit()
        return r
    return _make_room

@pytest.fixture
def make_slot(test_db_session, make_room):
    from datetime import datetime, timedelta
    def _make_slot(slot_id="s-1", room_id=None, start=None, end=None, is_booked=False):
        if room_id is None:
            room = make_room()  # default 1 room
            room_id = room.id
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        start = start or (now + timedelta(hours=1))
        end = end or (start + timedelta(hours=1))
        ts = TimeSlot(id=slot_id, room_id=room_id, start_time=start, end_time=end, is_booked=is_booked)
        test_db_session.add(ts)
        test_db_session.commit()
        return ts
    return _make_slot