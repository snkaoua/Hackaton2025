from firebase_admin import messaging

def send_fcm_notification(token: str, title: str, body: str, data: dict | None = None) -> str:
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    return messaging.send(message)