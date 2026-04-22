import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useTheme } from "../lib/theme";
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  HardDrive,
  Settings,
  BookOpen,
  LogOut,
  Moon,
  Sun
} from "lucide-react";

export default function AdminLayout() {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="dashboard-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <img src="/orbit-logo.png" alt="Orbit Logo" className="logo-icon" />
          <h2 className="logo-text">Orbit</h2>
        </div>

        <nav style={{ flex: 1 }}>
          <NavLink to="/admin" end className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <LayoutDashboard className="nav-icon" />
            Home Dashboard
          </NavLink>
          <NavLink to="/admin/courses" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <BookOpen className="nav-icon" />
            Course Content
          </NavLink>
          <NavLink to="/admin/users" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <Users className="nav-icon" />
            Student Directory
          </NavLink>
          <NavLink to="/admin/incidents" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <AlertTriangle className="nav-icon" />
            Incident Reports
          </NavLink>
          <NavLink to="/admin/quarantine" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <HardDrive className="nav-icon" />
            Quarantine
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <button onClick={toggleTheme} className="theme-toggle" title="Toggle Theme">
            {theme === "night" ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          
          <NavLink to="/admin/settings" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <Settings className="nav-icon" />
            Settings
          </NavLink>
          <button onClick={logout} className="nav-item" style={{ background: "none", border: "none", width: "100%", textAlign: "left", color: "#dc2626", marginTop: "4px" }}>
            <LogOut className="nav-icon" />
            Log Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, overflowY: "auto" }}>
        <Outlet />
      </main>
    </div>
  );
}
