import cv2
import pytesseract
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from gtts import gTTS
import os
from pdf2image import convert_from_path


def deskew_image(image):
    """
    Detect and correct skew in the image using OpenCV's minAreaRect.
    This method uses contour detection to find the minimum area rectangle
    that encloses the text, then calculates the angle needed to deskew the image.
    
    Args:
        image: Input image (can be grayscale or color)
        
    Returns:
        Deskewed image
    """
    # Get image dimensions
    height, width = image.shape[:2]
    
    # If image is color, convert to grayscale for contour detection
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply thresholding to get binary image for contour detection
    # Use Otsu's thresholding for automatic threshold selection
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Invert the binary image (text should be white on black for contour detection)
    binary = cv2.bitwise_not(binary)
    
    # Find contours in the binary image
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        # No contours found, return original image
        return image
    
    # Find the largest contour (likely the main text area)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get the minimum area rectangle
    rect = cv2.minAreaRect(largest_contour)
    
    # Get the angle of the rectangle
    angle = rect[2]
    
    # Adjust angle based on rectangle orientation
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Only rotate if angle is significant (more than 0.5 degrees)
    if abs(angle) > 0.5:
        # Determine rotation center
        center = (width // 2, height // 2)
        
        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new dimensions to avoid cropping
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))
        
        # Adjust the rotation matrix for translation
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # Apply rotation
        image = cv2.warpAffine(
            image, 
            rotation_matrix, 
            (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
    
    return image


def process_pdf(pdf_path):
    """
    Convert a PDF file into a list of images using pdf2image.
    Each page of the PDF becomes one image in the list.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of numpy arrays representing images (in BGR format for OpenCV)
        
    Raises:
        ValueError: If the PDF cannot be read
    """
    if not os.path.exists(pdf_path):
        raise ValueError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("File must be a PDF")
    
    # Convert PDF to images (all pages)
    images = convert_from_path(pdf_path)
    
    # Convert PIL images to OpenCV format (BGR)
    opencv_images = []
    for pil_image in images:
        # Convert RGB to BGR for OpenCV
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        opencv_images.append(opencv_image)
    
    return opencv_images


def apply_otsu_binarization(image):
    """
    Apply Otsu's Binarization for automatic thresholding.
    This is particularly effective for images with varying lighting conditions.
    """
    # Apply Gaussian blur to reduce noise before Otsu's thresholding
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    
    # Apply Otsu's thresholding
    _, binary_image = cv2.threshold(
        blurred, 
        0, 255, 
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    return binary_image


def apply_dilation(image, kernel_size=(3, 3)):
    """
    Apply morphological dilation to enhance text regions.
    This helps to connect broken characters and make text more readable for OCR.
    """
    # Create a kernel for dilation
    kernel = np.ones(kernel_size, np.uint8)
    
    # Apply dilation
    dilated_image = cv2.dilate(image, kernel, iterations=1)
    
    return dilated_image


def preprocess_image(image_path):
    """
    Enhanced preprocessing pipeline for better OCR accuracy:
    1. Handle PDF files by converting to images (all pages)
    2. For each image:
       - Convert to grayscale
       - Apply bilateral filter for noise reduction while preserving edges
       - Apply Otsu's Binarization for automatic thresholding
       - Apply deskewing to correct tilted images
       - Apply dilation to enhance text regions
    
    Args:
        image_path: Path to the image or PDF file
        
    Returns:
        List of preprocessed images ready for OCR
    """
    # Check if file is a PDF
    if image_path.lower().endswith('.pdf'):
        # Convert PDF to images (all pages)
        pdf_images = convert_from_path(image_path)
        preprocessed_images = []
        
        for pil_image in pdf_images:
            # Convert PIL image to numpy array and RGB to BGR for OpenCV
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter for noise reduction while preserving edges
            filtered = cv2.bilateralFilter(gray_image, 9, 75, 75)
            
            # Apply Otsu's Binarization for automatic thresholding
            binarized = apply_otsu_binarization(filtered)
            
            # Apply deskewing to correct tilted images
            deskewed = deskew_image(binarized)
            
            # Apply dilation to enhance text regions
            preprocessed = apply_dilation(deskewed)
            
            preprocessed_images.append(preprocessed)
        
        return preprocessed_images
    else:
        # Read the image
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Could not read image from {image_path}")

        # Convert to grayscale - simple preprocessing for better OCR accuracy
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Return as a list for consistency
        return [gray_image]


def extract_text(image, psm=6):
    """
    Extract text from a preprocessed image using pytesseract.
    
    Args:
        image: Preprocessed image ready for OCR
        psm: Page Segmentation Mode (PSM) for Tesseract
            - PSM 3: Fully automatic page segmentation (Best for Receipts/Tables)
            - PSM 6: Assume a single uniform block of text (Default, Best for Text)
    
    Returns:
        Extracted text string
    """
    text = pytesseract.image_to_string(image, lang='eng', config=f"--oem 1 --psm {psm}")
    return text


# Global summarizer (lazy loading)
_summarizer = None


def get_summarizer():
    global _summarizer
    if _summarizer is None:
        tokenizer = AutoTokenizer.from_pretrained("t5-small")
        model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")

        _summarizer = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer
        )
    return _summarizer


def summarize_text(text):
    """
    Summarize the given text using Hugging Face transformers pipeline.
    """
    summarizer = get_summarizer()
    words = text.split()

    if not words:
        return ""

    max_input_length = 1024

    # 🔹 Chunk long text
    if len(words) > max_input_length:
        chunks = []
        for i in range(0, len(words), max_input_length // 2):
            chunk = " ".join(words[i:i + max_input_length // 2])
            chunks.append(chunk)

        summaries = []
        for chunk in chunks:
            try:
                input_text = "summarize: " + chunk

                output = summarizer(
                    input_text,
                    max_length=120,
                    do_sample=False,
                    truncation=True
                )
                summaries.append(output[0]["generated_text"])
            except Exception as e:
                print(f"Error summarizing chunk: {e}")

        return " ".join(summaries) if summaries else ""

    # 🔹 Short text
    input_text = "summarize: " + text

    output = summarizer(
        input_text,
        max_length=120,
        do_sample=False,
        truncation=True
    )
    return output[0]["generated_text"]


def speak_text(text, filename):
    """
    Convert text to speech and save as an mp3 file.
    """
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
