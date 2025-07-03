# firebase_config.py

import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Load the service account credentials from JSON file
cred = credentials.Certificate("../myphoneapp2025-firebase-adminsdk-fbsvc-6b9cc6a64c.json")

# Initialize the Firebase app with the Realtime Database URL
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://myphoneapp2025-default-rtdb.firebaseio.com/"
})

def get_db_reference(path: str):
    """
        Return a reference to the specified Realtime Database path.
        This helper simplifies reading and writing data.
        """
    return db.reference(path)

def write_test():
    """
        Write a test object to '/test' path and return the stored data.
        Used for startup verification and debugging.
        """
    ref = get_db_reference("/test")
    data = {"msg": "init from firebase_config", "time": datetime.utcnow().isoformat()}
    ref.set(data)
    return ref.get()
