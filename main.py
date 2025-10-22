from fastapi import FastAPI
from routers import holds, slots
from db import init_db

app = FastAPI(title="Escape Room Booking API", version="0.1.0")

# include routers
app.include_router(holds.router, prefix="/holds", tags=["holds"])
app.include_router(slots.router, prefix="/slots", tags=["slots"])

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {"ok": True, "service": "escape-room-api"}
