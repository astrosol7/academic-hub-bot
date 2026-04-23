import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, User, Eye, EyeOff, Sparkles, Moon, Sun } from "lucide-react";
import { Button, Input } from "../../components/ui";
import { useAuth } from "../../lib/auth";
import { useTheme } from "../../lib/theme";
import { api, normalizeApiBaseUrl, getConfiguredApiBaseUrl, setConfiguredApiBaseUrl } from "../../api";
import TelegramLoginWidget from "../../components/TelegramLoginWidget";
import { useGoogleLogin } from "@react-oauth/google";

export default function AdminLogin() {
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiUrl, setApiUrl] = useState(getConfiguredApiBaseUrl());
  const [showApiConfig, setShowApiConfig] = useState(false);

  const loginWithGoogle = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        setLoading(true);
        setError("");
        const res = await api.googleLogin(tokenResponse.access_token);
        
        login(res.access_token, res.refresh_token, "admin-user");
        navigate("/dashboard");
      } catch (err: any) {
        console.error(err);
        setError(err.detail || "Failed to authenticate with Google as Admin");
      } finally {
        setLoading(false);
      }
    },
    onError: (error) => {
      console.error(error);
      setError("Google Login failed");
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Both fields are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const normalized = normalizeApiBaseUrl(apiUrl);
      setConfiguredApiBaseUrl(normalized);
      const res = await api.login(username, password, normalized);
      login(res.access_token, res.refresh_token, username);
      navigate("/admin");
    } catch (err: any) {
      setError(err?.detail || err?.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4">
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 z-50 rounded-full border border-[var(--border)] bg-[var(--bg-elevated)] p-2.5 text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors"
      >
        {theme === "night" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-sm"
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent)] text-[var(--accent-fg)]">
            <Sparkles className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold text-[var(--fg)]">Orbit Admin</h1>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Sign in with your admin credentials</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username"
            placeholder="admin"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            icon={<User className="h-4 w-4" />}
            autoComplete="username"
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-[var(--fg-muted)]">Password</label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--fg-subtle)]">
                <Lock className="h-4 w-4" />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                autoComplete="current-password"
                className="w-full h-10 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--bg)] pl-10 pr-10 text-sm text-[var(--fg)] placeholder:text-[var(--fg-subtle)] focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--fg-subtle)] hover:text-[var(--fg)]"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {error && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-[var(--radius-sm)] border border-[var(--danger)]/20 bg-[var(--danger)]/5 px-3 py-2 text-xs text-[var(--danger)]"
            >
              {error}
            </motion.p>
          )}

          <Button type="submit" loading={loading} className="w-full">
            Sign In
          </Button>
        </form>

        {/* Divider */}
        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-[var(--border)]" />
          <span className="text-[11px] font-medium uppercase text-[var(--fg-subtle)]">or</span>
          <div className="h-px flex-1 bg-[var(--border)]" />
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-4">
          <TelegramLoginWidget 
            botName="academichubbot" 
            onAuth={(user) => setError(`Admin Telegram Login successful for ${user.first_name}. Backend integration required.`)} 
          />

          <Button 
            variant="secondary" 
            className="w-full relative overflow-hidden transition-all duration-300 hover:shadow-md hover:-translate-y-[1px] bg-white text-gray-700 border-gray-200 dark:bg-[#1A1A1A] dark:text-gray-200 dark:border-gray-800" 
            onClick={() => loginWithGoogle()}
            disabled={loading}
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5 mr-2 absolute left-4" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Continue with Google
          </Button>
        </div>

        {/* API Config */}
        <div className="mt-6 text-center">
          <button
            onClick={() => setShowApiConfig(!showApiConfig)}
            className="text-xs text-[var(--fg-subtle)] hover:text-[var(--fg-muted)] transition-colors"
          >
            {showApiConfig ? "Hide" : "Configure"} API Endpoint
          </button>
          {showApiConfig && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-3"
            >
              <Input
                placeholder="http://127.0.0.1:8000"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
              />
            </motion.div>
          )}
        </div>

        {/* Student link */}
        <p className="mt-6 text-center text-xs text-[var(--fg-subtle)]">
          Are you a student?{" "}
          <Link to="/login" className="font-medium text-[var(--fg-muted)] hover:text-[var(--fg)] underline underline-offset-2 transition-colors">
            Student Login
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
