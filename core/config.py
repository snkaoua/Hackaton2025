# app/core/config.py
import os
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "./serviceAccountKey.json")
cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_app = initialize_app(cred)
