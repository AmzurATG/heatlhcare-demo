import React, { useState, useEffect, useRef } from 'react';
import FileAttachment from './FileAttachment';

// SVG Icon Components (no external dependency)
const Send = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const MessageCircle = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const FileText = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const Trash2 = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface AttachedFile {
  file_id: string;
  name: string;
  type: string;
  size: number;
  uploaded_at: number;
}

interface EnhancedChatProps {
  patientContext?: string;
  onNewMessage?: (message: string, response: string) => void;
}

const EnhancedChat: React.FC<EnhancedChatProps> = ({ 
  patientContext = "", 
  onNewMessage 
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showFileAttachment, setShowFileAttachment] = useState(true); // Show by default
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Initialize chat session
  useEffect(() => {
    initializeChatSession();
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initializeChatSession = async () => {
    try {
      const response = await fetch('/api/chat/start-session', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        
        // Add welcome message
        const welcomeMessage: Message = {
          role: 'assistant',
          content: `Welcome to Healthix! 🏥 I'm your intelligent patient data assistant. You can ask me questions about your patient records, such as "Show me patients with diabetes" or "What medications has John Smith been prescribed?"
          
You can also attach files (CSV, Excel, PDF, Images) to add them to our conversation context for analysis.`,
          timestamp: Date.now()
        };
        setMessages([welcomeMessage]);
      }
    } catch (error) {
      console.error('Failed to initialize chat session:', error);
    }
  };

  const handleFileSelect = async (files: File[]) => {
    if (!sessionId) return;

    setIsUploading(true);
    
    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('session_id', sessionId);
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
          role: 'assistant',
          content: `📎 File "${file.name}" has been uploaded and added to the conversation context. You can now ask questions about its contents.`,
          timestamp: Date.now()
        };
        
        setMessages(prev => [...prev, fileMessage]);
        
      } catch (error) {
        console.error(`Error uploading file ${file.name}:`, error);
        alert(`Failed to upload ${file.name}. Please try again.`);
      }
    }
    
    setIsUploading(false);
  };

  const fetchAttachedFiles = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`/api/chat/session/${sessionId}/files`);
      if (response.ok) {
        const data = await response.json();
        setAttachedFiles(data.files);
      }
    } catch (error) {
      console.error('Error fetching attached files:', error);
    }
  };

  const handleRemoveFile = async (fileId: string) => {
    // For now, we'll just remove from UI
    // In a full implementation, you'd call an API to remove the file
    setAttachedFiles(prev => prev.filter(f => f.file_id !== fileId));
    
    const removeMessage: Message = {
      role: 'assistant',
      content: `📎 File has been removed from the conversation context.`,
      timestamp: Date.now()
    };
    
    setMessages(prev => [...prev, removeMessage]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !sessionId) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('query', inputMessage);
      if (patientContext) {
        formData.append('patient_context', patientContext);
      }

      const response = await fetch('/api/chat/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: Date.now()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (onNewMessage) {
        onNewMessage(inputMessage, data.response);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: Date.now()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSession = async () => {
    if (!sessionId) return;

    try {
      await fetch(`/api/chat/session/${sessionId}`, {
        method: 'DELETE',
      });
      
      // Reinitialize
      setMessages([]);
      setAttachedFiles([]);
      setSessionId(null);
      await initializeChatSession();
      
    } catch (error) {
      console.error('Error clearing session:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-green-100 rounded-full">
            <MessageCircle className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Patient Data Chat</h2>
            <p className="text-sm text-gray-600">Ask questions about your patient records</p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setShowFileAttachment(!showFileAttachment)}
            className={`p-2 rounded-lg transition-colors ${
              showFileAttachment ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
            }`}
            title="Toggle file attachments"
          >
            <FileText className="h-5 w-5" />
          </button>
          
          <button
            onClick={clearSession}
            className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
            title="Clear chat session"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* File Attachment Panel */}
      {showFileAttachment && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <FileAttachment
            onFileSelect={handleFileSelect}
            attachedFiles={attachedFiles}
            onRemoveFile={handleRemoveFile}
            isUploading={isUploading}
          />
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">{message.content}</div>
              <div className={`text-xs mt-2 ${
                message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Section with File Attachment */}
      <div className="p-4 border-t border-gray-200">
        {/* File Attachment Area - Always Visible */}
        <div className="mb-4">
          <FileAttachment
            onFileSelect={handleFileSelect}
            attachedFiles={attachedFiles}
            onRemoveFile={handleRemoveFile}
            isUploading={isUploading}
          />
        </div>
        
        {/* Message Input */}
        <div className="flex space-x-2">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about patient data or upload files above..."
            className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={1}
            disabled={isLoading}
          />
          
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        
        {attachedFiles.length > 0 && (
          <div className="mt-2 text-sm text-gray-500">
            📎 {attachedFiles.length} file(s) attached to this conversation
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedChat;