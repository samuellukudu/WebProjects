import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const vocabularyAPI = {
  getAll: (params) => api.get('/vocabulary/', { params }),
  getById: (id) => api.get(`/vocabulary/${id}`),
  search: (query) => api.get(`/vocabulary/search?query=${query}`),
  getCategories: () => api.get('/vocabulary/categories'),
};

export const practiceAPI = {
  getDailySession: () => api.get('/practice/daily-session'),
  updateProgress: (data) => api.post('/practice/update-progress', data),
  getStats: () => api.get('/practice/stats'),
};

export const authAPI = {
  login: (credentials) => api.post('/auth/token', credentials),
  getProfile: () => api.get('/auth/me'),
};

export default api;
