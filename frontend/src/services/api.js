import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('aqi_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor for graceful handling of 401 token expiry
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear expired credentials from localStorage without infinite reload loops
      if (localStorage.getItem('aqi_auth_token')) {
        localStorage.removeItem('aqi_auth_token');
        window.dispatchEvent(new Event('aqi-auth-expired'));
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Health check endpoint
 */
export const checkHealth = async () => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

/**
 * Readiness check endpoint
 */
export const checkReadiness = async () => {
  const response = await apiClient.get('/api/ready');
  return response.data;
};

/**
 * User Authentication APIs
 */
export const registerUser = async (name, email, password, confirmPassword) => {
  const payload = {
    name,
    email,
    password,
    confirm_password: confirmPassword,
  };
  const response = await apiClient.post('/api/auth/register', payload);
  return response.data;
};

export const loginUser = async (email, password) => {
  const payload = { email, password };
  const response = await apiClient.post('/api/auth/login', payload);
  return response.data;
};

export const logoutUser = async () => {
  const response = await apiClient.post('/api/auth/logout');
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await apiClient.get('/api/auth/me');
  return response.data;
};

export const updateUserProfile = async (name, email) => {
  const payload = {};
  if (name !== undefined) payload.name = name;
  if (email !== undefined) payload.email = email;
  const response = await apiClient.put('/api/users/me', payload);
  return response.data;
};

export const changeUserPassword = async (currentPassword, newPassword, confirmNewPassword) => {
  const payload = {
    current_password: currentPassword,
    new_password: newPassword,
    confirm_new_password: confirmNewPassword,
  };
  const response = await apiClient.post('/api/users/change-password', payload);
  return response.data;
};

/**
 * Fetch live environmental observation and ML AQI prediction for coordinates
 */
export const getLivePrediction = async (latitude, longitude, locationId = null) => {
  const payload = {
    latitude: parseFloat(latitude),
    longitude: parseFloat(longitude),
  };
  if (locationId) {
    payload.location_id = locationId;
  }
  const response = await apiClient.post('/api/predict/live', payload);
  return response.data;
};

/**
 * Direct feature prediction simulation endpoint
 */
export const getManualPrediction = async (featurePayload) => {
  const response = await apiClient.post('/api/predict', featurePayload);
  return response.data;
};

/**
 * Active ML model metadata
 */
export const getModelInfo = async () => {
  const response = await apiClient.get('/api/model/info');
  return response.data;
};

/**
 * AI Chatbot endpoint
 */
export const sendAIChatMessage = async (message, context = null, history = []) => {
  const payload = {
    message,
    context,
    history,
  };
  const response = await apiClient.post('/api/ai/chat', payload);
  return response.data;
};

/**
 * AI Report Generation endpoint
 */
export const generateAIReport = async (context) => {
  const payload = {
    context,
  };
  const response = await apiClient.post('/api/ai/report', payload);
  return response.data;
};

/**
 * AI Health & Safety Advice endpoint
 */
export const getAIHealthAdvice = async (activity, targetGroup, context) => {
  const payload = {
    activity,
    target_group: targetGroup,
    context,
  };
  const response = await apiClient.post('/api/ai/health-advice', payload);
  return response.data;
};

/**
 * AI Insights endpoint (GET /api/insights)
 */
export const getInsights = async (locationId = null) => {
  const params = locationId ? { location_id: locationId } : {};
  const response = await apiClient.get('/api/insights', { params });
  return response.data;
};

/**
 * Custom AI Insights on demand (POST /api/insights)
 */
export const postCustomInsights = async (customPayload) => {
  const response = await apiClient.post('/api/insights', customPayload);
  return response.data;
};

/**
 * Smart Air Quality Alerts endpoint
 */
export const getSmartAlerts = async (locationId = null) => {
  const params = locationId ? { location_id: locationId } : {};
  const response = await apiClient.get('/api/ai/alerts', { params });
  return response.data;
};

/**
 * Prediction History endpoint
 */
export const getPredictionHistory = async (limit = 20, offset = 0, locationId = null) => {
  const params = { limit, offset };
  if (locationId) {
    params.location_id = locationId;
  }
  const response = await apiClient.get('/api/predictions/history', { params });
  return response.data;
};

/**
 * Latest Prediction endpoint
 */
export const getLatestPrediction = async (locationId = null) => {
  const params = locationId ? { location_id: locationId } : {};
  const response = await apiClient.get('/api/predictions/latest', { params });
  return response.data;
};

/**
 * Analytics Summary endpoint
 */
export const getAnalyticsSummary = async (hours = 720, locationId = null) => {
  const params = { hours };
  if (locationId) {
    params.location_id = locationId;
  }
  const response = await apiClient.get('/api/analytics/summary', { params });
  return response.data;
};

/**
 * Analytics Trends endpoint
 */
export const getAnalyticsTrends = async (hours = 168, locationId = null) => {
  const params = { hours };
  if (locationId) {
    params.location_id = locationId;
  }
  const response = await apiClient.get('/api/analytics/trends', { params });
  return response.data;
};
