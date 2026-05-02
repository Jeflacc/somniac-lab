import React, { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface AuthContextType {
  token: string | null;
  username: string | null;
  profilePicture: string | null;
  isAuthenticated: boolean;
  login: (token: string, username?: string) => void;
  logout: () => void;
  setProfilePicture: (pic: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("somniac_token"));
  const [username, setUsername] = useState<string | null>(localStorage.getItem("somniac_username"));
  const [profilePicture, setProfilePictureState] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      localStorage.setItem("somniac_token", token);
    } else {
      localStorage.removeItem("somniac_token");
    }
  }, [token]);

  useEffect(() => {
    if (username) {
      localStorage.setItem("somniac_username", username);
    } else {
      localStorage.removeItem("somniac_username");
    }
  }, [username]);

  // Fetch profile on mount if authenticated
  useEffect(() => {
    if (token) {
      fetch(`${API_URL}/api/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            setUsername(data.username);
            setProfilePictureState(data.profile_picture || null);
          }
        })
        .catch(() => {});
    }
  }, [token]);

  const login = (newToken: string, newUsername?: string) => {
    localStorage.setItem("somniac_token", newToken);
    setToken(newToken);
    if (newUsername) {
      setUsername(newUsername);
    }
  };

  const logout = () => {
    setToken(null);
    setUsername(null);
    setProfilePictureState(null);
    localStorage.removeItem("somniac_username");
    navigate("/auth");
  };

  const setProfilePicture = (pic: string | null) => {
    setProfilePictureState(pic);
  };

  return (
    <AuthContext.Provider value={{ token, username, profilePicture, isAuthenticated: !!token, login, logout, setProfilePicture }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
