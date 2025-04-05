import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Route, Routes } from 'react-router-dom';
import './App.css';
import HomePage from './pages';
import DevToolsFix from './components/DevToolsFix';
import MentorCall from './components/MentorCall';
import MentorSelection from './components/MentorSelection';
import { checkMentorServiceHealth } from './services/mentorService';

// Create a client
const queryClient = new QueryClient();

function App() {
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);
  
  useEffect(() => {
    // Check if the backend service is available
    async function checkBackendStatus() {
      try {
        const available = await checkMentorServiceHealth();
        console.log('Backend health check result:', available);
        setBackendAvailable(available);
      } catch (error) {
        console.error('Error checking backend health:', error);
        setBackendAvailable(false);
      }
    }
    
    checkBackendStatus();
    
    // Check periodically
    const intervalId = setInterval(checkBackendStatus, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  return (
    <>
      <DevToolsFix />
      <div className="app-container">
        {backendAvailable === false && (
          <div style={{
            background: '#ffdddd',
            color: '#cc0000',
            padding: '8px 16px',
            textAlign: 'center',
            borderRadius: '4px',
            margin: '8px',
            zIndex: 1000,
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
          }}>
            ⚠️ Backend service appears to be offline. Voice interaction may not work properly.
            Please make sure the backend server is running on port 5001.
          </div>
        )}
        
        <QueryClientProvider client={queryClient}>
          <Routes>
            <Route path="/" element={<MentorSelection />} />
            <Route path="/call" element={<MentorCall />} />
          </Routes>
          
          <HomePage />
          
          <div style={{
            position: 'fixed',
            bottom: '4px',
            right: '8px',
            fontSize: '10px',
            opacity: 0.7,
            color: backendAvailable ? 'green' : 'red'
          }}>
            Backend: {backendAvailable === null ? 'Checking...' : 
                   backendAvailable ? 'Connected' : 'Disconnected'}
          </div>
        </QueryClientProvider>
      </div>
    </>
  );
}

export default App;
