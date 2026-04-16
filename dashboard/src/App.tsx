import React, { useEffect, useMemo, useState } from 'react';
import { 
  ShieldCheck, Server, AlertTriangle, Search, HardDrive, FileTerminal, Activity, 
  Users, BarChart3, RefreshCw, CheckCircle2, MessageSquareWarning, Zap, Filter, Lock, LogOut
} from 'lucide-react';
import { api, type Incident, type IncidentStatus, type Overview, type QuarantineItem, type StudentRow, type TelemetryRow } from './api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('orbit_access_token'));
  const [activeTab, setActiveTab] = useState('overview');


  const logout = () => {
    localStorage.removeItem('orbit_access_token');
    localStorage.removeItem('orbit_refresh_token');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginScreen onLogin={(access, refresh) => {
      localStorage.setItem('orbit_access_token', access);
      localStorage.setItem('orbit_refresh_token', refresh);
      setIsAuthenticated(true);
    }} />;
  }

  return (
    <div className="flex h-screen bg-[#0f1115] text-[#e2e8f0] font-sans antialiased overflow-hidden selection:bg-blue-500/30">
      {/* Dynamic Sidebar */}
      <aside className="w-64 border-r border-[#30363d] bg-[#161b22] flex flex-col glass-panel shadow-blue-500/5 z-20">
        <div className="p-6 border-b border-[#30363d] flex items-center gap-3">
          <Server className="text-blue-400 w-8 h-8" />
          <div className="flex-1">
            <h1 className="text-xl font-bold tracking-tight text-white leading-tight">Orbit Control</h1>
            <span className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-widest">v1.0 Live</span>
          </div>
          <button onClick={logout} className="text-slate-500 hover:text-white transition-colors" title="Logout">
             <LogOut className="w-5 h-5" />
          </button>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1">
          <NavItem active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={<Activity className="w-5 h-5"/>} label="Control Tower" />
          <NavItem active={activeTab === 'search'} onClick={() => setActiveTab('search')} icon={<BarChart3 className="w-5 h-5"/>} label="Search Intelligence" />
          <NavItem active={activeTab === 'incidents'} onClick={() => setActiveTab('incidents')} icon={<AlertTriangle className="w-5 h-5"/>} label="Incident War Room" badge="3" />
          <NavItem active={activeTab === 'quarantine'} onClick={() => setActiveTab('quarantine')} icon={<ShieldCheck className="w-5 h-5"/>} label="Quarantine Station" badge="1" alert />
          <NavItem active={activeTab === 'students'} onClick={() => setActiveTab('students')} icon={<Users className="w-5 h-5"/>} label="Identity Matrix" />
        </nav>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 overflow-y-auto p-10 relative scroll-smooth bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-blend-overlay">
        <div className="absolute top-0 right-0 p-32 -z-10 blur-[150px] opacity-20 pointer-events-none rounded-full bg-blue-600 w-[600px] h-[600px]"></div>
        
        {activeTab === 'overview' && <OverviewPanel />}
        {activeTab === 'search' && <SearchIntelligencePanel />}
        {activeTab === 'incidents' && <IncidentsWarRoom />}
        {activeTab === 'quarantine' && <QuarantineInteractive />}
        {activeTab === 'students' && <VerificationShield />}
      </main>
    </div>
  );
}

// ── 1. CONTROL TOWER (Actionable Only) ────────────────────────────────

