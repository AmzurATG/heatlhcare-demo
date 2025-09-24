# Patient Document Management System

A comprehensive healthcare document management system that uses AI to extract and organize patient information from documents, with an intelligent chat interface for querying patient data.

## 🏗️ Architecture

The system consists of four main components:

1. **React Frontend**: Modern web interface for document upload and patient management
2. **FastAPI Backend**: Python API server with document processing and chat endpoints
3. **SQLite Database**: Local database for patient data storage (zero setup required!)
4. **RAG System**: Vector-based retrieval system for intelligent chat queries

## 🚀 Features

### Document Processing
- Upload patient documents (images, PDFs, text files)
- AI-powered data extraction using Google Gemini 2.5-pro
- Automatic form population with extracted information
- Confidence scoring for extraction accuracy

### Patient Management
- Create, read, update, and delete patient records
- Structured data storage (name, DOB, diagnosis, prescription)
- Data validation and error handling
- Audit trail with creation/update timestamps

### Intelligent Chat
- RAG-powered chat interface for querying patient data
- Natural language questions about patient records
- Source attribution and confidence scoring
- Real-time responses with relevant patient information

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **React Dropzone** for file uploads
- **Axios** for API communication

### Backend
- **FastAPI** for API development
- **Google Gemini 2.5-pro** for document processing
- **ChromaDB** for vector storage
- **Sentence Transformers** for embeddings
- **Supabase** Python client

### Database & Infrastructure
- **SQLite** for local data storage (zero setup!)
- **ChromaDB** for vector embeddings
- **Google AI Studio** for Gemini API

## 📁 Project Structure

```
PatientDB/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── uploads/            # Temporary file storage
│   ├── requirements.txt    # Python dependencies
│   └── main.py            # Application entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Utility functions
│   ├── public/            # Static assets
│   └── package.json       # Node dependencies
├── database/              # Database schema
│   ├── schema.sql         # SQLite table definitions (reference)
│   └── README.md          # Database setup guide
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google AI Studio API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

5. Update `.env` with your API keys:
```env
DATABASE_URL=sqlite:///./patients.db
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

6. Start the server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

### Database Setup

**No setup required!** The SQLite database is created automatically when you start the backend server.

The database file will be created at `backend/patients.db` with all necessary tables and indexes.

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/documents/upload` - Upload and process document
- `GET|POST|PUT|DELETE /api/patients/` - Patient CRUD operations
- `POST /api/chat/` - Chat with patient data
- `POST /api/chat/refresh-knowledge-base` - Refresh RAG index

## 🔧 Configuration

### Environment Variables

**Backend (.env)**:
- `DATABASE_URL`: SQLite database file path (defaults to sqlite:///./patients.db)
- `GEMINI_API_KEY`: Google Gemini API key
- `SECRET_KEY`: JWT secret key
- `ALLOWED_ORIGINS`: CORS allowed origins
- `MAX_FILE_SIZE`: Maximum upload file size
- `UPLOAD_DIR`: Temporary upload directory

**Frontend (.env.local)** (optional):
- `REACT_APP_API_URL`: Backend API URL (defaults to http://localhost:8000)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure `ALLOWED_ORIGINS` includes your frontend URL
2. **Database Issues**: Database is created automatically - no setup needed
3. **Gemini API**: Check API key and quota limits
4. **File Upload**: Ensure `uploads/` directory exists and is writable

### Support

For questions or issues, please create an issue in the GitHub repository.

---

Built with ❤️ for better healthcare document management.
