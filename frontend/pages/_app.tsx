// pages/_app.tsx
import React from 'react';
import Head from 'next/head';
import { AppProps } from 'next/app';
import { AuthProvider } from '../firebase/AuthContext';
import '../styles/globals.css';
import Layout from '../components/Layout'

// Do not initialize Firebase here - it should only be in firebaseClient.ts

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <Layout>
      <AuthProvider>
        <Head>
          <title>Task Manager App</title>
          <meta name="description" content="A smart assistant to help with task management and scheduling" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <link rel="icon" type="image/png" href="/favicon.png" />
        </Head>
        <Component {...pageProps} />
      </AuthProvider>
    </Layout>
  );
}

export default MyApp;
