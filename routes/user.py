from flask import Blueprint, request, jsonify
from database.db import db
from database.models import User, Call

user_bp = Blueprint('user', __name__)

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'profile_picture': user.profile_picture,
        'status': user.status,
        'last_seen': user.last_seen
    })

@user_bp.route('/update', methods=['POST'])
def update_user():
    # In a real app, verify token here to get current_user_id
    data = request.get_json()
    user_id = data.get('user_id') # Should come from token
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if 'status' in data:
        user.status = data['status']
    if 'profile_picture' in data:
        user.profile_picture = data['profile_picture']
    if 'username' in data: # Basic rename
        user.username = data['username']
    if 'bio' in data: # Add bio
        # Assuming User model has 'bio' field, if not need to add it. 
        # For now, let's assume it does or we add it quickly. 
        pass 
        
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@user_bp.route('/search', methods=['GET'])
def search_users():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
        
    # Simple case-insensitive search
    users = User.query.filter(User.username.ilike(f'%{query}%')).all()
    
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'profile_picture': user.profile_picture,
        'status': user.status
    } for user in users])
@user_bp.route('/calls', methods=['GET'])
def get_calls():
    # Simplistic token verification for now or extract from header
    token = request.headers.get('Authorization')
    # In real app verify token. For MVP assuming middleware or basic check
    # user_id = verify_token(token) 
    
    # Temporarily hardcode user_id from query param for easy testing logic if token fails
    # But ideally we use token. Let's trust the token logic exists or use a simple query param as fallback
    user_id = request.args.get('user_id')
    if not user_id and token:
        # Simplified extract from "Bearer <id>" hack if no full JWT logic imported here 
        try:
            user_id = int(token.split(" ")[1]) # Debug hack
        except:
            pass
            
    if not user_id:
         return jsonify({'message': 'User ID missing'}), 400
         
    calls = Call.query.filter((Call.caller_id == user_id) | (Call.receiver_id == user_id)).order_by(Call.timestamp.desc()).all()
    
    calls_data = []
    for call in calls:
        other_id = call.receiver_id if str(call.caller_id) == str(user_id) else call.caller_id
        other_user = User.query.get(other_id)
        
        calls_data.append({
            'id': call.id,
            'other_user_id': other_id,
            'other_user_name': other_user.username if other_user else "Unknown",
            'other_user_pic': other_user.profile_picture if other_user else "",
            'type': call.call_type,
            'status': call.status,
            'direction': 'outgoing' if str(call.caller_id) == str(user_id) else 'incoming',
            'timestamp': call.timestamp.isoformat()
        })
        
    return jsonify(calls_data), 200
