// App.jsx or your main component file
import React from 'react';
import PatientDataChat from './PatientDataChat';

const App = () => {
  return (
    <div className="h-screen">
      {/* Your existing header/navigation */}
      <div className="flex h-full">
        {/* Your sidebar if any */}
        
        {/* Chat Section - Replace your existing chat with this */}
        <div className="flex-1">
          <PatientDataChat />
        </div>
      </div>
    </div>
  );
};

export default App;