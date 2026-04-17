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
  list: (projectId = 'default') => api.get('/api/pages', { params: { project_id: projectId } }),
  get: (id) => api.get(`/api/pages/${id}`),
  updateContent: (pageId, elementId, content) =>
    api.put(`/api/pages/${pageId}/content`, { element_id: elementId, content }),
  updateContentBulk: (pageId, updates) =>
    api.put(`/api/pages/${pageId}/content/bulk`, { updates }),
  updateStatus: (pageId, status) =>
    api.put(`/api/pages/${pageId}/status`, { status }),
};

// Page Versions / History
export const versionsAPI = {
  list: (pageId) => api.get(`/api/pages/${pageId}/versions`),
  get: (pageId, versionNumber) => api.get(`/api/pages/${pageId}/versions/${versionNumber}`),
  restore: (pageId, versionNumber) => api.post(`/api/pages/${pageId}/versions/${versionNumber}/restore`),
};

// Users (Admin only)
export const usersAPI = {
  list: () => api.get('/api/users'),
  create: (data) => api.post('/api/auth/register', data),
  update: (userId, data) => api.put(`/api/users/${userId}`, data),
  changePassword: (userId, newPassword) => api.put(`/api/users/${userId}/password`, { new_password: newPassword }),
  delete: (userId) => api.delete(`/api/users/${userId}`),
};

// Projects
export const projectsAPI = {
  list: () => api.get('/api/projects'),
  create: (data) => api.post('/api/projects', data),
  importSchema: (data) => api.post('/api/projects/import', data),
};

export default api;
