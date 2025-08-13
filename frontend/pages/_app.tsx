// pages/_app.tsx
import React, { useEffect, useState } from "react";
import Head from "next/head";
import type { AppProps } from "next/app";
import { useRouter } from "next/router";
import { getAuth, onIdTokenChanged, User } from "firebase/auth";
import { AuthProvider } from "../firebase/AuthContext";
import apiClient from "@/api/axiosClient";
import "../styles/globals.css";
import Layout from "../components/Layout";

/**
 * Global guard:
 * - Allows /login and /onboarding without checks.
 * - Waits for Firebase token to be ready (onIdTokenChanged).
 * - If user logged in → check /api/preferences:
 *     - exists === false → redirect to /onboarding (once).
 *     - exists === true  → continue.
 * - On 401/failed request → redirect to /login (once).
 */
export default function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    const auth = getAuth();
    const allowlist = new Set<string>(["/login", "/onboarding"]);

    const go = async (user: User | null) => {
      // If this route is allowlisted, skip guard logic
      if (allowlist.has(router.pathname)) {
        setReady(true);
        return;
      }

      // Not logged in → let existing flows handle redirect (don’t loop)
      if (!user) {
        setReady(true);
        return;
      }

      try {
        // Ensure token is minted before calling backend (prevents 401 race)
        await user.getIdToken(/* forceRefresh */ false);

        const res = await apiClient.get("/preferences");
        const exists = !!res.data?.exists;

        if (!exists && router.pathname !== "/onboarding" && !redirecting) {
          setRedirecting(true);
          await router.replace("/onboarding");
          return;
        }

        setReady(true);
      } catch (e: any) {
        const status = e?.response?.status;
        // Only redirect to /login if we’re not already there and not in a redirect
        if (status === 401 && router.pathname !== "/login" && !redirecting) {
          setRedirecting(true);
          await router.replace("/login");
          return;
        }
        // For other errors: don’t loop; just allow render and show console
        console.error("Guard error:", e);
        setReady(true);
      } finally {
        // release redirect flag after navigation settles
        setTimeout(() => setRedirecting(false), 0);
      }
    };

    // Subscribe to token readiness (fires on first load and token refresh)
    const unsub = onIdTokenChanged(auth, go);

    return () => unsub();
    // Re-evaluate when the pathname changes (e.g., user navigates)
  }, [router.pathname]);

  return (
    <Layout>
      <AuthProvider>
        <Head>
          <title>Task Manager App</title>
          <meta
            name="description"
            content="A smart assistant to help with task management and scheduling"
          />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <link rel="icon" type="image/png" href="/favicon.png" />
        </Head>

        {!ready ? (
          <div className="min-h-screen flex items-center justify-center">
            <span className="loading loading-spinner loading-lg" />
          </div>
        ) : (
          <Component {...pageProps} />
        )}
      </AuthProvider>
    </Layout>
  );
}
