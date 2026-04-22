import { useEffect, useState } from "react";
import { api, type Overview } from "../../api";

function formatNum(n: number | undefined): string {
  return new Intl.NumberFormat().format(n ?? 0);
}

export default function AdminDashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);

  const fetchData = async () => {
    try {
      const ov = await api.overview();
      setOverview(ov);
    } catch {
      /* silent */
    }
  };

  useEffect(() => { void fetchData(); }, []);

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Control Center</h1>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={fetchData}>Refresh</button>
        </div>
      </div>

      <div className="welcome-section">
        <h2 className="welcome-title">Welcome back, Admin</h2>
        <p className="welcome-subtitle">Here is what is happening with the Orbit Academic Hub today.</p>
        <button className="cta-button">View Active Reports</button>
      </div>

      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-number">{formatNum(overview?.students_total)}</div>
          <div className="stat-label">Total Students</div>
        </div>
        <div className="card stat-card">
          <div className="stat-number">{formatNum(overview?.links_total)}</div>
          <div className="stat-label">Linked Accounts</div>
        </div>
        <div className="card stat-card">
          <div className="stat-number">{formatNum(overview?.incidents_open)}</div>
          <div className="stat-label">Open Incidents</div>
        </div>
        <div className="card stat-card">
          <div className="stat-number">{formatNum(overview?.quarantine_pending)}</div>
          <div className="stat-label">Quarantine Pending</div>
        </div>
      </div>
      
      <div className="content-area" style={{ paddingTop: 0 }}>
        <div className="card">
          <div className="card-header">Recent Activity</div>
          <div className="card-content">
            <p style={{ color: "#666" }}>Telemetry stream connected. Waiting for new events...</p>
          </div>
        </div>
      </div>
    </div>
  );
}
