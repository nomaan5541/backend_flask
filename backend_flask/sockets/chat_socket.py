from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from database.models import Message, Call, User
from utils.token import verify_token

# Store active users map: user_id -> set(request_sid)
connected_users = {}

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    if not token:
        return False
        
    user_id = verify_token(token)
    if not user_id:
        return False
        
    join_room(str(user_id))
    connected_users[user_id] = request.sid
    
    # Update status to online (Optional: Sync with DB)
    emit('user_online', {'user_id': user_id}, broadcast=True)
    print(f"User {user_id} connected")

@socketio.on('disconnect')
def handle_disconnect():
    # Find user_id from connected_users (inefficient reverse lookup, ideally store in session)
    user_id = None
    for uid, sid in connected_users.items():
        if sid == request.sid:
            user_id = uid
            break
            
    if user_id:
        if user_id in connected_users:
            del connected_users[user_id]
        
        # Persistence for Last Seen
        try:
            user = User.query.get(user_id)
            if user:
                user.status = "offline"
                import datetime
                user.last_seen = datetime.datetime.utcnow().isoformat()
                db.session.commit()
        except Exception as e:
            print(f"Error updating last seen: {e}")
            
        emit('user_offline', {'user_id': user_id}, broadcast=True)
        print(f"User {user_id} disconnected")

@socketio.on('mark_read')
def handle_mark_read(data):
    sender_id = data.get('sender_id') # Who sent the message (that is now read)
    receiver_id = data.get('receiver_id') # Who read it (current user)
    
    # In a real app, update DB status for all messages from sender to receiver as 'read'
    # db.session.query(Message).filter(...)
    
    emit('messages_read', {
        'reader_id': receiver_id,
        'sender_id': sender_id
    }, room=str(sender_id))

@socketio.on('send_message')
def handle_message(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    message = data.get('message')
    
    # Save to DB
    new_msg = Message(sender_id=sender_id, receiver_id=receiver_id, group_id=group_id, message=message, message_type='text')
    db.session.add(new_msg)
    db.session.commit()
    
    sender_user = User.query.get(sender_id)
    sender_name = sender_user.username if sender_user else "Unknown"

    response_data = {
        'id': new_msg.id,
        'sender_id': sender_id, 
        'sender_name': sender_name,
        'group_id': group_id,
        'message': message,
        'timestamp': str(new_msg.timestamp)
    }

    if group_id:
        emit('new_group_message', response_data, room=f"group_{group_id}")
    else:
        emit('new_message', response_data, room=str(receiver_id))

@socketio.on('join_group')
def handle_join_group(data):
    group_id = data.get('group_id')
    if group_id:
        join_room(f"group_{group_id}")
        print(f"User joined group_{group_id}")
    
    # Push Notification (Stub)
    # In a real app, fetch receiver's FCM token from DB
    from utils.fcm import send_push_notification
    # receiver = User.query.get(receiver_id)
    # if receiver and receiver.fcm_token:
    #     send_push_notification(receiver.fcm_token, "New Message", message)
    
    # Emit acknowledgment back to sender (optional)
    emit('group_joined', {'group_id': group_id}, room=request.sid)

@socketio.on('typing')
def handle_typing(data):
    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')
    is_typing = data.get('is_typing')
    
    emit('user_typing', {
        'user_id': sender_id,
        'is_typing': is_typing
    }, room=str(receiver_id))

# --- WebRTC Signaling ---

@socketio.on('start_call')
def handle_start_call(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    call_type = data.get('call_type', 'video') # voice or video
    
    # Create Call Record
    new_call = Call(caller_id=sender_id, receiver_id=receiver_id, call_type=call_type, status='missed')
    db.session.add(new_call)
    db.session.commit()
    
    emit('call_request', {
        'call_id': new_call.id,
        'sender_id': sender_id,
        'call_type': call_type,
        'offer': data.get('offer') # SDP offer
    }, room=str(receiver_id))

@socketio.on('answer_call')
def handle_answer_call(data):
    caller_id = data['caller_id']
    receiver_id = data['receiver_id']
    call_id = data.get('call_id')
    
    if call_id:
        call = Call.query.get(call_id)
        if call:
            call.status = 'ended' # Mark as valid call (ended normally later, or just not missed)
            # Or 'answered' if we track duration later. 
            # For simplistic history: 'missed' vs 'ended' (meaning taken).
            call.status = 'answered' 
            db.session.commit()

    emit('call_answered', {
        'receiver_id': receiver_id,
        'answer': data.get('answer') # SDP answer
    }, room=str(caller_id))

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    target_id = data['target_id']
    candidate = data['candidate']
    
    emit('ice_candidate', {
        'sender_id': data.get('sender_id'), # Who sent the candidate
        'candidate': candidate
    }, room=str(target_id))

@socketio.on('end_call')
def handle_end_call(data):
    target_id = data['target_id']
    emit('call_ended', {'reason': 'hangup'}, room=str(target_id))
