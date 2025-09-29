from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime

from ..services.gemini_service import GeminiService
from ..services.patient_service import get_patient_service
from ..services.file_cache_service import file_cache_service

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session storage (use Redis in production)
chat_sessions = {}

@router.post("/start-session")
async def start_chat_session():
    """Start a new chat session"""
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        "created_at": datetime.now(),
        "messages": [],
        "files": []
    }
    
    return {"session_id": session_id}

@router.post("/chat")
async def chat_with_context(
    session_id: str = Form(...),
    query: str = Form(...),
    patient_context: Optional[str] = Form(None)
):
    """Chat with AI using patient database context"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get patient service and context
        patient_service = get_patient_service()
        gemini_service = GeminiService()
        
        # Get patient context from database
        patients = await patient_service.get_all_patients(limit=10)
        
        # Format patient context for AI
        if patients:
            patient_context_text = _format_patients_for_chat(patients)
        else:
            patient_context_text = "No patient data available in the database."
        
        # Get any attached files context from session
        session = chat_sessions[session_id]
        files_context = ""
        if session.get("files"):
            # Process files if any (implement file processing if needed)
            pass
        
        # Combine contexts
        full_context = f"""
PATIENT DATABASE CONTEXT:
{patient_context_text}

ADDITIONAL CONTEXT:
{patient_context or ""}

