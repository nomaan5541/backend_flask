import jwt
import datetime
import os

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, os.environ.get('SECRET_KEY') or 'you-will-never-guess', algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY') or 'you-will-never-guess', algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
