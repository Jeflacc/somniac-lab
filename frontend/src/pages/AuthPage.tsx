import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
      let body;
      let headers: HeadersInit = {};

      if (isLogin) {
        body = new URLSearchParams();
        body.append("username", username);
        body.append("password", password);
        headers = { "Content-Type": "application/x-www-form-urlencoded" };
      } else {
        body = JSON.stringify({ username, password });
        headers = { "Content-Type": "application/json" };
      }

      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const url = `${API_URL}${endpoint}`;
      
      const res = await fetch(url, {
        method: "POST",
        headers,
        body,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Authentication failed");
      }

      const data = await res.json();
      login(data.access_token);
      navigate("/lab");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-secondary)] px-4">
      <div className="bg-[var(--bg-card)] p-8 rounded-xl shadow-sm w-full max-w-md border border-[var(--border)]">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-[var(--accent)] rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg viewBox="0 0 100 100" className="w-8 h-8 fill-white">
              <path d="M50 20 L80 80 L20 80 Z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Somniac AI</h1>
          <p className="text-[var(--text-secondary)] mt-2">
            {isLogin ? "Welcome back" : "Create your account"}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6 text-sm border border-red-100 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Username</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] focus:outline-none focus:border-[var(--accent-2)] focus:ring-2 focus:ring-[var(--accent-glow)] text-[var(--text-primary)] transition-all"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Password</label>
            <input
              type="password"
              required
              className="w-full px-4 py-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] focus:outline-none focus:border-[var(--accent-2)] focus:ring-2 focus:ring-[var(--accent-glow)] text-[var(--text-primary)] transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] font-medium hover:bg-[var(--accent-2)] transition-colors mt-6 disabled:opacity-70"
          >
            {loading ? "Processing..." : isLogin ? "Sign In" : "Register"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm transition-colors font-medium"
          >
            {isLogin ? "Don't have an account? Register" : "Already have an account? Sign In"}
          </button>
        </div>
      </div>
    </div>
  );
}
