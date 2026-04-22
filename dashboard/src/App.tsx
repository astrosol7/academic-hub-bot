import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./lib/auth";

// Layouts
import AdminLayout from "./layouts/AdminLayout";
import StudentLayout from "./layouts/StudentLayout";

// Auth Pages
import AdminLogin from "./pages/auth/AdminLogin";
import StudentLogin from "./pages/auth/StudentLogin";
import Register from "./pages/auth/Register";
import Privacy from "./pages/Privacy";

// Admin Pages
import AdminDashboard from "./pages/admin/Dashboard";
import AdminUsers from "./pages/admin/Users";
import CourseContent from "./pages/admin/CourseContent";

// Student Pages
import StudentDashboard from "./pages/student/Dashboard";

// ─── Route Guards ───
function AdminGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/admin/login" replace />;
  if (!isAdmin) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function StudentGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isStudent, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!isStudent) return <Navigate to="/admin" replace />;
  return <>{children}</>;
}

function AuthRedirect() {
  const { isAuthenticated, isAdmin, isStudent, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (isAdmin) return <Navigate to="/admin" replace />;
  if (isStudent) return <Navigate to="/student" replace />;
  return <Navigate to="/login" replace />;
}

// ─── App ───
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Root redirect */}
        <Route path="/" element={<AuthRedirect />} />

        {/* Auth Routes */}
        <Route path="/login" element={<StudentLogin />} />
        <Route path="/register" element={<Register />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/privacy" element={<Privacy />} />

        {/* Admin Routes (Protected) */}
        <Route
          path="/admin"
          element={
            <AdminGuard>
              <AdminLayout />
            </AdminGuard>
          }
        >
          <Route index element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="courses" element={<CourseContent />} />
          <Route path="incidents" element={<AdminUsers />} />
          <Route path="quarantine" element={<AdminUsers />} />
          <Route path="settings" element={<AdminUsers />} />
        </Route>

        {/* Student Routes (Protected) */}
        <Route
          path="/student"
          element={
            <StudentGuard>
              <StudentLayout />
            </StudentGuard>
          }
        >
          <Route index element={<StudentDashboard />} />
          <Route path="resources" element={<StudentDashboard />} />
          <Route path="search" element={<StudentDashboard />} />
          <Route path="chat" element={<StudentDashboard />} />
          <Route path="settings" element={<StudentDashboard />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
