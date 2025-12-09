from flask import Blueprint, jsonify, request
from database.models import User, Message
from database.db import db
from functools import wraps
from utils.token import decode_token

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            payload = decode_token(token)
            user_id = payload['sub']
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({'message': 'Admin privileges required'}), 403
        except Exception as e:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    total_users = User.query.count()
    total_messages = Message.query.count()
    active_users = User.query.filter(User.last_seen != None).count()
    return jsonify({
        'total_users': total_users,
        'total_messages': total_messages,
        'active_users': active_users
    }), 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    users_list = [{
        'id': user.id,
        'username': user.username,
        'phone': user.phone,
        'status': user.status,
        'is_admin': user.is_admin
    } for user in users]
    return jsonify(users_list), 200

@admin_bp.route('/users/<int:id>/status', methods=['POST'])
@admin_required
def toggle_user_status(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    data = request.get_json()
    new_status = data.get('status')
    if new_status:
        user.status = new_status
        db.session.commit()
        return jsonify({'message': 'User status updated', 'status': user.status}), 200
    return jsonify({'message': 'Status missing'}), 400

@admin_bp.route('/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Optional: Delete messages too
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200
