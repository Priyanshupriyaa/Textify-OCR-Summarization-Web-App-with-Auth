# 📝 OCR Document Summarizer

A Flask-based web application that lets users upload images or PDF documents, extract text using OCR with image preprocessing, and generate concise summaries using Hugging Face transformers. Includes JWT authentication.

---

## 🚀 Features

- 🔐 **User Authentication** – Secure registration and login with password hashing (bcrypt) and JWT token support for API access.
- 📤 **Document Upload** – Upload images (PNG, JPG, JPEG) and PDF files with automatic unique filename generation.
- 📄 **PDF Support** – Convert PDF files to images for OCR processing, supporting multi-page documents.
- 🔍 **OCR Processing** – Uses OpenCV and pytesseract with preprocessing:
  - Grayscale conversion
  - Bilateral filtering for noise reduction while preserving edges
  - Otsu's Binarization for automatic thresholding
  - Deskewing to correct tilted images
  - Morphological dilation to enhance text regions
- 🧠 **Text Summarization** – Utilizes Hugging Face T5-small transformer model with intelligent text chunking for long documents.
- 🗄️ **MongoDB Integration** – Stores user data, document metadata, OCR results, and summaries.
- 🖥️ **User Interface** – Built with Flask templates and Bootstrap.
- 🧾 **Smart Caching** – Image hashing to detect duplicate uploads and avoid re-processing.
- 🌐 **REST API Endpoints** – Synchronous endpoints for OCR and summarization with JWT authentication.

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **OCR**: OpenCV, pytesseract, pdf2image
- **Summarization**: Hugging Face Transformers (T5-small)
- **Database**: MongoDB (via Flask-PyMongo)
- **Authentication**: bcrypt, Flask-JWT-Extended
- **Frontend**: HTML, CSS, Bootstrap (via Jinja2)

---

## 📋 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/register` | GET/POST | None | User registration |
| `/login` | GET/POST | None | User login (returns JWT) |
| `/logout` | GET | - | User logout |
| `/upload` | GET/POST | JWT | Upload image or PDF |
| `/ocr` | POST | JWT | OCR processing (synchronous) |
| `/summarize` | POST | JWT | Text summarization (synchronous) |

---

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MongoDB
- Tesseract OCR

### 1. Clone the Repository

```
bash
git clone <repository-url>
cd OCR-Document-Summarizer
```

### 2. Create Virtual Environment

```
bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```
bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```
env
FLASK_SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
MONGO_URI=mongodb://localhost:27017/ocr_summarizer_db
UPLOAD_FOLDER=uploads
```

### 5. Install Tesseract OCR

**Windows:**
- Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Add the installation path to your system PATH

**macOS:**
```
bash
brew install tesseract
```

**Linux (Ubuntu):**
```
bash
sudo apt-get install tesseract-ocr
```

### 6. Run the Application

```
bash
python app.py
```

The application will be available at `http://localhost:5000`.

---

## 📁 Project Structure

```
OCR-Document-Summarizer/
├── app.py                  # Main Flask application
├── ocr_summarizer.py       # OCR and summarization logic
├── requirements.txt        # Python dependencies
├── Procfile                # Deployment configuration
├── runtime.txt             # Python runtime version
├── .env                    # Environment variables (create this)
├── .gitignore              # Git ignore rules
├── TODO.md                 # Project TODO list
├── static/                 # Static assets
│   ├── style.css
│   ├── favicon.ico
│   └── logo_web.png
├── templates/              # HTML templates
│   ├── login.html
│   ├── register.html
│   └── upload.html
└── uploads/                # Uploaded files directory
```

---

## 📝 Usage

1. **Register** a new account or **login** if you already have one.
2. **Upload** an image (PNG, JPG, JPEG) or PDF document.
3. Click **Extract Text (OCR)** to extract text from the uploaded document.
4. Click **Summarize Text** to generate a summary of the extracted text.
5. Use the **API** endpoints with JWT authentication for programmatic access.

### API Usage Example

```
bash
# Login to get JWT token
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "yourusername", "password": "yourpassword"}'

# Upload a document (use the token)
curl -X POST http://localhost:5000/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@document.jpg"

# Perform OCR
curl -X POST http://localhost:5000/ocr \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Summarize
curl -X POST http://localhost:5000/summarize \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 🚀 Deployment Considerations

This application was tested and validated in a local development environment.

Due to the memory-intensive nature of OCR (OpenCV + Tesseract) and transformer-based summarization, deploying on low-memory free-tier platforms led to out-of-memory (OOM) constraints.

For production deployment, the system is designed to run on higher-memory instances or with isolated worker processes (e.g., background workers or task queues) to safely handle ML workloads.

---

---
