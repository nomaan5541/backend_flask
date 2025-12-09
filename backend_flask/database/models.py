from datetime import datetime
from database.db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    profile_picture = db.Column(db.String(255))
    status = db.Column(db.String(255), default="Hey there! I am using ChatApp")
    status = db.Column(db.String(255), default="Hey there! I am using ChatApp")
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for Group Messages
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), default="text") # text, image, audio
    media_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default="sent") # sent, delivered, seen

class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    call_type = db.Column(db.String(10)) # voice, video
    duration = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20)) # missed, ended, cancelled
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
