import React, { useState, useRef, useEffect } from 'react';
import { chatApi } from '../services/api';
import { ChatResponse } from '../types';

// Markdown components (will work when react-markdown is installed, fallback to div if not)
let ReactMarkdown: any;
try {
  ReactMarkdown = require('react-markdown').default;
} catch {
  ReactMarkdown = ({ children }: { children: any }) => (
    <div 
      className="whitespace-pre-wrap" 
      dangerouslySetInnerHTML={{ 
        __html: String(children)
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/\n/g, '<br/>')
      }} 
    />
  );
}

// File attachment interfaces
interface AttachedFile {
  file_id: string;
  name: string;
  type: string;
  size: number;
  uploaded_at: number;
}

interface ChatInterfaceProps {
  className?: string;
}

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  sources?: string[];
  patientIds?: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Welcome to Healthix! 👋 I\'m your intelligent patient data assistant. You can ask me questions about your patient records, such as "Show me patients with diabetes" or "What medications has John Smith been prescribed?"\n\n📎 You can also attach files (CSV, Excel, PDF, Images) using the attachment button below to add context to our conversation.',
      isUser: false,
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
    // Only initialize chat session if we don't have one already
    if (!sessionId) {
      initializeChatSession();
    }
  }, [messages]); // Remove sessionId from dependencies to prevent re-initialization

  // Initialize chat session only once
  const initializeChatSession = async () => {
    // Check if we already have a session in localStorage
    const existingSessionId = localStorage.getItem('chat_session_id');
    
    if (existingSessionId) {
      setSessionId(existingSessionId);
      // Load existing files for this session
      await fetchAttachedFiles(existingSessionId);
      return;
    }

    try {
      const response = await fetch('/api/chat/start-session', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        // Store session ID in localStorage for persistence
        localStorage.setItem('chat_session_id', data.session_id);
      }
    } catch (error) {
      console.error('Failed to initialize chat session:', error);
    }
  };

  // File attachment handlers
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    uploadFiles(fileArray);
  };

  // Drag and drop handlers
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
      const fileArray = Array.from(e.dataTransfer.files);
      uploadFiles(fileArray);
    }
  };

  const validateFiles = (files: File[]): File[] => {
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
    
    return files.filter(file => {
      const hasValidExtension = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
      );
      return validTypes.includes(file.type) || hasValidExtension;
    });
  };

  const uploadFiles = async (files: File[]) => {
    const validFiles = validateFiles(files);
    
    if (validFiles.length === 0) {
      alert('Please select valid files (CSV, Excel, PDF, Images, Text files)');
      return;
    }

    if (!sessionId) {
      await initializeChatSession();
    }

    setIsUploading(true);

    for (const file of validFiles) {
      try {
        const formData = new FormData();
        formData.append('session_id', sessionId || '');
        formData.append('file', file);

        const response = await fetch('/api/chat/upload-file', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Failed to upload ${file.name}`);
        }

        // Refresh attached files list
        await fetchAttachedFiles();
        
        // Add system message about file upload
        const fileMessage: Message = {
          id: Date.now().toString(),
          text: `📎 **${file.name}** has been uploaded and processed. You can now ask questions about its contents.`,
          isUser: false,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, fileMessage]);
        
      } catch (error) {
        console.error(`Error uploading file ${file.name}:`, error);
        
        const errorMessage: Message = {
          id: Date.now().toString(),
          text: `❌ Failed to upload **${file.name}**. Please try again.`,
          isUser: false,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    }
    
    setIsUploading(false);
    
    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const fetchAttachedFiles = async (sessionIdParam?: string) => {
    const targetSessionId = sessionIdParam || sessionId;
    if (!targetSessionId) return;

    try {
      const response = await fetch(`/api/chat/session/${targetSessionId}/files`);
      if (response.ok) {
        const data = await response.json();
        setAttachedFiles(data.files);
      }
    } catch (error) {
      console.error('Error fetching attached files:', error);
    }
  };

  const handleRemoveFile = (fileId: string) => {
    setAttachedFiles(prev => prev.filter(f => f.file_id !== fileId));
    
    const removeMessage: Message = {
      id: Date.now().toString(),
      text: `📎 File has been removed from the conversation context.`,
      isUser: false,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, removeMessage]);
  };

  const getFileIcon = (fileType: string, fileName: string) => {
    if (fileType.startsWith('image/')) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      );
    } else if (fileType.includes('excel') || fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileType === 'text/csv') {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V5a2 2 0 012-2h4a2 2 0 012 2v2" />
        </svg>
      );
    } else if (fileType === 'application/pdf') {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    try {
      // Always ensure we have a session
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        await initializeChatSession();
        currentSessionId = sessionId;
      }

      // Use the file-aware chat API if we have a session and files
      if (currentSessionId && attachedFiles.length > 0) {
        const formData = new FormData();
        formData.append('session_id', currentSessionId);
        formData.append('query', messageText);
        formData.append('patient_context', 'Patient data context available.');

        const response = await fetch('/api/chat/chat', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Failed to get response from chat API');
        }

        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          isUser: false,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Use chat API for simple conversation without files
        if (!currentSessionId) {
          // Create a temporary session for the conversation
          const sessionResponse = await fetch('/api/chat/start-session', {
            method: 'POST',
          });
          
          if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            currentSessionId = sessionData.session_id;
            setSessionId(currentSessionId);
            if (currentSessionId) {
              localStorage.setItem('chat_session_id', currentSessionId);
            }
          }
        }

        // Ensure we have a valid session ID
        if (!currentSessionId) {
          throw new Error('Unable to create chat session');
        }

        // Use the chat endpoint with empty context
        const formData = new FormData();
        formData.append('session_id', currentSessionId);
        formData.append('query', messageText);
        formData.append('patient_context', 'No specific patient data provided.');

        const response = await fetch('/api/chat/chat', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Failed to get response from chat API');
        }

        const data = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          isUser: false,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={`w-full max-w-none h-full bg-healthix-dark rounded-lg shadow-2xl ${className}`}>
      {/* Chat Header */}
      <div className="border-b border-healthix-dark-lighter p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-healthix-green/20 rounded-lg">
              <svg className="w-6 h-6 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Patient Data Chat</h2>
              <p className="text-healthix-gray-light text-sm">Ask questions about your patient records</p>
            </div>
          </div>
          
          {attachedFiles.length > 0 && (
            <div className="flex items-center space-x-2 bg-healthix-green/10 px-3 py-1 rounded-full">
              <svg className="w-4 h-4 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              <span className="text-healthix-green text-sm font-medium">{attachedFiles.length} file(s)</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages Area - Full Width */}
      <div 
        className={`flex-1 overflow-y-auto p-6 space-y-4 bg-healthix-dark/30 ${dragActive ? 'bg-healthix-green/10 border-2 border-dashed border-healthix-green' : ''}`}
        style={{ minHeight: '60vh', maxHeight: '70vh' }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {dragActive && (
          <div className="fixed inset-0 bg-healthix-green/20 flex items-center justify-center z-50">
            <div className="bg-healthix-dark-light border-2 border-dashed border-healthix-green rounded-lg p-8 text-center">
              <svg className="w-12 h-12 text-healthix-green mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-healthix-green text-lg font-medium">Drop files here to upload</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
          >
            <div
              className={`max-w-4xl px-6 py-4 rounded-2xl shadow-lg transition-all duration-300 ${
                message.isUser
                  ? 'bg-gradient-to-r from-healthix-green to-healthix-green-light text-white shadow-glow ml-12'
                  : 'bg-healthix-dark-light border border-healthix-dark-lighter text-white mr-12'
              }`}
            >
              {/* Use ReactMarkdown for better formatting */}
              <div className="text-sm leading-relaxed prose prose-invert max-w-none">
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </div>
              
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-healthix-dark-lighter/50">
                  <p className="text-xs text-healthix-green font-medium">Sources:</p>
                  <ul className="text-xs text-healthix-gray-light mt-1 space-y-1">
                    {message.sources.map((source, index) => (
                      <li key={index} className="flex items-center">
                        <svg className="w-2 h-2 mr-2 text-healthix-green" fill="currentColor" viewBox="0 0 8 8">
                          <circle cx="4" cy="4" r="3" />
                        </svg>
                        {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <p className="text-xs mt-3 opacity-70 text-right">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-healthix-dark-light border border-healthix-dark-lighter px-6 py-4 rounded-2xl mr-12">
              <div className="flex items-center space-x-3">
                <div className="loading-spinner h-4 w-4"></div>
                <p className="text-sm text-healthix-gray-light">AI is thinking...</p>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Attached Files - Compact Display */}
      {attachedFiles.length > 0 && (
        <div className="px-6 py-2 border-t border-healthix-dark-lighter bg-healthix-dark-light/30">
          <div className="flex flex-wrap gap-2">
            {attachedFiles.map((file) => (
              <div
                key={file.file_id}
                className="flex items-center space-x-2 bg-healthix-dark-light rounded-full px-3 py-1 text-xs border border-healthix-dark-lighter"
              >
                <div className="text-healthix-green">
                  {getFileIcon(file.type, file.name)}
                </div>
                <span className="text-white font-medium">{file.name}</span>
                <span className="text-healthix-gray-light">({formatFileSize(file.size)})</span>
                <button
                  onClick={() => handleRemoveFile(file.file_id)}
                  className="text-red-400 hover:text-red-300 transition-colors ml-1"
                  title="Remove file"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Section with Paperclip Button */}
      <div className="border-t border-healthix-dark-lighter p-6 bg-healthix-dark-light/50">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          multiple
          accept=".csv,.xlsx,.xls,.pdf,.jpg,.jpeg,.png,.gif,.txt,.json"
          className="hidden"
        />
        
        <div className="flex items-center space-x-3">
          {/* Paperclip Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="p-3 bg-healthix-green/20 hover:bg-healthix-green/30 text-healthix-green rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Attach files"
          >
            {isUploading ? (
              <div className="loading-spinner h-5 w-5"></div>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            )}
          </button>
          
          {/* Message Input */}
          <input
            ref={chatInputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={attachedFiles.length > 0 ? "Ask about uploaded files or patient data..." : "Ask about patient data or drag files here..."}
            className="flex-1 p-4 bg-healthix-dark-light border border-healthix-dark-lighter rounded-lg text-white placeholder-healthix-gray-light focus:outline-none focus:ring-2 focus:ring-healthix-green focus:border-transparent"
            disabled={isLoading}
          />
          
          {/* Send Button */}
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="p-4 bg-gradient-to-r from-healthix-green to-healthix-green-light hover:from-healthix-green-light hover:to-healthix-green text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-glow"
          >
            {isLoading ? (
              <div className="loading-spinner h-5 w-5"></div>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        {/* Upload Status */}
        {isUploading && (
          <div className="mt-3 flex items-center space-x-2 text-sm text-healthix-green">
            <div className="loading-spinner h-4 w-4"></div>
            <span>Uploading files...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
