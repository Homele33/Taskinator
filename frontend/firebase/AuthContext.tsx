// firebase/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from 'firebase/auth';
import { onAuthStateChangedListener, getIdToken } from './firebaseClient';

type AuthContextType = {
  user: User | null;
  loading: boolean;
  idToken: string | null;
  refreshToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  idToken: null,
  refreshToken: async () => null,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Function to refresh token
  const refreshToken = async () => {
    if (user) {
      const token = await getIdToken();
      setIdToken(token);
      return token;
    }
    return null;
  };

  useEffect(() => {
    // Use the listener from firebaseClient.ts to avoid re-initialization
    const unsubscribe = onAuthStateChangedListener(async (authUser: User | null) => {
      console.log("Auth state changed:", authUser ? "User logged in" : "No user");
      setUser(authUser);

      if (authUser) {
        // Get the ID token
        const token = await getIdToken();
        setIdToken(token);
      } else {
        setIdToken(null);
      }

      setLoading(false);
    });

    // Clean up subscription
    return () => unsubscribe();
  }, []);

  if (loading) {
    return <></>
  }
  return (
    <AuthContext.Provider value={{ user, loading, idToken, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
};
