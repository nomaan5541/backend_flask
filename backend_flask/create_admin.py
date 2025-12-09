from app import create_app
from database.db import db
from database.models import User, Group
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    email = "virusx@gmail.com"
    username = "virusx" 
    # Logic: Login uses 'phone' to filter. So 'virusx@gmail.com' must be in phone column.
    
    password = "123123123"

    user = User.query.filter_by(phone=email).first()
    
    if user:
        print(f"User {email} exists. Promoting to admin...")
        user.is_admin = True
        user.password_hash = generate_password_hash(password)
    else:
        print(f"Creating new admin user {email}...")
        # Check if username 'virusx' is taken
        if User.query.filter_by(username=username).first():
             # fallback username
             username = "virusx_admin"
             
        user = User(
            username=username,
            phone=email, # Using email as phone identifier
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(user)
    
    db.session.commit()
    print("Admin user created/updated successfully.")
