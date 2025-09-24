from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Add static file serving for the chat interface
def setup_static_files(app: FastAPI):
    """Setup static file serving for the chat interface"""
    
    # Serve the frontend directory
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    
    if os.path.exists(frontend_dir):
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
        
        # Serve chat.html at /chat
        @app.get("/chat")
        async def chat_interface():
            chat_file = os.path.join(frontend_dir, "chat.html")
            if os.path.exists(chat_file):
                return FileResponse(chat_file)
            return {"error": "Chat interface not found"}
    
    return app