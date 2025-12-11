from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import hashlib
from ocr_summarizer import preprocess_image, extract_text, summarize_text, speak_text
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/ocr_summarizer_db"
mongo = PyMongo(app)


@app.route('/')
def home():
    print(f"Session contents at root: {session}")
    if 'username' in session:
        return redirect(url_for('upload'))
    return redirect(url_for('login'))

@app.route('/clear_session')
def clear_session():
    session.clear()
    return "Session cleared. You can now <a href='/'>go to home</a>."

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
            session['username'] = username
            return redirect(url_for('upload'))
        else:
            message = "Invalid username or password."
            return render_template('login.html', message=message)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    message = ''
    if request.method == 'POST':
        if 'image' not in request.files:
            message = "No file part in the request."
            return render_template('upload.html', message=message)
        image = request.files['image']
        if image.filename == '':
            message = "No selected file."
            return render_template('upload.html', message=message)
        # Read image data for hashing
        image_data = image.read()
        file_hash = hashlib.sha256(image_data).hexdigest()
        # Check if image already exists for this user
        documents = mongo.db.documents
        existing_doc = documents.find_one({'username': session['username'], 'file_hash': file_hash})
        if existing_doc:
            message = "This image has already been uploaded and processed. You can proceed to OCR or Summarize."
            return render_template('upload.html', message=message)
        # If not exists, save the file
        image.seek(0)  # Reset file pointer
        import uuid
        ext = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        filename = secure_filename(unique_filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        # Save upload info to MongoDB
        from datetime import datetime
        documents.insert_one({
            'username': session['username'],
            'filename': filename,
            'file_hash': file_hash,
            'upload_time': datetime.utcnow()
        })
        message = "Uploaded Successfully"
        return render_template('upload.html', message=message)
    return render_template('upload.html', message=message)

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    documents = mongo.db.documents
    user_docs = list(documents.find({'username': session['username']}).sort('upload_time', -1))
    return render_template('history.html', documents=user_docs)

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    documents = mongo.db.documents
    latest_doc = documents.find_one({'username': session['username']}, sort=[('upload_time', -1)])
    if not latest_doc or 'filename' not in latest_doc:
        return jsonify({'error': "No uploaded image found. Please upload an image first."}), 400
    # Check if text is already extracted
    if 'extracted_text' in latest_doc:
        text = latest_doc['extracted_text']
    else:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], latest_doc['filename'])
        if not os.path.exists(image_path):
            return jsonify({'error': "Uploaded image file not found."}), 400
        try:
            preprocessed_image = preprocess_image(image_path)
            text = extract_text(preprocessed_image)
            # Save extracted text to the document
            documents.update_one({'_id': latest_doc['_id']}, {'$set': {'extracted_text': text}})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    # Generate speech audio
    audio_filename = f"{latest_doc['_id']}_extracted.mp3"
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    speak_text(text, audio_path)
    audio_url = url_for('uploaded_file', filename=audio_filename)
    return jsonify({'text': text, 'audio_url': audio_url}), 200

@app.route('/summarize', methods=['POST'])
def summarize():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    documents = mongo.db.documents
    latest_doc = documents.find_one({'username': session['username']}, sort=[('upload_time', -1)])
    if not latest_doc or 'filename' not in latest_doc:
        return jsonify({'error': "No uploaded image found. Please upload an image first."}), 400
    # Check if summary is already generated
    if 'summary_text' in latest_doc:
        summary = latest_doc['summary_text']
    else:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], latest_doc['filename'])
        if not os.path.exists(image_path):
            return jsonify({'error': "Uploaded image file not found."}), 400
        try:
            preprocessed_image = preprocess_image(image_path)
            text = extract_text(preprocessed_image)
            summary = summarize_text(text)
            # Save summary text to the document
            documents.update_one({'_id': latest_doc['_id']}, {'$set': {'summary_text': summary}})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    # Generate speech audio
    audio_filename = f"{latest_doc['_id']}_summary.mp3"
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    speak_text(summary, audio_path)
    audio_url = url_for('uploaded_file', filename=audio_filename)
    return jsonify({'summary': summary, 'audio_url': audio_url}), 200

from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
