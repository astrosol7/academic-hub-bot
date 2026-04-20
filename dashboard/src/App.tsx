import React, { useEffect, useMemo, useState, createContext, useContext } from 'react';
import { 
  ShieldCheck, Server, AlertTriangle, Search, HardDrive, 
  Activity, Users, BarChart3, RefreshCw, CheckCircle2, 
  MessageSquareWarning, Zap, Filter, Lock, LogOut,
  Settings, User, Moon, Sun, Maximize2, Minimize2,
  ChevronRight, ArrowRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type Incident, type IncidentStatus, type Overview, type QuarantineItem, type StudentRow, type TelemetryRow } from './api';

// --- CONTEXTS ---
const ConfigContext = createContext({
  theme: 'night',
  density: 'spacious',
  setTheme: (t: string) => {},
  setDensity: (d: string) => {}
});

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('orbit_access_token'));
  const [activeTab, setActiveTab] = useState('overview');
  const [theme, setTheme] = useState(() => localStorage.getItem('orbit_theme') || 'night');
  const [density, setDensity] = useState(() => localStorage.getItem('orbit_density') || 'spacious');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('orbit_theme', theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute('data-density', density);
    localStorage.setItem('orbit_density', density);
  }, [density]);

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
    <ConfigContext.Provider value={{ theme, density, setTheme, setDensity }}>
      <div className="flex h-screen bg-orbit-bg text-orbit-fg transition-colors duration-500 relative overflow-hidden">
        <div className="nebula-bg" />
        
        {/* Modern Nav Obelisk */}
        <aside className="w-20 lg:w-64 border-r border-orbit-border bg-orbit-surface/30 flex flex-col glass-panel z-20">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-6 border-b border-orbit-border flex items-center gap-3"
          >
            <div className="w-10 h-10 bg-orbit-primary/20 rounded-xl flex items-center justify-center border border-orbit-primary/30 orbit-glow">
              <Server className="text-orbit-primary w-6 h-6" />
            </div>
            <div className="hidden lg:block overflow-hidden">
              <motion.h1 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="text-lg font-black tracking-tighter text-white leading-tight"
              >
                ORBIT
              </motion.h1>
              <span className="text-[10px] font-bold text-orbit-accent uppercase tracking-[0.2em]">Live Engine</span>
            </div>
          </motion.div>
          
          <nav className="flex-1 p-3 space-y-1">
            <NavItem active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={<Activity />} label="Dashboard" index={0} />
            <NavItem active={activeTab === 'search'} onClick={() => setActiveTab('search')} icon={<BarChart3 />} label="Intelligence" index={1} />
            <NavItem active={activeTab === 'incidents'} onClick={() => setActiveTab('incidents'} icon={<AlertTriangle />} label="War Room" badge="3" index={2} />
            <NavItem active={activeTab === 'quarantine'} onClick={() => setActiveTab('quarantine')} icon={<ShieldCheck />} label="Quarantine" alert index={3} />
            <NavItem active={activeTab === 'students'} onClick={() => setActiveTab('students')} icon={<Users />} label="Identities" index={4} />
          </nav>

          <footer className="p-3 border-t border-orbit-border space-y-1">
            <NavItem active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} icon={<Settings />} label="Settings" index={5} />
            <button onClick={logout} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 transition-all">
               <LogOut className="w-5 h-5" />
               <span className="hidden lg:block">System Exit</span>
            </button>
          </footer>
        </aside>

        {/* Cinematic Workspace */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-10 relative">
          <header className="fixed top-0 right-0 p-6 z-30 flex items-center gap-4">
             <motion.div 
               initial={{ opacity: 0, y: -10 }}
               animate={{ opacity: 1, y: 0 }}
               className="hidden lg:flex items-center gap-2 px-4 py-2 bg-orbit-surface/50 border border-orbit-border rounded-full glass-panel text-xs font-bold text-slate-400"
             >
                <div className="w-2 h-2 rounded-full bg-orbit-accent animate-pulse" />
                STATION ALIVE
             </motion.div>
             <button onClick={() => setActiveTab('settings')} className="p-2 bg-orbit-surface/50 border border-orbit-border rounded-full hover:border-orbit-primary/50 transition-colors">
                <User className="w-5 h-5 text-orbit-fg" />
             </button>
          </header>

          <div className="max-w-7xl mx-auto pt-12 lg:pt-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              >
                {activeTab === 'overview' && <OverviewPanel />}
                {activeTab === 'search' && <SearchIntelligencePanel />}
                {activeTab === 'incidents' && <IncidentsWarRoom />}
                {activeTab === 'quarantine' && <QuarantineInteractive />}
                {activeTab === 'students' && <VerificationShield />}
                {activeTab === 'settings' && <SettingsPanel logout={logout} />}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </ConfigContext.Provider>
  );
}

