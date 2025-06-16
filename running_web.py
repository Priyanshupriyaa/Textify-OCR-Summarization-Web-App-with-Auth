from flask import Flask, render_template, request, redirect, url_for
import os
from transformers import pipeline
import cv2
import pytesseract
import numpy as np

import os

app = Flask(__name__)
import os

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Ensure uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

from flask import redirect, url_for

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/u')
def index():
    return render_template('upload.html')

@app.route('/u', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        message = "No file part in the request."
        return render_template('upload.html', message=message)
    image = request.files['image']
    if image.filename == '':
        message = "No selected file."
        return render_template('upload.html', message=message)
    try:
        image_name = 'upload.jpeg'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
        print(f"Uploads folder absolute path: {app.config['UPLOAD_FOLDER']}")
        print(f"Saving image to path: {image_path}")
        image.save(image_path)
        message = "Uploaded Successfully"
        return render_template('upload.html', message=message)
    except Exception as e:
        message = f"Failed to save file: {str(e)}"
        return render_template('upload.html', message=message)
        
@app.route('/r', methods=['POST'])
def run_script():
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'upload.jpeg')
    if not os.path.exists(image_path):
        return render_template('upload.html', output="Error: No uploaded image found. Please upload an image first.")
    try:
        image = cv2.imread(image_path)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((5, 5), dtype=int)
        image = cv2.erode(image, kernel, iterations=1)
        image = cv2.dilate(image, kernel, iterations=1)
        image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        image = cv2.bitwise_not(image)
        
        text = pytesseract.image_to_string(image, lang='eng')

        return render_template('upload.html', output=text)
        
    except Exception as e:
        return render_template('upload.html', output=f"Error: {str(e)}")
    
    
@app.route('/sum',methods=["POST"])
def summarize():
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'upload.jpeg')
    if not os.path.exists(image_path):
        return render_template('upload.html', summary="Error: No uploaded image found. Please upload an image first.")
    try:
        image = cv2.imread(image_path)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((5, 5), dtype=int)
        image = cv2.erode(image, kernel, iterations=1)
        image = cv2.dilate(image, kernel, iterations=1)
        image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        image = cv2.bitwise_not(image)
        summarizer = pipeline("summarization")
        text = pytesseract.image_to_string(image, lang='eng')
        words = text.split()
        if len(words) == 0:
            return render_template('upload.html', summary="Error: No text found to summarize.")
        # Summarize the text
        summary = summarizer(text, max_length=len(words)//2)
        summ_print = summary[0]['summary_text']
        return render_template('upload.html', summary=summ_print)
    except Exception as e:
        return render_template('upload.html', summary=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run()
    
    

    

