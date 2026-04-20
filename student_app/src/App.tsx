import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { 
  Search, BookOpen, GraduationCap, User, Globe, 
  ChevronRight, ArrowLeft, Loader2, ShieldCheck,
  LayoutGrid, Clock, Star, Sparkles, LogIn, Download,
  TrendingUp, Award, Zap, Eye, Heart, Share2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type Institution, type Course, type SearchResult, type MaterialCategory } from './api';
import './styles.css';

// --- MOCK TMA FOR DEV ---
const isTMA = () => !!(window as any).Telegram?.WebApp?.initData;

export default function App() {
  const [view, setView] = useState<'home' | 'browse' | 'search' | 'profile'>('home');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [studentName, setStudentName] = useState('Guest Voyager');
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedSchool, setSelectedSchool] = useState<Institution | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [downloadHistory, setDownloadHistory] = useState<any[]>([]);
  const searchTimeoutRef = useRef<NodeJS.Timeout>();

  // 1. Identity Gateway (The Bot-Auth Flow)
  useEffect(() => {
    const tma = (window as any).Telegram?.WebApp;
    if (tma && tma.initData) {
      tma.ready();
      tma.expand();
      // Enable haptic feedback
      tma.HapticFeedback.impactOccurred('medium');
      api.loginWithTelegram(tma.initData)
        .then(data => {
          localStorage.setItem('voyager_token', data.access_token);
          setIsAuthenticated(true);
          setStudentName(tma.initDataUnsafe?.user?.first_name || 'Voyager');
          tma.HapticFeedback.notificationOccurred('success');
        })
        .catch(() => {
          tma.HapticFeedback.notificationOccurred('error');
        });
    }
    
    // Load cached data
    const cachedFavorites = localStorage.getItem('voyager_favorites');
    const cachedRecent = localStorage.getItem('voyager_recent_searches');
    const cachedHistory = localStorage.getItem('voyager_download_history');
    
    if (cachedFavorites) setFavorites(JSON.parse(cachedFavorites));
    if (cachedRecent) setRecentSearches(JSON.parse(cachedRecent));
    if (cachedHistory) setDownloadHistory(JSON.parse(cachedHistory));
    
    api.getInstitutions().then(setInstitutions).catch(console.error);
  }, []);

  // Debounced search with caching
  const handleSearch = useCallback(async (q: string) => {
    setSearchQuery(q);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (q.length < 2) { 
      setResults([]); 
      return; 
    }
    
    searchTimeoutRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.search(q);
        setResults(res);
        
        // Add to recent searches
        setRecentSearches(prev => {
          const updated = [q, ...prev.filter(item => item !== q)].slice(0, 5);
          localStorage.setItem('voyager_recent_searches', JSON.stringify(updated));
          return updated;
        });
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }, 300);
  }, []);

  const toggleFavorite = useCallback((resourceId: string) => {
    setFavorites(prev => {
      const updated = prev.includes(resourceId) 
        ? prev.filter(id => id !== resourceId)
        : [...prev, resourceId];
      localStorage.setItem('voyager_favorites', JSON.stringify(updated));
      return updated;
    });
    
    // Haptic feedback
    const tma = (window as any).Telegram?.WebApp;
    if (tma?.HapticFeedback) {
      tma.HapticFeedback.impactOccurred('light');
    }
  }, []);

  const addToDownloadHistory = useCallback((resource: any) => {
    const entry = {
      id: Date.now(),
      resource_id: resource.resource_id,
      title: resource.title,
      timestamp: new Date().toISOString(),
      course_id: resource.course_id
    };
    
    setDownloadHistory(prev => {
      const updated = [entry, ...prev].slice(0, 20);
      localStorage.setItem('voyager_download_history', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const handleSelectSchool = async (inst: Institution) => {
    setSelectedSchool(inst);
    setLoading(true);
    setView('browse');
    try {
      const data = await api.getCourses(inst.slug);
      setCourses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-orbit-bg text-orbit-fg pb-24 selection:bg-orbit-primary/30 relative overflow-x-hidden">
      <div className="nebula" />
      
      {/* Dynamic Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 safe-area-spacing"
      >
         <div className="flex justify-between items-center mb-2">
            <div>
               <h1 className="text-2xl font-black text-white tracking-tighter flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-orbit-primary" />
                  VOYAGER
               </h1>
               <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Sector SIT • Academic Hub</p>
            </div>
            <motion.button 
              whileTap={{ scale: 0.9 }}
              onClick={() => setView('profile')} 
              className="w-12 h-12 bg-orbit-surface/50 border border-orbit-border rounded-full flex items-center justify-center glass-panel shadow-lg"
            >
               <User className="w-5 h-5 text-orbit-fg" />
            </motion.button>
         </div>
      </motion.header>

      {/* Main Command Deck */}
      <main className="px-6 space-y-8">
        
        {/* Search Pulse */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="relative group"
        >
           <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-5 h-5 group-focus-within:text-orbit-primary transition-colors" />
           <input 
             type="text" 
             placeholder="Search books, exams, lectures..."
             value={searchQuery}
             onChange={(e) => { 
               if (view !== 'search') setView('search'); 
               handleSearch(e.target.value); 
             }}
             className="w-full bg-orbit-surface/50 border border-orbit-border rounded-[1.5rem] px-12 py-5 glass-panel focus:outline-none focus:border-orbit-primary/50 transition-all text-sm font-medium shadow-xl"
           />
        </motion.div>

        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          >
            {view === 'home' && (
              <HomeScreen onSelectSchool={handleSelectSchool} institutions={institutions} studentName={studentName} />
            )}

            {view === 'search' && (
              <SearchScreen 
                results={results} 
                loading={loading} 
                query={searchQuery} 
                onBack={() => setView('home')}
                favorites={favorites}
                toggleFavorite={toggleFavorite}
                addToDownloadHistory={addToDownloadHistory}
                recentSearches={recentSearches}
                onSearch={handleSearch}
              />
            )}

            {view === 'browse' && (
              <BrowseScreen school={selectedSchool} courses={courses} loading={loading} onBack={() => setView('home')} />
            )}

            {view === 'profile' && (
              <ProfileScreen studentName={studentName} isAuthenticated={isAuthenticated} onBack={() => setView('home')} />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Custom Bottom Nav (Mini App Aesthetic) */}
      <motion.nav 
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        className="fixed bottom-0 left-0 w-full glass-panel border-t border-orbit-border px-8 py-5 flex justify-between items-center z-50 rounded-t-[2.5rem] shadow-[0_-10px_30px_rgba(0,0,0,0.5)]"
      >
         <NavIconButton active={view === 'home'} onClick={() => setView('home')} icon={<Globe />} />
         <NavIconButton active={view === 'browse'} onClick={() => setView('browse')} icon={<LayoutGrid />} />
         <NavIconButton active={view === 'search'} onClick={() => setView('search')} icon={<Search />} />
         <NavIconButton active={view === 'profile'} onClick={() => setView('profile')} icon={<User />} />
      </motion.nav>
    </div>
  );
}

// ── SCREENS ──────────────────────────────────────────────────

function HomeScreen({ onSelectSchool, institutions, studentName }: any) {
  return (
    <div className="space-y-10">
       <motion.div 
         initial={{ scale: 0.9, opacity: 0 }}
         animate={{ scale: 1, opacity: 1 }}
         className="bg-orbit-primary/10 border border-orbit-primary/20 p-8 rounded-[2.5rem] relative overflow-hidden orbit-glow"
       >
          <motion.h2 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="text-2xl font-black text-white mb-2"
          >
            Welcome, {studentName}
          </motion.h2>
          <p className="text-sm text-slate-400 max-w-[220px] font-medium leading-relaxed">Access SIT resources through the dual-link intelligent portal.</p>
          <BookOpen className="absolute -right-6 -bottom-6 w-32 h-32 text-orbit-primary/5 -rotate-12" />
          <motion.div 
            animate={{ scale: [1, 1.2, 1], opacity: [0.1, 0.2, 0.1] }}
            transition={{ duration: 4, repeat: Infinity }}
            className="absolute top-0 right-0 w-32 h-32 bg-orbit-primary/20 rounded-full blur-3xl"
          />
       </motion.div>

       <div className="space-y-4">
          <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] px-1">Select Institution</h3>
          <div className="grid grid-cols-1 gap-4">
             {institutions.map((inst: any, idx: number) => (
                <motion.button 
                  key={inst.id} 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + (idx * 0.1) }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onSelectSchool(inst)} 
                  className="p-6 flex items-center justify-between glass-panel rounded-3xl border-orbit-border hover:border-orbit-primary/30 transition-all group"
                >
                   <div className="flex items-center gap-5">
                      <div className="w-12 h-12 bg-orbit-surface rounded-2xl flex items-center justify-center border border-orbit-border shadow-inner">
                         <GraduationCap className="text-orbit-primary w-6 h-6" />
                      </div>
                      <div className="text-left">
                         <div className="text-base font-bold text-white group-hover:text-orbit-primary transition-colors">{inst.name}</div>
                         <div className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{inst.slug}</div>
                      </div>
                   </div>
                   <ChevronRight className="w-5 h-5 text-slate-700 group-hover:text-orbit-primary transition-colors" />
                </motion.button>
             ))}
          </div>
       </div>
    </div>
  );
}

function SearchScreen({ results, loading, query, onBack, favorites, toggleFavorite, addToDownloadHistory, recentSearches, onSearch }: any) {
  const handleResourceAction = (resource: any, action: 'open' | 'favorite') => {
    if (action === 'favorite') {
      toggleFavorite(resource.resource_id);
    } else {
      addToDownloadHistory(resource);
      const tma = (window as any).Telegram?.WebApp;
      if (tma?.HapticFeedback) {
        tma.HapticFeedback.notificationOccurred('success');
      }
    }
  };

  return (
    <div className="space-y-8">
       <div className="flex items-center gap-3">
          <motion.button whileTap={{ scale: 0.8 }} onClick={onBack} className="p-2 -ml-2 text-slate-500"><ArrowLeft className="w-5 h-5" /></motion.button>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest leading-none">Intelligence Stream</h3>
       </div>

       {/* Recent Searches */}
       {!query && recentSearches.length > 0 && (
         <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">Memory Cache</h4>
            <div className="flex flex-wrap gap-2">
               {recentSearches.map((term, index) => (
                  <motion.button
                    key={index}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onSearch(term)}
                    className="px-4 py-2 text-xs font-bold glass-panel bg-orbit-surface/30 rounded-full border-orbit-border hover:border-orbit-primary/30 transition-all text-slate-400"
                  >
                     {term}
                  </motion.button>
               ))}
            </div>
         </motion.div>
       )}

       {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
             <motion.div 
               animate={{ rotate: 360 }}
               transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
               className="mb-4"
             >
                <Loader2 className="w-10 h-10 text-orbit-primary" />
             </motion.div>
             <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Querying Orbit...</div>
          </div>
       ) : results.length === 0 && query ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            className="text-center py-20"
          >
             <Search className="w-16 h-16 mx-auto mb-6 text-slate-800" />
             <div className="text-lg font-bold text-slate-500 mb-2">No Uplink Found</div>
             <div className="text-xs text-slate-600 font-medium px-10">Neural filters could not resolve "{query}". Try institutional browsing.</div>
          </motion.div>
       ) : (
          <div className="space-y-4">
             {results.map((res: any, i: number) => (
                <motion.div 
                  key={res.resource_id} 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-5 glass-panel rounded-3xl border-orbit-border hover:border-orbit-primary/30 transition-all group overflow-hidden relative"
                >
                   <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                         <div className="text-[10px] font-black text-orbit-accent mb-2 flex items-center gap-1.5 uppercase tracking-widest">
                            <Zap className="w-3 h-3" /> {res.course_id}
                         </div>
                         <div className="text-base font-bold text-white mb-2 line-clamp-2 leading-tight">{res.title}</div>
                         <div className="text-[10px] text-slate-500 flex items-center gap-2 font-bold">
                            <Clock className="w-3 h-3" /> {new Date(res.created_at || Date.now()).toLocaleDateString()}
                         </div>
                      </div>
                      <motion.button
                        whileTap={{ scale: 0.8 }}
                        onClick={() => handleResourceAction(res, 'favorite')}
                        className={`p-3 rounded-2xl transition-all ${
                          favorites.includes(res.resource_id) 
                            ? 'text-rose-400 bg-rose-400/10 shadow-[0_0_15px_rgba(244,63,94,0.3)]' 
                            : 'text-slate-600 hover:text-rose-400'
                        }`}
                      >
                         <Heart className={`w-5 h-5 ${favorites.includes(res.resource_id) ? 'fill-current' : ''}`} />
                      </motion.button>
                   </div>
                   <div className="flex items-center gap-3">
                      <motion.button 
                        whileTap={{ scale: 0.96 }}
                        onClick={() => handleResourceAction(res, 'open')}
                        className="flex-1 flex items-center justify-center gap-2 text-[10px] font-black text-white bg-orbit-primary px-4 py-4 rounded-2xl shadow-lg shadow-orbit-primary/20 tracking-widest"
                      >
                         <Download className="w-4 h-4" /> OPEN ASSET
                      </motion.button>
                      <motion.button 
                        whileTap={{ scale: 0.96 }}
                        className="p-4 bg-orbit-surface/50 glass-panel rounded-2xl border border-orbit-border text-slate-400"
                      >
                         <Share2 className="w-4 h-4" />
                      </motion.button>
                   </div>
                   {i === 0 && <div className="absolute top-0 right-0 w-16 h-16 bg-orbit-primary/10 rounded-full blur-2xl pointer-events-none" />}
                </motion.div>
             ))}
          </div>
       )}
    </div>
  );
}

function BrowseScreen({ school, courses, loading, onBack }: any) {
  return (
    <div className="space-y-8 text-white">
       <div className="flex items-center gap-3">
          <motion.button whileTap={{ scale: 0.8 }} onClick={onBack} className="p-2 -ml-2 text-slate-500"><ArrowLeft className="w-5 h-5" /></motion.button>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest leading-none">Sector Index: {school?.slug}</h3>
       </div>

       {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="w-10 h-10 animate-spin text-orbit-primary" /></div>
       ) : (
          <div className="grid grid-cols-1 gap-4">
             {courses.map((c: any, i: number) => (
                <motion.div 
                  key={c.id} 
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-6 glass-panel rounded-3xl border-orbit-border flex items-center justify-between group hover:border-orbit-primary/20"
                >
                   <div className="flex-1">
                      <div className="text-[10px] font-black text-slate-500 mb-2 uppercase tracking-widest">{c.id}</div>
                      <div className="text-base font-bold text-white group-hover:text-orbit-primary transition-colors">{c.title}</div>
                   </div>
                   <div className="flex items-center gap-2 px-3 py-1.5 bg-orbit-surface/50 rounded-xl border border-orbit-border text-[9px] font-black text-orbit-primary shadow-sm uppercase tracking-tighter">
                      {c.week_count || 'N/A'} WKS
                   </div>
                </motion.div>
             ))}
             {courses.length === 0 && <div className="text-center py-20 text-slate-500 font-bold uppercase text-[10px] tracking-[0.2em]">No courses indexed yet.</div>}
          </div>
       )}
    </div>
  );
}

