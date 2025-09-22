import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import './DataVisualization.css';

const DataVisualization = ({ data, title }) => {
  const [viewMode, setViewMode] = useState('auto');

  if (!data) return null;

  const renderPlotlyChart = () => {
    if (data.type !== 'plotly' || !data.data) return null;

    return (
      <div className="plotly-container">
        <Plot
          data={data.data.data}
          layout={{
            ...data.data.layout,
            autosize: true,
            responsive: true,
            margin: { t: 40, b: 40, l: 60, r: 20 }
          }}
          config={{
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'resetScale2d'],
            responsive: true
          }}
          style={{ width: '100%', height: '400px' }}
        />
      </div>
    );
  };

  const renderTable = () => {
    if (data.type !== 'table' || !data.data) return null;

    const tableData = Array.isArray(data.data) ? data.data : [data.data];

    if (tableData.length === 0) return null;

    const columns = Object.keys(tableData[0]);

    return (
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => (
              <tr key={index}>
                {columns.map(col => (
                  <td key={col}>
                    {typeof row[col] === 'number' ?
                      row[col].toFixed(3) :
                      String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderContent = () => {
    if (data.type === 'plotly') {
      return renderPlotlyChart();
    } else if (data.type === 'table') {
      return renderTable();
    } else {
      return (
        <div className="unsupported-viz">
          <p>Visualization type '{data.type}' not supported yet.</p>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      );
    }
  };

  return (
    <div className="data-visualization">
      <div className="viz-header">
        <h4 className="viz-title">{title}</h4>
        <div className="viz-controls">
          {data.type === 'plotly' && (
            <div className="view-mode-toggle">
              <button
                className={`toggle-btn ${viewMode === 'chart' ? 'active' : ''}`}
                onClick={() => setViewMode('chart')}
              >
                Chart
              </button>
              <button
                className={`toggle-btn ${viewMode === 'data' ? 'active' : ''}`}
                onClick={() => setViewMode('data')}
              >
                Data
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="viz-content">
        {viewMode === 'data' && data.type === 'plotly' ? (
          <div className="raw-data-view">
            <pre className="data-json">
              {JSON.stringify(data.data, null, 2)}
            </pre>
          </div>
        ) : (
          renderContent()
        )}
      </div>

      <div className="viz-footer">
        <div className="viz-metadata">
          <span className="metadata-item">Type: {data.type}</span>
          {data.data?.layout?.title && (
            <span className="metadata-item">Title: {data.data.layout.title.text || data.data.layout.title}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;