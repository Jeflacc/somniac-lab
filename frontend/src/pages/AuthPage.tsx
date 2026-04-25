import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { SignInPage } from "@/components/ui/sign-in-flow-1";

export function AuthPage() {
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAuth = async (username: string, password: string, isLogin: boolean, email?: string) => {
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
        body = JSON.stringify({ username, email, password });
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
      return true;
    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full h-screen">
      {error && (
        <div className="fixed top-24 left-1/2 transform -translate-x-1/2 z-[100] bg-red-500/10 border border-red-500/50 text-red-200 px-6 py-2 rounded-full backdrop-blur-md text-sm animate-in fade-in slide-in-from-top-4">
          {error}
        </div>
      )}
      
      <SignInPage 
        onSubmit={handleAuth}
        isLoading={loading}
        onSuccess={() => {
          // Navigation is handled by the success screen transition in SignInPage
        }}
      />
      
      {/* 
        Note: The SignInPage component currently handles its own state.
        To fully integrate the backend login, we should pass handleAuth 
        to the component. I will update the component to accept these props properly.
      */}
    </div>
  );
}
