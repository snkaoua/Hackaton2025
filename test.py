from pathlib import Path
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

@app.get("/users")
def create_user():
    return {"response": "Hello World"}