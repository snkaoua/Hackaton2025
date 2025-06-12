from __future__ import annotations

"""events.py – CRUD routes & SQLAlchemy model for the **Event** domain
-----------------------------------------------------------------------
This module encapsulates everything related to *events* in the system:
• SQLAlchemy model (``Event``)
• Pydantic schemas (``EventCreate`` & ``EventResponse``)
• FastAPI router with CRUD endpoints, including a filtered read for a specific user.

Usage (in ``main.py``):
>>> from events import router as events_router
>>> app.include_router(events_router)
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from model import Base, engine, get_db  # type: ignore

# ───────────────────────────── SQLAlchemy model ────────────────────────────────
class Event(Base):
    """Persisted *event* emitted by a device/user pair."""

    __tablename__ = "events"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, index=True, nullable=False)
    device_id: str = Column(String, index=True, nullable=False)

    event_type: str = Column(String, index=True, nullable=False)  # e.g. "rage", "stress"
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, index=True)

    description: Optional[str] = Column(Text, nullable=True)


# Create the table if it does not yet exist (only on first import)
Base.metadata.create_all(bind=engine)

# ───────────────────────────── Pydantic schemas ────────────────────────────────
class EventCreate(BaseModel):
    """Input payload for creating a new event (POST /events)."""

    user_id: int
    device_id: str
    event_type: str
    timestamp: Optional[datetime] = None  # if omitted → server‑side default (UTC now)
    description: Optional[str] = None


class EventResponse(EventCreate):
    """Serialized representation returned to clients."""

    id: int

    class Config:
        orm_mode = True  # Enable SQLAlchemy→Pydantic conversion


# ──────────────────────────────── API router ───────────────────────────────────
router = APIRouter(prefix="/events", tags=["events"])

# ─────────────── General listing ───────────────
@router.get("/", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
def list_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return **all** events (paginated)."""

    events = db.query(Event).offset(skip).limit(limit).all()
    return events


# ─────────────── Single event by ID ───────────────
@router.get("/{event_id}", response_model=EventResponse, status_code=status.HTTP_200_OK)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Return a **single** event by primary key."""

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# ─────────────── Events for a single user ───────────────
@router.get(
    "/check-for-tamar-status/{user_id}",
    response_model=List[EventResponse],
    status_code=status.HTTP_200_OK,
)
def check_for_tamar_status(user_id: int, db: Session = Depends(get_db)):
    """Return **all events** (possibly *zero*) for the given ``user_id``.
    If no events exist, an **empty list** is returned with HTTP 200 (OK).
    """

    events = (
        db.query(Event)
        .filter(Event.user_id == user_id)
        .order_by(Event.timestamp.desc())
        .all()
    )

    # No error raising – simply return the (possibly empty) list
    return events


# ─────────────────────────────── Future endpoints ──────────────────────────────
# Uncomment/extend as needed
# -----------------------------------------------------------------------------
#
# @router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
# def create_event(event: EventCreate, db: Session = Depends(get_db)):
#     data = event.dict(exclude_unset=True)
#     if not data.get("timestamp"):
#         data["timestamp"] = datetime.utcnow()
#     db_event = Event(**data)
#     db.add(db_event)
#     db.commit()
#     db.refresh(db_event)
#     return db_event
#
# @router.delete("/{event_id}", response_model=EventResponse, status_code=status.HTTP_200_OK)
# def delete_event(event_id: int, db: Session = Depends(get_db)):
#     event = db.query(Event).filter(Event.id == event_id).first()
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     db.delete(event)
#     db.commit()
#     return event