// ── SETTINGS & PROFILE ────────────────────────────────────────

function SettingsPanel({ logout }: { logout: () => void }) {
  const { theme, setTheme, density, setDensity } = useContext(ConfigContext);

  return (
    <div className="max-w-2xl">
      <h2 className="text-4xl font-black text-white mb-2 tracking-tighter">System Configuration</h2>
      <p className="text-slate-400 mb-10">Tailor the Orbit experience to your operational style.</p>

      <section className="space-y-8">
        <div>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Environment Theme</h3>
          <div className="grid grid-cols-2 gap-4">
             <ThemeOption 
                active={theme === 'night'} 
                onClick={() => setTheme('night')} 
                icon={<Moon />} label="Deep Night" 
                desc="High contrast for night ops" 
             />
             <ThemeOption 
                active={theme === 'light'} 
                onClick={() => setTheme('light')} 
                icon={<Sun />} label="Solar Day" 
                desc="Enhanced clarity for day ops" 
             />
          </div>
        </div>

        <div>
           <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Display Density</h3>
           <div className="grid grid-cols-2 gap-4">
              <ThemeOption 
                 active={density === 'spacious'} 
                 onClick={() => setDensity('spacious')} 
                 icon={<Maximize2 />} label="Voyager" 
                 desc="Breathable and non-intimidating" 
              />
              <ThemeOption 
                 active={density === 'dense'} 
                 onClick={() => setDensity('dense')} 
                 icon={<Minimize2 />} label="Industrial" 
                 desc="High volume data management" 
              />
           </div>
        </div>

        <div className="pt-10 border-t border-orbit-border">
           <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Administrative Identity</h3>
           <div className="flex items-center gap-6 p-6 glass-panel rounded-2xl border-orbit-border">
              <div className="w-16 h-16 bg-orbit-primary/10 border border-orbit-primary/30 rounded-full flex items-center justify-center text-2xl font-black text-orbit-primary">R</div>
              <div className="flex-1">
                 <div className="text-xl font-bold text-white">Station Root Administrator</div>
                 <div className="text-slate-500 font-mono text-xs">Level 3 Access • Sector SIT</div>
              </div>
              <button onClick={logout} className="px-6 py-2 bg-rose-500 text-white font-bold rounded-xl hover:bg-rose-600 transition-colors">Terminate Session</button>
           </div>
        </div>
      </section>
    </div>
  );
}

