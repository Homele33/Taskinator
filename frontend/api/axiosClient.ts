// api/axiosClient.ts
import axios from 'axios';
import { getIdToken } from '../firebase/firebaseClient';

const API_BASE_URL = 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// THIS IS WHERE THE TOKEN IS SENT TO THE BACKEND
// This interceptor runs before every API request
apiClient.interceptors.request.use(
  async (config) => {
    try {
      // Get the Firebase ID token from the currently logged in user
      const token = await getIdToken();

      if (token) {
        // Attach the token to the Authorization header using Bearer scheme
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return config;
    }
  },
  (error) => {
    return Promise.reject(error);
  }
);
export default apiClient
