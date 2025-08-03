# 📝 OCR Document Summarizer

A Flask-based web application that lets users upload images with text, extract text using OCR, and generate concise summaries using Hugging Face transformers. Includes secure authentication, upload history, and text-to-speech features.

---

## 🚀 Features

- 🔐 **User Authentication** – Secure registration and login with password hashing and session management.
- 📤 **Image Upload** – Upload images with automatic unique filename generation.
- 🔍 **OCR Processing** – Uses OpenCV and pytesseract for text extraction.
- 🧠 **Text Summarization** – Utilizes Hugging Face transformers for summarizing extracted text.
- 🗄️ **MongoDB Integration** – Stores user data, document metadata, OCR results, and summaries.
- 🖥️ **User Interface** – Built with Flask templates and Bootstrap.
- 🔊 **Text-to-Speech** – Plays extracted and summarized text aloud.
- 🧾 **Upload History** – View past uploads along with text and summary.
- ⚙️ **REST API Endpoints** – Perform OCR and summarization programmatically.

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **OCR**: OpenCV, pytesseract
- **Summarization**: Hugging Face Transformers
- **Database**: MongoDB
- **Authentication**: Flask-Login, bcrypt
- **Text-to-Speech**: pyttsx3
- **Frontend**: HTML, CSS, Bootstrap (via Jinja2)

---