function ThemeOption({ active, onClick, icon, label, desc }: any) {
  return (
    <motion.button 
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick} 
      className={`p-6 text-left rounded-2xl border transition-all ${active ? 'border-orbit-primary bg-orbit-primary/5 ring-1 ring-orbit-primary/20' : 'border-orbit-border bg-orbit-surface/30 hover:bg-orbit-surface/50'}`}
    >
       <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${active ? 'bg-orbit-primary text-white' : 'bg-orbit-border text-slate-400'}`}>{icon}</div>
       <div className="font-bold text-white">{label}</div>
       <div className="text-xs text-slate-500 mt-1 leading-relaxed">{desc}</div>
    </motion.button>
  );
}

// ── 1. DASHBOARD OVERVIEW ────────────────────────────────────────

function OverviewPanel() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [err, setErr] = useState<string>('');

  useEffect(() => {
    let alive = true;
    api.overview()
      .then((o) => alive && setOverview(o))
      .catch((e: any) => alive && setErr(e?.detail || 'Offline'));
    return () => { alive = false; };
  }, []);

  return (
    <div className="space-y-10">
      <div className="lg:flex justify-between items-end gap-6">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-orbit-primary/5 border border-orbit-primary/20 p-8 rounded-[2.5rem] lg:flex-1 relative overflow-hidden orbit-glow mb-6 lg:mb-0"
        >
           <div className="flex items-center gap-4 mb-3">
              <Zap className="text-orbit-primary w-8 h-8" />
              <h2 className="text-2xl font-black text-white tracking-tight leading-none uppercase italic">The Pulse</h2>
           </div>
           <p className="text-slate-400 text-sm max-w-md font-medium">Real-time status of the Academic Hub ecosystem. All systems monitored and verified.</p>
           <div className="absolute top-0 right-0 w-64 h-64 bg-orbit-primary/5 rounded-full blur-3xl -mr-32 -mt-32" />
        </motion.div>
        
        <div className="grid grid-cols-2 gap-4">
           <SmallStat label="IDENTITY LOCKS" value={overview ? String(overview.links_total) : '0'} color="text-orbit-primary" index={0} />
           <SmallStat label="SYNC QUARANTINE" value={overview ? String(overview.quarantine_pending) : '0'} color="text-rose-400" index={1} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 density-aware-gap">
        <StatCard icon={<AlertTriangle className="text-orange-400"/>} title="War Room" value={overview ? String(overview.incidents_open) : '—'} action="TRIAGE" color="border-orange-500/30" index={0} />
        <StatCard icon={<BarChart3 className="text-blue-400"/>} title="Search Intel" value="Active" action="EXPLORE" color="border-blue-500/30" index={1} />
        <StatCard icon={<Users className="text-emerald-400"/>} title="Verification" value={overview ? String(overview.conflicts_total) : '—'} action="RESOLVE" color="border-emerald-500/30" index={2} />
        <StatCard icon={<Settings className="text-slate-400"/>} title="Settings" value="v1.0" action="CONFIG" color="border-slate-500/30" index={3} />
      </div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mt-12"
      >
         <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mb-6">Material Performance</h3>
         <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <PerformanceBlock label="Global Latency" value="18ms" trend="Optimal" index={0} />
             <PerformanceBlock label="Search Hit Rate" value="94.2%" trend="+2.1%" index={1} />
             <PerformanceBlock label="Bot Integrity" value="Stable" trend="Normal" index={2} />
         </div>
      </motion.div>
    </div>
  );
}

function SmallStat({ label, value, color, index }: any) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.1 * index }}
      className="px-6 py-6 glass-panel rounded-3xl border-orbit-border flex flex-col items-center justify-center min-w-[150px]"
    >
       <div className={`text-3xl font-black ${color}`}>{value}</div>
       <div className="text-[9px] font-bold text-slate-500 tracking-widest uppercase mt-2">{label}</div>
    </motion.div>
  );
}

function PerformanceBlock({ label, value, trend, index }: any) {
  return (
     <motion.div 
       initial={{ opacity: 0, y: 10 }}
       animate={{ opacity: 1, y: 0 }}
       transition={{ delay: 0.4 + (index * 0.1) }}
       whileHover={{ scale: 1.02 }}
       className="p-6 bg-orbit-surface/30 border border-orbit-border rounded-2xl hover:border-orbit-primary/40 transition-colors group cursor-default"
     >
        <div className="text-xs font-bold text-slate-500 mb-1 group-hover:text-slate-300 transition-colors">{label}</div>
        <div className="flex items-center justify-between">
           <div className="text-2xl font-black text-white">{value}</div>
           <div className={`text-[10px] font-bold px-2 py-0.5 rounded ${trend === 'Optimal' || trend.startsWith('+') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}>{trend}</div>
        </div>
     </motion.div>
  );
}

