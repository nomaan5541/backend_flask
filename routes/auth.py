from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import db
from database.models import User
from utils.token import generate_token
from utils.validation import validate_email, validate_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    phone = data.get('phone')
    password = data.get('password')
    
    if not username or not phone or not password:
        return jsonify({'error': 'Missing required fields'}), 400
        
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone number already registered'}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400

    new_user = User(
        username=username,
        phone=phone,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    token = generate_token(new_user.id)
    return jsonify({'message': 'User created successfully', 'token': token, 'user': {
        'id': new_user.id,
        'username': new_user.username,
        'phone': new_user.phone
    }}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid phone or password'}), 401
        
    token = generate_token(user.id)
    return jsonify({'message': 'Login successful', 'token': token, 'user': {
        'id': user.id,
        'username': user.username,
        'profile_picture': user.profile_picture,
        'is_admin': user.is_admin
    }}), 200
