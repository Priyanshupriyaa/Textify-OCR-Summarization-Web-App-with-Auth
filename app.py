from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import hashlib
from ocr_summarizer import preprocess_image, extract_text, summarize_text, get_summarizer
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32))

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY",
    app.secret_key
)

# Initialize JWT
jwt = JWTManager(app)

# Get upload folder path - support both relative and absolute paths
upload_folder = os.environ.get("UPLOAD_FOLDER", "uploads")
if not os.path.isabs(upload_folder):
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_folder)

app.config['UPLOAD_FOLDER'] = upload_folder
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/ocr_summarizer_db")
mongo = PyMongo(app)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}


def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    Only .png, .jpg, .jpeg, .pdf are allowed for security.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# JWT Unauthorized Loader - Returns clean JSON error for missing/invalid tokens
@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({'error': 'Missing or invalid token'}), 401


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = users.find_one({'username': username})
        if existing_user:
            message = "Username already exists."
            return render_template('register.html', message=message)
        hashed_password = generate_password_hash(password)
        users.insert_one({'username': username, 'password': hashed_password})
        message = "Registration successful. Please log in."
        return render_template('login.html', message=message)
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        username = request.form.get('username')
        password = request.form.get('password')
        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            # Generate JWT access token
            access_token = create_access_token(identity=str(user['_id']))
            return jsonify({
                'access_token': access_token,
                'username': username,
                'message': 'Login successful'
            }), 200
        else:
            message = "Invalid username or password."
            return jsonify({'message': message}), 401
    return render_template('login.html')


@app.route('/logout')
def logout():
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload():
    user_id = get_jwt_identity()

    message = ''
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('upload.html', message="No file part in the request.")

        file = request.files['image']
        if file.filename == '':
            return render_template('upload.html', message="No selected file.")

        if not allowed_file(file.filename):
            return render_template(
                'upload.html',
                message="Invalid file type. Only .png, .jpg, .jpeg, and .pdf files are allowed."
            )

        image_data = file.read()
        file_hash = hashlib.sha256(image_data).hexdigest()

        documents = mongo.db.documents
        existing_doc = documents.find_one({
            'user_id': ObjectId(user_id),
            'file_hash': file_hash
        })

        # DUPLICATE UPLOAD
        if existing_doc:
            documents.update_one(
                {'_id': existing_doc['_id']},
                {'$set': {'upload_time': datetime.utcnow()}}
            )
            return render_template(
                'upload.html',
                message="This image was already uploaded. Using existing document."
            )

        # NEW UPLOAD
        file.seek(0)

        import uuid
        ext = os.path.splitext(file.filename)[1].lower()
        filename = secure_filename(f"{uuid.uuid4().hex}{ext}")

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        documents.insert_one({
            'user_id': ObjectId(user_id),
            'filename': filename,
            'file_hash': file_hash,
            'upload_time': datetime.utcnow()
        })

        return render_template('upload.html', message="Uploaded Successfully")

    return render_template('upload.html', message=message)


@app.route('/ocr', methods=['POST'])
@jwt_required()
def ocr():
    """
    OCR endpoint - processes synchronously.
    Uses default PSM 6 (single uniform block of text).
    """
    user_id = get_jwt_identity()
    
    documents = mongo.db.documents
    latest_doc = documents.find_one(
        {'user_id': ObjectId(user_id)},
        sort=[('upload_time', -1)]
    )
    
    if not latest_doc or 'filename' not in latest_doc:
        return jsonify({'error': "No uploaded image found. Please upload an image first."}), 400
    
    # Use default PSM 6
    ocr_mode = 6
    
    # Check cache - return immediately if text already extracted
    if 'extracted_text' in latest_doc:
        text = latest_doc['extracted_text']
        return jsonify({'text': text, 'cached': True}), 200
    
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], latest_doc['filename'])
    if not os.path.exists(image_path):
        return jsonify({'error': "Uploaded image file not found."}), 400
    
    try:
        preprocessed_images = preprocess_image(image_path)
        text_parts = []
        for img in preprocessed_images:
            page_text = extract_text(img, psm=ocr_mode)
            if page_text and page_text.strip():
                text_parts.append(page_text)
        text = '\n\n'.join(text_parts)

        if not text or text.strip() == '':
            return jsonify({'error': "No text could be extracted from the image. Please try a clearer image."}), 400
        
        # Save extracted text
        documents.update_one(
            {'_id': latest_doc['_id']}, 
            {'$set': {'extracted_text': text, 'ocr_psm': ocr_mode}}
        )
        
        return jsonify({'text': text}), 200
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return jsonify({'error': f"OCR processing failed: {str(e)}"}), 500


@app.route('/summarize', methods=['POST'])
@jwt_required()
def summarize():
    """
    Summarize endpoint - processes synchronously.
    """
    user_id = get_jwt_identity()

    documents = mongo.db.documents
    latest_doc = documents.find_one(
        {'user_id': ObjectId(user_id)},
        sort=[('upload_time', -1)]
    )

    if not latest_doc:
        return jsonify({'error': "No uploaded image found."}), 400

    if 'extracted_text' not in latest_doc:
        return jsonify({'error': "Please perform OCR before summarizing."}), 400

    # Check cache - return immediately if summary already exists
    if 'summary_text' in latest_doc:
        summary = latest_doc['summary_text']
        return jsonify({'summary': summary, 'cached': True}), 200

    try:
        summary = summarize_text(latest_doc['extracted_text'])

        if not summary or summary.strip() == '':
            return jsonify({'error': "Could not generate summary. The text may be too short."}), 400

        # Save summary
        documents.update_one(
            {'_id': latest_doc['_id']},
            {'$set': {'summary_text': summary}}
        )

        return jsonify({'summary': summary}), 200
    except Exception as e:
        print(f"Summarization Error: {str(e)}")
        return jsonify({'error': f"Summarization failed: {str(e)}"}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    print("Loading summarization model...")
    get_summarizer()
    print("Model loaded successfully!")
    app.run(debug=True)
