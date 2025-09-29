import axios from 'axios';
import { Patient, PatientCreate, PatientUpdate, DocumentProcessingResult, ChatMessage, ChatResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Documents API
export const documentsApi = {
  uploadDocument: async (file: File): Promise<DocumentProcessingResult> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  uploadDocuments: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    const response = await api.post('/api/documents/upload-multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getSupportedTypes: async () => {
    const response = await api.get('/api/documents/supported-types');
    return response.data;
  },
};

// Patients API
export const patientsApi = {
  createPatient: async (patientData: PatientCreate): Promise<Patient> => {
    // Send patient data directly (no files)
    const response = await fetch('/api/patients/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: patientData.name,
        date_of_birth: patientData.date_of_birth,
        diagnosis: patientData.diagnosis || null,
        prescription: patientData.prescription || null,
        confidence_score: null,
        raw_text: null
      })
    });

    if (!response.ok) {
      throw new Error('Failed to create patient');
    }

    const result = await response.json();
    return result.patient;
  },

  getPatients: async (): Promise<Patient[]> => {
    const response = await fetch('/api/patients/');
    
    if (!response.ok) {
      throw new Error('Failed to fetch patients');
    }

    const result = await response.json();
    // Extract patients array from the new response structure
    return result.patients || [];
  },

  getPatient: async (id: string): Promise<Patient> => {
    const response = await fetch(`/api/patients/${id}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch patient');
    }

    const result = await response.json();
    return result.patient;
  },

  updatePatient: async (id: string, patientData: PatientUpdate): Promise<Patient> => {
    const response = await fetch(`/api/patients/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: patientData.name,
        date_of_birth: patientData.date_of_birth,
        diagnosis: patientData.diagnosis,
        prescription: patientData.prescription
      })
    });

    if (!response.ok) {
      throw new Error('Failed to update patient');
    }

    const result = await response.json();
    return result.patient;
  },

  deletePatient: async (id: string): Promise<void> => {
    const response = await fetch(`/api/patients/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete patient');
    }
  }
};

// Chat API
export const chatApi = {
  sendMessage: async (message: ChatMessage): Promise<ChatResponse> => {
    const response = await api.post('/api/chat/', message);
    return response.data;
  },

  refreshKnowledgeBase: async (): Promise<void> => {
    await api.post('/api/chat/refresh-knowledge-base');
  },

  // Add new methods for patient-aware chat
  sendMessageWithPatientContext: async (
    sessionId: string, 
    query: string, 
    files?: File[]
  ): Promise<any> => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('query', query);
    formData.append('include_all_patients', 'true');
    formData.append('max_patients', '10');
    
    if (files && files.length > 0) {
      files.forEach(file => {
        formData.append('files', file);
      });
    }

    const response = await fetch('/api/patients/context/chat-query', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to get chat response');
    }

    return response.json();
  },

  getPatientContext: async (patientIds?: string[], limit: number = 10): Promise<any> => {
    const params = new URLSearchParams();
    if (patientIds && patientIds.length > 0) {
      params.append('patient_ids', patientIds.join(','));
    }
    params.append('limit', limit.toString());
    params.append('include_recent', 'true');

    const response = await fetch(`/api/patients/context/chat?${params}`);
    if (!response.ok) {
      throw new Error('Failed to get patient context');
    }

    return response.json();
  },

  startChatSession: async (): Promise<{ session_id: string }> => {
    const response = await fetch('/api/chat/start-session', {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('Failed to start chat session');
    }

    return response.json();
  },
};

export default api;
