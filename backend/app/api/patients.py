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
