import time
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
from model import *
from tamar import router as tamar_route
from model import User, UserCreate, UserResponse, get_db
from openAI import Proxy as OpenAIProxy
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
from fastapi.requests import Request
from fastapi.responses import Response
import firebase_admin
from firebase_admin import credentials, messaging
from model import router as model_router

app.include_router(model_router, tags=["alerts"])

START_TIME = time.time()

cred = credentials.Certificate("../myphoneapp2025-firebase-adminsdk-fbsvc-af8b6574a1.json")
firebase_admin.initialize_app(cred)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("server")

app = FastAPI()
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    body = await request.body()
    log.info(f"↘️  Request: {request.method} {request.url} | Body: {body.decode(errors='ignore')}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    content = b""
    if isinstance(body_iter, AsyncIterable):
        async for chunk in body_iter:
            content += chunk
    else:
        for chunk in body_iter:
            content += chunk

        # איפוס ה־body_iterator עם התוכן המלא
        response.body_iterator = iter([content])

    log.info(f"↗️  Response: {request.method} {request.url.path} | status={response.status_code} | Time={process_time:.1f}ms | Body={content.decode(errors='ignore')}")
    return response

app.include_router(tamar_route, tags=["events"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # allow browsers from any origin
    allow_origin_regex=".*",        # also match any Origin header for WebSocket handshakes
    allow_methods=["*"],            # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],            # any request headers
    allow_credentials=True,         # send cookies/authifneeded
)
app.include_router(tamar_route, tags=["events"])

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    log.info(f"POST /users | Received: {user}")
    db_user = User(name=user.name, email=user.email, user_id=user.user_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log.info(f"User created in DB: {db_user}")
    return db_user

@app.get("/users", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    log.info(f"GET /users | skip={skip}, limit={limit} → Found: {len(users)} users")
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    log.info(f"GET /users/{user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        log.warning(f"User {user_id} not found")
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
        log.info(
            f"[📡 SENSOR] user_id={data.get('user_id')} | heart_rate={data.get('heart_rate')} | stress_level={data.get('stress_level')}")

    db_reading = SensorReading(**data)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    log.info(f"[🧠 DB] Saved SensorReading: id={db_reading.id} | time={db_reading.timestamp}")
    return db_reading

class AlertRequest(BaseModel):
    token: str
    title: str
    body: str
    data: dict | None = None


@app.post("/send-alert")
async def send_alert(req: AlertRequest):
    message_id = send_fcm_notification(
        token=req.token,
        title=req.title,
        body=req.body,
        data=req.data,
    )
    return {"success": True, "message_id": message_id}

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

# === Realtime Audio Proxy WebSocket and Health ===
proxy = OpenAIProxy()

@app.websocket("/v1/realtime")
async def realtime_ws(ws: WebSocket):
    await proxy.websocket_proxy(ws)

@app.get("/health")
async def health_proxy():
    return {"mode": "OpenAI" if proxy.use_ai else "local","status":"ok"}


def send_fcm_notification(token: str, title: str, body: str, data: dict | None = None) -> str:
    """
    שולחת הודעת פוש ל־FCM.
    מחזירה את message_id של FCM.
    """
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    return messaging.send(message)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint – מחזיר OK אם השרת חי.
    """
    return {
        "status": "ok",
        "uptime_ms": int((time.time() - START_TIME) * 1000)
    }
