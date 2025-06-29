# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import log
from app.routers import users, sensors, alerts, websocket

app = FastAPI(title="Realtime Audio System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(sensors.router, prefix="/readings", tags=["Sensor Readings"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(websocket.router, prefix="/v1", tags=["WebSocket"])

@app.get("/")
def root():
    return {"message": "Welcome to Realtime Audio System!"}
