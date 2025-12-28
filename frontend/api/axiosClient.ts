// api/axiosClient.ts
import axios from "axios";
import { getIdToken } from "../firebase/firebaseClient";

// Resolve base URL for API
const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000").replace(/\/$/, "");

const apiClient = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: false,
  headers: { "Content-Type": "application/json" },
});

// === Request interceptor: attach Firebase ID token ===
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await getIdToken(); // null if not logged in
      if (token) {
        (config.headers as any).Authorization = `Bearer ${token}`;
      }
      return config;
    } catch (err) {
      console.error("Error getting auth token:", err);
      return config;
    }
  },
  (err) => Promise.reject(err)
);

// === Response interceptor: better diagnostics for "Network Error" ===
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    const data   = error?.response?.data;
    const url    = `${error?.config?.baseURL || ""}${error?.config?.url || ""}`;
    
    // Silent handling for 409 Conflict - these are expected and handled gracefully
    if (status === 409) {
      console.log(`[409 Conflict] ${url} - Triggering conflict resolution flow`);
      return Promise.reject(error);
    }
    
    // Log other errors for debugging
    console.error("API error:", { url, status, data });
    return Promise.reject(error);
  }
);

export default apiClient;
