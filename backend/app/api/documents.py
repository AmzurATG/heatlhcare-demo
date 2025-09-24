from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
import shutil
from pathlib import Path
import pandas as pd
import json
import uuid
import logging

from app.models.patient import DocumentProcessingResult, PatientBase
from app.services.gemini_service import GeminiService
from app.models.patient import DocumentProcessingResultMulti
from app.services.rag_service import RAGService
from app.services.tabular_processor import TabularProcessor

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get Gemini service
def get_gemini_service() -> GeminiService:
    return GeminiService()

# Dependency to get RAG service
def get_rag_service() -> RAGService:
    return RAGService()

# Dependency to get TabularProcessor service
def get_tabular_processor() -> TabularProcessor:
    return TabularProcessor()

@router.post("/upload", response_model=DocumentProcessingResult)
async def upload_document(
    file: UploadFile = File(...),
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Upload and process a patient document"""
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'text/plain', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (10MB max)
    max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size: {max_size} bytes"
        )
    
    try:
        # Save file temporarily
        upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
        upload_dir.mkdir(exist_ok=True)
        
        safe_filename = file.filename or "uploaded_file"
        file_path = upload_dir / safe_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Process document with Gemini
        result = await gemini_service.extract_patient_data(file_content, file.content_type)
        
        # Clean up temporary file
        if file_path.exists():
            file_path.unlink()
        
        return DocumentProcessingResult(
            extracted_data=PatientBase(
                name=result.get("name") or "Unknown",
                date_of_birth=result.get("date_of_birth") or "1900-01-01",
                diagnosis=result.get("diagnosis"),
                prescription=result.get("prescription")
            ),
            confidence_score=result.get("confidence_score", 0.0),
            raw_text=result.get("raw_text", "")
        )
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/supported-types")
async def get_supported_file_types():
    """Get list of supported file types"""
    return {
        "supported_types": [
            "image/jpeg",
            "image/png", 
            "image/jpg",
            "text/plain",
            "application/pdf"
        ],
        "max_file_size_bytes": int(os.getenv("MAX_FILE_SIZE", 10485760))
    }

@router.post("/upload-multiple", response_model=DocumentProcessingResultMulti)
async def upload_multiple_documents(
    files: list[UploadFile] = File(...),
    gemini_service: GeminiService = Depends(get_gemini_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Upload and process multiple patient documents in a single LLM context."""
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'text/plain', 'application/pdf']
    max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))

    # Validate all files and prepare payloads
    files_data = []
    total_bytes = 0
    for f in files:
        if f.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {f.content_type} not supported. Allowed types: {', '.join(allowed_types)}"
            )
        content = await f.read()
        total_bytes += len(content)
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} exceeds maximum size of {max_size} bytes"
            )
        files_data.append({
            "content": content,
            "name": f.filename or "uploaded_file",
            "type": f.content_type
        })

    try:
        # Single LLM call with all files via Gemini file upload API
        result = await gemini_service.extract_patient_data_from_multiple_files(files_data)
        # Create an upload_batch_id for staging
        upload_batch_id = str(uuid.uuid4())
        # Stage combined raw_text + basic fields for immediate chat availability
        combined_text = " | ".join(filter(None, [
            result.get("name"),
            result.get("date_of_birth"),
            result.get("diagnosis"),
            result.get("prescription"),
            result.get("raw_text", "")
        ]))
        try:
            await rag_service.add_staging_documents(
                upload_batch_id=upload_batch_id,
                text=combined_text,
                metadata={"document_types": result.get("document_types") or []}
            )
        except Exception as stage_err:
            print(f"Warning: staging index failed: {stage_err}")

        # Map to a response shape similar to single-file result plus metadata
        return {
            "extracted_data": {
                "name": result.get("name") or "Unknown",
                "date_of_birth": result.get("date_of_birth") or "1900-01-01",
                "diagnosis": result.get("diagnosis"),
                "prescription": result.get("prescription")
            },
            "confidence_score": result.get("confidence_score", 0.0),
            "raw_text": result.get("raw_text", ""),
            "documents_processed": result.get("documents_processed", len(files)),
            "processing_method": result.get("processing_method"),
            "document_types": result.get("document_types"),
            "medical_history": result.get("medical_history"),
            "doctor_name": result.get("doctor_name"),
            "hospital_clinic": result.get("hospital_clinic"),
            "upload_batch_id": upload_batch_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@router.post("/attach-to-chat")
async def attach_file_to_chat(
    file: UploadFile = File(...),
    chat_session_id: Optional[str] = None,
    gemini_service: GeminiService = Depends(get_gemini_service),
    rag_service: RAGService = Depends(get_rag_service),
    tabular_processor: TabularProcessor = Depends(get_tabular_processor)
):
    """Attach a file to chat context - supports all document types plus tabular data"""
    
    # Extended allowed types for chat attachments
    document_types = ['image/jpeg', 'image/png', 'image/jpg', 'text/plain', 'application/pdf']
    tabular_types = [
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'text/csv',  # .csv
        'text/tab-separated-values',  # .tsv
        'application/json'  # .json
    ]
    
    all_allowed_types = document_types + tabular_types
    
    if file.content_type not in all_allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Allowed types: {', '.join(all_allowed_types)}"
        )
    
    # Validate file size (20MB max for chat attachments)
    max_size = int(os.getenv("MAX_CHAT_FILE_SIZE", 20971520))  # 20MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size: {max_size} bytes"
        )
    
    try:
        # Generate chat session ID if not provided
        if not chat_session_id:
            chat_session_id = str(uuid.uuid4())
        
        filename = file.filename or "attached_file"
        processed_content = ""
        attachment_type = ""
        metadata = {
            "filename": filename,
            "content_type": file.content_type,
            "file_size": len(file_content),
            "chat_session_id": chat_session_id
        }
        
        # Process based on file type
        if tabular_processor.is_tabular_file(file.content_type, filename):
            # Process tabular data
            attachment_type = "tabular"
            tabular_result = await tabular_processor.process_tabular_file(
                file_content, filename, file.content_type
            )
            
            processed_content = f"""
TABULAR DATA ATTACHMENT: {filename}

{tabular_result.get('summary', '')}

DATA STRUCTURE:
- Shape: {tabular_result.get('shape', [0, 0])[0]} rows × {tabular_result.get('shape', [0, 0])[1]} columns
- Columns: {', '.join(tabular_result.get('columns', []))}

KEY INSIGHTS:
{chr(10).join(tabular_result.get('insights', []))}

CONTEXTUAL INFORMATION:
{tabular_result.get('contextual_text', '')}

This tabular data is now available for analysis and queries in this chat session.
"""
            
            metadata.update({
                "tabular_analysis": tabular_result,
                "data_columns": tabular_result.get('columns', []),
                "data_shape": tabular_result.get('shape', [0, 0])
            })
            
        elif file.content_type in document_types:
            # Process regular documents (images, PDFs, text)
            attachment_type = "document"
            if file.content_type.startswith('image/'):
                # For images, we'll extract text content
                doc_result = await gemini_service.extract_patient_data(file_content, file.content_type)
                processed_content = f"""
DOCUMENT ATTACHMENT: {filename} (Image)

EXTRACTED CONTENT:
{doc_result.get('raw_text', 'No text extracted')}

STRUCTURED DATA:
- Name: {doc_result.get('name', 'N/A')}
- Date of Birth: {doc_result.get('date_of_birth', 'N/A')}
- Diagnosis: {doc_result.get('diagnosis', 'N/A')}
- Prescription: {doc_result.get('prescription', 'N/A')}

This document content is now available in the chat context.
"""
                metadata.update({
                    "extracted_data": doc_result,
                    "confidence_score": doc_result.get('confidence_score', 0.0)
                })
                
            elif file.content_type == 'application/pdf':
                # Process PDF
                doc_result = await gemini_service.extract_patient_data(file_content, file.content_type)
                processed_content = f"""
DOCUMENT ATTACHMENT: {filename} (PDF)

EXTRACTED CONTENT:
{doc_result.get('raw_text', 'No text extracted')}

STRUCTURED DATA:
- Name: {doc_result.get('name', 'N/A')}
- Date of Birth: {doc_result.get('date_of_birth', 'N/A')}
- Diagnosis: {doc_result.get('diagnosis', 'N/A')}
- Prescription: {doc_result.get('prescription', 'N/A')}

This document content is now available in the chat context.
"""
                metadata.update({
                    "extracted_data": doc_result,
                    "confidence_score": doc_result.get('confidence_score', 0.0)
                })
                
            elif file.content_type == 'text/plain':
                # Process text file
                try:
                    text_content = file_content.decode('utf-8', errors='ignore')
                    processed_content = f"""
TEXT ATTACHMENT: {filename}

CONTENT:
{text_content[:2000]}{'...' if len(text_content) > 2000 else ''}

This text content is now available in the chat context.
"""
                except:
                    processed_content = f"TEXT ATTACHMENT: {filename} (Could not decode text content)"
        
        # Add to chat context via RAG service
        try:
            await rag_service.add_chat_attachment(
                chat_session_id=chat_session_id,
                content=processed_content,
                metadata=metadata
            )
        except Exception as rag_error:
            logger.error(f"Failed to add attachment to RAG: {str(rag_error)}")
            # Continue without RAG - attachment still processed
        
        return {
            "message": f"File {filename} successfully attached to chat",
            "chat_session_id": chat_session_id,
            "attachment_type": attachment_type,
            "processed_content_preview": processed_content[:500] + "..." if len(processed_content) > 500 else processed_content,
            "metadata": {
                "filename": filename,
                "content_type": file.content_type,
                "file_size": len(file_content),
                "attachment_type": attachment_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing attachment: {str(e)}")

@router.get("/chat-attachments/{chat_session_id}")
async def get_chat_attachments(
    chat_session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get all attachments for a chat session"""
    try:
        attachments = await rag_service.get_chat_attachments(chat_session_id)
        return {
            "chat_session_id": chat_session_id,
            "attachments": attachments,
            "total_attachments": len(attachments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attachments: {str(e)}")
