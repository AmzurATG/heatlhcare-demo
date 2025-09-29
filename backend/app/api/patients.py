from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel

# Import the new patient service
from ..services.patient_service import get_patient_service
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()

# Add new Pydantic model for direct patient creation
class PatientCreateRequest(BaseModel):
    name: str
    date_of_birth: str
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    confidence_score: Optional[float] = None
    raw_text: Optional[str] = None

@router.post("/", response_model=Dict[str, Any])
async def create_patient(patient_data: PatientCreateRequest):
    """Create a new patient with direct field data (no files)"""
    try:
        print(f"📥 Received request for patient creation with data: {patient_data}")
        logger.info(f"Received request for patient creation")
        
        # Get patient service
        patient_service = get_patient_service()
        
        # Convert Pydantic model to dict
        patient_dict = {
            "name": patient_data.name,
            "date_of_birth": patient_data.date_of_birth,
            "diagnosis": patient_data.diagnosis,
            "prescription": patient_data.prescription,
            "confidence_score": patient_data.confidence_score or 0.0,
            "raw_text": patient_data.raw_text or ""
        }
        
        print(f"🧠 Patient data to create: {patient_dict}")
        logger.info(f"Patient data to create: {patient_dict}")
        
        # Create patient using the service (handles both Supabase and SQLite)
        created_patient = await patient_service.create_patient(patient_dict)
        
        print(f"✅ Patient created successfully: {created_patient}")
        logger.info(f"Patient created successfully with ID: {created_patient.get('id')}")
        
        return {
            "success": True,
            "message": "Patient created successfully",
            "patient": created_patient
        }
        
    except Exception as e:
        error_msg = f"Failed to create patient: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# Keep the file-based endpoint for document processing, but rename it
