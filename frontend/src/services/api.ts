import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';
import { message } from 'antd';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const requestUrl = error.config?.url || '';
    const isLoginRequest = typeof requestUrl === 'string' && requestUrl.includes('/auth/login');
    const errMsg =
      error.code === 'ECONNABORTED'
        ? '请求超时，请确认后端服务已启动'
        : error.response?.data?.detail || '请求失败';

    if (error.response?.status === 401) {
      if (!isLoginRequest) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
      message.error(errMsg);
    } else {
      message.error(errMsg);
    }
    return Promise.reject(error);
  }
);
