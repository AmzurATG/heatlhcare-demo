import React, { useState, useEffect } from 'react';
import { Patient } from '../types';
import { patientsApi } from '../services/api';

interface PatientListProps {
  onPatientSelect?: (patient: Patient) => void;
  refreshTrigger?: number;
}

const PatientList: React.FC<PatientListProps> = ({ onPatientSelect, refreshTrigger }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPatients = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patientsApi.getPatients(); // Fixed: changed from getAllPatients to getPatients
      setPatients(data);
    } catch (err) {
      setError('Failed to load patients');
      console.error('Error loading patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, [refreshTrigger]);

  const handleDelete = async (patientId: string) => {
    if (!window.confirm('Are you sure you want to delete this patient record?')) {
      return;
    }

    try {
      await patientsApi.deletePatient(patientId);
      setPatients(prev => prev.filter(p => p.id !== patientId));
    } catch (err) {
      console.error('Error deleting patient:', err);
      alert('Failed to delete patient');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card-modern p-8 text-center">
        <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={loadPatients}
          className="btn-primary"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Retry
        </button>
      </div>
    );
  }

  if (patients.length === 0) {
    return (
      <div className="card-modern p-12 text-center">
        <div className="p-4 bg-healthix-green/20 rounded-full w-fit mx-auto mb-6">
          <svg className="w-12 h-12 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <p className="text-white text-lg font-medium mb-2">No patients found</p>
        <p className="text-healthix-gray-light">Upload a document to get started!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="card-modern p-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-healthix-green/20 rounded-lg">
            <svg className="w-5 h-5 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white">Patient Records</h2>
        </div>
        <p className="text-healthix-gray-light">{patients.length} patient{patients.length !== 1 ? 's' : ''} found</p>
      </div>
      
      <div className="grid gap-4">
        {patients.map((patient, index) => (
          <div
            key={patient.id}
            className="card-modern p-6 hover-lift animate-slide-up"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-healthix-green to-healthix-green-light rounded-full flex items-center justify-center shadow-glow">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">{patient.name}</h3>
                    <p className="text-sm text-healthix-gray-light">
                      Born: {new Date(patient.date_of_birth).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  {patient.diagnosis && (
                    <div className="p-3 bg-healthix-dark/50 rounded-lg border border-healthix-dark-lighter">
                      <p className="text-sm font-medium text-healthix-green mb-1">Medical Condition:</p>
                      <p className="text-sm text-white">{patient.diagnosis}</p>
                    </div>
                  )}
                  
                  {patient.prescription && (
                    <div className="p-3 bg-healthix-dark/50 rounded-lg border border-healthix-dark-lighter">
                      <p className="text-sm font-medium text-healthix-green mb-1">Notes:</p>
                      <p className="text-sm text-white">{patient.prescription}</p>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center text-xs text-healthix-gray-light space-x-4">
                  <span className="flex items-center">
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Added: {new Date(patient.created_at).toLocaleDateString()}
                  </span>
                  {patient.updated_at && (
                    <span className="flex items-center">
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Updated: {new Date(patient.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="flex flex-col space-y-2 ml-6">
                {onPatientSelect && (
                  <button
                    onClick={() => onPatientSelect(patient)}
                    className="btn-secondary text-sm"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit
                  </button>
                )}
                <button
                  onClick={() => handleDelete(patient.id)}
                  className="btn-danger text-sm"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PatientList;