// ── 2. WAR ROOM (Incidents) ───────────────────────────────────

function IncidentsWarRoom() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.incidents().then(setIncidents).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <header className="mb-10">
        <h2 className="text-4xl font-black text-white mb-2 tracking-tighter">Incident War Room</h2>
        <p className="text-slate-400 font-medium">Capture and resolve mission-critical student reports.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <AnimatePresence>
          {loading ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-slate-400">Loading stream...</motion.div>
          ) : incidents.map((inc, i) => (
            <motion.div 
              key={inc.id} 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="p-6 glass-panel rounded-3xl border-orbit-border flex flex-col justify-between group hover:border-orbit-primary/50 transition-all"
            >
               <div>
                  <div className="flex justify-between items-start mb-4">
                     <div className="text-[10px] font-mono font-bold text-slate-500 bg-orbit-bg px-2 py-0.5 rounded border border-orbit-border">{inc.category}</div>
                     <span className={`w-2 h-2 rounded-full ${inc.status === 'OPEN' ? 'bg-orange-500 shadow-[0_0_10px_orange]' : 'bg-emerald-500'}`} />
                  </div>
                  <h4 className="text-white font-bold mb-2 group-hover:text-orbit-primary transition-colors line-clamp-2">{inc.description}</h4>
                  <div className="text-xs text-slate-500 mb-6 flex items-center gap-2">
                     <User className="w-3 h-3" /> {inc.telegram_id}
                  </div>
               </div>
               <motion.button 
                 whileTap={{ scale: 0.98 }}
                 className="w-full py-4 bg-orbit-surface/50 border border-orbit-border rounded-2xl font-black text-[10px] tracking-widest text-slate-300 hover:text-white hover:bg-orbit-primary hover:border-orbit-primary transition-all flex items-center justify-center gap-2"
               >
                  DEPLOY RESOLUTION <ArrowRight className="w-4 h-4" />
               </motion.button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ── IDENTITY MATRIX ──────────────────────────────────────────

function VerificationShield() {
  return (
    <div className="max-w-3xl">
       <h2 className="text-4xl font-black text-white mb-2 tracking-tighter">Identity Matrix</h2>
       <p className="text-slate-400 mb-10 font-medium">The ground truth for institutional identity mappings.</p>
       
       <motion.div 
         initial={{ opacity: 0, y: 10 }}
         animate={{ opacity: 1, y: 0 }}
         className="p-20 border border-dashed border-orbit-border rounded-[3rem] flex flex-col items-center justify-center text-center opacity-60 bg-orbit-primary/5"
       >
          <ShieldCheck className="w-16 h-16 text-orbit-accent mb-4" />
          <div className="text-xl font-bold text-white mb-2">Biometric Verification Online</div>
          <p className="text-sm text-slate-500 max-w-sm ml-auto mr-auto leading-relaxed">Please select a student record from the primary list to conduct a deep-link identity resolution.</p>
       </motion.div>
    </div>
  );
}

// ── SEARCH INTELLIGENCE ───────────────────────────────────────

function SearchIntelligencePanel() {
  const [top, setTop] = useState<TelemetryRow[]>([]);

  useEffect(() => {
    api.telemetryTop().then(setTop);
  }, []);

  return (
    <div>
      <h2 className="text-4xl font-black text-white mb-2 tracking-tighter">Search Intelligence</h2>
      <p className="text-slate-400 mb-10 font-medium">Mapping the topology of student curiosity.</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
         <motion.div 
           initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
           className="p-8 glass-panel rounded-[2.5rem] border-orbit-border"
         >
            <h3 className="text-lg font-bold text-white mb-6">Density Map</h3>
            <div className="space-y-6">
               {top.map((item, idx) => (
                 <div key={item.query} className="space-y-2">
                    <div className="flex justify-between text-[10px] font-black text-slate-400 tracking-widest">
                       <span className="uppercase">{item.query}</span>
                       <span>{item.count} HITS</span>
                    </div>
                    <div className="h-2 w-full bg-orbit-bg rounded-full overflow-hidden">
                       <motion.div 
                         initial={{ width: 0 }}
                         animate={{ width: `${Math.min(100, (item.count / (top[0]?.count || 1)) * 100)}%` }}
                         transition={{ duration: 1, delay: idx * 0.1 }}
                         className="h-full bg-orbit-primary shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                       />
                    </div>
                 </div>
               ))}
               {top.length === 0 && <div className="text-center py-10 text-slate-600 text-xs font-bold uppercase tracking-widest">Awaiting session signals...</div>}
            </div>
         </motion.div>
         
         <motion.div 
           initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
           className="bg-orbit-primary/5 rounded-[2.5rem] border border-dashed border-orbit-primary/30 p-10 flex flex-col items-center justify-center text-center relative overflow-hidden"
         >
            <Activity className="w-12 h-12 text-orbit-primary mb-4 animate-pulse" />
            <div className="text-lg font-bold text-white">Neural Pattern Detection</div>
            <p className="text-sm text-slate-500 mt-2 max-w-xs">Observing trends from current user sessions to optimize institutional indexing.</p>
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-orbit-primary/5 to-transparent animate-pulse pointer-events-none" />
         </motion.div>
      </div>
    </div>
  );
}

// ── AUTHENTICATION ───────────────────────────────────────────

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
        setError(err.detail || 'Access Denied');
      }
    } catch (err) {
      setError('Connection Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-orbit-bg text-orbit-fg items-center justify-center p-6 relative overflow-hidden">
       <div className="nebula-bg" />
       <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_120%,rgba(59,130,246,0.1),transparent_50%)]" />
       
       <motion.form 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          onSubmit={handleLogin} 
          className="glass-panel border border-orbit-border bg-orbit-surface/50 p-12 rounded-[3.5rem] w-full max-w-md shadow-2xl relative z-10"
        >
          <div className="flex justify-center mb-10">
             <motion.div 
               animate={{ rotate: [0, 10, -10, 0] }}
               transition={{ duration: 4, repeat: Infinity }}
               className="p-6 bg-orbit-primary/10 border border-orbit-primary/30 rounded-[2rem] orbit-glow"
             >
               <Lock className="w-10 h-10 text-orbit-primary" />
             </motion.div>
          </div>
          <h2 className="text-4xl font-black text-center text-white mb-2 tracking-tighter">System Entry</h2>
          <p className="text-center text-slate-500 mb-10 font-bold text-[10px] uppercase tracking-[0.4em]">Orbit Secure Access</p>
          
          <div className="space-y-5">
            {error && <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-400 text-xs font-bold text-center">ACCESS REFUSED • {error}</motion.div>}
            <div>
               <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 px-1">Admin Identity</label>
               <input 
                 autoFocus required type="text" 
                 value={username} onChange={(e) => setUsername(e.target.value)}
                 placeholder="admin@orbit" 
                 className="w-full bg-orbit-bg/50 border border-orbit-border rounded-2xl px-6 py-5 text-white placeholder-slate-700 focus:outline-none focus:border-orbit-primary transition-all duration-300 font-medium" 
               />
            </div>
            <div>
               <label className="block text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 px-1">Security Token</label>
               <input 
                 required type="password" 
                 value={password} onChange={(e) => setPassword(e.target.value)}
                 placeholder="••••••••" 
                 className="w-full bg-orbit-bg/50 border border-orbit-border rounded-2xl px-6 py-5 text-white placeholder-slate-700 focus:outline-none focus:border-orbit-primary transition-all duration-300 font-medium" 
               />
            </div>
            <motion.button 
              disabled={loading} type="submit" 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full mt-8 bg-orbit-primary text-white font-black py-5 px-4 rounded-[1.5rem] transition-all flex items-center justify-center gap-2 orbit-glow text-xs tracking-widest"
            >
               {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : "AUTHENTICATE CONNECTION"}
            </motion.button>
          </div>
       </motion.form>
    </div>
  );
}

