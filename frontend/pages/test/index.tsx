import { getIdToken } from "@/firebase/firebaseClient";
import { useEffect } from "react";
import { useAuth } from "@/firebase/AuthContext";
import apiClient from "@/api/axiosClient";

const TestPage: React.FC = () => {
  useAuth()
  // Add to your application somewhere to debug
  useEffect(() => {
    const checkToken = async () => {
      const token = await getIdToken();
      console.log("Token available:", !!token);
      // Don't log the actual token for security reasons
    };
    checkToken();
  }, []);


  useEffect(() => {
    const testAuth = async () => {
      try {
        console.log("Testing auth...");
        const response = await apiClient.get("/auth-test");
        console.log("Auth successful:", response.data);
      } catch (error) {
        console.error("Auth error:", error.response?.status, error.response?.data);
      }
    };
    testAuth();
  }, []);


  return (
    <div>
      <p>{ }</p>
    </div>
  )

}

export default TestPage
