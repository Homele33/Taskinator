// pages/_app.tsx
import React from 'react';
import Head from 'next/head';
import { AppProps } from 'next/app';
import { AuthProvider } from '../firebase/AuthContext';
import '../styles/globals.css';

// Do not initialize Firebase here - it should only be in firebaseClient.ts

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Head>
        <title>Task Manager App</title>
        <meta name="description" content="A smart assistant to help with task management and scheduling" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;
