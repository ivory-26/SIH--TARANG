import React from 'react';
import './ChatMessage.css';
import DataVisualization from './DataVisualization';

const ChatMessage = ({ message, userName }) => {
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderMessageContent = () => {
    if (message.type === 'error') {
      return (
        <div className="error-content">
          <span className="error-icon">⚠️</span>
          {message.content}
        </div>
      );
    }

    if (message.type === 'system') {
      return (
        <div className="system-content">
          <span className="system-icon">🤖</span>
          {message.content}
        </div>
      );
    }

    return message.content;
  };

  const renderDataSummary = () => {
    if (!message.data || !message.data.success) return null;

    const { data, metadata } = message.data;

    return (
      <div className="data-summary">
        <div className="summary-header">
          <span className="data-icon">📊</span>
          <strong>Data Summary</strong>
        </div>

        <div className="summary-content">
          {typeof data === 'number' && (
            <div className="metric">
              <span className="metric-label">Value:</span>
              <span className="metric-value">
                {data.toFixed(2)} {metadata?.units || ''}
              </span>
            </div>
          )}

          {metadata && (
            <>
              <div className="metric">
                <span className="metric-label">Variable:</span>
                <span className="metric-value">{metadata.variable}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Operation:</span>
                <span className="metric-value">{metadata.operation}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Profiles:</span>
                <span className="metric-value">{metadata.n_profiles}</span>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`message ${message.type}`}>
      <div className="message-header">
        <div className="message-avatar">
          {message.type === 'user' ? (
            <span className="user-avatar">
              {userName?.charAt(0)?.toUpperCase() || '👤'}
            </span>
          ) : message.type === 'assistant' ? (
            <span className="assistant-avatar">🤖</span>
          ) : message.type === 'system' ? (
            <span className="system-avatar">ℹ️</span>
          ) : (
            <span className="error-avatar">⚠️</span>
          )}
        </div>

        <div className="message-meta">
          <span className="message-sender">
            {message.type === 'user'
              ? userName
              : message.type === 'assistant'
              ? 'Float-Chat-AI'
              : message.type === 'system'
              ? 'System'
              : 'Error'}
          </span>
          <span className="message-time">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>
      </div>

      <div className="message-content">
        {renderMessageContent()}

        {/* Data Summary */}
        {renderDataSummary()}

        {/* Visualization */}
        {message.visualization && (
          <div className="visualization-container">
            <DataVisualization
              data={message.visualization}
              title={message.data?.description || 'Data Visualization'}
            />
          </div>
        )}

        {/* Export Options */}
        {message.queryId && message.data?.success && (
          <div className="message-actions">
            <button className="action-btn export-btn">📥 Export Data</button>
            <button className="action-btn share-btn">🔗 Share Result</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
