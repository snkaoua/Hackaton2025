import time
import logging
from pathlib import Path
import shutil
from datetime import datetime
from typing import List, Optional, AsyncIterable

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, Response
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker

from model import (
    router       as model_router,
    User, UserCreate, UserResponse, get_db,
    SensorReading, SensorReadingCreate, SensorReadingResponse,
    send_fcm_notification
)
from model import router as alert_router
from tamar import router as tamar_route
from openAI import Proxy as OpenAIProxy
from firebase_config  import get_db_reference, write_test
from firebase_admin import messaging, credentials, db

app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("server")

app.include_router(model_router, tags=["alerts"])
app.include_router(alert_router, prefix="")

START_TIME = time.time()

cred = credentials.Certificate("../myphoneapp2025-firebase-adminsdk-fbsvc-af8b6574a1.json")
firebase_admin.initialize_app(cred)

@app.on_event("startup")
def startup_event():
    # Optionally verify Firebase connectivity on startup
    result = write_test()
    print("Firebase test data:", result)

@app.get("/firebase-test")
def firebase_test():
    """
        Endpoint to test reading and writing to Firebase.
        Writes a sample object to '/test' and returns both written and read data.
        """
    ref = get_db_reference("/test")
    data = {"msg": "hello from FastAPI", "time": datetime.utcnow().isoformat()}
    # Write data to Firebase
    ref.set(data)
    # Read the data back from Firebase
    return {"wrote": data, "read": ref.get()}

@app.post("/operations/{op_id}")
def create_operation(op_id: str, payload: dict):
    """
        Create a new operation entry in Firebase under '/operations/{op_id}'.
        Stores the provided payload and a timestamp, then returns the stored data.
        """
    ref = get_db_reference(f"/operations/{op_id}")
    ref.set({
        "payload": payload,
        "createdAt": datetime.utcnow().isoformat()
    })
    # Write operation entry to Firebase
    # Retrieve stored entry for confirmation
    return {"id": op_id, "stored": ref.get()}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    log.info(f"↘️  Incoming Request → {request.method} {request.url}")
    start_time = time.time()
    log.debug("Recorded start time")
    body = await request.body()
    log.info(f"↘️  Request: {request.method} {request.url} | Body: {body.decode(errors='ignore')}")

    log.info("Calling next handler in middleware chain")
    response = await call_next(request)
    log.info("Received Response object from call_next")

    process_time = (time.time() - start_time) * 1000
    log.debug(f"Processing time (ms): {process_time:.1f}")

    content = b""
    if isinstance(body_iter, AsyncIterable):
        log.debug("body_iterator is AsyncIterable, reading chunks async")
        async for chunk in body_iter:
            content += chunk
            log.debug(f"Read {len(content)} bytes asynchronously")
    else:
        log.debug("body_iterator is sync iterable, reading chunks")
        for chunk in body_iter:
            content += chunk
            log.debug(f"Read {len(content)} bytes synchronously")

        # איפוס ה־body_iterator עם התוכן המלא
        response.body_iterator = iter([content])
        log.info(f"↗️  Response Body (length={len(content)}): {content.decode(errors='ignore')}")

    log.info(f"↗️  Response: {request.method} {request.url.path} | status={response.status_code} | Time={process_time:.1f}ms | Body={content.decode(errors='ignore')}")
    return response

log.info("Registering router tamar_route with tags ['events']")
app.include_router(tamar_route, tags=["events"])

log.info("Adding CORS middleware: allow_origins=['*'], allow_methods=['*'], allow_headers=['*']")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # allow browsers from any origin
    allow_origin_regex=".*",        # also match any Origin header for WebSocket handshakes
    allow_methods=["*"],            # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],            # any request headers
    allow_credentials=True,         # send cookies/authifneeded
)

