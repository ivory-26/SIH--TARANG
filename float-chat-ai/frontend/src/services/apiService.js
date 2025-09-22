import axios from 'axios';

// Configure axios defaults
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log('API Request:', config.method?.toUpperCase(), config.url);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log('API Response:', response.status, response.config.url);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.status, error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Check if the backend is healthy
   */
  async checkHealth() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Unable to connect to backend service');
    }
  }

  /**
   * Send a natural language query to the AI service
   */
  async sendQuery(query, sessionId, userId = 'anonymous') {
    try {
      const response = await this.client.post('/query', {
        query: query,
        session_id: sessionId,
        user_id: userId
      });
      return response.data;
    } catch (error) {
      console.error('Query failed:', error);
      
      if (error.response?.status === 500) {
        throw new Error('Server error occurred while processing your query');
      } else if (error.response?.status === 422) {
        throw new Error('Invalid query format');
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('Query timed out. Please try a simpler question.');
      } else {
        throw new Error(error.response?.data?.detail || 'Failed to process query');
      }
    }
  }

  /**
   * Get raw data by ID
   */
  async getRawData(dataId, format = 'json') {
    try {
      const response = await this.client.get(`/data/${dataId}`, {
        params: { format }
      });
      return response.data;
    } catch (error) {
      console.error('Get raw data failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to retrieve data');
    }
  }

  /**
   * Get session history
   */
  async getSessionHistory(sessionId) {
    try {
      const response = await this.client.get(`/sessions/${sessionId}/history`);
      return response.data;
    } catch (error) {
      console.error('Get session history failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to retrieve session history');
    }
  }

  /**
   * Export query results
   */
  async exportResults(queryId, format = 'csv') {
    try {
      const response = await this.client.get(`/export/${queryId}`, {
        params: { format }
      });
      return response.data;
    } catch (error) {
      console.error('Export failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to export results');
    }
  }

  /**
   * Get available oceanographic variables
   */
  async getAvailableVariables() {
    try {
      // For prototype, return hardcoded list
      // In production, this could be a dedicated endpoint
      return [
        { name: 'TEMP', description: 'Sea Water Temperature', units: 'degrees_Celsius' },
        { name: 'PSAL', description: 'Practical Salinity', units: 'PSU' },
        { name: 'PRES', description: 'Pressure', units: 'dbar' },
        { name: 'LATITUDE', description: 'Latitude', units: 'degrees_north' },
        { name: 'LONGITUDE', description: 'Longitude', units: 'degrees_east' }
      ];
    } catch (error) {
      console.error('Get variables failed:', error);
      return [];
    }
  }

  /**
   * Get sample queries for user guidance
   */
  getSampleQueries() {
    return [
      "What's the average temperature at 1000 meters depth?",
      "Show me a salinity profile",
      "Find the maximum temperature in the dataset",
      "What's the temperature at the surface?",
      "Show me pressure data",
      "What's the salinity at 500 meters?"
    ];
  }

  /**
   * Format error message for user display
   */
  formatErrorMessage(error) {
    if (error.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred. Please try again.';
  }

  /**
   * Check if the error is a network error
   */
  isNetworkError(error) {
    return !error.response || error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED';
  }

  /**
   * Retry a failed request with exponential backoff
   */
  async retryRequest(requestFunction, maxRetries = 3) {
    let lastError;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await requestFunction();
      } catch (error) {
        lastError = error;
        
        // Don't retry if it's not a network error
        if (!this.isNetworkError(error)) {
          throw error;
        }
        
        // Wait before retrying (exponential backoff)
        if (i < maxRetries - 1) {
          const waitTime = Math.pow(2, i) * 1000; // 1s, 2s, 4s
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }
      }
    }
    
    throw lastError;
  }
}

const apiService = new ApiService();
export default apiService;