FILES CONTEXT:
{files_context or "No additional files attached."}
        """
        
        # Generate AI response
        response = await gemini_service.chat_with_context(query, full_context)
        
        # Store in session
        session["messages"].append({
            "query": query,
            "response": response,
            "timestamp": datetime.now()
        })
        
        return {
            "response": response,
            "patients_available": len(patients),
            "has_context": bool(patients)
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/upload-file")
async def upload_file_to_session(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a file to a chat session"""
    try:
        print(f"📤 Uploading file: {file.filename}, session: {session_id}")
        logger.info(f"Uploading file: {file.filename}, session: {session_id}")
        
        # Create session if it doesn't exist
        if session_id not in chat_sessions:
            print(f"🔄 Creating new session: {session_id}")
            chat_sessions[session_id] = {
                "created_at": datetime.now(),
                "messages": [],
                "files": []
            }
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Read file content
        content = await file.read()
        print(f"📄 File content size: {len(content)} bytes")
        
        # Store file in session
        file_data = {
            "file_id": str(uuid.uuid4()),
            "name": file.filename,
            "type": file.content_type or "application/octet-stream",
            "content": content,
            "uploaded_at": datetime.now()
        }
        
        chat_sessions[session_id]["files"].append(file_data)
        
        print(f"✅ File uploaded successfully: {file.filename}")
        logger.info(f"File uploaded successfully: {file.filename}")
        
        return {
            "success": True,
            "file_id": file_data["file_id"],
            "message": f"File {file.filename} uploaded successfully",
            "attachment_type": "file_upload"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"File upload failed: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# Add enhanced chat endpoint that processes files
@router.post("/chat-enhanced")
async def chat_with_files_context(
    session_id: str = Form(...),
    query: str = Form(...),
    patient_context: Optional[str] = Form(None)
):
    """Enhanced chat with file processing support and caching"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Clear expired cache periodically
        file_cache_service.clear_expired_cache()
        
        # Get patient service and context
        patient_service = get_patient_service()
        gemini_service = GeminiService()
        
        # Get patient context from database (limit for performance)
        patients = await patient_service.get_all_patients(limit=5)  # Reduced from 10
        
        # Format patient context for AI (truncated)
        if patients:
            patient_context_text = _format_patients_for_chat_optimized(patients)
        else:
            patient_context_text = "No patient data available in the database."
        
        # Get and process attached files from session with caching
        session = chat_sessions[session_id]
        files_context = ""
        attached_files = session.get("files", [])
        
        if attached_files:
            print(f"📎 Processing {len(attached_files)} attached files with caching")
            
            # Convert file data format for gemini service
            file_data_for_processing = []
            for file_info in attached_files:
                file_data_for_processing.append({
                    'content': file_info['content'],
                    'name': file_info['name'],
                    'type': file_info['type']
                })
            
            # Process files with optimized caching
            files_context = await gemini_service._process_attached_files_optimized(file_data_for_processing)
        
        # Combine contexts (truncated for performance)
        full_context = f"""
PATIENT DATABASE CONTEXT:
{patient_context_text[:1500]}

ATTACHED FILES CONTEXT:
{files_context[:2000]}
        """
        
        # Generate AI response
        response = await gemini_service.chat_with_context(query, full_context)
        
        # Store in session
        session["messages"].append({
            "query": query,
            "response": response,
            "timestamp": datetime.now()
        })
        
        return {
            "response": response,
            "patients_available": len(patients),
            "has_context": bool(patients),
            "files_processed": len(attached_files),
            "cache_stats": file_cache_service.get_cache_stats()
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

def _format_patients_for_chat_optimized(patients: List[Dict[str, Any]]) -> str:
    """Format patient data for chat context - optimized version"""
    if not patients:
        return "No patient records available."
    
    context_parts = [f"Available Patient Records ({len(patients)} total):"]
    
    for i, patient in enumerate(patients[:5], 1):  # Limit to first 5 for performance
        context_parts.append(f"\n{i}. {patient.get('name', 'Unknown')}")
        context_parts.append(f"   - DOB: {patient.get('date_of_birth', 'Not specified')}")
        if patient.get('diagnosis'):
            diagnosis = patient.get('diagnosis', '')[:50]  # Truncate diagnosis
            context_parts.append(f"   - Diagnosis: {diagnosis}{'...' if len(patient.get('diagnosis', '')) > 50 else ''}")
        if patient.get('prescription'):
            prescription = patient.get('prescription', '')[:50]  # Truncate prescription
            context_parts.append(f"   - Prescription: {prescription}{'...' if len(patient.get('prescription', '')) > 50 else ''}")
    
    if len(patients) > 5:
        context_parts.append(f"\n... and {len(patients) - 5} more patients")
    
    return "\n".join(context_parts)

@router.get("/cache-stats")
async def get_cache_statistics():
    """Get file processing cache statistics"""
    return {
        "cache_stats": file_cache_service.get_cache_stats(),
        "message": "Cache statistics retrieved successfully"
    }

@router.post("/clear-cache")
async def clear_file_cache():
    """Clear file processing cache"""
    file_cache_service.processed_files_cache.clear()
    file_cache_service.file_summaries_cache.clear()
    return {"message": "File cache cleared successfully"}

@router.get("/session/{session_id}/files")
async def get_session_files(session_id: str):
    """Get files attached to a session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    files = chat_sessions[session_id].get("files", [])
    
    # Return file info without content
    file_list = []
    for file_data in files:
        file_list.append({
            "file_id": file_data.get("file_id"),
            "name": file_data.get("name"),
            "type": file_data.get("type"),
            "uploaded_at": file_data.get("uploaded_at").isoformat() if file_data.get("uploaded_at") else None,
            "size": len(file_data.get("content", b""))
        })
    
    return {"files": file_list}

@router.delete("/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

def _format_patients_for_chat(patients: List[Dict[str, Any]]) -> str:
    """Format patient data for chat context"""
    if not patients:
        return "No patient records available."
    
    context_parts = [f"Available Patient Records ({len(patients)} total):"]
    
    for i, patient in enumerate(patients[:10], 1):  # Limit to first 10 for context
        context_parts.append(f"\n{i}. {patient.get('name', 'Unknown')}")
        context_parts.append(f"   - DOB: {patient.get('date_of_birth', 'Not specified')}")
        if patient.get('diagnosis'):
            context_parts.append(f"   - Diagnosis: {patient.get('diagnosis')}")
        if patient.get('prescription'):
            prescription = patient.get('prescription', '')
            if len(prescription) > 100:
                prescription = prescription[:100] + "..."
            context_parts.append(f"   - Prescription: {prescription}")
    
    if len(patients) > 10:
        context_parts.append(f"\n... and {len(patients) - 10} more patients")
    
    return "\n".join(context_parts)
