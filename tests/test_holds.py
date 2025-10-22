from app.main import app 
# apply conftest.py fixtures: client, make_user, make_slot

def get_first_available_slot_id(client):
    r = client.get("/slots")
    r.raise_for_status()
    data = r.json()
    for s in data:
        if s["status"] == "AVAILABLE":
            return s["slot_id"]
    return data[0]["slot_id"] if data else None

def test_hold_and_confirm_flow(client, make_user, make_slot):
    # create data: user + slot
    u = make_user(user_id="u-demo", name="Demo", email="demo@example.com")
    make_slot(slot_id="s-1")

    slot_id = get_first_available_slot_id(client)
    assert slot_id == "s-1"

    # create hold
    r = client.post("/holds", json={"slot_id": slot_id, "user_id": u.id})
    assert r.status_code == 201
    hold_id = r.json()["hold_id"]

    # confirm hold
    r2 = client.post(f"/holds/{hold_id}/confirm", json={"user_id": u.id})
    assert r2.status_code == 200
    assert r2.json()["status"] == "CONFIRMED"

    # verify slot as booked
    slots = client.get("/slots").json()
    s = next(x for x in slots if x["slot_id"] == slot_id)
    assert s["status"] in ("BOOKED_BY_ME", "BOOKED_BY_OTHER", "BOOKED")

def test_conflict_on_second_hold_same_slot(client, make_user, make_slot):
    u1 = make_user(user_id="u-1", email="u1@example.com")
    u2 = make_user(user_id="u-2", email="u2@example.com")
    make_slot(slot_id="s-1")

    slot_id = get_first_available_slot_id(client)
    assert slot_id == "s-1"

    r1 = client.post("/holds", json={"slot_id": slot_id, "user_id": u1.id})
    assert r1.status_code == 201

    r2 = client.post("/holds", json={"slot_id": slot_id, "user_id": u2.id})
    assert r2.status_code in (409, 423)  # conflict code