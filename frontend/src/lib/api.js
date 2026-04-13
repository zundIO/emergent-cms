import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('monolith_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('monolith_token');
      localStorage.removeItem('monolith_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  getMe: () => api.get('/api/auth/me'),
  register: (data) => api.post('/api/auth/register', data),
};

// Pages
export const pagesAPI = {
  list: () => api.get('/api/pages'),
  get: (id) => api.get(`/api/pages/${id}`),
  updateContent: (pageId, elementId, content) =>
    api.put(`/api/pages/${pageId}/content`, { element_id: elementId, content }),
  updateContentBulk: (pageId, updates) =>
    api.put(`/api/pages/${pageId}/content/bulk`, { updates }),
  updateStatus: (pageId, status) =>
    api.put(`/api/pages/${pageId}/status`, { status }),
};

export default api;
