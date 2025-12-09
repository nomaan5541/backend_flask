import firebase_admin
from firebase_admin import credentials, messaging

_is_initialized = False

def init_fcm():
    global _is_initialized
    if not _is_initialized:
        try:
            # Placeholder: User needs to provide path to serviceAccountKey.json
            # cred = credentials.Certificate('config/serviceAccountKey.json')
            # firebase_admin.initialize_app(cred)
            # _is_initialized = True
            print("FCM not fully configured. Add serviceAccountKey.json to config/")
        except Exception as e:
            print(f"Failed to init FCM: {e}")

def send_push_notification(token, title, body, data=None):
    if not _is_initialized:
        print("FCM skipped: Not initialized")
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('Error sending message:', e)
