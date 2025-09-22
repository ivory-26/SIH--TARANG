import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ChatInterface.css';
import ChatMessage from './ChatMessage';
// import DataVisualization from './DataVisualization'; // FIX: Removed unused import

const ChatInterface = ({ sessionId, userName, apiService }) => {
  const [messages, setMessages] = useState(() => [
    {
      id: 1,
      type: 'system',
      content: `Hello ${userName || 'Explorer'}! 🌊 I'm your AI assistant for ARGO oceanographic data. 
                Ask me about sea temperature, salinity, pressure, or depth profiles!`,
      timestamp: new Date()
    }
  ]);

  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [sampleQueries] = useState(apiService.getSampleQueries());
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, { ...message, id: Date.now() + Math.random() }]);
  }, []);

  // FIX: Wrapped checkConnection in useCallback to safely use it in useEffect
  const checkConnection = useCallback(async () => {
    try {
      await apiService.checkHealth();
      setConnectionStatus('connected');
    } catch (error) {
      setConnectionStatus('disconnected');
      addMessage({
        type: 'error',
        content: '❌ Unable to connect to the backend service. Please ensure the server is running.',
        timestamp: new Date()
      });
    }
  }, [apiService, addMessage]);

  useEffect(() => {
    checkConnection();
  }, [checkConnection]); // FIX: Added checkConnection to dependency array

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!currentQuery.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: currentQuery.trim(),
      timestamp: new Date()
    };

    addMessage(userMessage);
    setCurrentQuery('');
    setIsLoading(true);

    try {
      const response = await apiService.sendQuery(currentQuery, sessionId, userName);

      const aiMessage = {
        type: 'assistant',
        content: response.response,
        timestamp: new Date(),
        data: response.data || null,
        visualization: response.visualization || null,
        queryId: response.query_id || null
      };

      addMessage(aiMessage);
    } catch (error) {
      console.error('Query error:', error);
      addMessage({
        type: 'error',
        content: apiService.formatErrorMessage(error),
        timestamp: new Date()
      });
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };
  
  // ... rest of the component remains the same
  // (handleKeyDown, handleSampleQueryClick, handleRetryConnection, and JSX)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSampleQueryClick = (query) => {
    setCurrentQuery(query);
    inputRef.current?.focus();
  };

  const handleRetryConnection = () => {
    setConnectionStatus('checking');
    checkConnection();
  };

  return (
    <div className="chat-interface">
      <div className={`connection-status ${connectionStatus}`}>
        {connectionStatus === 'checking' && <span>🔄 Connecting to server...</span>}
        {connectionStatus === 'connected' && <span>🟢 Connected</span>}
        {connectionStatus === 'disconnected' && (
          <span>
            🔴 Disconnected
            <button onClick={handleRetryConnection} className="retry-btn">Retry</button>
          </span>
        )}
      </div>

      <div className="messages-container">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            userName={userName}
          />
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-content loading">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
              <span className="loading-text">Analyzing your query...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {messages.filter(m => m.type === 'user').length === 0 && (
        <div className="sample-queries-container">
          <p className="sample-queries-title">Try these example queries:</p>
          <div className="sample-queries-grid">
            {sampleQueries.map((query, index) => (
              <button
                key={index}
                onClick={() => handleSampleQueryClick(query)}
                className="sample-query-btn"
                disabled={isLoading}
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={currentQuery}
            onChange={(e) => setCurrentQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me about oceanographic data..."
            className="query-input"
            disabled={isLoading || connectionStatus === 'disconnected'}
            rows={1}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
          />
          <button
            onClick={handleSendMessage}
            disabled={!currentQuery.trim() || isLoading || connectionStatus === 'disconnected'}
            className="send-button"
          >
            Send
          </button>
        </div>

        <div className="input-help">
          <span className="tip"> Tip: Ask about temperature, salinity, pressure, or depth profiles</span>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