@router.post("/from-files", response_model=Dict[str, Any])
async def create_patient_from_files(files: List[UploadFile] = File(None)):
    """Create a new patient from uploaded documents"""
    try:
        print(f"📥 Received request for patient creation")
        print(f"📋 Files parameter: {files}")
        print(f"📋 Files type: {type(files)}")
        
        logger.info(f"Received request for patient creation")
        
        # Handle case where files might be None or empty
        if not files:
            print("❌ No files provided")
            raise HTTPException(status_code=400, detail="No files uploaded")
            
        # Check if we received empty file upload
        if len(files) == 1 and (not files[0].filename or files[0].filename == ''):
            print("❌ Empty file upload detected")
            raise HTTPException(status_code=400, detail="No valid files uploaded")
        
        print(f"📁 Processing {len(files)} files")
        logger.info(f"Processing {len(files)} files")
        
        # Get services
        patient_service = get_patient_service()
        gemini_service = GeminiService()
        
        # Process files with Gemini
        files_data = []
        for i, file in enumerate(files):
            print(f"📄 File {i}: {file.filename}, type: {file.content_type}")
            if file.filename:  # Skip empty files
                content = await file.read()
                print(f"📄 File {i} content size: {len(content)} bytes")
                files_data.append({
                    'content': content,
                    'name': file.filename,
                    'type': file.content_type or 'application/octet-stream'
                })
        
        if not files_data:
            raise HTTPException(status_code=400, detail="No valid files to process")
        
        print(f"📋 Processing {len(files_data)} valid files")
        
        # Extract patient data
        if len(files_data) == 1:
            # Single file processing
            patient_data = await gemini_service.extract_patient_data(
                files_data[0]['content'],
                files_data[0]['type']
            )
        else:
            # Multiple files processing
            patient_data = await gemini_service.extract_patient_data_from_multiple_files(files_data)
        
        print(f"🧠 Extracted patient data: {patient_data}")
        logger.info(f"Extracted patient data: {patient_data}")
        
        # Create patient using the service (handles both Supabase and SQLite)
        created_patient = await patient_service.create_patient(patient_data)
        
        print(f"✅ Patient created successfully: {created_patient}")
        logger.info(f"Patient created successfully with ID: {created_patient.get('id')}")
        
        return {
            "success": True,
            "message": "Patient created successfully",
            "patient": created_patient
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to create patient: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/test", response_model=Dict[str, Any])
async def test_endpoint(files: List[UploadFile] = File(None)):
    """Test endpoint to debug file upload issues"""
    try:
        print(f"🧪 TEST: Received request")
        logger.info("TEST: Received request")
        
        if not files:
            return {"message": "No files received", "files": None}
        
        files_info = []
        for i, file in enumerate(files):
            if file and file.filename:
                content_size = len(await file.read())
                files_info.append({
                    "index": i,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": content_size
                })
        
        return {
            "message": "Test successful",
            "files_count": len(files) if files else 0,
            "files_info": files_info
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/", response_model=Dict[str, Any])
async def get_patients(limit: int = 100):
    """Get all patients"""
    try:
        patient_service = get_patient_service()
        patients = await patient_service.get_all_patients(limit)
        
        return {
            "success": True,
            "patients": patients,
            "count": len(patients)
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve patients: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{patient_id}", response_model=Dict[str, Any])
async def get_patient(patient_id: int):
    """Get a specific patient by ID"""
    try:
        patient_service = get_patient_service()
        patient = await patient_service.get_patient_by_id(patient_id)
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "success": True,
            "patient": patient
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to retrieve patient: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.put("/{patient_id}", response_model=Dict[str, Any])
async def update_patient(patient_id: int, patient_data: PatientCreateRequest):
    """Update an existing patient"""
    try:
        print(f"📝 Updating patient ID {patient_id} with data: {patient_data}")
        logger.info(f"Updating patient ID {patient_id}")
        
        # Get patient service
        patient_service = get_patient_service()
        
        # Convert Pydantic model to dict
        update_dict = {
            "name": patient_data.name,
            "date_of_birth": patient_data.date_of_birth,
            "diagnosis": patient_data.diagnosis,
            "prescription": patient_data.prescription
        }
        
        # Update patient using the service
        if patient_service.db_type == "supabase":
            # For Supabase, we need to use the SupabaseService
            from ..services.supabase_service import SupabaseService
            supabase_service = SupabaseService()
            updated_patient = await supabase_service.update_patient(patient_id, update_dict)
        else:
            # For SQLite fallback
            from ..database import SessionLocal
            from ..services.database_service import DatabaseService
            db = SessionLocal()
            try:
                db_service = DatabaseService(db)
                updated_patient = db_service.update_patient(str(patient_id), update_dict)
                if updated_patient:
                    updated_patient = {
                        "id": updated_patient.id,
                        "name": updated_patient.name,
                        "date_of_birth": updated_patient.date_of_birth,
                        "diagnosis": updated_patient.diagnosis,
                        "prescription": updated_patient.prescription,
                        "created_at": updated_patient.created_at.isoformat() if updated_patient.created_at else None,
                        "updated_at": updated_patient.updated_at.isoformat() if updated_patient.updated_at else None
                    }
            finally:
                db.close()
        
        if not updated_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        print(f"✅ Patient updated successfully: {updated_patient}")
        logger.info(f"Patient updated successfully with ID: {patient_id}")
        
        return {
            "success": True,
            "message": "Patient updated successfully",
            "patient": updated_patient
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to update patient: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.delete("/{patient_id}", response_model=Dict[str, Any])
async def delete_patient(patient_id: int):
    """Delete a patient"""
    try:
        print(f"🗑️ Deleting patient ID {patient_id}")
        logger.info(f"Deleting patient ID {patient_id}")
        
        # Get patient service
        patient_service = get_patient_service()
        
        # Delete patient using the service
        if patient_service.db_type == "supabase":
            # For Supabase, we need to use the SupabaseService
            from ..services.supabase_service import SupabaseService
            supabase_service = SupabaseService()
            success = await supabase_service.delete_patient(patient_id)
        else:
            # For SQLite fallback
            from ..database import SessionLocal
            from ..services.database_service import DatabaseService
            db = SessionLocal()
            try:
                db_service = DatabaseService(db)
                success = db_service.delete_patient(str(patient_id))
            finally:
                db.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        print(f"✅ Patient deleted successfully: ID {patient_id}")
        logger.info(f"Patient deleted successfully with ID: {patient_id}")
        
        return {
            "success": True,
            "message": "Patient deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to delete patient: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/search/{search_term}", response_model=Dict[str, Any])
async def search_patients(search_term: str, limit: int = 50):
    """Search patients by name or diagnosis"""
    try:
        patient_service = get_patient_service()
        patients = await patient_service.search_patients(search_term, limit)
        
        return {
            "success": True,
            "patients": patients,
            "count": len(patients),
            "search_term": search_term
        }
        
    except Exception as e:
        error_msg = f"Failed to search patients: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_patient_stats():
    """Get patient statistics"""
    try:
        patient_service = get_patient_service()
        stats = await patient_service.get_patients_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve patient stats: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/health/check", response_model=Dict[str, Any])
async def health_check():
    """Check database connectivity"""
    try:
        patient_service = get_patient_service()
        is_connected = await patient_service.test_connection()
        
        return {
            "success": True,
            "database_connected": is_connected,
            "database_type": patient_service.db_type
        }
        
    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/context/chat", response_model=Dict[str, Any])
async def get_patients_for_chat_context(
    patient_ids: Optional[str] = None,  # Comma-separated patient IDs
    limit: int = 10,
    include_recent: bool = True
):
    """Get patient data formatted for chat context"""
    try:
        patient_service = get_patient_service()
        
        # Parse patient IDs if provided
        specific_patient_ids = None
        if patient_ids:
            try:
                specific_patient_ids = [int(pid.strip()) for pid in patient_ids.split(',')]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid patient IDs format")
        
        # Get patients based on criteria
        if specific_patient_ids:
            patients = []
            for patient_id in specific_patient_ids:
                patient = await patient_service.get_patient_by_id(patient_id)
                if patient:
                    patients.append(patient)
        else:
            # Get recent patients or all patients up to limit
            patients = await patient_service.get_all_patients(limit)
            if include_recent and patients:
                # Sort by created_at or updated_at if available
                patients = sorted(patients, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Format for chat context
        context_text = _format_patients_for_chat(patients)
        
        return {
            "success": True,
            "context": context_text,
            "patients_count": len(patients),
            "patient_summaries": [
                {
                    "id": p.get('id'),
                    "name": p.get('name'),
                    "diagnosis": p.get('diagnosis', 'Not specified')
                }
                for p in patients
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to retrieve patient context: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

def _format_patients_for_chat(patients: List[Dict[str, Any]]) -> str:
    """Format patient data for use as chat context"""
    if not patients:
        return "No patient data available."
    
    context_parts = ["=== PATIENT DATABASE CONTEXT ===\n"]
    
    for i, patient in enumerate(patients, 1):
        context_parts.append(f"PATIENT {i}:")
        context_parts.append(f"- ID: {patient.get('id', 'Unknown')}")
        context_parts.append(f"- Name: {patient.get('name', 'Unknown')}")
        context_parts.append(f"- Date of Birth: {patient.get('date_of_birth', 'Not specified')}")
        context_parts.append(f"- Diagnosis: {patient.get('diagnosis', 'Not specified')}")
        context_parts.append(f"- Prescription: {patient.get('prescription', 'Not specified')}")
        
        if patient.get('confidence_score'):
            context_parts.append(f"- Confidence Score: {patient.get('confidence_score')}")
        
        if patient.get('raw_text'):
            # Truncate raw text if too long
            raw_text = patient.get('raw_text', '')[:500]
            if len(patient.get('raw_text', '')) > 500:
                raw_text += "... [truncated]"
            context_parts.append(f"- Additional Notes: {raw_text}")
        
        context_parts.append("")  # Empty line between patients
    
    context_parts.append("=== END PATIENT CONTEXT ===")
    
    return "\n".join(context_parts)

@router.post("/context/chat-query", response_model=Dict[str, Any])
async def chat_with_patient_context(
    query: str = Form(...),
    patient_ids: Optional[str] = Form(None),  # Comma-separated patient IDs
    files: List[UploadFile] = File(None),
    include_all_patients: bool = Form(False),
    max_patients: int = Form(5)
):
    """Chat with AI using patient data as context, optionally with additional documents"""
    try:
        print(f"💬 Chat query with patient context: {query[:100]}...")
        logger.info(f"Chat query received with patient context")
        
        # Get patient context
        patient_service = get_patient_service()
        gemini_service = GeminiService()
        
        # Determine which patients to include
        patients = []
        if patient_ids:
            # Specific patients requested
            try:
                specific_patient_ids = [int(pid.strip()) for pid in patient_ids.split(',')]
                for patient_id in specific_patient_ids:
                    patient = await patient_service.get_patient_by_id(patient_id)
                    if patient:
                        patients.append(patient)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid patient IDs format")
        elif include_all_patients:
            # Include recent patients
            patients = await patient_service.get_all_patients(max_patients)
        
        # Format patient context
        patient_context = _format_patients_for_chat(patients)
        
        # Process any uploaded files for additional context
        additional_context = ""
        if files and files[0].filename:  # Check if actual files were uploaded
            files_data = []
            for file in files:
                if file.filename:
                    content = await file.read()
                    files_data.append({
                        'content': content,
                        'name': file.filename,
                        'type': file.content_type or 'application/octet-stream'
                    })
            
            if files_data:
                # Extract text from documents for context
                additional_context = await gemini_service.extract_text_for_context(files_data)
        
        # Combine contexts
        full_context = patient_context
        if additional_context:
            full_context += f"\n\n=== ADDITIONAL DOCUMENT CONTEXT ===\n{additional_context}"
        
        # Generate response using Gemini
        response = await gemini_service.chat_with_context(query, full_context)
        
        print(f"✅ Chat response generated successfully")
        logger.info(f"Chat response generated for query about {len(patients)} patients")
        
        return {
            "success": True,
            "response": response,
            "context_summary": {
                "patients_included": len(patients),
                "patient_names": [p.get('name', 'Unknown') for p in patients],
                "has_document_context": bool(additional_context),
                "document_count": len(files_data) if 'files_data' in locals() else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to process chat query: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)
