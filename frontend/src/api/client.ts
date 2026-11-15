import axios from 'axios';

// Base Axios instance configured with API URL from environment
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  headers: {
    'Accept': 'application/json',
  },
});
