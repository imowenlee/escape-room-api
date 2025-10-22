# 🧩 Escape Room Booking API

### Overview
A minimal **FastAPI + SQLite** project implementing an *escape room booking system* with 5-minute hold/expiration logic and race-condition-safe booking.

---

## 🚀 Quick Start

### 1️⃣ Setup environment
```bash
cd escape-room-api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Run API server
```bash
uvicorn main:app --reload
```
Visit → [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧱 Project Structure
```
escape-room-api/
├─ main.py          # FastAPI entry point
├─ db.py            # DB engine setup + seed data
├─ models.py        # ORM models
├─ routers/
│   ├─ holds.py     # /holds endpoints (create, confirm, release)
│   └─ slots.py     # /slots endpoints (list user-aware availability)
├─ tests/
│   └─ test_holds.py  # pytest examples
└─ requirements.txt
```

---

## 🗃 Database Schema
| Table | Purpose | Key Fields |
|--------|----------|-------------|
| **users** | demo users | `id`, `name`, `email` |
| **rooms** | escape rooms | `id`, `name`, `capacity` |
| **time_slots** | bookable time windows per room | `id`, `room_id`, `start_time`, `end_time`, `is_booked` |
| **holds** | temporary reservations | `id`, `slot_id`, `user_id`, `status`, `expires_at` |

---

## ⚙️ API Endpoints

### `GET /slots`
List slots for a given room.  
Supports optional `user_id` for **user-aware statuses**:
- `BOOKED`: confirmed booking
- `HELD_BY_ME`: user currently holds this slot (not expired)
- `HELD_BY_OTHER`: another user holds it (not expired)
- `AVAILABLE`: free to hold

Example:
```bash
GET /slots?room_id=r-101&user_id=u-demo
```

---

### `POST /holds`
Create a **5-minute hold** for a given `slot_id` and `user_id`.

#### Request
```json
{
  "slot_id": "s-1",
  "user_id": "u-demo"
}
```
#### Response `201`
```json
{
  "hold_id": "uuid",
  "status": "HOLD",
  "expires_at": "2025-10-22T03:15:00Z"
}
```
> Uses single-statement SQL (`INSERT ... SELECT ... WHERE NOT EXISTS`) for atomic race-safe creation.

---

### `POST /holds/{hold_id}/confirm`
Confirm a valid (non-expired) hold → marks slot as booked.

#### Request
```json
{
  "user_id": "u-demo"
}
```
#### Response
```json
{
  "hold_id": "uuid",
  "slot_id": "s-1",
  "status": "CONFIRMED"
}
```

---

### `POST /holds/{hold_id}/release`
Release a hold (by owner only).
#### Request
```json
{
  "user_id": "u-demo"
}
```
#### Response
```json
{
  "hold_id": "uuid",
  "status": "RELEASED"
}
```

---

## 💡 Expiration Logic (Lazy Expiration)
- Each hold lasts **5 minutes** (`expires_at = now + 5m`).
- No background job required.
- Any query/update ignores holds where `expires_at <= now()`.
- Ensures correctness even if background cleanup is never run.

---

## 🧪 Running Tests
```bash
pytest -q
```

Key test cases:
1. **Basic Flow** — create → confirm → verify booked.
2. **Conflict Handling** — two users attempt same slot → second gets 409 Conflict.

---

## 🧠 Design Notes
- **Concurrency safety**: implemented via single SQL atomic conditions.
- **Lazy expiration**: avoids background jobs.
- **User-awareness**: `/slots` reports `HELD_BY_ME` vs `HELD_BY_OTHER`.
- **Simple setup**: SQLite included; no external dependency.
- **Extensible**: easy to upgrade to Postgres by changing connection URL.

---

## 🧰 Future Enhancements
- Add `pg_cron` or Redis TTL-based real-time expiration.
- Enforce uniqueness via partial index (`WHERE status='HOLD' AND expires_at>now()`).
- Add `/holds/{id}/extend` endpoint (optional 1-time extension).
- Add room-level filtering & pagination for `/slots`.
