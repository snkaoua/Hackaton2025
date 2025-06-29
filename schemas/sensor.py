from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SensorStatus(BaseModel):
    heart_rate: bool
    accelerometer: bool
    skin_temp: bool
    ambient_temp: bool
    eda: bool

class SensorReadingCreate(BaseModel):
    user_id: str
    device_id: str
    timestamp: datetime

    heart_rate: Optional[int] = None
    heart_rate_bpm: Optional[int] = Field(None, alias="heart_rate_bpm")
    hrv_ms: Optional[float] = None
    acceleration: Optional[float] = None
    skin_temp_c: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    spo2_percent: Optional[float] = None
    eda_microsiemens: Optional[float] = None

    hr_baseline: Optional[int] = None
    hr_spike_rate: Optional[float] = None
    hrv_drop_percent: Optional[float] = None
    rage_probability: Optional[float] = None

    alert_level: Optional[str] = None
    stress_level: Optional[str] = None

    sensor_status: Optional[SensorStatus] = None

    class Config:
        populate_by_name = True

class SensorReadingResponse(SensorReadingCreate):
    id: int

    class Config:
        from_attributes = True
