import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  Search, BookOpen, User, Loader2, Download,
  Award, Zap, Eye, Heart, Clock,
  Menu, X, Bell, Sparkles, ArrowLeft, Home
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type SearchResult } from './api';
import { 
  EnhancedSearch, 
  EnhancedCourseCard, 
  EnhancedStatsDashboard,
  EnhancedQuickActions,
  EnhancedActivityFeed
} from './enhanced-components';
import './modern-styles.css';
import './enhanced-modern-styles.css';

interface StudentStats {
  totalDownloads: number;
  favoriteCount: number;
  studyStreak: number;
  completedCourses: number;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
  read: boolean;
}

export default function ModernApp() {
  const [view, setView] = useState<'home' | 'browse' | 'search' | 'profile' | 'notifications'>('home');
  const [studentName, setStudentName] = useState('Guest Voyager');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [downloadHistory, setDownloadHistory] = useState<any[]>([]);
  const [notifications] = useState<NotificationItem[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [stats, setStats] = useState<StudentStats>({
    totalDownloads: 0,
    favoriteCount: 0,
    studyStreak: 0,
    completedCourses: 0
  });
  
  const searchTimeoutRef = useRef<number>();
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize Telegram Web App
  useEffect(() => {
    const tma = (window as any).Telegram?.WebApp;
    if (tma && tma.initData) {
      tma.ready();
      tma.expand();
      try {
        tma.HapticFeedback?.impactOccurred?.('medium');
      } catch (e) {
        // Haptic feedback failed, continue anyway
      }
      
      api.loginWithTelegram(tma.initData)
        .then(data => {
          localStorage.setItem('voyager_token', data.access_token);
          setStudentName(tma.initDataUnsafe?.user?.first_name || 'Voyager');
          try {
            tma.HapticFeedback?.notificationOccurred?.('success');
          } catch (e) {
            // Haptic feedback failed, continue anyway
          }
        })
        .catch(() => {
          try {
            tma.HapticFeedback?.notificationOccurred?.('error');
          } catch (e) {
            // Haptic feedback failed, continue anyway
          }
        });
    }
    
    // Load cached data
    const cachedFavorites = localStorage.getItem('voyager_favorites');
    const cachedRecent = localStorage.getItem('voyager_recent_searches');
    const cachedHistory = localStorage.getItem('voyager_download_history');
    
    if (cachedFavorites) {
      const favs = JSON.parse(cachedFavorites);
      setFavorites(favs);
      setStats(prev => ({ ...prev, favoriteCount: favs.length }));
    }
    if (cachedRecent) setRecentSearches(JSON.parse(cachedRecent));
    if (cachedHistory) {
      const history = JSON.parse(cachedHistory);
      setDownloadHistory(history);
      setStats(prev => ({ ...prev, totalDownloads: history.length }));
    }
    
    // Generate animated stars background will be added later
  }, []);

  
  // Advanced search with debouncing
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
      setStats(s => ({ ...s, favoriteCount: updated.length }));
      return updated;
    });
  }, []);

  
  // Navigation components
  const Navigation = () => (
    <header className="header safe-area-top">
      <div className="nav-container">
        <div className="logo">
          <Sparkles className="w-6 h-6" />
          <span>Orbit Voyager</span>
        </div>
        
        <nav className="nav-buttons">
          <button 
            className="btn btn-ghost btn-icon"
            onClick={() => setView('notifications')}
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            {notifications.filter(n => !n.read).length > 0 && (
              <span className="notification-badge">
                {notifications.filter(n => !n.read).length}
              </span>
            )}
          </button>
          
          <button 
            className="btn btn-ghost btn-icon lg:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </nav>
      </div>
    </header>
  );

  // Home view with enhanced modern design
  const HomeView = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="container mx-auto px-4 py-8"
    >
      {/* Welcome Section */}
      <section className="mb-12 text-center">
        <motion.div
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 100 }}
          className="inline-block"
        >
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Welcome back, {studentName}! 
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Your academic journey continues through the cosmos
          </p>
        </motion.div>
      </section>

      {/* Enhanced Stats Dashboard */}
      <section className="mb-12">
        <EnhancedStatsDashboard stats={stats} />
      </section>

      {/* Enhanced Quick Actions */}
      <section className="mb-12">
        <EnhancedQuickActions onAction={(action: string) => {
          if (action === 'search') setView('search');
          else if (action === 'browse') setView('browse');
          else if (action === 'profile') setView('profile');
          else if (action === 'notifications') setView('notifications');
        }} />
      </section>

      {/* Enhanced Activity Feed */}
      {downloadHistory.length > 0 && (
        <section>
          <EnhancedActivityFeed activities={downloadHistory.slice(0, 5).map((item: any, index: number) => ({
            id: index.toString(),
            type: 'download',
            title: item.title || 'Downloaded Resource',
            description: item.course || 'Course Material',
            timestamp: item.timestamp || new Date().toISOString()
          }))} />
        </section>
      )}
    </motion.div>
  );

  // Modern Search View
  const SearchView = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="container mx-auto px-4 py-8"
    >
      <div className="mb-8">
        <button
          onClick={() => setView('home')}
          className="btn btn-ghost mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </button>
        
        <h1 className="text-3xl font-bold text-white mb-6 text-center">Search Resources</h1>
        
        <div className="search-container">
          <Search className="search-icon w-5 h-5" />
          <input
            type="text"
            className="search-input"
            placeholder="Search for courses, materials, or topics..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            autoFocus
          />
          {loading && <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin" />}
        </div>
      </div>

      {/* Recent Searches */}
      {recentSearches.length > 0 && !searchQuery && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Recent Searches</h2>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((term, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => handleSearch(term)}
                className="btn btn-secondary"
              >
                <Clock className="w-3 h-3 mr-1" />
                {term}
              </motion.button>
            ))}
          </div>
        </section>
      )}

      {/* Search Results */}
      <section>
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
          </div>
        ) : results.length > 0 ? (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">
              Found {results.length} results
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {results.map((result, index) => (
                <motion.div
                  key={result.resource_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="card"
                >
                  <div className="card-header">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center mr-3">
                      <BookOpen className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="card-title">{result.title}</h3>
                      <p className="text-sm text-gray-400">Course ID: {result.course_id}</p>
                    </div>
                    <button
                      onClick={() => toggleFavorite(result.resource_id)}
                      className={`btn btn-icon ${favorites.includes(result.resource_id) ? 'text-red-400' : 'text-gray-400'}`}
                    >
                      <Heart className={`w-5 h-5 ${favorites.includes(result.resource_id) ? 'fill-current' : ''}`} />
                    </button>
                  </div>
                  <p className="card-description mt-3">Category: {result.category_slug}</p>
                  <div className="flex gap-2 mt-4">
                    <button className="btn btn-primary btn-small">
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </button>
                    <button className="btn btn-ghost btn-small">
                      <Eye className="w-4 h-4 mr-1" />
                      Preview
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        ) : searchQuery ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No results found for "{searchQuery}"</p>
              <p className="text-sm mt-2">Try different keywords or browse courses</p>
            </div>
          </div>
        ) : null}
      </section>
    </motion.div>
  );

  return (
    <div className="app-container" ref={containerRef}>
      {/* Background Effects */}
      <div className="cosmic-background" />
      
      {/* Navigation */}
      <Navigation />
      
      {/* Main Content */}
      <main className="flex-1 safe-area-bottom">
        <AnimatePresence mode="wait">
          {view === 'home' && <HomeView key="home" />}
          {view === 'search' && <SearchView key="search" />}
          {view === 'browse' && <div key="browse">Browse View Coming Soon</div>}
          {view === 'profile' && <div key="profile">Profile View Coming Soon</div>}
          {view === 'notifications' && <div key="notifications">Notifications View Coming Soon</div>}
        </AnimatePresence>
      </main>
      
      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-50 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          >
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              className="fixed left-0 top-0 h-full w-64 bg-gray-900 p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-8">
                <h2 className="text-xl font-bold text-white">Menu</h2>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="btn btn-ghost btn-icon"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <nav className="space-y-4">
                {[
                  { icon: Home, label: 'Home', view: 'home' },
                  { icon: Search, label: 'Search', view: 'search' },
                  { icon: BookOpen, label: 'Browse', view: 'browse' },
                  { icon: User, label: 'Profile', view: 'profile' },
                  { icon: Bell, label: 'Notifications', view: 'notifications' }
                ].map((item) => (
                  <button
                    key={item.view}
                    onClick={() => {
                      setView(item.view as any);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full btn btn-ghost text-left justify-start ${
                      view === item.view ? 'bg-blue-600 bg-opacity-20' : ''
                    }`}
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </button>
                ))}
              </nav>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
