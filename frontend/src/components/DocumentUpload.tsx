import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface DocumentUploadProps {
  onFileUpload: (file: File) => void;
  onUploadComplete: () => void;
  isUploading: boolean;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onFileUpload, onUploadComplete, isUploading }) => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const newFile = acceptedFiles[0];
      setUploadedFiles(prev => [...prev, newFile]);
      onFileUpload(newFile);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf']
    },
    multiple: true,
    disabled: isUploading
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 ease-in-out transform
          ${isDragActive ? 'border-healthix-green bg-healthix-green/10 scale-105 shadow-glow' : 'border-healthix-dark-lighter bg-healthix-dark-light/50'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-healthix-green hover:bg-healthix-green/5 hover:scale-102 hover:shadow-glow'}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-6">
          <div className="flex justify-center">
            <div className={`p-4 rounded-full transition-all duration-300 ${isDragActive ? 'bg-healthix-green/20' : 'bg-healthix-dark-lighter'}`}>
              <svg
                className={`h-16 w-16 transition-colors duration-300 ${isDragActive ? 'text-healthix-green' : 'text-healthix-gray-light'}`}
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
          
          {isUploading ? (
            <div className="animate-fade-in">
              <p className="text-white text-lg font-medium">Processing document...</p>
              <div className="mt-4">
                <div className="loading-spinner h-8 w-8 mx-auto"></div>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-white text-lg font-medium mb-2">
                {isDragActive
                  ? 'Drop the documents here...'
                  : 'Drag & drop patient documents, or click to select'}
              </p>
              <p className="text-healthix-gray-light mb-3">
                Supports: Images (JPG, PNG), Text files, PDFs
              </p>
              <p className="text-healthix-green text-sm font-medium">
                You can upload multiple documents for the same patient
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6 animate-slide-up">
          <h3 className="text-sm font-medium text-white mb-4">
            Uploaded Documents ({uploadedFiles.length}):
          </h3>
          <div className="space-y-3 max-h-40 overflow-y-auto">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-3 card-modern hover-lift">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-healthix-green/20 rounded-lg">
                    <svg className="h-4 w-4 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <span className="text-sm text-white truncate max-w-xs font-medium">{file.name}</span>
                </div>
                <span className="text-xs text-healthix-gray-light bg-healthix-dark-lighter px-2 py-1 rounded">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ))}
          </div>
          
          {/* Upload Complete Button */}
          <div className="mt-6 text-center">
            <button
              onClick={onUploadComplete}
              disabled={isUploading}
              className="btn-primary"
            >
              <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Complete Upload & Process Documents
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
