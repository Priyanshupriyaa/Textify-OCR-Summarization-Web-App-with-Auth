# OCR Document Summarizer

## Overview

This project is a Flask-based web application that allows users to:

- Register and log in.
- Upload images containing text.
- Perform Optical Character Recognition (OCR) on uploaded images to extract text.
- Summarize the extracted text using a Hugging Face transformers pipeline.
- View upload history and results.

The application uses MongoDB to store user data, uploaded document metadata, extracted text, and summaries.
