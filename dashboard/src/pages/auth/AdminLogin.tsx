import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, User, Eye, EyeOff, Sparkles, Moon, Sun } from "lucide-react";
import { Button, Input } from "../../components/ui";
import { useAuth } from "../../lib/auth";
import { useTheme } from "../../lib/theme";
import { api, normalizeApiBaseUrl, getConfiguredApiBaseUrl, setConfiguredApiBaseUrl } from "../../api";

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
          <a href="/login" className="font-medium text-[var(--fg-muted)] hover:text-[var(--fg)] underline underline-offset-2 transition-colors">
            Student Login
          </a>
        </p>
      </motion.div>
    </div>
  );
}
