import { Shield, Lock, Eye, FileText, ChevronRight } from "lucide-react";
import { useTheme } from "../lib/theme";

export default function PrivacyPolicy() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="fade-in" style={{ maxWidth: '1000px', margin: '0 auto', padding: '64px 24px' }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '48px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <img src="/orbit-logo.png" alt="Orbit Logo" style={{ width: '48px', height: '48px', borderRadius: '12px' }} />
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-accent)', margin: 0 }}>Orbit Academic Hub</h1>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0 }}>Privacy & Data Security</p>
          </div>
        </div>
        <button onClick={toggleTheme} className="theme-toggle" style={{ marginBottom: 0 }}>
          {theme === 'night' ? '🌙' : '☀️'}
        </button>
      </div>

      <div className="welcome-section" style={{ margin: '0 0 48px 0', background: 'linear-gradient(135deg, #6B46C1 0%, #4C1D95 100%)' }}>
        <h2 className="welcome-title">Your Privacy Matters</h2>
        <p className="welcome-subtitle">We are committed to protecting your academic data and personal identity within the SIT ecosystem.</p>
      </div>

      <div style={{ display: 'grid', gap: '32px' }}>
        {/* Section 1 */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Shield size={20} color="var(--text-accent)" />
            Data Collection
          </div>
          <div className="card-content">
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Orbit collects minimal data required to provide academic assistance. This includes:
            </p>
            <ul style={{ color: 'var(--text-primary)', paddingLeft: '20px', lineHeight: '2' }}>
              <li>Telegram User ID for session management</li>
              <li>Academic course selection for personalized resources</li>
              <li>Search queries to improve Voyager AI responses</li>
              <li>Optional identity verification for SIT student access</li>
            </ul>
          </div>
        </div>

        {/* Section 2 */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Lock size={20} color="var(--text-accent)" />
            Data Usage & Security
          </div>
          <div className="card-content">
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Your data is encrypted and stored securely. We use industry-standard protocols to ensure that:
            </p>
            <ul style={{ color: 'var(--text-primary)', paddingLeft: '20px', lineHeight: '2' }}>
              <li>Personal chats with Voyager AI are private and not shared with third parties.</li>
              <li>Student records are only accessible to verified Orbit administrators.</li>
              <li>All telemetry data is anonymized before analysis.</li>
            </ul>
          </div>
        </div>

        {/* Section 3 */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Eye size={20} color="var(--text-accent)" />
            Cookies & Tracking
          </div>
          <div className="card-content">
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              The Orbit Dashboard uses local storage only to remember your theme preference and secure session token. We do not use third-party tracking cookies or advertising scripts.
            </p>
          </div>
        </div>

        {/* Section 4 */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <FileText size={20} color="var(--text-accent)" />
            Your Rights
          </div>
          <div className="card-content">
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Under the SIT Data Protection guidelines, you have the right to:
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '16px' }}>
              <div style={{ padding: '16px', background: 'var(--bg-hover)', borderRadius: '8px' }}>
                <span style={{ fontWeight: 600, display: 'block', marginBottom: '4px' }}>Request Access</span>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>View all data stored about your account.</span>
              </div>
              <div style={{ padding: '16px', background: 'var(--bg-hover)', borderRadius: '8px' }}>
                <span style={{ fontWeight: 600, display: 'block', marginBottom: '4px' }}>Data Portability</span>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Export your study logs and saved resources.</span>
              </div>
              <div style={{ padding: '16px', background: 'var(--bg-hover)', borderRadius: '8px' }}>
                <span style={{ fontWeight: 600, display: 'block', marginBottom: '4px' }}>Right to Erase</span>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Permanently delete your account and all data.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <footer style={{ marginTop: '64px', textAlign: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '32px' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          &copy; {new Date().getFullYear()} Orbit Academic Hub. Built for SIT Students.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '16px' }}>
          <a href="/login" style={{ color: 'var(--text-accent)', textDecoration: 'none', fontSize: '14px', fontWeight: 500 }}>Back to Login</a>
          <a href="https://t.me/SIT_Academic_Hub_bot" style={{ color: 'var(--text-accent)', textDecoration: 'none', fontSize: '14px', fontWeight: 500 }}>Open Telegram Bot</a>
        </div>
      </footer>
    </div>
  );
}
