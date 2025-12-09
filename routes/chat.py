from flask import Blueprint, request, jsonify
from database.db import db
from database.models import Message, User, Group, GroupMember
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/history/<int:user_id>/<int:other_user_id>', methods=['GET'])
def get_chat_history(user_id, other_user_id):
    # Fetch messages between two users
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.timestamp).all()
    
    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'receiver_id': msg.receiver_id,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'message_type': msg.message_type,
            'media_url': msg.media_url,
            'status': msg.status
        })
        
    return jsonify(result)

@chat_bp.route('/groups/<int:group_id>/messages', methods=['GET'])
def get_group_messages(group_id):
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    result = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        result.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': sender.username if sender else "Unknown",
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'message_type': msg.message_type
        })
    return jsonify(result), 200

@chat_bp.route('/groups/<int:group_id>/members', methods=['GET'])
def get_group_members(group_id):
    members = GroupMember.query.filter_by(group_id=group_id).all()
    result = []
    for m in members:
        user = User.query.get(m.user_id)
        if user:
            result.append({
                'user_id': user.id,
                'username': user.username,
                'profile_picture': user.profile_picture,
                'role': m.role
            })
    return jsonify(result), 200

@chat_bp.route('/groups/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
def remove_group_member(group_id, user_id):
    # Security: Verify requester is admin (skipped for MVP speed, assume UI handles check)
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if member:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Member removed'}), 200
    return jsonify({'error': 'Member not found'}), 404

@chat_bp.route('/groups/<int:group_id>/members/<int:user_id>', methods=['PUT'])
def update_member_role(group_id, user_id):
    data = request.get_json()
    new_role = data.get('role') # 'admin' or 'member'
    
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if member and new_role:
        member.role = new_role
        db.session.commit()
        return jsonify({'message': 'Role updated'}), 200
    return jsonify({'error': 'Member not found or invalid role'}), 400

@chat_bp.route('/sendMessage', methods=['POST'])
def send_message():
    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    message_content = data.get('message')
    msg_type = data.get('message_type', 'text')
    media_url = data.get('media_url')
    
    if not sender_id or not receiver_id or not message_content:
        return jsonify({'error': 'Missing required fields'}), 400
        
    new_message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=message_content,
        message_type=msg_type,
        media_url=media_url
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # Emit SocketIO event
    from extensions import socketio
    socketio.emit('new_message', {
        'id': new_message.id,
        'sender_id': new_message.sender_id,
        'receiver_id': new_message.receiver_id,
        'message': new_message.message,
        'timestamp': new_message.timestamp.isoformat(),
        'message_type': new_message.message_type,
        'media_url': new_message.media_url,
        'status': new_message.status
    }, room=None) # Broadcast to all for MVP, or implement rooms for scale
    
    return jsonify({'message': 'Message sent successfully', 'id': new_message.id}), 201

@chat_bp.route('/conversations/<int:user_id>', methods=['GET'])
def get_conversations(user_id):
    # Logic to fetch last message for each conversation
    from sqlalchemy import func, case, desc
    
    # 1. Identify all unique pairs (user_id, other_id)
    # This is efficiently done by finding the Max Message ID for each conversation grouping
    
    # Subquery to get max ID per conversation
    # We group by the "other" user ID
    
    # Simplified Python-side processing for readability and reliability given SQLite limitations or complexity
    # Fetch all messages involving user
    all_msgs = Message.query.filter(
        or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).order_by(Message.timestamp.desc()).all()
    
    conversations = {}
    
    for msg in all_msgs:
        other_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
        
        if other_id not in conversations:
            conversations[other_id] = msg
            
    result = []
    for other_id, msg in conversations.items():
        other_user = User.query.get(other_id)
        if other_user:
            result.append({
                'chatId': str(other_id), # Treat userId as chatId for 1-on-1
                'otherUserId': str(other_id),
                'otherUserName': other_user.username,
                'otherUserProfileUrl': other_user.profile_picture,
                'lastMessage': msg.message if msg.message_type == 'text' else 'Photo',
                'timestamp': msg.timestamp.isoformat(), # ISO format for frontend
                'unreadCount': 0 # Logic for unread count requires 'status' check
            })
            
    return jsonify(result)