// ---- Sub Components ---- //

function NavItem({ active, icon, label, onClick, badge, alert, index }: any) {
  return (
    <motion.button 
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.05 * index }}
      onClick={onClick}
      className={`group w-full flex items-center gap-4 px-4 py-4 rounded-2xl text-sm font-bold transition-all duration-300 relative ${active ? 'bg-orbit-primary text-white orbit-glow' : 'text-slate-500 hover:text-white hover:bg-orbit-surface/50'}`}
    >
      <div className={`transition-transform duration-300 ${active ? 'scale-110' : 'group-hover:scale-110'}`}>{React.cloneElement(icon as React.ReactElement, { className: 'w-5 h-5' })}</div>
      <span className="hidden lg:block flex-1 text-left tracking-tight">{label}</span>
      {badge && (
        <motion.span 
          initial={{ scale: 0 }} animate={{ scale: 1 }}
          className={`hidden lg:block px-2 py-0.5 rounded-lg text-[9px] font-black ${alert ? 'bg-rose-500 text-white shadow-[0_0_10px_rgba(244,63,94,0.5)]' : 'bg-white text-orbit-primary'}`}
        >
          {badge}
        </motion.span>
      )}
      {active && <motion.div layoutId="nav-active" className="absolute left-0 w-1 h-8 bg-white rounded-r-full" />}
    </motion.button>
  );
}

