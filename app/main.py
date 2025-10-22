import os
from fastapi import FastAPI
from routers import holds, slots
from app.db import init_db

app = FastAPI(title="Escape Room Booking API", version="0.1.0")

app.include_router(holds.router, prefix="/holds", tags=["holds"])
app.include_router(slots.router, prefix="/slots", tags=["slots"])

@app.on_event("startup")
def on_startup():
    if os.getenv("SKIP_DB_INIT") == "1":
        return
    init_db()

@app.get("/")
def root():
    return {"ok": True, "service": "escape-room-api"}