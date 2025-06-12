from pathlib import Path
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session
from model import BiometricInput, BiometricResponse
from fastapi import Depends
from sqlalchemy.orm import Session
from model import *

from model import User, UserCreate, UserResponse, get_db
app = FastAPI()

def detect_state(data: BiometricInput) -> str:
    hr = data.heart_rate
    hrv = data.hrv
    temp = data.skin_temp
    move = data.movement.lower()
    spo2 = data.spo2
    eda = data.eda
    env = data.env_temp

    # 😌 מנוחה
    if 55 <= hr <= 75 and 50 <= hrv <= 80 and 32.5 <= temp <= 34.5 and ("zero" in move or "gentle" in move) and spo2 > 96 and 1 <= eda <= 4 and 20 <= env <= 28:
        return "😌 Rest"

    # 🏃‍♀️ פעילות גופנית
    elif 100 <= hr <= 170 and 30 <= hrv <= 50 and 0.5 <= (temp - 32) <= 1 and "strong" in move and spo2 > 95 and 6 <= eda <= 12 and 20 <= env <= 35:
        return "🏃‍♀️ Physical Activity"

    # 💓 פעילות מינית
    elif 85 <= hr <= 160 and 20 <= hrv <= 40 and 0.5 <= (temp - 32) <= 1.2 and "jumps" in move and 94 <= spo2 <= 99 and 5 <= eda <= 10 and 20 <= env <= 28:
        return "💓 Sexual Activity"

    # 😰 התקף חרדה
    elif 100 <= hr <= 130 and 10 <= hrv <= 35 and 31.5 <= temp <= 32.5 and ("tremor" in move or "sharp" in move) and 90 <= spo2 <= 96 and 8 <= eda <= 14 and 20 <= env <= 28:
        return "😰 Anxiety Attack"

    # 😡 התקף זעם
    elif 95 <= hr <= 140 and 15 <= hrv <= 40 and (temp < 31.5 or temp > 32.5) and "sharp" in move and spo2 > 94 and 10 <= eda <= 16 and 20 <= env <= 28:
        return "😡 Rage Attack"

    # 😍 התרגשות רגשית
    elif 85 <= hr <= 110 and 40 <= hrv <= 65 and 0.3 <= (temp - 32) <= 0.6 and "tremor" in move and spo2 >= 96 and 4 <= eda <= 7 and 20 <= env <= 28:
        return "😍 Emotional Excitement"

    # 🥶 פחד קפוא
    elif 70 <= hr <= 100 and 20 <= hrv <= 40 and 31 <= temp <= 32 and ("freeze" in move or "little movement" in move) and spo2 > 95 and 1 <= eda <= 4 and env < 20:
        return "🥶 Frozen Fear"

    # 💤 שינה עמוקה
    elif 45 <= hr <= 65 and 50 <= hrv <= 80 and 33 <= temp <= 34.5 and ("zero" in move or "minimal" in move) and spo2 > 96 and 1 <= eda <= 3 and 18 <= env <= 25:
        return "💤 Deep Sleep"

    # 🧠 עומס קוגניטיבי
    elif 80 <= hr <= 100 and 30 <= hrv <= 50 and 3 <= eda <= 6 and "minimal" in move and spo2 >= 96 and 22 <= env <= 28:
        return "🧠 Cognitive Load"

    # 📺 בינג'/מסך
    elif 60 <= hr <= 85 and 40 <= hrv <= 60 and temp > 32 and "zero" in move and spo2 >= 96 and 2 <= eda <= 5 and 22 <= env <= 28:
        return "📺 Binge/Screen Time"

    # 🧍‍♀️ בדידות
    elif 65 <= hr <= 90 and 25 <= hrv <= 45 and "minimal" in move and spo2 >= 96 and 2 <= eda <= 4 and 20 <= env <= 28:
        return "🧍‍♀️ Loneliness"

    # 🥵 חום/זיהום
    elif temp > 35.5 and 5 <= eda <= 9 and 20 <= env <= 28:
        return "🥵 Fever/Infection"

    # 🫁 קוצר נשימה
    elif 90 <= hr <= 120 and hrv < 40 and spo2 < 93 and ("flat breaths" in move or "shallow" in move) and 4 <= eda <= 8 and 20 <= env <= 28:
        return "🫁 Shortness of Breath"

    # 😴 עייפות
    elif 60 <= hr <= 75 and 30 <= hrv <= 50 and (temp > 32 or temp == 32) and ("low movement" in move or "minimal" in move) and 2 <= eda <= 4 and 20 <= env <= 28:
        return "😴 Fatigue"

    else:
        return "🤷‍♂️ Unknown State"



@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email, user_id=user.user_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.name = user.name if user.name is not None else db_user.name
    db_user.email = user.email if user.email is not None else db_user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return db_user

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = Path("uploaded_files")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI example!"}


@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    file_location = UPLOAD_DIRECTORY / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Reopen the file to read its content after saving

    with open(file_location, "rb") as f:
        content = f.read().strip()

    result = {
        "filename": file.filename,
        "detail": "File uploaded successfully",
        "content": content
    }
    return result


@app.get("/downloadfile/{filename}")
async def download_file(filename: str):
    file_location = UPLOAD_DIRECTORY / filename
    if not file_location.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_location, filename=filename)


# ────────────────────────── Pydantic schema ───────────────────────
class SensorStatus(BaseModel):
    heart_rate: bool
    accelerometer: bool
    skin_temp: bool
    ambient_temp: bool
    eda: bool


class SensorReadingCreate(BaseModel):
    # מזהים
    user_id: str
    device_id: str
    timestamp: datetime

    heart_rate: Optional[int]          = None
    heart_rate_bpm: Optional[int]      = Field(None, alias="heart_rate_bpm")
    hrv_ms: Optional[float]            = None
    acceleration: Optional[float]      = None
    skin_temp_c: Optional[float]       = None
    ambient_temp_c: Optional[float]    = None
    spo2_percent: Optional[float]      = None
    eda_microsiemens: Optional[float]  = None

    # אינדיקטורים
    hr_baseline: Optional[int]         = None
    hr_spike_rate: Optional[float]     = None
    hrv_drop_percent: Optional[float]  = None
    rage_probability: Optional[float]  = None

    alert_level: Optional[str]         = None
    stress_level: Optional[str]        = None

    sensor_status: Optional[SensorStatus] = None

    class Config:
        populate_by_name = True        # מכבד alias (heart_rate_bpm)


class SensorReadingResponse(SensorReadingCreate):
    id: int

    class Config:
        from_attributes = True

@app.post("/readings", response_model=SensorReadingResponse, status_code=201)
def create_reading(
    reading: SensorReadingCreate,
    db: Session = Depends(get_db)
):
    # אם מגיע גם heart_rate_bpm – נעדיף אותו אם heart_rate חסר
    data = reading.model_dump(by_alias=True, exclude_unset=True)
    if "heart_rate_bpm" in data and "heart_rate" not in data:
        data["heart_rate"] = data.pop("heart_rate_bpm")

    db_reading = SensorReading(**data)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading


@app.get("/readings/{reading_id}", response_model=SensorReadingResponse)
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    reading = db.query(SensorReading).filter(
        SensorReading.id == reading_id
    ).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/biometric/state", response_model=BiometricResponse)
def get_state(data: BiometricInput, db: Session = Depends(get_db)):
    state = detect_state(data)
    return {"state": state}
