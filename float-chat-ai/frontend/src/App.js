import React, { useState, useEffect } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import LoginScreen from './components/LoginScreen';
// FIX 1: Changed to a default import (no curly braces)
import apiService from './services/apiService';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [userName, setUserName] = useState('');
  // FIX 2: Removed useState for the apiService, as we import the instance directly.

  useEffect(() => {
    // Check if user has an active session
    const storedSessionId = localStorage.getItem('floatChatSessionId');
    const storedUserName = localStorage.getItem('floatChatUserName');
    
    if (storedSessionId && storedUserName) {
      setSessionId(storedSessionId);
      setUserName(storedUserName);
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = (name) => {
    const newSessionId = `session_${name}_${Date.now()}`;
    setUserName(name);
    setSessionId(newSessionId);
    setIsLoggedIn(true);
    
    // Store in localStorage for persistence
    localStorage.setItem('floatChatSessionId', newSessionId);
    localStorage.setItem('floatChatUserName', name);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setSessionId('');
    setUserName('');
    
    // Clear localStorage
    localStorage.removeItem('floatChatSessionId');
    localStorage.removeItem('floatChatUserName');
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo">
            <h1>🌊 Float-Chat-AI</h1>
            <p className="tagline">Your conversational guide to ARGO oceanographic data</p>
          </div>
          {isLoggedIn && (
            <div className="user-info">
              <span className="welcome-text">Welcome, {userName}!</span>
              <button onClick={handleLogout} className="logout-btn">
                Logout
              </button>
            </div>
          )}
        </div>
      </header>
      
      <main className="App-main">
        {!isLoggedIn ? (
          <LoginScreen onLogin={handleLogin} />
        ) : (
          <ChatInterface 
            sessionId={sessionId}
            userName={userName}
            apiService={apiService}
          />
        )}
      </main>
      
      <footer className="App-footer">
        <p>Powered by ARGO float data | Built for marine research accessibility</p>
      </footer>
    </div>
  );
}

export default App;