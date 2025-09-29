from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from pathlib import Path

from app.api import documents, patients, chat
from app.services.gemini_service import GeminiService
from app.services.rag_service import RAGService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Patient Document Management API",
    description="API for managing patient documents with AI transcription and RAG chat",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup (no database table creation needed for Supabase)
@app.on_event("startup")
def startup():
    # Skip table creation - using Supabase REST API
    print("🚀 Starting PatientDB API...")
    print("✅ Using Supabase for data storage (tables already exist)")
    
    # Optional: Test Supabase connection here if needed
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        print(f"🔗 Connected to Supabase: {supabase_url}")
    else:
        print("📁 Using local SQLite fallback")

# Include API routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Setup static files for chat interface
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    
    # Add route for the enhanced index.html as the default interface
    @app.get("/interface")
    async def enhanced_interface():
        """Serve the enhanced React-based chat interface"""
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "Enhanced interface not found"}

@app.get("/chat")
async def chat_interface():
    """Serve the enhanced chat interface with file attachment functionality"""
    # Serve the enhanced React-based chat interface
    enhanced_chat_file = frontend_dir / "index.html"
    if enhanced_chat_file.exists():
        return FileResponse(str(enhanced_chat_file))
    
    # Fallback to basic HTML chat
    basic_chat_file = frontend_dir / "chat.html"
    if basic_chat_file.exists():
        return FileResponse(str(basic_chat_file))
    
    return {
        "error": "Chat interface not found", 
        "note": "Enhanced chat with file attachments should be in frontend/index.html",
        "available_routes": ["/docs", "/", "/static/index.html"]
    }

@app.get("/")
async def root():
    return {
        "message": "Patient Document Management API - Enhanced with File Attachments",
        "chat_interface": "/chat",
        "api_docs": "/docs",
        "features": [
            "📎 File attachment in chat",
            "📊 Tabular data processing (Excel, CSV)",
            "🏥 Medical document analysis", 
            "💬 Context-aware conversations"
        ],
        "endpoints": {
            "attach_files": "POST /api/documents/attach-to-chat",
            "chat_message": "POST /api/chat/message", 
            "get_attachments": "GET /api/documents/chat-attachments/{session_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
