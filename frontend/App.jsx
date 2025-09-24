// Main App.jsx - Integration example for your Healthix application
import React from 'react';
import PatientDataChat from './PatientDataChat';

const App = () => {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header matching your existing design */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">H</span>
            </div>
            <div>
              <h1 className="text-white font-semibold">Healthix</h1>
              <p className="text-slate-400 text-xs">Healthcare Data Platform</p>
            </div>
          </div>
          
          <nav className="flex items-center gap-6">
            <a href="/dashboard" className="text-slate-300 hover:text-white text-sm">
              📊 Dashboard
            </a>
            <a href="/patients" className="text-slate-300 hover:text-white text-sm">
              👥 Patients  
            </a>
            <a href="/chat" className="text-green-400 font-medium text-sm">
              💬 Chat
            </a>
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm">👤</span>
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content - Chat Interface */}
      <main className="h-[calc(100vh-80px)]">
        <PatientDataChat />
      </main>
    </div>
  );
};

export default App;