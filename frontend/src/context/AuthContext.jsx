import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getCurrentUser, loginUser, registerUser, logoutUser } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('aqi_auth_token'));
  const [isLoading, setIsLoading] = useState(true);

  // Validate existing token and restore session on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('aqi_auth_token');
      if (storedToken) {
        try {
          const userData = await getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.warn('Session expired or invalid token:', err);
          localStorage.removeItem('aqi_auth_token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    initAuth();

    // Listen to token expiry event from axios response interceptor
    const handleAuthExpired = () => {
      setToken(null);
      setUser(null);
    };
    window.addEventListener('aqi-auth-expired', handleAuthExpired);
    return () => window.removeEventListener('aqi-auth-expired', handleAuthExpired);
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await loginUser(email, password);
    if (res.access_token) {
      localStorage.setItem('aqi_auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    }
  }, []);

  const register = useCallback(async (name, email, password, confirmPassword) => {
    const res = await registerUser(name, email, password, confirmPassword);
    if (res.access_token) {
      localStorage.setItem('aqi_auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch (e) {
      // Best effort server logout notification
    } finally {
      localStorage.removeItem('aqi_auth_token');
      setToken(null);
      setUser(null);
    }
  }, []);

  const updateUser = useCallback((updatedUserData) => {
    setUser(updatedUserData);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
