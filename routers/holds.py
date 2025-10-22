from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from datetime import datetime, timedelta
import uuid

router = APIRouter()

class CreateHoldBody(BaseModel):
    slot_id: str
    user_id: str

class ConfirmBody(BaseModel):
    user_id: str

class ReleaseBody(BaseModel):
    user_id: str

@router.post("", status_code=201)
def create_hold(body: CreateHoldBody, db: Session = Depends(get_db)):
    """
    Atomically create a 5-minute HOLD for a slot if:
      - slot exists and is not booked
      - no active (non-expired) HOLD exists for the same slot
    Uses single-statement INSERT...SELECT...WHERE NOT EXISTS to avoid races.
    """
    # Use UTC now for API response; SQL uses SQLite datetime('now')
    expires_in_minutes = 5

    hold_id = str(uuid.uuid4())

    sql = text("""
        INSERT INTO holds (id, slot_id, user_id, status, created_at, expires_at)
        SELECT :hold_id, :slot_id, :user_id, 'HOLD', datetime('now'), datetime('now', '+' || :mins || ' minutes')
        WHERE EXISTS (
            SELECT 1 FROM time_slots s WHERE s.id = :slot_id AND s.is_booked = 0
        )
        AND NOT EXISTS (
            SELECT 1 FROM holds h
            WHERE h.slot_id = :slot_id AND h.status = 'HOLD' AND h.expires_at > datetime('now')
        );
    """)
    res = db.execute(sql, {"hold_id": hold_id, "slot_id": body.slot_id, "user_id": body.user_id, "mins": expires_in_minutes})
    db.commit()

    if res.rowcount != 1:
        # Either slot not found/not available OR already held by someone
        raise HTTPException(status_code=409, detail="Slot is already held or booked.")

    # fetch expires_at for response
    fetch_sql = text("SELECT expires_at FROM holds WHERE id = :hold_id")
    row = db.execute(fetch_sql, {"hold_id": hold_id}).fetchone()
    return {"hold_id": hold_id, "status": "HOLD", "expires_at": row[0] if row else None}

@router.post("/{hold_id}/confirm")
def confirm_hold(hold_id: str, body: ConfirmBody, db: Session = Depends(get_db)):
    """
    Confirm a valid (non-expired) HOLD belonging to the user and book the slot.
    Done atomically using CTE-style sequence (emulated via short transaction).
    """
    # Validate the hold ownership and validity
    select_sql = text("""
        SELECT h.id, h.slot_id
        FROM holds h
        WHERE h.id = :hold_id
          AND h.user_id = :user_id
          AND h.status = 'HOLD'
          AND h.expires_at > datetime('now')
    """)
    row = db.execute(select_sql, {"hold_id": hold_id, "user_id": body.user_id}).fetchone()
    if not row:
        # Not found / not owned / expired
        raise HTTPException(status_code=410, detail="Hold not found or expired.")

    slot_id = row[1]

    # Book slot if not yet booked
    update_slot = text("""
        UPDATE time_slots SET is_booked = 1
        WHERE id = :slot_id AND is_booked = 0
    """)
    res1 = db.execute(update_slot, {"slot_id": slot_id})

    if res1.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slot already booked.")

    # Mark hold as confirmed
    update_hold = text("""
        UPDATE holds SET status = 'CONFIRMED'
        WHERE id = :hold_id
    """)
    db.execute(update_hold, {"hold_id": hold_id})
    db.commit()

    return {"hold_id": hold_id, "slot_id": slot_id, "status": "CONFIRMED"}

@router.post("/{hold_id}/release")
def release_hold(hold_id: str, body: ReleaseBody, db: Session = Depends(get_db)):
    # Only the owner can release an active hold
    select_sql = text("""
        SELECT h.id FROM holds h
        WHERE h.id = :hold_id
          AND h.user_id = :user_id
          AND h.status = 'HOLD'
    """)
    row = db.execute(select_sql, {"hold_id": hold_id, "user_id": body.user_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Hold not found or not releasable by user.")

    db.execute(text("UPDATE holds SET status = 'RELEASED' WHERE id = :hold_id"), {"hold_id": hold_id})
    db.commit()
    return {"hold_id": hold_id, "status": "RELEASED"}
