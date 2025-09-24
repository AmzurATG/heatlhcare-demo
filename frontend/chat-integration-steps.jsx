// Add these to your existing chat component

// 1. IMPORTS - Add these to your existing imports
import { Paperclip, X, FileText, Image, Table } from 'lucide-react';

// 2. STATE - Add these state variables to your existing component
const [attachedFiles, setAttachedFiles] = useState([]);
const [isUploading, setIsUploading] = useState(false);
const [chatSessionId] = useState(() => `chat_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`);
const fileInputRef = useRef(null);

// 3. FUNCTIONS - Add these functions to your component
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
      } else {
        throw new Error('Failed to upload file');
      }
    }
  } catch (error) {
    console.error('File upload error:', error);
  } finally {
    setIsUploading(false);
    event.target.value = '';
  }
};

const removeFile = (fileId) => {
  setAttachedFiles(prev => prev.filter(file => file.id !== fileId));
};

// 4. UPDATE YOUR SEND MESSAGE FUNCTION - Modify your existing sendMessage to include chatSessionId
const sendMessage = async () => {
  if (!inputMessage.trim() || isUploading) return;

  // Your existing message logic...
  
  try {
    const response = await fetch('/api/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: inputMessage,
        chat_session_id: chatSessionId  // Add this line
      })
    });
    
    // Rest of your existing logic...
  } catch (error) {
    // Your existing error handling...
  }
};

// 5. JSX - Add these elements to your existing JSX

// A. Add this AFTER your chat header (to show attached files)
{attachedFiles.length > 0 && (
  <div className="bg-slate-800 p-3 border-b border-slate-700">
    <div className="text-xs text-slate-400 mb-2">Attached Files:</div>
    <div className="flex flex-wrap gap-2">
      {attachedFiles.map(file => (
        <div key={file.id} className="flex items-center gap-2 bg-slate-700 rounded px-2 py-1 text-sm">
          {getFileIcon(file.type)}
          <span className="text-slate-300">{file.name}</span>
          <span className="text-green-400 text-xs">({file.attachmentType})</span>
          <button
            onClick={() => removeFile(file.id)}
            className="text-slate-400 hover:text-red-400 ml-1"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  </div>
)}

// B. Add this BEFORE your existing input area (for upload progress)
{isUploading && (
  <div className="bg-yellow-900 text-yellow-200 p-2 mx-4 rounded text-sm">
    Uploading files...
  </div>
)}

// C. Modify your input area to include the attachment button
{/* Replace your existing input area with this */}
<div className="bg-slate-800 p-4 border-t border-slate-700">
  <div className="flex items-end gap-3">
    <input
      type="file"
      ref={fileInputRef}
      onChange={handleFileSelect}
      multiple
      accept=".pdf,.jpg,.jpeg,.png,.txt,.xlsx,.xls,.csv,.tsv,.json"
      className="hidden"
    />
    
    {/* Attachment Button */}
    <button
      onClick={() => fileInputRef.current?.click()}
      disabled={isUploading}
      className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors"
      title="Attach Files"
    >
      <Paperclip className="w-5 h-5 text-white" />
    </button>
    
    {/* Your existing textarea */}
    <div className="flex-1">
      <textarea
        value={inputMessage}
        onChange={(e) => setInputMessage(e.target.value)}
        placeholder="Ask about patient data..."
        className="w-full bg-slate-700 text-white rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
        rows="1"
        onKeyPress={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        }}
      />
    </div>
    
    {/* Your existing send button */}
    <button
      onClick={sendMessage}
      disabled={!inputMessage.trim() || isUploading}
      className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors"
    >
      <Send className="w-5 h-5 text-white" />
    </button>
  </div>
</div>