import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

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
  search: (query) => api.get(`/vocabulary/search/${query}`),
  getCategories: () => api.get('/vocabulary/categories/all'),
};

export const practiceAPI = {
  getDailySession: (sessionType = 'standard') => 
    api.get('/practice/daily-session', { params: { session_type: sessionType } }),
  updateProgress: (data) => api.post('/practice/update-progress', {
    vocabulary_id: data.vocabulary_id,
    proficiency_level: data.proficiency_level,
    is_correct: data.is_correct
  }),
  getStats: () => api.get('/practice/stats'),
  createLearningGoal: (data) => api.post('/practice/goals', data),
  getNextLesson: () => api.get('/practice/lessons/next'),
  createCurriculum: (data) => api.post('/practice/curriculum', data),
  getCurriculumProgress: () => api.get('/practice/curriculum/progress'),
  startWeeklyLesson: (data) => api.post('/practice/weekly-lesson', data),
  getWeeklyLesson: (lessonId) => api.get(`/practice/weekly-lesson/${lessonId}`),
};

export const authAPI = {
  login: (credentials) => api.post('/auth/token', credentials),
  getProfile: () => api.get('/auth/me'),
};

export default api;
