from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Float, JSON, DateTime
from datetime import datetime
from dateutil import parser
from pydantic import BaseModel, Field

DATABASE_URL = "sqlite:///./test2.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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

    # שדות מורכבים (סטטוס חיישנים) – נשמר כ-JSON
    sensor_status = Column(JSON, nullable=True)

Base.metadata.create_all(bind=engine)