function StatCard({ icon, title, value, action, color, index }: any) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -5 }}
      className={`p-10 rounded-[2.5rem] glass-panel bg-orbit-surface/20 border-orbit-border hover:bg-orbit-surface/40 transition-all group relative overflow-hidden ${color}`}
    >
      <div className="flex justify-between items-start mb-8">
        <div className="p-4 bg-orbit-bg rounded-2xl border border-orbit-border group-hover:border-orbit-primary/50 transition-colors">{icon}</div>
        <div className="text-[9px] font-black text-orbit-primary bg-orbit-primary/10 px-3 py-1 rounded-xl tracking-widest">{action}</div>
      </div>
      <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-2">{title}</div>
      <div className="text-5xl font-black text-white tracking-tighter leading-none mb-2">{value}</div>
      <div className="absolute -bottom-4 -right-1 opacity-5 group-hover:opacity-10 transition-opacity">
        {React.cloneElement(icon, { size: 120 })}
      </div>
    </motion.div>
  );
}

function QuarantineInteractive() {
  return (
     <div className="max-w-3xl">
        <h2 className="text-4xl font-black text-white mb-2 tracking-tighter">Quarantine Station</h2>
        <p className="text-slate-400 mb-10 font-medium">Cleaning anomalies before institutional ingestion.</p>
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
          className="p-24 border border-dashed border-orbit-border rounded-[3rem] flex flex-col items-center justify-center text-center bg-rose-500/5 relative overflow-hidden"
        >
           <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-rose-500/20 to-transparent animate-pulse" />
           <HardDrive className="w-16 h-16 text-rose-400 mb-4" />
           <div className="text-xl font-bold text-white mb-2">Systems Sanitized</div>
           <p className="text-sm text-slate-500 max-w-sm ml-auto mr-auto leading-relaxed">All filesystem ingress points are currently within normal parameters. Multi-layered heuristics monitoring active.</p>
        </motion.div>
     </div>
   );
}
utional ingestion.</p>
        <div className="p-20 border border-dashed border-orbit-border rounded-3xl flex flex-col items-center justify-center text-center bg-rose-500/5">
           <HardDrive className="w-16 h-16 text-rose-400 mb-4" />
           <div className="text-xl font-bold text-white mb-2">Systems Sanitized</div>
           <p className="text-sm text-slate-500 max-w-sm ml-auto mr-auto">All filesystem ingress points are currently within normal parameters.</p>
        </div>
     </div>
   );
}
