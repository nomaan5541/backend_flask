from flask import Flask
import os
from flask_socketio import SocketIO
from flask_cors import CORS
from config.config import Config
from database.db import db

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Import routes
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.chat import chat_bp
    from routes.media import media_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(media_bp, url_prefix='/media')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()

    # Import sockets events
    from sockets import chat_socket

    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=int(os.environ.get('PORT', 5000)))
