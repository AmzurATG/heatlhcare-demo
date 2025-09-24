from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., description="Date in YYYY-MM-DD format")
    diagnosis: Optional[str] = Field(None, max_length=500)
    prescription: Optional[str] = Field(None, max_length=1000)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[str] = None
    diagnosis: Optional[str] = Field(None, max_length=500)
    prescription: Optional[str] = Field(None, max_length=1000)

class Patient(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., description="Date in YYYY-MM-DD format")
    diagnosis: Optional[str] = Field(None, max_length=500)
    prescription: Optional[str] = Field(None, max_length=1000)
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentProcessingResult(BaseModel):
    extracted_data: PatientBase
    confidence_score: float = Field(..., ge=0, le=1)
    raw_text: str

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    upload_batch_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    patient_ids: List[str] = []

class DocumentProcessingResultMulti(BaseModel):
    extracted_data: PatientBase
    confidence_score: float = Field(..., ge=0, le=1)
    raw_text: str
    documents_processed: int = Field(..., ge=1)
    processing_method: Optional[str] = None
    document_types: Optional[List[str]] = None
    medical_history: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_clinic: Optional[str] = None
    upload_batch_id: Optional[str] = None
