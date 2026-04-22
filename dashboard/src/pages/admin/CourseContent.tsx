import { useState } from "react";

export default function CourseContent() {
  const [activeTab, setActiveTab] = useState("courses");

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Course Content</h1>
        <div className="header-actions">
          <button className="btn btn-secondary">Upload Material</button>
          <button className="btn btn-primary">Sync Database</button>
        </div>
      </div>

      <div className="content-area">
        <div className="tabs-container">
          <button 
            className={`tab ${activeTab === 'courses' ? 'active' : ''}`}
            onClick={() => setActiveTab('courses')}
          >
            Course Dictionary
          </button>
          <button 
            className={`tab ${activeTab === 'snippets' ? 'active' : ''}`}
            onClick={() => setActiveTab('snippets')}
          >
            Content Snippets
          </button>
        </div>

        {activeTab === 'courses' && (
          <div className="card">
            <div className="card-header">Active Courses</div>
            <div className="card-content" style={{ padding: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '16px 24px', borderBottom: '1px solid var(--border-color)' }}>
                <span style={{ fontWeight: 500 }}>CHEM 1210 — Introductory Chemistry I</span>
                <span style={{ color: 'var(--text-secondary)' }}>12 Resources</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '16px 24px', borderBottom: '1px solid var(--border-color)' }}>
                <span style={{ fontWeight: 500 }}>MATH 1110 — Calculus I</span>
                <span style={{ color: 'var(--text-secondary)' }}>8 Resources</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '16px 24px' }}>
                <span style={{ fontWeight: 500 }}>PHYS 1310 — Advanced Physics</span>
                <span style={{ color: 'var(--text-secondary)' }}>15 Resources</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'snippets' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            <div className="card" style={{ cursor: 'pointer' }}>
              <div className="card-content">
                <h3 style={{ fontSize: '18px', margin: '0 0 8px 0' }}>Chemistry Syllabus Snippet</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: '0 0 16px 0' }}>Exams: 60% (4 total, lowest 1 dropped)...</p>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ background: 'var(--bg-hover)', padding: '4px 8px', borderRadius: '4px', fontSize: '11px' }}>Syllabus</span>
                  <span style={{ background: 'var(--bg-hover)', padding: '4px 8px', borderRadius: '4px', fontSize: '11px' }}>CHEM 1210</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