function OverviewPanel() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [err, setErr] = useState<string>('');

  useEffect(() => {
    let alive = true;
    api.overview()
      .then((o) => alive && setOverview(o))
      .catch((e: any) => alive && setErr(e?.detail || 'Failed to load overview'));
    return () => { alive = false; };
  }, []);

  const healthScore = useMemo(() => {
    if (!overview) return 0;
    const penalty = Math.min(overview.conflicts_total, 10) * 4 + Math.min(overview.quarantine_pending, 10) * 4;
    return Math.max(0, 100 - penalty);
  }, [overview]);
  const healthColor = healthScore > 75 ? 'text-emerald-400' : healthScore > 40 ? 'text-orange-400' : 'text-rose-500';

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-7xl mx-auto">
      <header className="mb-10 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">System Telemetry</h2>
          <p className="text-slate-400 mt-2 text-lg">High-level determinism overview. Scan and react.</p>
        </div>
        <div className="flex items-center gap-4 bg-[#161b22] px-6 py-4 rounded-xl border border-[#30363d] glass-panel">
           <Zap className={`${healthColor} w-8 h-8`} />
           <div>
             <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Health Score</div>
             <div className={`text-4xl font-black ${healthColor}`}>{healthScore}<span className="text-2xl text-slate-600">/100</span></div>
           </div>
        </div>
      </header>

      {/* Actionable Top Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard icon={<AlertTriangle className="w-6 h-6 text-orange-400"/>} title="Active Issues" value={overview ? String(overview.incidents_open) : '—'} subtitle="Require Priority Resolution" />
        <StatCard icon={<ShieldCheck className="w-6 h-6 text-rose-400"/>} title="Sync Failures" value={overview ? String(overview.quarantine_pending) : '—'} subtitle="In Quarantine" />
        <StatCard icon={<Users className="w-6 h-6 text-blue-400"/>} title="Student Directory" value={overview ? String(overview.students_total) : '—'} subtitle="Seeded from SIT CSV" />
        <StatCard icon={<MessageSquareWarning className="w-6 h-6 text-orange-400"/>} title="Identity Conflicts" value={overview ? String(overview.conflicts_total) : '—'} subtitle="Admin must resolve" />
      </div>

      {/* Performance Latency Board */}
      <h3 className="text-xl font-bold text-white mb-4 mt-12 flex items-center gap-2"><HardDrive className="w-5 h-5 text-purple-400"/> Core Performance</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-[#0f1115] border border-[#30363d] rounded-xl flex items-center justify-between">
           <div className="text-slate-400 font-medium">PostgreSQL Latency (p95)</div>
           <div className="text-2xl font-bold text-emerald-400">18ms</div>
        </div>
        <div className="p-6 bg-[#0f1115] border border-[#30363d] rounded-xl flex items-center justify-between">
           <div className="text-slate-400 font-medium">Search Engine Avg</div>
           <div className="text-2xl font-bold text-emerald-400">112ms</div>
        </div>
        <div className="p-6 bg-[#0f1115] border border-[#30363d] rounded-xl flex items-center justify-between group cursor-pointer hover:border-blue-500/50 transition-colors">
           <div className="text-slate-400 font-medium group-hover:text-white transition-colors">Slowest Query</div>
           <div className="text-xl font-mono text-orange-400">890ms</div>
        </div>
      </div>
      {err && <div className="mt-6 text-sm text-rose-400 font-semibold">{err}</div>}
    </div>
  );
}

// ── 2. INCIDENT WAR ROOM (Interactive triage) ─────────────────────────

