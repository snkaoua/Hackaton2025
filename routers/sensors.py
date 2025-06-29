from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.sensor import SensorReading
from app.schemas.sensor import SensorReadingCreate, SensorReadingResponse
from app.core.logger import log

router = APIRouter()

@router.post("/", response_model=SensorReadingResponse, status_code=201)
def create_reading(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    data = reading.model_dump(by_alias=True, exclude_unset=True)
    if "heart_rate_bpm" in data and "heart_rate" not in data:
        data["heart_rate"] = data.pop("heart_rate_bpm")
    db_reading = SensorReading(**data)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    log.info(f"[🧠 DB] Saved SensorReading: id={db_reading.id}")
    return db_reading

@router.get("/{reading_id}", response_model=SensorReadingResponse)
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading