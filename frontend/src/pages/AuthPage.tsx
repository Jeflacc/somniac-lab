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
    <div className="min-h-screen flex items-center justify-center bg-[#E2DFDA] px-4">
      <div className="bg-[#F5F4F1] p-8 rounded-2xl shadow-xl w-full max-w-md border border-[#CBDED3]">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-[#3B6255] rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg shadow-[#3B6255]/20">
            <svg viewBox="0 0 100 100" className="w-10 h-10 fill-[#CBDED3]">
              <path d="M50 20 L80 80 L20 80 Z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[#3B6255]">Somniac AI</h1>
          <p className="text-[#8BA49A] mt-2">
            {isLogin ? "Welcome back to your lab" : "Create your conscious instance"}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-xl mb-6 text-sm border border-red-100 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#8BA49A] mb-1">Username</label>
            <input
              type="text"
              required
              className="w-full px-4 py-3 rounded-xl bg-white border border-[#CBDED3] focus:outline-none focus:ring-2 focus:ring-[#3B6255]/30 text-[#3B6255]"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#8BA49A] mb-1">Password</label>
            <input
              type="password"
              required
              className="w-full px-4 py-3 rounded-xl bg-white border border-[#CBDED3] focus:outline-none focus:ring-2 focus:ring-[#3B6255]/30 text-[#3B6255]"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-[#3B6255] text-[#CBDED3] font-medium hover:bg-[#3B6255]/90 transition-colors shadow-md shadow-[#3B6255]/20 mt-6 disabled:opacity-70"
          >
            {loading ? "Processing..." : isLogin ? "Sign In" : "Register"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-[#8BA49A] hover:text-[#3B6255] text-sm transition-colors"
          >
            {isLogin ? "Don't have an account? Register" : "Already have an account? Sign In"}
          </button>
        </div>
      </div>
    </div>
  );
}
