import React, { useState, useRef } from 'react';

// SVG Icon Components (no external dependency)
const Upload = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const File = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const FileText = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const FileSpreadsheet = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V5a2 2 0 012-2h4a2 2 0 012 2v2" />
  </svg>
);

const Image = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

interface FileAttachmentProps {
  onFileSelect: (files: File[]) => void;
  attachedFiles: AttachedFile[];
  onRemoveFile: (fileId: string) => void;
  isUploading?: boolean;
}

interface AttachedFile {
  file_id: string;
  name: string;
  type: string;
  size: number;
  uploaded_at: number;
}

const FileAttachment: React.FC<FileAttachmentProps> = ({
  onFileSelect,
  attachedFiles,
  onRemoveFile,
  isUploading = false
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      // Accept common file types
      const validTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/gif',
        'text/plain',
        'application/json'
      ];
      
      const validExtensions = ['.csv', '.xls', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.json'];
      const hasValidExtension = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
      );
      
      return validTypes.includes(file.type) || hasValidExtension;
    });
    
    if (validFiles.length > 0) {
      onFileSelect(validFiles);
    } else {
      alert('Please select valid files (CSV, Excel, PDF, Images, Text files)');
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const getFileIcon = (fileType: string, fileName: string) => {
    if (fileType.startsWith('image/')) {
      return <Image className="h-4 w-4" />;
    } else if (fileType.includes('excel') || fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileType === 'text/csv') {
      return <FileSpreadsheet className="h-4 w-4" />;
    } else if (fileType === 'application/pdf') {
      return <FileText className="h-4 w-4" />;
    } else {
      return <File className="h-4 w-4" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="file-attachment-container">
      {/* File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={(e) => handleFileSelect(e.target.files)}
        className="hidden"
        accept=".csv,.xlsx,.xls,.pdf,.jpg,.jpeg,.png,.gif,.txt,.json,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/pdf,image/*,text/plain"
      />

      {/* Drag and Drop Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
        <p className="text-sm text-gray-600">
          {isUploading ? 'Uploading files...' : 'Drag & drop files here, or click to select'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Supports: CSV, Excel, PDF, Images, Text files
        </p>
      </div>

      {/* Attached Files List */}
      {attachedFiles.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Attached Files ({attachedFiles.length})
          </h4>
          <div className="space-y-2">
            {attachedFiles.map((file) => (
              <div
                key={file.file_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
              >
                <div className="flex items-center space-x-3">
                  {getFileIcon(file.type, file.name)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)} • {new Date(file.uploaded_at * 1000).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => onRemoveFile(file.file_id)}
                  className="text-red-500 hover:text-red-700 transition-colors"
                  title="Remove file"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileAttachment;