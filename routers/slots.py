from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db

router = APIRouter()

@router.get("")
def list_slots(
    room_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    List time slots with user-aware availability status:
      - BOOKED: time_slots.is_booked = 1
      - HELD_BY_ME: there is an active hold (status='HOLD' AND expires_at > now) by this user_id
      - HELD_BY_OTHER: there is an active hold by someone else
      - AVAILABLE: otherwise

    If user_id is not provided, falls back to simple AVAILABLE/HELD/BOOKED (HELD means held by someone).
    """
    params = {}
    where = ""
    if room_id:
        where = "WHERE s.room_id = :room_id"
        params["room_id"] = room_id

    # Get active hold's user_id if any (LIMIT 1). Using a scalar subquery keeps it SQLite friendly.
    sql = text(f"""
        SELECT
            s.id AS slot_id,
            s.room_id,
            s.start_time,
            s.end_time,
            s.is_booked,
            (
                SELECT h.user_id
                FROM holds h
                WHERE h.slot_id = s.id
                AND h.status = 'CONFIRMED'
                LIMIT 1
            ) AS booked_user_id,
            (
              SELECT h.user_id
              FROM holds h
              WHERE h.slot_id = s.id
                AND h.status = 'HOLD'
                AND h.expires_at > datetime('now')
              LIMIT 1
            ) AS hold_user_id
        FROM time_slots s
        {where}
        ORDER BY s.start_time ASC
    """)
    rows = db.execute(sql, params).fetchall()

    results = []
    for r in rows:
        if r.is_booked:
            if user_id and r.booked_user_id == user_id:
                status = "BOOKED_BY_ME"
            else:
                status = "BOOKED_BY_OTHER"
        elif r.hold_user_id is None:
            status = "AVAILABLE"
        else:
            if user_id and r.hold_user_id == user_id:
                status = "HELD_BY_ME"
            else:
                status = "HELD_BY_OTHER" if user_id else "HELD"
        results.append({
            "slot_id": r.slot_id,
            "room_id": r.room_id,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "status": status
        })
    return results
