// Example of corrected Next.js page with proper data fetching method

// pages/dashboard.tsx
import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import AuthLayout from '@/components/AuthLayout';
import { useAuth } from '@/firebase/AuthContext';
import apiClient from '@/api/axiosClient';
import { Task } from '@/components/tasksTypes';

// IMPORTANT: Remove any getStaticProps or getStaticPaths if you're using getServerSideProps
// Or remove getServerSideProps if you're using getStaticProps/getStaticPaths

const Dashboard: React.FC = () => {
  const { user, loading, idToken, refreshToken } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Use client-side data fetching with useEffect
  useEffect(() => {
    // Only fetch data if user is logged in and has a token
    if (user && idToken) {
      fetchTasks();
    }
  }, [user, idToken]);

  const fetchTasks = async () => {
    try {
      setIsLoading(true);
      setError('');

      // Make API request
      const response = await apiClient.get('/tasks');

      // Update state with fetched data
      setTasks(response.data);
    } catch (err: any) {
      console.error('Error fetching tasks:', err);
      setError('Failed to load tasks. Please try again.');

      // Show more specific error message if available
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Rest of your component code...
  return (
    <AuthLayout>
      <div></div>
    </AuthLayout>
  );
};

// DO NOT include both getServerSideProps and getStaticProps/getStaticPaths
// Choose only one approach for data fetching

// Option 1: If you want server-side rendering on each request
// export async function getServerSideProps(context) {
//   // Server-side logic here
//   return {
//     props: {}, // Will be passed to the page component as props
//   };
// }

// Option 2: If you want static generation
// export async function getStaticProps() {
//   // Static site generation logic here
//   return {
//     props: {}, // Will be passed to the page component as props
//   };
// }

export default Dashboard;
