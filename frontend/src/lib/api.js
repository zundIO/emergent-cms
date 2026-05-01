import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
// All routes are mounted under /api/cms in the installable build. The dev
// backend also exposes them at /api/* for legacy compatibility.
const API_BASE = process.env.REACT_APP_CMS_API_BASE || '/api/cms';

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
  login: (email, password) => api.post(`${API_BASE}/auth/login`, { email, password }),
  getMe: () => api.get(`${API_BASE}/auth/me`),
  register: (data) => api.post(`${API_BASE}/auth/register`, data),
};

// Pages
export const pagesAPI = {
  list: (projectId = 'default') => api.get(`${API_BASE}/pages`, { params: { project_id: projectId } }),
  get: (id) => api.get(`${API_BASE}/pages/${id}`),
  updateContent: (pageId, elementId, content) =>
    api.put(`${API_BASE}/pages/${pageId}/content`, { element_id: elementId, content }),
  updateContentBulk: (pageId, updates) =>
    api.put(`${API_BASE}/pages/${pageId}/content/bulk`, { updates }),
  updateStatus: (pageId, status) =>
    api.put(`${API_BASE}/pages/${pageId}/status`, { status }),
};

// Page Versions / History
export const versionsAPI = {
  list: (pageId) => api.get(`${API_BASE}/pages/${pageId}/versions`),
  get: (pageId, versionNumber) => api.get(`${API_BASE}/pages/${pageId}/versions/${versionNumber}`),
  restore: (pageId, versionNumber) => api.post(`${API_BASE}/pages/${pageId}/versions/${versionNumber}/restore`),
};

// Users (Admin only)
export const usersAPI = {
  list: () => api.get(`${API_BASE}/users`),
  create: (data) => api.post(`${API_BASE}/auth/register`, data),
  update: (userId, data) => api.put(`${API_BASE}/users/${userId}`, data),
  changePassword: (userId, newPassword) => api.put(`${API_BASE}/users/${userId}/password`, { new_password: newPassword }),
  delete: (userId) => api.delete(`${API_BASE}/users/${userId}`),
};

// Projects
export const projectsAPI = {
  list: () => api.get(`${API_BASE}/projects`),
  create: (data) => api.post(`${API_BASE}/projects`, data),
  importSchema: (data) => api.post(`${API_BASE}/projects/import`, data),
};

export default api;
