import cv2
import pytesseract
import numpy as np
from transformers import pipeline
from gtts import gTTS
import os

def preprocess_image(image_path):
    """
    Enhanced preprocessing for better OCR accuracy:
    - Convert to grayscale
    - Apply bilateral filter for noise reduction while preserving edges
    - Apply adaptive thresholding for better binarization
    """
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray_image, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 2)
    return thresh

def extract_text(image):
    """
    Extract text from a preprocessed image using pytesseract.
    Experimenting with PSM 6 (Assume a single uniform block of text).
    """
    text = pytesseract.image_to_string(image, lang='eng', config="--oem 1 --psm 6")
    return text

def summarize_text(text):
    """
    Summarize the given text using Hugging Face transformers pipeline.
    """
    summarizer = pipeline("summarization")
    words = text.split()
    if len(words) == 0:
        return ""
    summary = summarizer(text, max_length=len(words)//2)
    return summary[0]['summary_text']

def speak_text(text, filename):
    """
    Convert text to speech and save as an mp3 file.
    """
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
