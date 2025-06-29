from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from app.models.user import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(String, index=True)
    device_id     = Column(String, index=True)
    timestamp     = Column(DateTime, default=datetime.utcnow)

    heart_rate        = Column(Integer, nullable=True)
    hrv_ms            = Column(Float,   nullable=True)
    acceleration      = Column(Float,   nullable=True)
    skin_temp_c       = Column(Float,   nullable=True)
    ambient_temp_c    = Column(Float,   nullable=True)
    spo2_percent      = Column(Float,   nullable=True)
    eda_microsiemens  = Column(Float,   nullable=True)

    hr_baseline       = Column(Integer, nullable=True)
    hr_spike_rate     = Column(Float,   nullable=True)
    hrv_drop_percent  = Column(Float,   nullable=True)
    rage_probability  = Column(Float,   nullable=True)

    alert_level   = Column(String, nullable=True)
    stress_level  = Column(String, nullable=True)
    sensor_status = Column(JSON, nullable=True)