# firebase_config.py

import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Load the service account credentials from JSON file
cred = credentials.Certificate("path/to/firebase-service-account.json")

# Initialize the Firebase app with the Realtime Database URL
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://<MyPhoneApp2025>.firebaseio.com"
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
