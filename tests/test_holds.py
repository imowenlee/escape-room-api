import os
import tempfile
from fastapi.testclient import TestClient
from main import app
from db import init_db, SessionLocal
from models import TimeSlot, User

client = TestClient(app)

def get_first_available_slot_id():
    r = client.get("/slots")
    data = r.json()
    for s in data:
        if s["status"] == "AVAILABLE":
            return s["slot_id"]
    # fallback: first any
    return data[0]["slot_id"] if data else None

def test_hold_and_confirm_flow():
    # ensure DB is initialized
    init_db()

    # use seeded demo user
    user_id = "u-demo"
    slot_id = get_first_available_slot_id()
    assert slot_id is not None

    # create hold
    r = client.post("/holds", json={"slot_id": slot_id, "user_id": user_id})
    assert r.status_code == 201
    hold_id = r.json()["hold_id"]

    # confirm hold
    r2 = client.post(f"/holds/{hold_id}/confirm", json={"user_id": user_id})
    assert r2.status_code == 200
    assert r2.json()["status"] == "CONFIRMED"

    # slot should now be booked
    slots = client.get("/slots").json()
    s = next(x for x in slots if x["slot_id"] == slot_id)
    assert s["status"] == "BOOKED"

def test_conflict_on_second_hold_same_slot():
    init_db()
    user1 = "u-demo"
    user2 = "u-other"
    # seed another user if missing
    db = SessionLocal()
    try:
        from models import User
        if not db.query(User).filter(User.id == user2).first():
            db.add(User(id=user2, name="Other", email="other@example.com"))
            db.commit()
    finally:
        db.close()

    slot_id = get_first_available_slot_id()
    assert slot_id

    r1 = client.post("/holds", json={"slot_id": slot_id, "user_id": user1})
    assert r1.status_code == 201

    r2 = client.post("/holds", json={"slot_id": slot_id, "user_id": user2})
    assert r2.status_code == 409