log.info("Re-registering router tamar_route with tags ['events']")
app.include_router(tamar_route, tags=["events"])

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    log.info(f"POST /users | Received: {user}")
    db_user = User(name=user.name, email=user.email, user_id=user.user_id)
    logger.info(f"Instantiated User object (not yet persisted): {db_user}")
    logger.info("Adding new user to DB session")
    db.add(db_user)
    logger.info("Committing transaction for new user")
    db.commit()
    logger.info(f"Refreshing User from DB (id: {db_user.id})")
    db.refresh(db_user)
    logger.info(f"User created successfully: {db_user}")
    return db_user

@app.get("/users", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    log.info(f"GET /users → skip={skip}, limit={limit}")

    log.debug(f"Querying DB: OFFSET {skip} LIMIT {limit}")
    users = db.query(User).offset(skip).limit(limit).all()
    log.info(f"GET /users | skip={skip}, limit={limit} → Found: {len(users)} users")

    log.info(f"Returning {len(response)} users to client")
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    log.info(f"GET /users/{user_id}")

    log.debug(f"Path parameter: user_id={user_id}")

    log.info(f"Querying database for user with id={user_id}")
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        log.warning(f"User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    log.info(
        f"User found: id={user.id}, "
        f"name='{user.name}', email='{user.email}'"
    )

    log.debug(f"Returning UserResponse for id={user.id}")
    return user

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):

    log.info(f"PUT /users/{user_id} called | payload: {user.dict(exclude_unset=True)}")
    db_user = db.query(User).filter(User.id == user_id).first()
    log.info(f"Database lookup for user_id={user_id}: {'FOUND' if db_user else 'NOT FOUND'}")

    if db_user is None:
        log.warning(f"User {user_id} not found, raising 404")
        raise HTTPException(status_code=404, detail="User not found")

    
    db_user.name = user.name if user.name is not None else db_user.name
    db_user.email = user.email if user.email is not None else db_user.email

    log.info(
        f"Updating user {user_id}: "
        f"name '{old_name}' → '{new_name}', "
        f"email '{old_email}' → '{new_email}'"
    )

    log.info(f"Committing changes for user {user_id}")
    db.commit()

    log.info(f"Refreshing user {user_id} from database")
    db.refresh(db_user)

    log.info(f"User {user_id} updated successfully: {db_user}")
    return db_user

@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):

    log.info(f"DELETE /users/{user_id} called")

    log.info(f"Querying DB for user_id={user_id}")
    db_user = db.query(User).filter(User.id == user_id).first()
    log.info(f"Database lookup for user_id={user_id}: {'FOUND' if db_user else 'NOT FOUND'}")

    if db_user is None:
        log.warning(f"User {user_id} not found, raising 404")
        raise HTTPException(status_code=404, detail="User not found")

    log.info(f"Deleting user {user_id} from DB")
    db.delete(db_user)

    log.info("Committing transaction for delete")
    db.commit()

    log.info(f"User {user_id} deleted successfully")
    return db_user

