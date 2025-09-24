from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Optional, List
import json
import base64
import uuid

from ..services.gemini_service import GeminiService
from ..services.chat_context_service import chat_context_service
from app.models.chat import ChatMessage, ChatResponse
from app.services.rag_service import RAGService

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get RAG service
def get_rag_service() -> RAGService:
    return RAGService()

# Dependency to get Gemini service
def get_gemini_service():
    return GeminiService()

@router.post("/start-session")
async def start_chat_session():
    """Start a new chat session"""
    session_id = chat_context_service.create_session()
    return {"session_id": session_id}

@router.post("/upload-file")
async def upload_file_to_chat(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        if not session_id or not file or not file.filename:
            raise HTTPException(status_code=400, detail="Missing session_id or file")
        
        print(f"📁 Attempting to upload {file.filename} to session {session_id}")
        
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Check if session exists, create if it doesn't
        context = chat_context_service.get_context(session_id)
        if not context:
            print(f"🔄 Session {session_id} not found, creating new session")
            # Create session with the provided session_id
            chat_context_service.chat_contexts[session_id] = {
                'session_id': session_id,
                'created_at': __import__('time').time(),
                'messages': [],
                'attached_files': [],
                'context_summary': "",
                'processed_file_summaries': []
            }
        
        file_data = {
            'name': file.filename,
            'type': file.content_type or 'application/octet-stream',
            'content': file_content
        }
        
        success = chat_context_service.add_attached_file(session_id, file_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to attach file")
        
        print(f"✅ File {file.filename} uploaded successfully to session {session_id}")
        
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully",
            "file_info": {
                "name": file.filename,
                "type": file.content_type or 'application/octet-stream',
                "size": len(file_content)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_request: ChatMessage,
    rag_service: RAGService = Depends(get_rag_service),
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Send a message and get AI response with separate contexts"""
    try:
        # Get attached files context (separate from RAG database)
        attached_files_context = ""
        if message_request.chat_session_id:
            attached_files_context = rag_service.get_chat_context(message_request.chat_session_id)
        
        # Get RAG database context (from stored patient documents) - optional and separate
        rag_database_context = ""
        if hasattr(rag_service, 'similarity_search'):
            try:
                # Only search RAG database if user wants general medical knowledge
                # Don't mix with attached files context
                relevant_docs = rag_service.similarity_search(message_request.message, k=2)
                if relevant_docs:
                    rag_database_context = "\n".join([doc.get("content", "") for doc in relevant_docs])
            except:
                pass  # Continue without RAG database context
        
        # Build context with clear separation
        context_parts = []
        
        # 1. Attached files context (primary - from current chat session)
        if attached_files_context:
            context_parts.append("=== ATTACHED FILES CONTEXT ===")
            context_parts.append(attached_files_context)
            context_parts.append("=== END ATTACHED FILES ===")
        
        # 2. Optional: RAG database context (secondary - from stored documents)
        # if rag_database_context:
        #     context_parts.append("=== GENERAL MEDICAL KNOWLEDGE ===")
        #     context_parts.append(rag_database_context)
        #     context_parts.append("=== END GENERAL KNOWLEDGE ===")
        
        # 3. User's question
        context_parts.append(f"USER QUESTION: {message_request.message}")
        
        final_context = "\n\n".join(context_parts) if context_parts else "No additional context available."
        
        # Generate response with clear context hierarchy
        response = await gemini_service.generate_chat_response(
            message_request.message,
            final_context
        )
        
        return ChatResponse(
            message=response,
            chat_session_id=message_request.chat_session_id or str(uuid.uuid4()),
            has_context=bool(attached_files_context)  # Only count attached files as "context"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.post("/chat")
async def chat_with_context(
    session_id: str = Form(...),
    query: str = Form(...),
    patient_context: Optional[str] = Form(None),
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Chat with file context support"""
    try:
        # Get chat context
        context = chat_context_service.get_context(session_id)
        if not context:
            # Create new session if not found
            session_id = chat_context_service.create_session()
            context = chat_context_service.get_context(session_id)
        
        # Add user message to context
        chat_context_service.add_message(session_id, query, 'user')
        
        # Get attached files
        attached_files = chat_context_service.get_attached_files(session_id)
        
        # Prepare context for LLM
        base_context = patient_context or "No patient data available."
        previous_context = context.get('context_summary', '')
        
        full_context = f"{base_context}\n\nPrevious conversation context: {previous_context}"
        
        # Generate response with file attachments
        if attached_files:
            response = await gemini_service.generate_chat_response_with_files(
                query=query,
                context=full_context,
                attached_files=attached_files
            )
        else:
            response = await gemini_service.generate_chat_response(
                query=query,
                context=full_context
            )
        
        # Add assistant response to context
        chat_context_service.add_message(session_id, response, 'assistant')
        
        # Update context summary (keep last 5 exchanges for context)
        messages = context['messages'][-10:]  # Keep last 10 messages
        context_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        chat_context_service.update_context_summary(session_id, context_summary)
        
        return {
            "response": response,
            "session_id": session_id,
            "attached_files_count": len(attached_files)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.get("/session/{session_id}/files")
async def get_session_files(session_id: str):
    """Get all files attached to a chat session"""
    try:
        attached_files = chat_context_service.get_attached_files(session_id)
        
        # Return file info without content
        file_list = []
        for file_data in attached_files:
            file_list.append({
                "file_id": file_data.get('file_id'),
                "name": file_data.get('name'),
                "type": file_data.get('type'),
                "uploaded_at": file_data.get('uploaded_at'),
                "size": len(file_data.get('content', b''))
            })
        
        return {"files": file_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session files: {str(e)}")

@router.delete("/session/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session"""
    success = chat_context_service.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True, "message": "Session cleared successfully"}

@router.get("/sessions")
async def get_chat_sessions():
    """Get list of all chat sessions"""
    sessions = chat_context_service.get_session_list()
    return {"sessions": sessions}
