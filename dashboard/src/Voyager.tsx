import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { 
  Search, BookOpen, GraduationCap, User, Globe, 
  ChevronRight, ArrowLeft, Loader2, ShieldCheck,
  LayoutGrid, Clock, Star, Sparkles, LogIn, Download,
  TrendingUp, Award, Zap, Eye, Heart, Share2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type Institution, type Course, type SearchResult } from './api';
import classNames from 'classnames';

export default function StudentVoyager({ studentName, isAuthenticated }: { studentName: string; isAuthenticated: boolean }) {
  const [view, setView] = useState<'home' | 'browse' | 'search' | 'profile'>('home');
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

  useEffect(() => {
    const cachedFavorites = localStorage.getItem('voyager_favorites');
    const cachedRecent = localStorage.getItem('voyager_recent_searches');
    const cachedHistory = localStorage.getItem('voyager_download_history');
    
    if (cachedFavorites) setFavorites(JSON.parse(cachedFavorites));
    if (cachedRecent) setRecentSearches(JSON.parse(cachedRecent));
    if (cachedHistory) setDownloadHistory(JSON.parse(cachedHistory));
    
    api.getInstitutions().then(setInstitutions).catch(console.error);
  }, []);

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
        setResults(res.results);
        
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
    <div className="min-h-screen bg-[#0a0a0f] text-white pb-24 selection:bg-cyan-500/30 relative overflow-x-hidden">
      <div className="nebula" />
      
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

      <main className="px-6 space-y-8 max-w-2xl mx-auto">
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

      <motion.nav 
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        className="fixed bottom-0 left-0 w-full glass-panel border-t border-orbit-border px-8 py-5 flex justify-between items-center z-50 rounded-t-[2.5rem] shadow-[0_-10px_30px_rgba(0,0,0,0.5)] lg:hidden"
      >
         <NavIconButton active={view === 'home'} onClick={() => setView('home')} icon={<Globe />} />
         <NavIconButton active={view === 'browse'} onClick={() => setView('browse')} icon={<LayoutGrid />} />
         <NavIconButton active={view === 'search'} onClick={() => setView('search')} icon={<Search />} />
         <NavIconButton active={view === 'profile'} onClick={() => setView('profile')} icon={<User />} />
      </motion.nav>
    </div>
  );
}

function HomeScreen({ onSelectSchool, institutions, studentName }: any) {
  return (
    <div className="space-y-10">
       <motion.div 
         initial={{ scale: 0.9, opacity: 0 }}
         animate={{ scale: 1, opacity: 1 }}
         className="bg-orbit-primary/10 border border-orbit-primary/20 p-8 rounded-[2.5rem] relative overflow-hidden orbit-glow"
       >
          <motion.h2 className="text-2xl font-black text-white mb-2">Welcome, {studentName}</motion.h2>
          <p className="text-sm text-slate-400 max-w-[220px] font-medium leading-relaxed">Access SIT resources through the dual-link intelligent portal.</p>
          <BookOpen className="absolute -right-6 -bottom-6 w-32 h-32 text-orbit-primary/5 -rotate-12" />
       </motion.div>

       <div className="space-y-4">
          <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] px-1">Select Institution</h3>
          <div className="grid grid-cols-1 gap-4">
             {institutions.map((inst: any, idx: number) => (
                <motion.button 
                  key={inst.id} 
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
  return (
    <div className="space-y-8">
       <div className="flex items-center gap-3">
          <motion.button whileTap={{ scale: 0.8 }} onClick={onBack} className="p-2 -ml-2 text-slate-500"><ArrowLeft className="w-5 h-5" /></motion.button>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest leading-none">Intelligence Stream</h3>
       </div>

       {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
             <Loader2 className="w-10 h-10 text-orbit-primary animate-spin mb-4" />
             <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Querying Orbit...</div>
          </div>
       ) : results.length === 0 && query ? (
          <div className="text-center py-20">
             <Search className="w-16 h-16 mx-auto mb-6 text-slate-800" />
             <div className="text-lg font-bold text-slate-500 mb-2">No Uplink Found</div>
          </div>
       ) : (
          <div className="space-y-4">
             {results.map((res: any, i: number) => (
                <div key={res.resource_id} className="p-5 glass-panel rounded-3xl border-orbit-border hover:border-orbit-primary/30 transition-all group overflow-hidden relative">
                   <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                         <div className="text-[10px] font-black text-orbit-accent mb-2 flex items-center gap-1.5 uppercase tracking-widest">
                            <Zap className="w-3 h-3" /> {res.course_id}
                         </div>
                         <div className="text-base font-bold text-white mb-2 line-clamp-2 leading-tight">{res.title}</div>
                      </div>
                   </div>
                   <div className="flex items-center gap-3">
                      <button className="flex-1 flex items-center justify-center gap-2 text-[10px] font-black text-white bg-orbit-primary px-4 py-4 rounded-2xl shadow-lg tracking-widest">
                         <Download className="w-4 h-4" /> OPEN ASSET
                      </button>
                   </div>
                </div>
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
                <div key={c.id} className="p-6 glass-panel rounded-3xl border-orbit-border flex items-center justify-between group hover:border-orbit-primary/20">
                   <div className="flex-1">
                      <div className="text-[10px] font-black text-slate-500 mb-2 uppercase tracking-widest">{c.id}</div>
                      <div className="text-base font-bold text-white group-hover:text-orbit-primary transition-colors">{c.title}</div>
                   </div>
                </div>
             ))}
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

       <div className="flex flex-col items-center">
          <div className="w-28 h-28 bg-orbit-primary/10 border-2 border-orbit-primary/50 rounded-full flex items-center justify-center mb-6 orbit-glow relative">
             <User className="w-12 h-12 text-orbit-primary" />
          </div>
          <h2 className="text-3xl font-black text-white tracking-tighter">{studentName}</h2>
          <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mt-2">Authenticated Voyager</div>
       </div>
    </div>
  );
}

function NavIconButton({ active, icon, onClick }: any) {
  return (
    <motion.button 
      whileTap={{ scale: 0.8 }}
      onClick={onClick}
      className={`p-4 rounded-2xl transition-all relative ${active ? 'text-orbit-primary' : 'text-slate-600'}`}
    >
       {active && (
         <motion.div layoutId="bottom-nav-indicator" className="absolute inset-0 bg-orbit-primary/10 rounded-2xl border border-orbit-primary/20" />
       )}
       <div className="relative z-10">
          {React.cloneElement(icon, { className: `w-6 h-6 ${active ? 'stroke-[2.5px]' : ''}` })}
       </div>
    </motion.button>
  );
}
