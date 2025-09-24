import React, { useState } from 'react';
import { PatientCreate, PatientUpdate } from '../types';

interface PatientFormProps {
  initialData?: PatientCreate;
  onSubmit: (data: PatientCreate | PatientUpdate) => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  title?: string;
}

const PatientForm: React.FC<PatientFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
  title = 'Patient Information'
}) => {
  const [formData, setFormData] = useState<PatientCreate>({
    name: initialData?.name || '',
    date_of_birth: initialData?.date_of_birth || '',
    diagnosis: initialData?.diagnosis || '',
    prescription: initialData?.prescription || ''
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.date_of_birth.trim()) {
      newErrors.date_of_birth = 'Date of birth is required';
    } else {
      // Basic date format validation
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(formData.date_of_birth)) {
        newErrors.date_of_birth = 'Date must be in YYYY-MM-DD format';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  return (
    <div className="card-glow p-8 max-w-2xl mx-auto animate-slide-up">
      <div className="flex items-center space-x-3 mb-8">
        <div className="p-2 bg-healthix-green/20 rounded-lg">
          <svg className="w-6 h-6 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-white">{title}</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="name" className="block text-sm font-medium text-white mb-2">
            Patient Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={`input-modern ${errors.name ? 'error-glow' : ''}`}
            placeholder="Enter patient's full name"
          />
          {errors.name && (
            <p className="mt-2 text-sm text-red-400 animate-fade-in flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {errors.name}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="date_of_birth" className="block text-sm font-medium text-white mb-2">
            Date of Birth *
          </label>
          <input
            type="date"
            id="date_of_birth"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleChange}
            className={`input-modern ${errors.date_of_birth ? 'error-glow' : ''}`}
          />
          {errors.date_of_birth && (
            <p className="mt-2 text-sm text-red-400 animate-fade-in flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {errors.date_of_birth}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="diagnosis" className="block text-sm font-medium text-white mb-2">
            Medical Condition
          </label>
          <textarea
            id="diagnosis"
            name="diagnosis"
            value={formData.diagnosis}
            onChange={handleChange}
            rows={3}
            className="textarea-modern"
            placeholder="Enter medical diagnosis or condition"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="prescription" className="block text-sm font-medium text-white mb-2">
            Notes
          </label>
          <textarea
            id="prescription"
            name="prescription"
            value={formData.prescription}
            onChange={handleChange}
            rows={4}
            className="textarea-modern"
            placeholder="Enter prescribed medications and instructions"
          />
        </div>

        <div className="flex justify-end space-x-4 pt-6 border-t border-healthix-dark-lighter">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn-secondary"
              disabled={isSubmitting}
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary"
          >
            {isSubmitting ? (
              <>
                <div className="loading-spinner h-4 w-4 mr-2"></div>
                Validating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Validate
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PatientForm;
