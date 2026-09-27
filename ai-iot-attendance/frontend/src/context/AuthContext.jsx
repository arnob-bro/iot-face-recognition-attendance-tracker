/**
 * AuthContext — global authentication state for FastAPI JWT-based auth.
 *
 * The FastAPI backend returns a Bearer JWT token on login.
 * Token is stored in localStorage and sent as Authorization: Bearer <token>
 * on every subsequent request via the api/client.js wrapper.
 *
 * User state shape mirrors FastAPI TeacherResponse:
 *   { teacher_id, name, email, role, created_at }
 */

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { login as apiLogin, getMe, registerTeacher } from "../api/auth";
import { setToken, clearToken, setUserInfo, getUserInfo, getToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getUserInfo); // Initialize from localStorage
  const [loading, setLoading] = useState(true);

  // On mount, validate stored token by calling /me
  useEffect(() => {
    let cancelled = false;

    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }

    getMe()
      .then((profile) => {
        if (!cancelled) {
          setUser(profile);
          setUserInfo(profile);
        }
      })
      .catch(() => {
        if (!cancelled) {
          // Token invalid or expired — clear everything
          clearToken();
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      setUser,

      /**
       * Login with email + password.
       * Stores token and fetches full user profile.
       */
      async login(email, password) {
        // POST /api/v1/auth/login → { access_token, token_type, role, name }
        const tokenData = await apiLogin(email, password);

        // Store the access token
        setToken(tokenData.access_token);

        // Fetch the full user profile
        const profile = await getMe();
        setUser(profile);
        setUserInfo(profile);
        return profile;
      },

      /**
       * Register a new account and immediately log in.
       */
      async register(data) {
        await registerTeacher({
          name: data.name,
          email: data.email,
          password: data.password,
          role: data.role || "teacher",
        });
        const tokenData = await apiLogin(data.email, data.password);
        setToken(tokenData.access_token);
        const profile = await getMe();
        setUser(profile);
        setUserInfo(profile);
        return profile;
      },

      /**
       * Logout — clear the stored token and user info.
       */
      logout() {
        clearToken();
        setUser(null);
      },
    }),
    [user, loading]
  );


  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