function ProfileScreen({ studentName, isAuthenticated, onBack }: any) {
  return (
    <div className="space-y-10">
       <div className="flex items-center gap-3">
          <motion.button whileTap={{ scale: 0.8 }} onClick={onBack} className="p-2 -ml-2 text-slate-500"><ArrowLeft className="w-5 h-5" /></motion.button>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest leading-none">Identity Core</h3>
       </div>

       <motion.div 
         initial={{ y: 20, opacity: 0 }}
         animate={{ y: 0, opacity: 1 }}
         className="flex flex-col items-center"
       >
          <div className="w-28 h-28 bg-orbit-primary/10 border-2 border-orbit-primary/50 rounded-full flex items-center justify-center mb-6 orbit-glow relative">
             <User className="w-12 h-12 text-orbit-primary" />
             <motion.div 
               animate={{ scale: [1, 1.1, 1] }} 
               transition={{ duration: 3, repeat: Infinity }}
               className="absolute -bottom-1 -right-1 w-8 h-8 bg-emerald-500 border-4 border-orbit-bg rounded-full flex items-center justify-center p-1"
             >
                <ShieldCheck className="text-white w-full h-full" />
             </motion.div>
          </div>
          <h2 className="text-3xl font-black text-white tracking-tighter">{studentName}</h2>
          <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mt-2">Authenticated Voyager</div>
       </motion.div>

       <div className="space-y-4">
          <ProfileLink icon={<ShieldCheck className="text-emerald-400" />} label="Identity Verification" status={isAuthenticated ? 'VERIFIED' : 'PENDING'} index={0} />
          <ProfileLink icon={<Star className="text-amber-400" />} label="Premium Station Pass" status="ACTIVE" index={1} />
          <ProfileLink icon={<Zap className="text-blue-400" />} label="Sync Integrity" status="99.9%" index={2} />
       </div>

       <AnimatePresence>
         {!isAuthenticated && (
           <motion.div 
             initial={{ opacity: 0, scale: 0.9 }}
             animate={{ opacity: 1, scale: 1 }}
             exit={{ opacity: 0, scale: 0.9 }}
             className="p-8 bg-amber-500/5 border border-amber-500/20 rounded-[2rem] relative overflow-hidden"
           >
              <div className="text-amber-400 text-xs font-bold mb-3 flex items-center gap-2 tracking-widest uppercase">
                 <LogIn className="w-4 h-4" /> Authentication Lead
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed font-medium">Your identity is cryptographically bound to your Telegram session. Launching Voyager via the official bot auto-resolves your institutional profile.</p>
              <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl" />
           </motion.div>
         )}
       </AnimatePresence>
    </div>
  );
}

