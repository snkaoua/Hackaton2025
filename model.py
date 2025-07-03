from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Float, JSON, DateTime
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter
from firebase_admin import messaging

DATABASE_URL = "sqlite:///./test2.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# create a router
router = APIRouter()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    user_id = Column(Integer, nullable=True)


Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    name: str
    email: str
    user_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class UserRead(UserCreate):
    id: int
    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(String, index=True)        # "user_123"
    device_id     = Column(String, index=True)        # "galaxy_watch_4_real"
    timestamp     = Column(DateTime, default=datetime.utcnow)

#main indicators
    heart_rate        = Column(Integer, nullable=True)
    hrv_ms            = Column(Float,   nullable=True)
    acceleration      = Column(Float,   nullable=True)
    skin_temp_c       = Column(Float,   nullable=True)
    ambient_temp_c    = Column(Float,   nullable=True)
    spo2_percent      = Column(Float,   nullable=True)
    eda_microsiemens  = Column(Float,   nullable=True)

    # indicators
    hr_baseline       = Column(Integer, nullable=True)
    hr_spike_rate     = Column(Float,   nullable=True)
    hrv_drop_percent  = Column(Float,   nullable=True)
    rage_probability  = Column(Float,   nullable=True)

    alert_level   = Column(String, nullable=True)     # "ELEVATED"
    stress_level  = Column(String, nullable=True)     # "low"

    # additional indicators
    sensor_status = Column(JSON, nullable=True)

class AlertData(BaseModel):
    heart_rate: str
    stress_level: str
    status_message: str
    alert_type: str
    alert_message: str

class AlertRequest(BaseModel):
    #The token is used to authenticate the request
    token: str
    # The data contains the alert information
    data: AlertData


@router.post("/send_alert")
async def send_alert(request: AlertRequest):
    alert = request.data
    device_token = request.token

    # 1) לוג ל-console
    print(f"[ALERT RECEIVED] type={alert.alert_type} message={alert.alert_message}")

    # 2) בניית הודעת FCM
    # פה נשלח לכל המכשירים שנרשמו לנושא "alerts"
    message = messaging.Message(
        notification=messaging.Notification(
            title=f"Alert: {alert.alert_type.capitalize()}",
            body=alert.alert_message
        ),
        data=alert.dict(),           # שולח גם את כל השדות כ־data payload
        token=device_token               # או שתשנו ל־token=<DEVICE_TOKEN> אם אתם שולחים למכשיר ספציפי
    )

    # 3) שליחה ל־FCM
    try:
        response = messaging.send(message)
        return {"success": True, "message_id": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FCM send failed: {e}")

Base.metadata.create_all(bind=engine)



