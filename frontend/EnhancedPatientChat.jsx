// Updated Chat Component - Replace your existing chat component with this
import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X, FileText, Image, Table } from 'lucide-react';

const EnhancedPatientChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: "Welcome to Healthix! 🏥 I'm your intelligent patient data assistant. You can ask me questions about your patient records, upload medical documents, Excel files with patient data, or ask about specific treatments and medications.",
      timestamp: '2:26:47 PM'
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [chatSessionId] = useState(() => `chat_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const getFileIcon = (fileType) => {
    if (fileType?.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (fileType?.includes('sheet') || fileType?.includes('csv') || fileType?.includes('excel')) return <Table className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsUploading(true);
    
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('chat_session_id', chatSessionId);

        const response = await fetch('/api/documents/attach-to-chat', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const result = await response.json();
          setAttachedFiles(prev => [...prev, {
            id: Date.now() + Math.random(),
            name: file.name,
            type: file.type,
            size: file.size,
            attachmentType: result.attachment_type
          }]);

          // Add system message
          setMessages(prev => [...prev, {
            id: Date.now() + Math.random(),
            type: 'system',
            content: `📎 Attached: ${file.name} (${result.attachment_type})`,
            timestamp: new Date().toLocaleTimeString()
          }]);
        } else {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to upload file');
        }
      }
    } catch (error) {
      console.error('File upload error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        type: 'system', 
        content: `❌ Upload failed: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsUploading(false);
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  const removeFile = (fileId) => {
    setAttachedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isUploading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputMessage;
    setInputMessage('');

    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: messageToSend,
          chat_session_id: chatSessionId
        })
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'assistant',
          content: data.message,
          timestamp: new Date().toLocaleTimeString(),
          hasContext: data.has_context
        }]);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to get response');
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure the backend server is running and try again.',
        timestamp: new Date().toLocaleTimeString()
      }]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="flex items-center gap-2 p-4 bg-slate-800/50 border-b border-slate-700">
        <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
          <span className="text-white text-xs">💬</span>
        </div>
        <div>
          <h3 className="text-white font-medium">Patient Data Chat</h3>
          <p className="text-slate-400 text-xs">
            {attachedFiles.length > 0 
              ? `${attachedFiles.length} file(s) attached - Context active`
              : 'Ask questions about your patient records'
            }
          </p>
        </div>
      </div>

      {/* Attached Files Panel */}
      {attachedFiles.length > 0 && (
        <div className="bg-slate-800/30 p-3 border-b border-slate-700">
          <div className="text-xs text-slate-400 mb-2">Attached Files:</div>
          <div className="flex flex-wrap gap-2">
            {attachedFiles.map(file => (
              <div key={file.id} className="flex items-center gap-2 bg-slate-700 rounded px-2 py-1 text-xs">
                {getFileIcon(file.type)}
                <span className="text-slate-300">{file.name}</span>
                <span className="text-green-400">({file.attachmentType})</span>
                <button
                  onClick={() => removeFile(file.id)}
                  className="text-slate-400 hover:text-red-400"
                  title="Remove file"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(message => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2 ${
              message.type === 'user' 
                ? 'bg-green-600 text-white'
                : message.type === 'system'
                ? 'bg-slate-700 text-slate-300 italic text-sm'
                : 'bg-slate-700 text-slate-100'
            }`}>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</div>
              <div className={`text-xs mt-1 opacity-70 ${
                message.type === 'user' ? 'text-green-100' : 'text-slate-400'
              }`}>
                {message.timestamp}
                {message.hasContext && (
                  <span className="ml-2 text-green-400">• Context available</span>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Upload Progress */}
      {isUploading && (
        <div className="mx-4 mb-2 bg-yellow-900/50 text-yellow-200 p-2 rounded text-sm">
          📤 Uploading files...
        </div>
      )}

      {/* Input Area with Attachment Button */}
      <div className="p-4 bg-slate-800/50 border-t border-slate-700">
        <div className="flex items-end gap-2">
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.txt,.xlsx,.xls,.csv,.tsv,.json"
            className="hidden"
          />
          
          {/* ATTACHMENT BUTTON - This is the key addition */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-xl transition-all duration-200 hover:scale-105"
            title="Attach Files (PDF, Excel, CSV, Images)"
          >
            <Paperclip className="w-5 h-5 text-white" />
          </button>
          
          {/* Message Input */}
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about patient data..."
              className="w-full bg-slate-700 text-white rounded-xl px-4 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-green-500 focus:bg-slate-600"
              rows="1"
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
          </div>
          
          {/* Send Button */}
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isUploading}
            className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-xl transition-all duration-200 hover:scale-105"
            title="Send Message"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedPatientChat;