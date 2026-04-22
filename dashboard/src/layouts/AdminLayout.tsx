import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  HardDrive,
  Settings,
  BookOpen
} from "lucide-react";

export default function AdminLayout() {
  const { logout } = useAuth();

  return (
    <div className="dashboard-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div style={{ padding: "0 16px", marginBottom: "32px" }}>
          <h2 style={{ fontSize: "20px", fontWeight: 700, color: "#6B46C1", margin: 0 }}>Orbit Hub</h2>
          <p style={{ fontSize: "12px", color: "#666", margin: "4px 0 0 0" }}>Administrator</p>
        </div>

        <nav>
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
          
          <div style={{ marginTop: "32px", borderTop: "1px solid #E5E5E5", paddingTop: "16px" }}>
            <NavLink to="/admin/settings" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
              <Settings className="nav-icon" />
              Settings
            </NavLink>
            <button onClick={logout} className="nav-item" style={{ background: "none", border: "none", width: "100%", textAlign: "left", color: "#dc2626" }}>
              Log Out
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main style={{ backgroundColor: "#FAFAFA", minHeight: "100vh" }}>
        <Outlet />
      </main>
    </div>
  );
}
