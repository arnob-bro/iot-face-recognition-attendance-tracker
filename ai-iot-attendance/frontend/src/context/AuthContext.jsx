/**
 * AuthContext — global authentication state for FastAPI JWT-based auth.
 *
 * Supports:
 * - Admin/Teacher JWT authentication
 * - Student JWT authentication
 *
 * Teacher/Admin user shape:
 *   { teacher_id, name, email, role, created_at }
 *
 * Student user shape:
 *   { student_id, name, email, role, created_at }
 */

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  login as apiLogin,
  getMe,
  registerTeacher,
} from "../api/auth";

import {
  studentLogin as apiStudentLogin,
  getStudentMe,
} from "../api/students";

import {
  setToken,
  clearToken,
  setUserInfo,
  getUserInfo,
  getToken,
} from "../api/client";


const AuthContext = createContext(null);


export function AuthProvider({ children }) {

  const [user, setUser] = useState(getUserInfo);
  const [loading, setLoading] = useState(true);


  // Validate stored token when application starts
  useEffect(() => {

    let cancelled = false;

    const token = getToken();

    if (!token) {
      setLoading(false);
      return;
    }


    const storedUser = getUserInfo();


    const profileRequest =
      storedUser?.role === "student"
        ? getStudentMe()
        : getMe();


    profileRequest
      .then((profile) => {

        if (!cancelled) {

          const updatedUser = {
            ...profile,
            role: storedUser?.role || profile.role,
          };

          setUser(updatedUser);
          setUserInfo(updatedUser);
        }

      })
      .catch(() => {

        if (!cancelled) {
          clearToken();
          setUser(null);
        }

      })
      .finally(() => {

        if (!cancelled) {
          setLoading(false);
        }

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
       * Admin/Teacher login
       *
       * Uses:
       * POST /api/v1/auth/login
       */
      async login(email, password) {

        const tokenData = await apiLogin(email, password);


        setToken(tokenData.access_token);


        const profile = await getMe();


        setUser(profile);
        setUserInfo(profile);


        return profile;
      },


      /**
       * Student login
       *
       * Uses:
       * POST /api/v1/students/login
       */
      async studentLogin(studentId, password) {

        const tokenData = await apiStudentLogin(
          studentId,
          password
        );


        setToken(tokenData.access_token);


        const profile = await getStudentMe();


        const studentUser = {
          ...profile,
          role: "student",
        };


        setUser(studentUser);
        setUserInfo(studentUser);


        return studentUser;
      },


      /**
       * Register teacher/admin account.
       */
      async register(data) {

        await registerTeacher({
          name: data.name,
          email: data.email,
          password: data.password,
          role: data.role || "teacher",
        });


        const tokenData = await apiLogin(
          data.email,
          data.password
        );


        setToken(tokenData.access_token);


        const profile = await getMe();


        setUser(profile);
        setUserInfo(profile);


        return profile;
      },


      /**
       * Logout
       */
      logout() {

        clearToken();
        setUser(null);

      },


    }),
    [user, loading]
  );


  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );

}



export function useAuth() {

  const context = useContext(AuthContext);


  if (!context) {
    throw new Error(
      "useAuth must be used within AuthProvider"
    );
  }


  return context;

}