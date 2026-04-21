import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  Search, BookOpen, User, Loader2, Download,
  Eye, Heart, Clock,
  Menu, X, Bell, Sparkles, ArrowLeft, Home,
  BarChart3, ChevronRight, Star, Award, Zap,
  Settings, LogOut
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type SearchResult } from './api';
import './working-responsive-styles.css';

interface StudentStats {
  totalDownloads: number;
  favoriteCount: number;
  studyStreak: number;
  completedCourses: number;
  averageGrade: number;
  studyHours: number;
  rank: number;
  achievements: number;
}

interface Course {
  id: string;
  title: string;
  description: string;
  instructor: string;
  duration: string;
  level: string;
  rating: number;
  students: number;
  category: string;
  progress: number;
  tags: string[];
  lastAccessed: string;
}

interface ActivityItem {
  id: string;
  type: 'download' | 'favorite' | 'complete' | 'search' | 'achievement' | 'login';
  title: string;
  description: string;
  timestamp: string;
  metadata?: any;
}

interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    handler: () => void;
  };
}

export default function WorkingApp() {
  const [view, setView] = useState<'dashboard' | 'courses' | 'search' | 'profile' | 'analytics' | 'notifications' | 'settings'>('dashboard');
  const [studentName, setStudentName] = useState('Voyager Student');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [downloadHistory, setDownloadHistory] = useState<ActivityItem[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [courses, setCourses] = useState<Course[]>([]);
  const [stats, setStats] = useState<StudentStats>({
    totalDownloads: 0,
    favoriteCount: 0,
    studyStreak: 0,
    completedCourses: 0,
    averageGrade: 0,
    studyHours: 0,
    rank: 0,
    achievements: 0
  });

  const searchTimeoutRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    initializeApp();
    loadMockData();
  }, []);

  const initializeApp = () => {
    const tma = (window as any).Telegram?.WebApp;
    if (tma && tma.initData) {
      tma.ready();
      tma.expand();
      try {
        tma.HapticFeedback?.impactOccurred?.('medium');
      } catch (e) {
        // Haptic feedback failed
      }
      
      api.loginWithTelegram(tma.initData)
        .then(data => {
          localStorage.setItem('voyager_token', data.access_token);
          setStudentName(tma.initDataUnsafe?.user?.first_name || 'Voyager');
          try {
            tma.HapticFeedback?.notificationOccurred?.('success');
          } catch (e) {
            // Haptic feedback failed
          }
        })
        .catch(() => {
          try {
            tma.HapticFeedback?.notificationOccurred?.('error');
          } catch (e) {
            // Haptic feedback failed
          }
        });
    }
    
    loadCachedData();
  };

  const loadCachedData = () => {
    const cachedFavorites = localStorage.getItem('voyager_favorites');
    const cachedRecent = localStorage.getItem('voyager_recent_searches');
    const cachedHistory = localStorage.getItem('voyager_download_history');
    
    if (cachedFavorites) {
      const favs = JSON.parse(cachedFavorites);
      setFavorites(favs);
    }
    if (cachedRecent) setRecentSearches(JSON.parse(cachedRecent));
    if (cachedHistory) setDownloadHistory(JSON.parse(cachedHistory));
  };

  const loadMockData = () => {
    const mockCourses: Course[] = [
      {
        id: '1',
        title: 'Advanced Web Development',
        description: 'Master modern web development with React, Node.js, and cloud deployment',
        instructor: 'Dr. Sarah Johnson',
        duration: '12 weeks',
        level: 'Advanced',
        rating: 4.8,
        students: 1250,
        category: 'Web Development',
        progress: 75,
        tags: ['React', 'Node.js', 'MongoDB', 'AWS'],
        lastAccessed: '2024-01-15'
      },
      {
        id: '2',
        title: 'Machine Learning Fundamentals',
        description: 'Introduction to ML algorithms, neural networks, and practical applications',
        instructor: 'Prof. Michael Chen',
        duration: '10 weeks',
        level: 'Intermediate',
        rating: 4.9,
        students: 2100,
        category: 'Data Science',
        progress: 60,
        tags: ['Python', 'TensorFlow', 'Scikit-learn', 'Deep Learning'],
        lastAccessed: '2024-01-14'
      },
      {
        id: '3',
        title: 'Mobile App Development',
        description: 'Build native mobile apps for iOS and Android using React Native',
        instructor: 'Emily Rodriguez',
        duration: '8 weeks',
        level: 'Intermediate',
        rating: 4.7,
        students: 890,
        category: 'Mobile Development',
        progress: 45,
        tags: ['React Native', 'iOS', 'Android', 'Firebase'],
        lastAccessed: '2024-01-13'
      },
      {
        id: '4',
        title: 'Cloud Architecture',
        description: 'Design and deploy scalable cloud solutions using AWS and Azure',
        instructor: 'David Kim',
        duration: '14 weeks',
        level: 'Advanced',
        rating: 4.6,
        students: 650,
        category: 'Cloud Computing',
        progress: 30,
        tags: ['AWS', 'Azure', 'Docker', 'Kubernetes'],
        lastAccessed: '2024-01-12'
      },
      {
        id: '5',
        title: 'UI/UX Design Principles',
        description: 'Learn modern design principles and create stunning user interfaces',
        instructor: 'Lisa Anderson',
        duration: '6 weeks',
        level: 'Beginner',
        rating: 4.8,
        students: 3200,
        category: 'Design',
        progress: 90,
        tags: ['Figma', 'Adobe XD', 'Prototyping', 'User Research'],
        lastAccessed: '2024-01-16'
      }
    ];

    setCourses(mockCourses);

    setStats({
      totalDownloads: 156,
      favoriteCount: 23,
      studyStreak: 7,
      completedCourses: 3,
      averageGrade: 87.5,
      studyHours: 142,
      rank: 42,
      achievements: 12
    });

    const mockNotifications: NotificationItem[] = [
      {
        id: '1',
        type: 'success',
        title: 'Course Completed!',
        message: 'Congratulations! You\'ve completed "UI/UX Design Principles"',
        timestamp: new Date(Date.now() - 3600000),
        read: false,
        action: {
          label: 'View Certificate',
          handler: () => console.log('View certificate')
        }
      },
      {
        id: '2',
        type: 'info',
        title: 'New Course Available',
        message: 'Check out "Advanced React Patterns" - now available!',
        timestamp: new Date(Date.now() - 7200000),
        read: false
      },
      {
        id: '3',
        type: 'warning',
        title: 'Assignment Due Soon',
        message: 'Machine Learning Fundamentals - Assignment due in 2 days',
        timestamp: new Date(Date.now() - 86400000),
        read: true
      }
    ];

    setNotifications(mockNotifications);
  };

  const handleSearch = useCallback(async (q: string) => {
    setSearchQuery(q);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    
    searchTimeoutRef.current = window.setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.search(q);
        setSearchResults(res);
        
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

  const toggleFavorite = useCallback((courseId: string) => {
    setFavorites(prev => {
      const updated = prev.includes(courseId)
        ? prev.filter(id => id !== courseId)
        : [...prev, courseId];
      localStorage.setItem('voyager_favorites', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const Dashboard = () => (
    <div className="container-fluid p-0">
      <header className="industry-navbar sticky-top">
        <div className="container">
          <div className="d-flex justify-content-between align-items-center py-3">
            <div className="d-flex align-items-center">
              <button
                className="btn btn-ghost btn-icon d-lg-none me-3"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="navbar-brand d-flex align-items-center">
                <Sparkles className="w-6 h-6 me-2" />
                <span>Orbit Voyager</span>
              </div>
            </div>
            
            <div className="d-flex align-items-center">
              <div className="position-relative me-3">
                <button className="btn btn-ghost btn-icon position-relative">
                  <Bell className="w-5 h-5" />
                  {notifications.filter(n => !n.read).length > 0 && (
                    <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                      {notifications.filter(n => !n.read).length}
                    </span>
                  )}
                </button>
              </div>
              
              <div className="dropdown">
                <button
                  className="btn btn-ghost d-flex align-items-center"
                  type="button"
                  data-bs-toggle="dropdown"
                >
                  <User className="w-5 h-5 me-2" />
                  <span className="d-none d-md-inline">{studentName}</span>
                </button>
                <ul className="dropdown-menu dropdown-menu-end">
                  <li><a className="dropdown-item" href="#" onClick={() => setView('profile')}>
                    <User className="w-4 h-4 me-2" /> Profile
                  </a></li>
                  <li><a className="dropdown-item" href="#" onClick={() => setView('settings')}>
                    <Settings className="w-4 h-4 me-2" /> Settings
                  </a></li>
                  <li><hr className="dropdown-divider" /></li>
                  <li><a className="dropdown-item" href="#">
                    <LogOut className="w-4 h-4 me-2" /> Logout
                  </a></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="d-flex">
        <aside className={`sidebar bg-dark text-white ${sidebarCollapsed ? 'collapsed' : ''} d-none d-lg-block`}>
          <div className="sidebar-content p-4">
            <button
              className="btn btn-ghost btn-icon mb-4"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              <Menu className="w-5 h-5" />
            </button>
            
            <nav className="nav flex-column">
              <a
                className={`nav-link ${view === 'dashboard' ? 'active' : ''}`}
                href="#"
                onClick={() => setView('dashboard')}
              >
                <Home className="w-5 h-5 me-3" />
                {!sidebarCollapsed && 'Dashboard'}
              </a>
              <a
                className={`nav-link ${view === 'courses' ? 'active' : ''}`}
                href="#"
                onClick={() => setView('courses')}
              >
                <BookOpen className="w-5 h-5 me-3" />
                {!sidebarCollapsed && 'Courses'}
              </a>
              <a
                className={`nav-link ${view === 'search' ? 'active' : ''}`}
                href="#"
                onClick={() => setView('search')}
              >
                <Search className="w-5 h-5 me-3" />
                {!sidebarCollapsed && 'Search'}
              </a>
              <a
                className={`nav-link ${view === 'analytics' ? 'active' : ''}`}
                href="#"
                onClick={() => setView('analytics')}
              >
                <BarChart3 className="w-5 h-5 me-3" />
                {!sidebarCollapsed && 'Analytics'}
              </a>
              <a
                className={`nav-link ${view === 'notifications' ? 'active' : ''}`}
                href="#"
                onClick={() => setView('notifications')}
              >
                <Bell className="w-5 h-5 me-3" />
                {!sidebarCollapsed && 'Notifications'}
              </a>
            </nav>
          </div>
        </aside>

        <main className="flex-grow-1 p-4">
          <section className="mb-4 animate__animated animate__fadeInUp">
            <div className="row align-items-center">
              <div className="col-lg-8">
                <h1 className="heading-responsive mb-3">
                  Welcome back, {studentName}! 
                </h1>
                <p className="lead text-responsive">
                  Your academic journey continues through the cosmos. Track your progress and explore new learning opportunities.
                </p>
              </div>
              <div className="col-lg-4 text-lg-end">
                <div className="d-flex justify-content-lg-end gap-2">
                  <button className="btn btn-primary">
                    <Search className="w-4 h-4 me-2" />
                    Search
                  </button>
                  <button className="btn btn-accent">
                    <BookOpen className="w-4 h-4 me-2" />
                    Browse Courses
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="mb-5 animate__animated animate__fadeInUp animate__delay-1s">
            <h2 className="h4 mb-4">Your Progress Overview</h2>
            <div className="row g-4">
              <div className="col-sm-6 col-lg-3">
                <div className="industry-card card-glass h-100">
                  <div className="card-body">
                    <div className="d-flex align-items-center mb-3">
                      <div className="icon-box bg-primary bg-opacity-10 text-primary rounded-circle p-3 me-3">
                        <Download className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="h5 mb-0">{stats.totalDownloads}</h3>
                        <p className="text-muted mb-0">Downloads</p>
                      </div>
                    </div>
                    <div className="progress" style={{height: '4px'}}>
                      <div className="progress-bar bg-primary" style={{width: '75%'}} />
                    </div>
                    <small className="text-muted">+12% this month</small>
                  </div>
                </div>
              </div>
              
              <div className="col-sm-6 col-lg-3">
                <div className="industry-card card-glass h-100">
                  <div className="card-body">
                    <div className="d-flex align-items-center mb-3">
                      <div className="icon-box bg-danger bg-opacity-10 text-danger rounded-circle p-3 me-3">
                        <Heart className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="h5 mb-0">{stats.favoriteCount}</h3>
                        <p className="text-muted mb-0">Favorites</p>
                      </div>
                    </div>
                    <div className="progress" style={{height: '4px'}}>
                      <div className="progress-bar bg-danger" style={{width: '60%'}} />
                    </div>
                    <small className="text-muted">+5 this week</small>
                  </div>
                </div>
              </div>
              
              <div className="col-sm-6 col-lg-3">
                <div className="industry-card card-glass h-100">
                  <div className="card-body">
                    <div className="d-flex align-items-center mb-3">
                      <div className="icon-box bg-warning bg-opacity-10 text-warning rounded-circle p-3 me-3">
                        <Zap className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="h5 mb-0">{stats.studyStreak}</h3>
                        <p className="text-muted mb-0">Day Streak</p>
                      </div>
                    </div>
                    <div className="progress" style={{height: '4px'}}>
                      <div className="progress-bar bg-warning" style={{width: '100%'}} />
                    </div>
                    <small className="text-muted">Keep it up!</small>
                  </div>
                </div>
              </div>
              
              <div className="col-sm-6 col-lg-3">
                <div className="industry-card card-glass h-100">
                  <div className="card-body">
                    <div className="d-flex align-items-center mb-3">
                      <div className="icon-box bg-success bg-opacity-10 text-success rounded-circle p-3 me-3">
                        <Award className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="h5 mb-0">{stats.completedCourses}</h3>
                        <p className="text-muted mb-0">Completed</p>
                      </div>
                    </div>
                    <div className="progress" style={{height: '4px'}}>
                      <div className="progress-bar bg-success" style={{width: '85%'}} />
                    </div>
                    <small className="text-muted">+2 this month</small>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="mb-5 animate__animated animate__fadeInUp animate__delay-2s">
            <div className="row g-4">
              <div className="col-md-4">
                <div className="industry-card card-glass">
                  <div className="card-body">
                    <div className="d-flex align-items-center justify-content-between">
                      <div>
                        <h4 className="h6 text-muted mb-1">Average Grade</h4>
                        <h2 className="h3 mb-0">{stats.averageGrade}%</h2>
                      </div>
                      <div className="icon-box bg-info bg-opacity-10 text-info rounded-circle p-3">
                        <BarChart3 className="w-6 h-6" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="col-md-4">
                <div className="industry-card card-glass">
                  <div className="card-body">
                    <div className="d-flex align-items-center justify-content-between">
                      <div>
                        <h4 className="h6 text-muted mb-1">Study Hours</h4>
                        <h2 className="h3 mb-0">{stats.studyHours}</h2>
                      </div>
                      <div className="icon-box bg-secondary bg-opacity-10 text-secondary rounded-circle p-3">
                        <Clock className="w-6 h-6" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="col-md-4">
                <div className="industry-card card-glass">
                  <div className="card-body">
                    <div className="d-flex align-items-center justify-content-between">
                      <div>
                        <h4 className="h6 text-muted mb-1">Global Rank</h4>
                        <h2 className="h3 mb-0">#{stats.rank}</h2>
                      </div>
                      <div className="icon-box bg-primary bg-opacity-10 text-primary rounded-circle p-3">
                        <Star className="w-6 h-6" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="mb-5 animate__animated animate__fadeInUp animate__delay-3s">
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2 className="h4">Continue Learning</h2>
              <button className="btn btn-outline btn-sm">
                View All Courses
                <ChevronRight className="w-4 h-4 ms-1" />
              </button>
            </div>
            
            <div className="row g-4">
              {courses.slice(0, 3).map((course) => (
                <div key={course.id} className="col-lg-4">
                  <div className="industry-card card-glass h-100 hover-lift">
                    <div className="card-body">
                      <div className="d-flex align-items-start mb-3">
                        <div className="course-thumbnail rounded me-3" style={{
                          width: '60px',
                          height: '60px',
                          background: `linear-gradient(135deg, var(--orbit-primary), var(--orbit-accent))`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <BookOpen className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-grow-1">
                          <h5 className="h6 mb-1">{course.title}</h5>
                          <p className="text-muted small mb-2">{course.instructor}</p>
                          <div className="d-flex align-items-center gap-2">
                            <span className="badge bg-primary bg-opacity-10 text-primary">
                              {course.level}
                            </span>
                            <span className="badge bg-secondary bg-opacity-10 text-secondary">
                              {course.duration}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mb-3">
                        <div className="d-flex justify-content-between align-items-center mb-1">
                          <small className="text-muted">Progress</small>
                          <small className="text-muted">{course.progress}%</small>
                        </div>
                        <div className="progress" style={{height: '6px'}}>
                          <div 
                            className="progress-bar bg-gradient-primary" 
                            style={{width: `${course.progress}%`}}
                          />
                        </div>
                      </div>
                      
                      <div className="d-flex justify-content-between align-items-center">
                        <div className="d-flex align-items-center">
                          <Star className="w-4 h-4 text-warning me-1" />
                          <small className="text-muted">{course.rating}</small>
                        </div>
                        <button 
                          className="btn btn-primary btn-sm"
                          onClick={() => toggleFavorite(course.id)}
                        >
                          {favorites.includes(course.id) ? (
                            <Heart className="w-4 h-4 fill-current" />
                          ) : (
                            <Heart className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="position-fixed top-0 start-0 w-100 h-100 bg-dark bg-opacity-75 z-index-1050 d-lg-none"
            onClick={() => setMobileMenuOpen(false)}
          >
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              className="position-fixed top-0 start-0 h-100 w-75 bg-dark text-white p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h5 className="mb-0">Menu</h5>
                <button
                  className="btn btn-ghost btn-icon"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <nav className="nav flex-column">
                <a
                  className={`nav-link ${view === 'dashboard' ? 'active' : ''}`}
                  href="#"
                  onClick={() => {
                    setView('dashboard');
                    setMobileMenuOpen(false);
                  }}
                >
                  <Home className="w-5 h-5 me-3" />
                  Dashboard
                </a>
                <a
                  className={`nav-link ${view === 'courses' ? 'active' : ''}`}
                  href="#"
                  onClick={() => {
                    setView('courses');
                    setMobileMenuOpen(false);
                  }}
                >
                  <BookOpen className="w-5 h-5 me-3" />
                  Courses
                </a>
                <a
                  className={`nav-link ${view === 'search' ? 'active' : ''}`}
                  href="#"
                  onClick={() => {
                    setView('search');
                    setMobileMenuOpen(false);
                  }}
                >
                  <Search className="w-5 h-5 me-3" />
                  Search
                </a>
                <a
                  className={`nav-link ${view === 'analytics' ? 'active' : ''}`}
                  href="#"
                  onClick={() => {
                    setView('analytics');
                    setMobileMenuOpen(false);
                  }}
                >
                  <BarChart3 className="w-5 h-5 me-3" />
                  Analytics
                </a>
                <a
                  className={`nav-link ${view === 'notifications' ? 'active' : ''}`}
                  href="#"
                  onClick={() => {
                    setView('notifications');
                    setMobileMenuOpen(false);
                  }}
                >
                  <Bell className="w-5 h-5 me-3" />
                  Notifications
                </a>
              </nav>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  const SearchView = () => (
    <div className="container-fluid p-4">
      <div className="row mb-4">
        <div className="col-12">
          <button
            className="btn btn-outline mb-3"
            onClick={() => setView('dashboard')}
          >
            <ArrowLeft className="w-4 h-4 me-2" />
            Back to Dashboard
          </button>
          
          <h1 className="heading-responsive mb-4">Search Resources</h1>
          
          <div className="position-relative">
            <div className="input-group input-group-lg">
              <span className="input-group-text bg-dark border-dark">
                <Search className="w-5 h-5" />
              </span>
              <input
                type="text"
                className="form-control bg-dark border-dark text-white"
                placeholder="Search for courses, materials, or topics..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                autoFocus
              />
              {loading && (
                <span className="input-group-text bg-dark border-dark">
                  <Loader2 className="w-5 h-5 animate-spin" />
                </span>
              )}
            </div>
          </div>

          {recentSearches.length > 0 && !searchQuery && (
            <div className="mt-4">
              <h3 className="h6 mb-3">Recent Searches</h3>
              <div className="d-flex flex-wrap gap-2">
                {recentSearches.map((term, idx) => (
                  <button
                    key={idx}
                    className="btn btn-outline-secondary btn-sm"
                    onClick={() => handleSearch(term)}
                  >
                    <Clock className="w-3 h-3 me-1" />
                    {term}
                  </button>
                ))}
              </div>
            </div>
          )}

          {searchResults.length > 0 && (
            <div className="mt-4">
              <h3 className="h6 mb-3">
                Found {searchResults.length} results
              </h3>
              <div className="row g-4">
                {searchResults.map((result) => (
                  <div key={result.resource_id} className="col-lg-6">
                    <div className="industry-card card-glass hover-lift">
                      <div className="card-body">
                        <div className="d-flex align-items-start mb-3">
                          <div className="icon-box bg-primary bg-opacity-10 text-primary rounded me-3">
                            <BookOpen className="w-5 h-5" />
                          </div>
                          <div className="flex-grow-1">
                            <h5 className="h6 mb-1">{result.title}</h5>
                            <p className="text-muted small mb-2">Course ID: {result.course_id}</p>
                            <span className="badge bg-secondary bg-opacity-10 text-secondary">
                              {result.category_slug}
                            </span>
                          </div>
                          <button
                            className="btn btn-ghost btn-icon"
                            onClick={() => toggleFavorite(result.resource_id)}
                          >
                            <Heart className={`w-5 h-5 ${favorites.includes(result.resource_id) ? 'fill-current text-danger' : ''}`} />
                          </button>
                        </div>
                        <div className="d-flex gap-2">
                          <button className="btn btn-primary btn-sm flex-grow-1">
                            <Download className="w-4 h-4 me-1" />
                            Download
                          </button>
                          <button className="btn btn-outline btn-sm">
                            <Eye className="w-4 h-4 me-1" />
                            Preview
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {searchQuery && searchResults.length === 0 && !loading && (
            <div className="text-center py-5">
              <Search className="w-12 h-12 text-muted mb-3" />
              <h4 className="h5 mb-2">No results found</h4>
              <p className="text-muted">
                Try different keywords or browse courses
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="industry-standard-app" ref={containerRef}>
      <div className="cosmic-background" />
      
      <AnimatePresence mode="wait">
        {view === 'dashboard' && <Dashboard key="dashboard" />}
        {view === 'search' && <SearchView key="search" />}
        {view === 'courses' && <div key="courses" className="p-4"><h1>Courses View Coming Soon</h1></div>}
        {view === 'profile' && <div key="profile" className="p-4"><h1>Profile View Coming Soon</h1></div>}
        {view === 'analytics' && <div key="analytics" className="p-4"><h1>Analytics View Coming Soon</h1></div>}
        {view === 'notifications' && <div key="notifications" className="p-4"><h1>Notifications View Coming Soon</h1></div>}
        {view === 'settings' && <div key="settings" className="p-4"><h1>Settings View Coming Soon</h1></div>}
      </AnimatePresence>
    </div>
  );
}
