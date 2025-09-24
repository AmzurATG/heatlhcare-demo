# Patient Document Management Backend

This directory contains the FastAPI backend for the Patient Document Management System.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file and configure:
```bash
cp .env.example .env
```

3. Update `.env` file with your API keys and configuration:
   - GEMINI_API_KEY from Google AI Studio
   - SECRET_KEY (generate a secure random string)

4. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Features

- Document upload and processing
- Gemini AI integration for document transcription
- SQLite database with automatic setup
- RAG (Retrieval-Augmented Generation) chat system
- Patient data management
