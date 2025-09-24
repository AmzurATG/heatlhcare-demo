import React from 'react';
import ChatInterface from '../components/ChatInterface';

const Chat: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-healthix-dark via-healthix-dark-light to-healthix-dark">
      <div className="w-full h-screen flex flex-col">
        <div className="p-6 text-center border-b border-healthix-dark-lighter bg-healthix-dark/80">
          <h1 className="text-3xl font-bold text-white mb-2">
            Patient Data Chat
          </h1>
          <p className="text-healthix-gray-light">
            Ask questions about patient records and upload files for context-aware conversations
          </p>
        </div>
        
        <div className="flex-1 p-6">
          <ChatInterface className="h-full" />
        </div>
      </div>
    </div>
  );
};

export default Chat;