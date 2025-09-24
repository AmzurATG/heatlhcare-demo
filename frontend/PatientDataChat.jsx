import React, { useState, useRef, useEffect } from 'react';
import { Upload, Send, Paperclip, X, FileText, Image, Table } from 'lucide-react';

const PatientDataChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: "Welcome to Healthix! 🏥 I'm your intelligent patient data assistant. You can ask me questions about your patient records, such as 'Show me patients with diabetes' or 'What medications has John Smith been prescribed?'",
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
    if (fileType.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (fileType.includes('sheet') || fileType.includes('csv') || fileType.includes('excel')) return <Table className="w-4 h-4" />;
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

          // Add a system message about the file attachment
          setMessages(prev => [...prev, {
            id: Date.now() + Math.random(),
            type: 'system',
            content: `📎 Attached: ${file.name} (${result.attachment_type})`,
            timestamp: new Date().toLocaleTimeString()
          }]);
        } else {
          throw new Error('Failed to upload file');
        }
      }
    } catch (error) {
      console.error('File upload error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        type: 'system',
        content: `❌ Failed to attach files: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsUploading(false);
      event.target.value = '';
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
    setInputMessage('');

    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage,
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
        throw new Error('Failed to get response');
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
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
    <div className="flex flex-col h-full bg-gray-900">
      {/* Chat Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold">💬</span>
          </div>
          <div>
            <h2 className="text-white font-semibold">Patient Data Chat</h2>
            <p className="text-gray-400 text-sm">
              {attachedFiles.length > 0 
                ? `${attachedFiles.length} file(s) attached - Context active`
                : 'Ask questions about your patient records'
              }
            </p>
          </div>
        </div>
      </div>

      {/* Attached Files Panel */}
      {attachedFiles.length > 0 && (
        <div className="bg-gray-800 p-3 border-b border-gray-700">
          <div className="flex flex-wrap gap-2">
            {attachedFiles.map(file => (
              <div key={file.id} className="flex items-center gap-2 bg-gray-700 rounded-lg px-3 py-1 text-sm">
                {getFileIcon(file.type)}
                <span className="text-gray-300">{file.name}</span>
                <span className="text-green-400 text-xs">({file.attachmentType})</span>
                <button
                  onClick={() => removeFile(file.id)}
                  className="text-gray-400 hover:text-red-400 ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 ${
              message.type === 'user' 
                ? 'bg-green-600 text-white ml-12'
                : message.type === 'system'
                ? 'bg-gray-700 text-gray-300 italic'
                : 'bg-gray-700 text-gray-100 mr-12'
            }`}>
              <div className="whitespace-pre-wrap">{message.content}</div>
              <div className={`text-xs mt-1 ${
                message.type === 'user' ? 'text-green-200' : 'text-gray-400'
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
        <div className="bg-yellow-900 text-yellow-200 p-2 mx-4 rounded text-sm">
          Uploading files...
        </div>
      )}

      {/* Input Area */}
      <div className="bg-gray-800 p-4 border-t border-gray-700">
        <div className="flex items-end gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.txt,.xlsx,.xls,.csv,.tsv,.json"
            className="hidden"
          />
          
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors"
            title="Attach Files"
          >
            <Paperclip className="w-5 h-5 text-white" />
          </button>
          
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about patient data..."
              className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
              rows="1"
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
          </div>
          
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isUploading}
            className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors"
            title="Send Message"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PatientDataChat;