// ── ATOMS ────────────────────────────────────────────────────

function NavIconButton({ active, icon, onClick }: any) {
  return (
    <motion.button 
      whileTap={{ scale: 0.8 }}
      whileHover={{ y: -2 }}
      onClick={onClick}
      className={`p-4 rounded-2xl transition-all relative ${active ? 'text-orbit-primary' : 'text-slate-600'}`}
    >
       {active && (
         <motion.div 
           layoutId="bottom-nav-indicator" 
           className="absolute inset-0 bg-orbit-primary/10 rounded-2xl border border-orbit-primary/20 shadow-[0_0_15px_rgba(59,130,246,0.2)]" 
         />
       )}
       <div className="relative z-10">
          {React.cloneElement(icon, { className: `w-6 h-6 ${active ? 'stroke-[2.5px]' : ''}` })}
       </div>
    </motion.button>
  );
}

function ProfileLink({ icon, label, status, index }: any) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 + (index * 0.1) }}
      className="p-6 glass-panel rounded-3xl border-orbit-border flex items-center justify-between group hover:border-orbit-primary/30 transition-all cursor-default"
    >
       <div className="flex items-center gap-5">
          <div className="w-10 h-10 bg-orbit-surface/50 rounded-[1rem] flex items-center justify-center border border-orbit-border group-hover:border-orbit-primary/30 transition-colors shadow-inner">{icon}</div>
          <div className="text-xs font-bold text-white group-hover:text-orbit-primary transition-colors">{label}</div>
       </div>
       <div className="text-[10px] font-black text-slate-500 tracking-[0.2em] font-mono group-hover:text-white transition-colors">{status}</div>
    </motion.div>
  )
}
