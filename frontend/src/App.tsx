import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import PatientForm from './components/PatientForm';
import PatientList from './components/PatientList';
import ChatInterface from './components/ChatInterface';
import { documentsApi, patientsApi } from './services/api';
import { DocumentProcessingResult, Patient, PatientCreate, PatientUpdate } from './types';
import './index.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'upload' | 'list' | 'chat'>('upload');
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [extractedData, setExtractedData] = useState<DocumentProcessingResult | null>(null);
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState<File[]>([]);

  const handleFileUpload = async (file: File) => {
    // Stage files only; defer processing until Complete Upload
    setUploadedDocuments(prev => [...prev, file]);
  };

  const handleUploadComplete = async () => {
    if (uploadedDocuments.length === 0) {
      setShowForm(true);
      return;
    }

    setIsUploading(true);
    try {
      const result = await documentsApi.uploadDocuments(uploadedDocuments);
      setExtractedData(result);
      setShowForm(true);
    } catch (error) {
      console.error('Error processing documents:', error);
      alert('Failed to process documents. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handlePatientSubmit = async (patientData: PatientCreate | PatientUpdate) => {
    setIsSubmitting(true);
    try {
      if (editingPatient) {
        // Update existing patient
        await patientsApi.updatePatient(editingPatient.id, patientData as PatientUpdate);
        alert('Patient updated successfully!');
        setEditingPatient(null);
      } else {
        // Create new patient - ensure we have all required fields
        const createData: PatientCreate = {
          name: patientData.name || '',
          date_of_birth: patientData.date_of_birth || '',
          diagnosis: patientData.diagnosis || '',
          prescription: patientData.prescription || ''
        };
        await patientsApi.createPatient(createData);
        alert('Patient created successfully!');
      }
      
      setExtractedData(null);
      setShowForm(false);
      setUploadedDocuments([]);
      setCurrentView('list');
      setRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Error saving patient:', error);
      alert('Failed to save patient. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePatientEdit = (patient: Patient) => {
    setEditingPatient(patient);
    setShowForm(true);
    setCurrentView('upload');
  };

  const handleCancel = () => {
    setExtractedData(null);
    setEditingPatient(null);
    setShowForm(false);
    setUploadedDocuments([]);
    setCurrentView('upload');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'upload':
        return (
          <div className="max-w-4xl mx-auto space-y-8 animate-slide-up">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-white mb-4">
                Patient Document Management
              </h1>
              <p className="text-healthix-gray-light text-lg">
                Upload patient documents to extract and organize medical information
              </p>
            </div>
            
            <DocumentUpload 
              onFileUpload={handleFileUpload} 
              onUploadComplete={handleUploadComplete}
              isUploading={isUploading} 
            />
            
            {/* Processing Status */}
            {uploadedDocuments.length > 0 && !showForm && (
              <div className="mt-6 p-4 card-glow animate-fade-in">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-healthix-green mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>

                  <p className="text-sm text-white">
                    <strong>{uploadedDocuments.length} document{uploadedDocuments.length !== 1 ? 's' : ''} uploaded and processed.</strong>
                    {extractedData ? ' Patient information extracted successfully!' : ' Click "Complete Upload" to continue.'}
                    {isUploading ? ' Processing...' : ' Click "Complete Upload & Process Documents" to continue.'}

                  </p>
                </div>
              </div>
            )}
            
            {/* Patient Form - Always visible below upload area */}
            {(showForm || editingPatient) && (
              <div className="border-t pt-8">
                <PatientForm
                  initialData={
                    extractedData?.extracted_data || 
                    (editingPatient ? {
                      name: editingPatient.name,
                      date_of_birth: editingPatient.date_of_birth,
                      diagnosis: editingPatient.diagnosis || '',
                      prescription: editingPatient.prescription || ''
                    } : undefined)
                  }
                  onSubmit={handlePatientSubmit}
                  onCancel={handleCancel}
                  isSubmitting={isSubmitting}
                  title={editingPatient ? 'Edit Patient Information' : 'Patient Information'}
                />
                
                {extractedData && (
                  <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-sm text-yellow-400">
                      <strong>Confidence Score:</strong> {(extractedData.confidence_score * 100).toFixed(1)}%
                    </p>
                    <p className="text-sm text-yellow-300 mt-2">
                      Information extracted from {uploadedDocuments.length} document{uploadedDocuments.length !== 1 ? 's' : ''}. Please review and correct before saving.
                    </p>
                  </div>
                )}
              </div>
            )}
            
            {/* Manual Entry Option */}
            {!showForm && !editingPatient && (
              <div className="text-center border-t border-healthix-dark-lighter pt-8">
                <p className="text-healthix-gray-light mb-4">
                  Or enter patient information manually
                </p>
                <button
                  onClick={() => setShowForm(true)}
                  className="btn-secondary"
                >
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Enter Patient Information Manually
                </button>
              </div>
            )}
          </div>
        );
      
      case 'list':
        return (
          <div className="max-w-6xl mx-auto">
            <PatientList 
              onPatientSelect={handlePatientEdit}
              refreshTrigger={refreshTrigger}
            />
          </div>
        );
      
      case 'chat':
        return (
          <div className="max-w-4xl mx-auto">
            <ChatInterface className="h-[600px]" />
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-healthix-dark">
      {/* Navigation */}
      <nav className="bg-healthix-dark-light border-b border-healthix-dark-lighter shadow-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20">
            <div className="flex items-center space-x-4">
              {/* Logo Space */}
              <div className="flex items-center space-x-4">
                <div className="relative group">
                  <img 
                    src="/logo_healthix.jpg" 
                    alt="Healthix Logo" 
                    className="w-12 h-12 rounded-xl shadow-glow hover:shadow-glow-lg transition-all duration-300 group-hover:scale-110 object-cover border-2 border-healthix-green/20 group-hover:border-healthix-green/40"
                  />
                  <div className="absolute inset-0 bg-gradient-to-br from-healthix-green/10 to-healthix-green-light/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
                <div className="flex flex-col">
                  <h1 className="text-2xl font-bold text-gradient hover:scale-105 transition-transform duration-300 cursor-default">
                    Healthix
                  </h1>
                  <p className="text-xs text-healthix-gray-light -mt-1 hover:text-healthix-green transition-colors duration-300">
                    Healthcare Data Platform
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-2 items-center">
              <button
                onClick={() => {
                  setCurrentView('upload');
                  if (currentView !== 'upload') {
                    setShowForm(false);
                    setExtractedData(null);
                    setEditingPatient(null);
                    setUploadedDocuments([]);
                  }
                }}
                className={currentView === 'upload' ? 'nav-link-active' : 'nav-link'}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v1H8V5z" />
                </svg>
                Dashboard
              </button>
              
              <button
                onClick={() => {
                  setCurrentView('list');
                  setShowForm(false);
                  setExtractedData(null);
                  setEditingPatient(null);
                  setUploadedDocuments([]);
                }}
                className={currentView === 'list' ? 'nav-link-active' : 'nav-link'}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Patients
              </button>
              
              <button
                onClick={() => {
                  setCurrentView('chat');
                  setShowForm(false);
                  setExtractedData(null);
                  setEditingPatient(null);
                  setUploadedDocuments([]);
                }}
                className={currentView === 'chat' ? 'nav-link-active' : 'nav-link'}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Chat
              </button>
              
              {/* User Profile Area */}
              <div className="ml-4 pl-4 border-l border-healthix-dark-lighter">
                <div className="w-8 h-8 bg-gradient-to-br from-healthix-green to-healthix-green-light rounded-full flex items-center justify-center shadow-glow cursor-pointer hover:shadow-glow-lg transition-all duration-300">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="py-8 px-4 animate-fade-in">
        {renderCurrentView()}
      </main>
    </div>
  );
};

export default App;
