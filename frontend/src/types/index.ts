export interface Patient {
  id: string;
  name: string;
  date_of_birth: string;
  diagnosis?: string;
  prescription?: string;
  created_at: string;
  updated_at?: string;
}

export interface PatientCreate {
  name: string;
  date_of_birth: string;
  diagnosis?: string;
  prescription?: string;
}

export interface PatientUpdate {
  name?: string;
  date_of_birth?: string;
  diagnosis?: string;
  prescription?: string;
}

export interface DocumentProcessingResult {
  extracted_data: PatientCreate;
  confidence_score: number;
  raw_text: string;
}

export interface DocumentProcessingResultMulti extends DocumentProcessingResult {
  documents_processed: number;
  processing_method?: string;
  document_types?: string[];
  medical_history?: string;
  doctor_name?: string;
  hospital_clinic?: string;
}

export interface ChatMessage {
  message: string;
}

export interface ChatResponse {
  response: string;
  sources: string[];
  patient_ids: string[];
}
