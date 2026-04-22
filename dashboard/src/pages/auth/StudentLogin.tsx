import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, CreditCard, Moon, Sun, Sparkles } from "lucide-react";
import { Button, Input } from "../../components/ui";
import { useTheme } from "../../lib/theme";

export default function StudentLogin() {
  const { theme, toggleTheme } = useTheme();

  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId.trim() || !password.trim()) {
      setError("Both fields are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      // TODO: Wire to backend student login endpoint
      // const res = await api.studentLogin(studentId, password);
      // login(res.access_token, res.refresh_token, studentId);
      // navigate("/student");
      setError("Student login coming soon. Please register first.");
    } catch (err: any) {
      setError(err?.detail || err?.message || "Login failed.");
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
          <h1 className="text-xl font-bold text-[var(--fg)]">Welcome Back</h1>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Sign in to your student dashboard</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Student ID"
            placeholder="SIT-ST-2029-00034"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            icon={<CreditCard className="h-4 w-4" />}
          />
          <Input
            label="Password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<Lock className="h-4 w-4" />}
          />

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

        {/* Telegram Login Placeholder */}
        <div className="space-y-3">
          <Button variant="secondary" className="w-full" disabled>
            <svg viewBox="0 0 24 24" className="h-4 w-4 mr-1" fill="currentColor">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.96 6.504-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
            </svg>
            Login with Telegram (Coming Soon)
          </Button>

          <Button variant="secondary" className="w-full" disabled>
            <svg viewBox="0 0 24 24" className="h-4 w-4 mr-1" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Sign in with Google (Coming Soon)
          </Button>
        </div>

        {/* Links */}
        <div className="mt-6 space-y-2 text-center">
          <p className="text-xs text-[var(--fg-subtle)]">
            New student?{" "}
            <Link to="/register" className="font-medium text-[var(--fg-muted)] hover:text-[var(--fg)] underline underline-offset-2 transition-colors">
              Create an account
            </Link>
          </p>
          <p className="text-xs text-[var(--fg-subtle)]">
            Admin?{" "}
            <Link to="/admin/login" className="font-medium text-[var(--fg-muted)] hover:text-[var(--fg)] underline underline-offset-2 transition-colors">
              Admin Login
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