log.info(
    "Adding CORS middleware: "
    "allow_origins=['*'], allow_credentials=True, "
    "allow_methods=['*'], allow_headers=['*']"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = Path("uploaded_files")
log.info(f"Ensuring upload directory exists at: {UPLOAD_DIRECTORY}")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
log.info(f"Upload directory ready: {UPLOAD_DIRECTORY}")


@app.get("/")
async def root():
    log.info("GET / called")

    log.debug(f"Response payload: {message}")
    return {"message": "Welcome to FastAPI example!"}


@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    log.info(f"POST /uploadfile called | filename: '{file.filename}'")

    if not file.filename:
        log.warning("No filename provided in upload")
        raise HTTPException(status_code=400, detail="No file provided")

    log.info(f"Saving uploaded file to: {file_location}")
    file_location = UPLOAD_DIRECTORY / file.filename


    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    log.info(f"File saved successfully: {file_location}")
    # Reopen the file to read its content after saving

    with open(file_location, "rb") as f:
        content = f.read().strip()
        log.info(f"Read {len(content)} bytes from saved file")

    result = {
        "filename": file.filename,
        "detail": "File uploaded successfully",
        "content": content
    }

    log.debug(f"Response payload: {{'filename': '{file.filename}', 'detail': '...', 'content_length': {len(content)}}}")
    log.info(f"Returning success response for '{file.filename}'")
    return result


@app.get("/downloadfile/{filename}")
async def download_file(filename: str):
    log.info(f"GET /downloadfile/{filename} called")
    file_location = UPLOAD_DIRECTORY / filename
    log.info(f"Checking if file exists at: {file_location}")

    if not file_location.is_file():
        log.warning(f"File not found: {file_location}")
        raise HTTPException(status_code=404, detail="File not found")

    log.info(f"File found: {file_location}, returning FileResponse")
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
    log.info(f"POST /readings called | payload: {reading.model_dump(by_alias=True, exclude_unset=True)}")
    # אם מגיע גם heart_rate_bpm – נעדיף אותו אם heart_rate חסר

    data = reading.model_dump(by_alias=True, exclude_unset=True)
    log.debug(f"Parsed reading data: {data}")

    if "heart_rate_bpm" in data and "heart_rate" not in data:
        data["heart_rate"] = data.pop("heart_rate_bpm")
        log.info(
            f"[📡 SENSOR] user_id={data.get('user_id')} | heart_rate={data.get('heart_rate')} | stress_level={data.get('stress_level')}")

    log.info("Instantiating SensorReading model")
    db_reading = SensorReading(**data)

    log.info("Adding SensorReading to DB session")
    db.add(db_reading)

    log.info("Committing DB session")
    db.commit()

    log.info("Refreshing SensorReading from DB")
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
    log.info(f"POST /send-alert called | payload: {req.dict()}")

    log.info(
        f"Calling send_fcm_notification with token={req.token}, "
        f"title={req.title}, body={req.body}"
    )
    message_id = send_fcm_notification(
        token=req.token,
        title=req.title,
        body=req.body,
        data=req.data,
    )

    log.info(f"FCM notification sent successfully | message_id={message_id}")
    return {"success": True, "message_id": message_id}

@app.get("/readings/{reading_id}", response_model=SensorReadingResponse)
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    log.info(f"GET /readings/{reading_id} called")

    log.debug(f"Path parameter: reading_id={reading_id}")

    log.info(f"Querying DB for SensorReading id={reading_id}")
    reading = db.query(SensorReading).filter(
        SensorReading.id == reading_id
    ).first()


    if not reading:
        log.warning(f"SensorReading id={reading_id} not found")
        raise HTTPException(status_code=404, detail="Reading not found")

    log.info(f"SensorReading found: id={reading.id} | timestamp={reading.timestamp}")

    log.debug(f"Returning SensorReadingResponse for id={reading.id}")
    return reading


@app.get("/")
def health():
    log.info("GET / → root health check")
    return {"status": "ok"}

# === Realtime Audio Proxy WebSocket and Health ===
proxy = OpenAIProxy()

@app.websocket("/v1/realtime")
async def realtime_ws(ws: WebSocket):
    log.info("WebSocket /v1/realtime connection opened")
    await proxy.websocket_proxy(ws)
    log.info("WebSocket /v1/realtime connection closed")

@app.get("/health")
async def health_proxy():
    log.info("GET /health → proxy health check")
    log.info(f"GET /health → proxy response: {result}")
    return {"mode": "OpenAI" if proxy.use_ai else "local","status":"ok"}


def send_fcm_notification(token: str, title: str, body: str, data: dict | None = None) -> str:
    """
    שולחת הודעת פוש ל־FCM.
    מחזירה את message_id של FCM.
    """
    log.info(f"FCM → sending notification to token={token} | title={title!r}")
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )

    log.info(f"FCM → sent successfully | message_id={message_id}")
    return messaging.send(message)


@app.get("/health", tags=["Health"])
async def health_check():
    log.info("GET /health [Health tag] → uptime health check")
    """
    Health check endpoint – מחזיר OK אם השרת חי.
    """

    log.info(f"GET /health [Health tag] → response: {result}")
    return {
        "status": "ok",
        "uptime_ms": int((time.time() - START_TIME) * 1000)
    }
