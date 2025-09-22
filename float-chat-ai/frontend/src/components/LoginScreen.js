import React, { useState } from 'react';
import './LoginScreen.css';

const LoginScreen = ({ onLogin }) => {
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name.trim()) {
      setIsLoading(true);
      // Simulate a brief loading state
      setTimeout(() => {
        onLogin(name.trim());
        setIsLoading(false);
      }, 500);
    }
  };

  const handleQuickLogin = (userName) => {
    setName(userName);
    onLogin(userName);
  };

  return (
    <div className="login-screen">
      <div className="login-container">
        <div className="welcome-section">
          <h2>Welcome to Float-Chat-AI</h2>
          <p className="description">
            Explore ARGO oceanographic data through natural language conversations.
            Ask questions about sea temperature, salinity, pressure, and more -
            all in plain English!
          </p>

          <div className="features-list">
            <div className="feature-item">
              <span className="feature-icon"></span>
              <span>Natural language queries</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon"></span>
              <span>Interactive visualizations</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon"></span>
              <span>Real oceanographic insights</span>
            </div>
          </div>
        </div>

        <div className="login-form-section">
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="name">Enter your name to get started:</label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name or session ID"
                className="name-input"
                disabled={isLoading}
                autoFocus
              />
            </div>

            <button
              type="submit"
              className="login-button"
              disabled={!name.trim() || isLoading}
            >
              {isLoading ? 'Loading...' : 'Start Exploring'}
            </button>
          </form>

          <div className="quick-login-section">
            <p className="quick-login-label">Quick start as:</p>
            <div className="quick-login-buttons">
              <button
                onClick={() => handleQuickLogin('Researcher')}
                className="quick-login-btn"
                disabled={isLoading}
              >
                Researcher
              </button>
              <button
                onClick={() => handleQuickLogin('Student')}
                className="quick-login-btn"
                disabled={isLoading}
              >
                Student
              </button>
              <button
                onClick={() => handleQuickLogin('Guest')}
                className="quick-login-btn"
                disabled={isLoading}
              >
                Guest
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="sample-queries-section">
        <h3>Try asking questions like:</h3>
        <div className="sample-queries">
          <div className="query-example">"What's the average temperature at 1000 meters depth?"</div>
          <div className="query-example">"Show me a salinity profile"</div>
          <div className="query-example">"Find the maximum temperature in the dataset"</div>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;