function IncidentsWarRoom() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [err, setErr] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const refresh = async () => {
    setLoading(true);
    setErr('');
    try {
      setIncidents(await api.incidents());
    } catch (e: any) {
      setErr(e?.detail || 'Failed to load incidents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const setStatus = async (id: string, status: IncidentStatus) => {
    try {
      await api.updateIncident(id, status);
      await refresh();
    } catch (e: any) {
      setErr(e?.detail || 'Failed to update incident');
    }
  };

  return (
    <div className="animate-in fade-in duration-500 max-w-7xl mx-auto">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Incident War Room</h2>
          <p className="text-slate-400">Triage, prioritize, and neutralize student reports.</p>
        </div>
        <div className="flex gap-3">
           <button className="px-4 py-2 border border-[#30363d] rounded bg-[#161b22] text-slate-300 font-medium flex items-center gap-2 hover:bg-[#30363d] transition-colors"><Filter className="w-4 h-4"/> Filter</button>
           <button className="px-4 py-2 bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 rounded font-bold hover:bg-emerald-600/40 transition-colors flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> Bulk Resolve</button>
        </div>
      </header>
      
      <div className="border border-[#30363d] rounded-xl overflow-hidden glass-panel">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#1c212a] text-xs uppercase tracking-wider text-slate-500 border-b border-[#30363d]">
              <th className="px-4 py-4 font-medium w-12 text-center"><input type="checkbox" className="accent-blue-500 bg-transparent border-[#30363d]"/></th>
              <th className="px-6 py-4 font-medium">Ticket</th>
              <th className="px-6 py-4 font-medium">Telegram ID</th>
              <th className="px-6 py-4 font-medium">Category</th>
              <th className="px-6 py-4 font-medium">Context</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Tactics</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#30363d]">
            {loading && (
              <tr><td className="px-6 py-6 text-slate-400" colSpan={7}>Loading…</td></tr>
            )}
            {!loading && incidents.map((inc) => (
              <tr key={inc.id} className="hover:bg-[#30363d]/30 transition-colors group align-top">
                <td className="px-4 py-4 text-center"><input type="checkbox" className="accent-blue-500" /></td>
                <td className="px-6 py-4 font-mono text-sm text-slate-300">{inc.id}</td>
                <td className="px-6 py-4 font-mono text-xs text-slate-400">{inc.telegram_id}</td>
                <td className="px-6 py-4 text-slate-200 font-medium">{inc.category}</td>
                <td className="px-6 py-4">
                  <div className="text-xs text-slate-400">{inc.course_id ? `course: ${inc.course_id}` : 'general'}</div>
                  <div className="text-sm text-slate-200 mt-1 whitespace-pre-wrap">{inc.description}</div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    inc.status === 'OPEN'
                      ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                      : inc.status === 'IN_PROGRESS'
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}>
                    {inc.status}
                  </span>
                </td>
                <td className="px-6 py-4 flex gap-2">
                  {inc.status !== 'IN_PROGRESS' && (
                    <button
                      onClick={() => setStatus(inc.id, 'IN_PROGRESS')}
                      className="text-xs px-3 py-1.5 rounded border border-[#30363d] hover:bg-[#404854] text-white transition-colors"
                    >
                      Start
                    </button>
                  )}
                  {inc.status !== 'RESOLVED' && (
                    <button
                      onClick={() => setStatus(inc.id, 'RESOLVED')}
                      className="text-xs px-3 py-1.5 rounded border border-[#30363d] bg-[#30363d]/50 hover:bg-emerald-500/20 hover:text-emerald-400 transition-colors"
                    >
                      Resolve
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {err && <div className="mt-4 text-sm text-rose-400 font-semibold">{err}</div>}
    </div>
  );
}

// ── 3. QUARANTINE STATION (Interactive Debugging Engine) ──────────────

function QuarantineInteractive() {
  const [items, setItems] = useState<QuarantineItem[]>([]);
  const [err, setErr] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const refresh = async () => {
    setLoading(true);
    setErr('');
    try {
      setItems(await api.quarantine());
    } catch (e: any) {
      setErr(e?.detail || 'Failed to load quarantine list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const mark = async (id: string, status: 'RECOVERED' | 'IGNORED') => {
    try {
      await api.updateQuarantine(id, status);
      await refresh();
    } catch (e: any) {
      setErr(e?.detail || 'Failed to update quarantine');
    }
  };

  return (
    <div className="animate-in fade-in duration-500 max-w-7xl mx-auto">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold text-rose-400 mb-2">Quarantine Debug Engine</h2>
          <p className="text-slate-400">Halt and neutralize filesystem anomalies before DB ingestion.</p>
        </div>
        <button onClick={refresh} className="px-4 py-2 border border-rose-500/30 bg-rose-500/10 text-rose-400 font-bold rounded flex items-center gap-2 hover:bg-rose-500/20 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}/> Refresh
        </button>
      </header>
      
      <div className="flex flex-col gap-4">
        {loading && <div className="text-slate-400">Loading…</div>}
        {!loading && items.length === 0 && (
          <div className="text-emerald-400 font-bold">No pending quarantine items.</div>
        )}
        {!loading && items.map((it) => (
          <div key={it.id} className="p-6 border border-rose-500/30 bg-[#161b22] rounded-xl relative overflow-hidden group">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h4 className="text-lg font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="text-orange-400 w-5 h-5"/> Quarantined File
                </h4>
                <p className="text-sm text-slate-400 mt-1">{it.reason}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => mark(it.id, 'RECOVERED')} className="px-4 py-2 bg-[#30363d] hover:bg-emerald-600 transition-colors text-white text-sm font-medium rounded-lg">Mark Recovered</button>
                <button onClick={() => mark(it.id, 'IGNORED')} className="px-4 py-2 bg-[#30363d] hover:bg-rose-600 transition-colors text-white text-sm font-medium rounded-lg">Ignore</button>
              </div>
            </div>
            <div className="bg-[#0f1115] p-4 rounded-lg border border-rose-500/20">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">File Path</div>
              <code className="text-sm text-rose-400 block break-all font-mono">{it.file_path}</code>
            </div>
          </div>
        ))}
      </div>
      {err && <div className="mt-4 text-sm text-rose-400 font-semibold">{err}</div>}
    </div>
  )
}

// ── 4. IDENTITY MATRIX (Conflict Controls) ────────────────────────────

function VerificationShield() {
  const [query, setQuery] = useState('');
  const [rows, setRows] = useState<StudentRow[]>([]);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(true);

  const refresh = async (q?: string) => {
    setLoading(true);
    setErr('');
    try {
      setRows(await api.students(q));
    } catch (e: any) {
      setErr(e?.detail || 'Failed to load students');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const conflicts = useMemo(() => rows.filter(r => r.is_conflicted), [rows]);
  const linked = useMemo(() => rows.filter(r => !!r.telegram_id), [rows]);

  const unbind = async (r: StudentRow) => {
    try {
      await api.unbind(r.telegram_id || undefined, r.student_id);
      await refresh(query);
    } catch (e: any) {
      setErr(e?.detail || 'Failed to unbind');
    }
  };

  return (
    <div className="animate-in fade-in duration-500 max-w-7xl mx-auto">
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Verification Matrix</h2>
        <p className="text-slate-400">Strict Telegram-to-Institution Identity resolution overrides.</p>
      </header>
      
      <div className="mb-6 relative max-w-2xl">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') refresh(query); }}
            type="text"
            placeholder="Search School ID or student name..."
            className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-4 py-3 pl-12 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors shadow-lg"
          />
          <Search className="absolute left-4 top-3.5 text-slate-500 w-5 h-5" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#30363d] flex items-center justify-between">
            <div className="text-white font-bold">Linked Students</div>
            <div className="text-xs text-slate-500 font-mono">{linked.length}</div>
          </div>
          <div className="p-0">
            {loading && <div className="p-6 text-slate-400">Loading…</div>}
            {!loading && linked.slice(0, 50).map((r) => (
              <div key={r.student_id} className="px-6 py-4 border-t border-[#30363d] flex items-center justify-between">
                <div>
                  <div className="text-white font-mono text-sm">{r.student_id}</div>
                  <div className="text-slate-400 text-sm">{r.full_name}</div>
                  <div className="text-slate-500 text-xs font-mono">telegram: {r.telegram_id}</div>
                </div>
                <button onClick={() => unbind(r)} className="px-4 py-2 rounded bg-orange-500/10 text-orange-400 border border-orange-500/30 hover:bg-orange-500/20 transition-colors text-sm font-bold">Unbind</button>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 overflow-hidden">
          <div className="bg-orange-500/20 px-6 py-3 border-b border-orange-500/30 flex items-center gap-2 justify-between">
            <div className="flex items-center gap-2">
              <MessageSquareWarning className="text-orange-400 w-4 h-4"/>
              <span className="text-orange-400 font-bold text-sm tracking-wide">ACTIVE IDENTITY CONFLICTS</span>
            </div>
            <span className="text-orange-400 font-bold text-sm tracking-wide">{conflicts.length}</span>
          </div>
          <div className="p-0">
            {!loading && conflicts.length === 0 && <div className="p-6 text-emerald-400 font-bold">No conflicts.</div>}
            {!loading && conflicts.slice(0, 50).map((r) => (
              <div key={r.student_id} className="px-6 py-4 border-t border-orange-500/20 flex items-center justify-between">
                <div>
                  <div className="text-white font-mono text-sm">{r.student_id}</div>
                  <div className="text-slate-400 text-sm">{r.full_name}</div>
                  <div className="text-orange-400 text-xs font-mono">conflicted</div>
                </div>
                <button onClick={() => unbind(r)} className="px-4 py-2 rounded bg-orange-500/20 text-orange-400 border border-orange-500/30 hover:bg-orange-500/30 transition-colors text-sm font-bold">Clear/Unbind</button>
              </div>
            ))}
          </div>
        </div>
      </div>
      {err && <div className="mt-4 text-sm text-rose-400 font-semibold">{err}</div>}
    </div>
  )
}

// ── 5. SEARCH INTELLIGENCE (Product Gap Metrics) ──────────────────────

function SearchIntelligencePanel() {
  const [top, setTop] = useState<TelemetryRow[]>([]);
  const [failed, setFailed] = useState<TelemetryRow[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    let alive = true;
    Promise.all([api.telemetryTop(), api.telemetryFailed()])
      .then(([t, f]) => { if (!alive) return; setTop(t); setFailed(f); })
      .catch((e: any) => alive && setErr(e?.detail || 'Failed to load telemetry'));
    return () => { alive = false; };
  }, []);

  return (
    <div className="animate-in fade-in duration-500 max-w-7xl mx-auto">
      <header className="mb-8 flex justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Search Intelligence</h2>
          <p className="text-slate-400">Discover material gaps and user request topologies.</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Top Queries Table */}
        <div className="border border-[#30363d] bg-[#161b22] glass-panel rounded-xl flex flex-col">
          <div className="p-5 border-b border-[#30363d] flex justify-between items-center">
             <h3 className="text-white font-bold flex items-center gap-2"><BarChart3 className="text-blue-400 w-5 h-5"/> Highest Volume Queries</h3>
             <span className="text-xs text-slate-500 font-mono">24h Vol</span>
          </div>
          <div className="p-0 overflow-auto">
             <table className="w-full text-left">
                <tbody className="divide-y divide-[#30363d]">
                  {top.map((r) => (
                    <tr key={r.query} className="hover:bg-[#30363d]/30">
                      <td className="px-5 py-3 text-white font-mono">{r.query}</td>
                      <td className="px-5 py-3 text-blue-400 text-right">{r.count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
             </table>
          </div>
        </div>

        {/* Failed Queries (0 results) */}
        <div className="border border-rose-500/20 bg-[#1a141a] glass-panel rounded-xl flex flex-col relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/10 rounded-full blur-[40px] -z-10"></div>
          <div className="p-5 border-b border-[#30363d] flex justify-between items-center">
             <h3 className="text-rose-400 font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Material Gaps (0 Results)</h3>
             <span className="text-xs text-rose-500/60 font-medium bg-rose-500/10 px-2 py-1 rounded">ACTION REQUIRED</span>
          </div>
          <div className="p-0 overflow-auto z-10">
             <table className="w-full text-left">
                <tbody className="divide-y divide-[#30363d]">
                  {failed.map((r) => (
                    <tr key={r.query} className="bg-rose-500/5 hover:bg-rose-500/10">
                      <td className="px-5 py-3 text-white font-mono text-sm">{r.query}</td>
                      <td className="px-5 py-3 text-rose-400 text-right font-bold tracking-widest text-xs uppercase">{r.count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
             </table>
          </div>
        </div>

      </div>
      {err && <div className="mt-4 text-sm text-rose-400 font-semibold">{err}</div>}
    </div>
  )
}

// ── AUTHENTICATION ──────────────────────────────────────────────────────

function LoginScreen({ onLogin }: { onLogin: (access: string, refresh: string) => void }) {
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      const resp = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        onLogin(data.access_token, data.refresh_token);
      } else {
        const err = await resp.json();
        setError(err.detail || 'Authentication failed');
      }
    } catch (err) {
      setError('Connection to Orbit Backend failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0f1115] text-[#e2e8f0] font-sans antialiased items-center justify-center relative overflow-hidden bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-blend-overlay">
       <div className="absolute top-0 right-0 p-32 -z-10 blur-[150px] opacity-20 pointer-events-none rounded-full bg-blue-600 w-[600px] h-[600px]"></div>
       <div className="absolute bottom-0 left-0 p-32 -z-10 blur-[150px] opacity-10 pointer-events-none rounded-full bg-emerald-600 w-[600px] h-[600px]"></div>
       
       <form onSubmit={handleLogin} className="glass-panel border border-[#30363d] bg-[#161b22]/90 p-10 rounded-2xl w-full max-w-md shadow-2xl relative z-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex justify-center mb-6">
             <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-full shadow-[0_0_50px_rgba(59,130,246,0.3)]">
               <Lock className="w-10 h-10 text-blue-400" />
             </div>
          </div>
          <h2 className="text-3xl font-black text-center text-white mb-2 tracking-tight">System Access</h2>
          <p className="text-center text-slate-400 mb-8 font-medium">Academic Hub Orbit Governance</p>
          
          <div className="space-y-4">
            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-rose-400 text-xs font-bold animate-pulse">
                ⚠️ {error}
              </div>
            )}
            <div>
               <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Admin Identification</label>
               <input 
                 autoFocus required type="text" 
                 value={username} onChange={(e) => setUsername(e.target.value)}
                 placeholder="e.g. astrosol_root" 
                 className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors" 
               />
            </div>
            <div>
               <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Security Token</label>
               <input 
                 required type="password" 
                 value={password} onChange={(e) => setPassword(e.target.value)}
                 placeholder="••••••••••••" 
                 className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors" 
               />
            </div>
            <button disabled={loading} type="submit" className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg transition-all active:scale-95 flex items-center justify-center gap-2">
               {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : "Authenticate Identity"}
            </button>
          </div>
          
          <div className="mt-8 pt-6 border-t border-[#30363d] text-center text-xs text-slate-500 font-mono">
            Requires Tier 3 Clearance.
          </div>
       </form>
    </div>
  );
}

// ---- Sub Components ---- //

function NavItem({ active, icon, label, onClick, badge, alert }: any) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 relative ${active ? 'bg-[#30363d]/50 text-white border border-[#30363d] shadow-inner' : 'text-slate-400 hover:text-white hover:bg-[#30363d]/30 border border-transparent'}`}
    >
      <div className={`${active ? 'text-blue-400' : ''}`}>{icon}</div>
      <span className="flex-1 text-left">{label}</span>
      {badge && <span className={`px-2 py-0.5 rounded text-[10px] font-black ${alert ? 'bg-rose-500 text-white' : 'bg-blue-600 text-white'}`}>{badge}</span>}
    </button>
  );
}

function StatCard({ icon, title, value, subtitle }: any) {
  return (
    <div className="p-6 rounded-xl border border-[#30363d] glass-panel bg-[#161b22] hover:border-slate-500/60 transition-colors shadow-lg">
      <div className="flex items-center gap-4 mb-3">
        <div className="p-2.5 bg-[#0f1115] rounded-lg border border-[#30363d] shadow-inner">{icon}</div>
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">{title}</h4>
      </div>
      <div className="text-3xl font-black text-white tracking-tight leading-none mb-2">{value}</div>
      <div className="text-xs font-semibold text-slate-500">{subtitle}</div>
    </div>
  );
}
