from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

media_bp = Blueprint('media', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'mp4', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@media_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Ensure uploads directory exists
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file.save(os.path.join(upload_folder, filename))
        
        # Return the URL
        # Use request.host_url (e.g., https://.../) + static path
        # Removing trailing slash from host_url just in case
        base_url = request.host_url.rstrip('/')
        file_url = f"{base_url}/static/uploads/{filename}"
        return jsonify({'message': 'File uploaded successfully', 'url': file_url}), 201
        
    return jsonify({'error': 'File type not allowed'}), 400
