from pathlib import Path
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional


from model import User, UserCreate, UserResponse, get_db
app = FastAPI()

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
