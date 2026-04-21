import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  Search, Download, Heart, BookOpen, FileText, Video, Code,
  Star, Home, User, Bell, Settings, Menu, X, Clock,
  TrendingUp, Users, Award, Zap, Target, Rocket,
  ChevronRight, LogOut, Grid3x3, Filter, BarChart3,
  Activity, Calendar, Shield, Globe, Database
} from 'lucide-react';
import { api } from './api';
import './orbit-apple-styles.css';

// Types for Orbit Control Center integration
interface OrbitResource {
  id: string;
  title: string;
  description: string;
  type: 'document' | 'video' | 'code' | 'course' | 'quiz' | 'assignment';
  category: string;
  tags: string[];
  downloads: number;
  rating: number;
  lastUpdated: string;
  url: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration?: string;
  instructor?: string;
  progress?: number;
  isFavorite?: boolean;
  isCompleted?: boolean;
}

interface OrbitUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'student' | 'instructor' | 'admin';
  joinDate: string;
  studyStreak: number;
  completedCourses: number;
  totalHours: number;
  rank: number;
  level: string;
  achievements: string[];
}

interface OrbitStats {
  totalResources: number;
  recentDownloads: number;
  favorites: number;
  activeCourses: number;
  studyStreak: number;
  completedLessons: number;
  averageGrade: number;
  totalHours: number;
  weeklyProgress: number;
}

interface OrbitNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'achievement';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    handler: () => void;
  };
}

export default function OrbitAppleApp() {
  // State management
  const [currentView, setCurrentView] = useState<'dashboard' | 'resources' | 'profile' | 'notifications' | 'settings' | 'analytics'>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [resources, setResources] = useState<OrbitResource[]>([]);
  const [filteredResources, setFilteredResources] = useState<OrbitResource[]>([]);
  const [user, setUser] = useState<OrbitUser | null>(null);
  const [stats, setStats] = useState<OrbitStats>({
    totalResources: 0,
    recentDownloads: 0,
    favorites: 0,
    activeCourses: 0,
    studyStreak: 0,
    completedLessons: 0,
    averageGrade: 0,
    totalHours: 0,
    weeklyProgress: 0
  });
  const [notifications, setNotifications] = useState<OrbitNotification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

  // Refs
  const searchTimeoutRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize app with Orbit Control Center integration
  useEffect(() => {
    initializeOrbitApp();
  }, []);

  const initializeOrbitApp = async () => {
    setLoading(true);
    
    try {
      // Initialize Telegram Web App
      const tma = (window as any).Telegram?.WebApp;
      if (tma && tma.initData) {
        tma.ready();
        tma.expand();
        tma.HeaderColor.set('#000000');
        tma.BackgroundColor.set('#0a0a1a');
        
        try {
          tma.HapticFeedback?.impactOccurred?.('medium');
        } catch (e) {
          // Haptic feedback failed
        }
      }

      // Load user data from Orbit Control Center
      await loadUserData();
      
      // Load resources from Orbit API
      await loadResources();
      
      // Load stats
      await loadStats();
      
      // Load notifications
      await loadNotifications();
      
    } catch (error) {
      console.error('Failed to initialize Orbit app:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserData = async () => {
    try {
      // In real app, this would fetch from Orbit Control Center API
      const tma = (window as any).Telegram?.WebApp;
      const userData: OrbitUser = {
        id: tma?.initDataUnsafe?.user?.id || '1',
        name: tma?.initDataUnsafe?.user?.first_name || 'Orbit Student',
        email: tma?.initDataUnsafe?.user?.id ? `user${tma.initDataUnsafe.user.id}@orbit.edu` : 'student@orbit.edu',
        role: 'student',
        joinDate: new Date().toISOString(),
        studyStreak: 7,
        completedCourses: 3,
        totalHours: 142,
        rank: 42,
        level: 'Advanced',
        achievements: ['First Steps', 'Week Streak', 'Quick Learner']
      };
      
      setUser(userData);
      
      // Store in local storage for offline access
      localStorage.setItem('orbit_user', JSON.stringify(userData));
      
    } catch (error) {
      console.error('Failed to load user data:', error);
      // Load from cache as fallback
      const cachedUser = localStorage.getItem('orbit_user');
      if (cachedUser) {
        setUser(JSON.parse(cachedUser));
      }
    }
  };

  const loadResources = async () => {
    try {
      // In real app, this would fetch from Orbit Control Center API
      const mockResources: OrbitResource[] = [
        {
          id: '1',
          title: 'Advanced React Patterns',
          description: 'Master advanced React patterns including hooks, context, and performance optimization',
          type: 'course',
          category: 'Frontend Development',
          tags: ['React', 'Hooks', 'Patterns', 'Performance'],
          downloads: 3420,
          rating: 4.9,
          lastUpdated: '2024-01-15',
          url: '/orbit/resources/advanced-react',
          difficulty: 'advanced',
          duration: '8 weeks',
          instructor: 'Sarah Johnson',
          progress: 75,
          isFavorite: false,
          isCompleted: false
        },
        {
          id: '2',
          title: 'Machine Learning Fundamentals',
          description: 'Introduction to ML algorithms, neural networks, and practical implementations',
          type: 'course',
          category: 'Data Science',
          tags: ['Machine Learning', 'Python', 'Neural Networks'],
          downloads: 2890,
          rating: 4.8,
          lastUpdated: '2024-01-14',
          url: '/orbit/resources/ml-fundamentals',
          difficulty: 'intermediate',
          duration: '10 weeks',
          instructor: 'Dr. Michael Chen',
          progress: 60,
          isFavorite: true,
          isCompleted: false
        },
        {
          id: '3',
          title: 'System Design Interview Prep',
          description: 'Complete guide to system design interviews with real-world examples',
          type: 'document',
          category: 'Engineering',
          tags: ['System Design', 'Interview', 'Architecture'],
          downloads: 4560,
          rating: 4.7,
          lastUpdated: '2024-01-13',
          url: '/orbit/resources/system-design',
          difficulty: 'advanced',
          isFavorite: false,
          isCompleted: false
        }
      ];
      
      setResources(mockResources);
      setFilteredResources(mockResources);
      
      // Cache for offline access
      localStorage.setItem('orbit_resources', JSON.stringify(mockResources));
      
    } catch (error) {
      console.error('Failed to load resources:', error);
      // Load from cache as fallback
      const cachedResources = localStorage.getItem('orbit_resources');
      if (cachedResources) {
        const resources = JSON.parse(cachedResources);
        setResources(resources);
        setFilteredResources(resources);
      }
    }
  };

  const loadStats = async () => {
    try {
      // In real app, this would fetch from Orbit Control Center API
      const mockStats: OrbitStats = {
        totalResources: 156,
        recentDownloads: 42,
        favorites: 23,
        activeCourses: 3,
        studyStreak: 7,
        completedLessons: 89,
        averageGrade: 87.5,
        totalHours: 142,
        weeklyProgress: 85
      };
      
      setStats(mockStats);
      localStorage.setItem('orbit_stats', JSON.stringify(mockStats));
      
    } catch (error) {
      console.error('Failed to load stats:', error);
      // Load from cache as fallback
      const cachedStats = localStorage.getItem('orbit_stats');
      if (cachedStats) {
        setStats(JSON.parse(cachedStats));
      }
    }
  };

  const loadNotifications = async () => {
    try {
      // In real app, this would fetch from Orbit Control Center API
      const mockNotifications: OrbitNotification[] = [
        {
          id: '1',
          type: 'achievement',
          title: 'Study Streak Milestone! ',
          message: 'You\'ve maintained a 7-day study streak. Keep it up!',
          timestamp: new Date(Date.now() - 3600000),
          read: false,
          action: {
            label: 'View Progress',
            handler: () => setCurrentView('analytics')
          }
        },
        {
          id: '2',
          type: 'info',
          title: 'New Course Available',
          message: 'Advanced TypeScript Patterns is now available',
          timestamp: new Date(Date.now() - 7200000),
          read: false,
          action: {
            label: 'Explore Course',
            handler: () => setCurrentView('resources')
          }
        },
        {
          id: '3',
          type: 'success',
          title: 'Assignment Completed',
          message: 'React Hooks assignment graded: 95%',
          timestamp: new Date(Date.now() - 86400000),
          read: true
        }
      ];
      
      setNotifications(mockNotifications);
      
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  // Search functionality with psychological optimization
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (query.length < 2) {
      setFilteredResources(resources);
      return;
    }
    
    // Debounced search for better UX
    searchTimeoutRef.current = window.setTimeout(() => {
      const filtered = resources.filter(resource =>
        resource.title.toLowerCase().includes(query.toLowerCase()) ||
        resource.description.toLowerCase().includes(query.toLowerCase()) ||
        resource.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase())) ||
        resource.category.toLowerCase().includes(query.toLowerCase())
      );
      
      setFilteredResources(filtered);
      
      // Track search for analytics (psychological insight)
      console.log('Search performed:', query, 'Results:', filtered.length);
      
    }, 300);
  }, [resources]);

  // Resource interactions with psychological triggers
  const handleDownload = useCallback(async (resource: OrbitResource) => {
    try {
      // Haptic feedback for engagement
      const tma = (window as any).Telegram?.WebApp;
      try {
        tma?.HapticFeedback?.notificationOccurred?.('success');
      } catch (e) {
        // Haptic feedback failed
      }
      
      // Track download
      console.log('Downloading resource:', resource.title);
      
      // Update stats
      setStats(prev => ({
        ...prev,
        recentDownloads: prev.recentDownloads + 1
      }));
      
      // Open resource
      window.open(resource.url, '_blank');
      
      // Show success notification
      const newNotification: OrbitNotification = {
        id: Date.now().toString(),
        type: 'success',
        title: 'Download Started',
        message: `${resource.title} is being downloaded`,
        timestamp: new Date(),
        read: false
      };
      
      setNotifications(prev => [newNotification, ...prev].slice(0, 10));
      
    } catch (error) {
      console.error('Failed to download resource:', error);
    }
  }, []);

  const handleFavorite = useCallback(async (resourceId: string) => {
    try {
      // Haptic feedback
      const tma = (window as any).Telegram?.WebApp;
      try {
        tma?.HapticFeedback?.impactOccurred?.('light');
      } catch (e) {
        // Haptic feedback failed
      }
      
      // Update resource favorite status
      setResources(prev => prev.map(resource =>
        resource.id === resourceId
          ? { ...resource, isFavorite: !resource.isFavorite }
          : resource
      ));
      
      setFilteredResources(prev => prev.map(resource =>
        resource.id === resourceId
          ? { ...resource, isFavorite: !resource.isFavorite }
          : resource
      ));
      
      // Update stats
      const resource = resources.find(r => r.id === resourceId);
      if (resource) {
        setStats(prev => ({
          ...prev,
          favorites: resource.isFavorite ? prev.favorites - 1 : prev.favorites + 1
        }));
      }
      
      // Cache updated resources
      const updatedResources = resources.map(r =>
        r.id === resourceId ? { ...r, isFavorite: !r.isFavorite } : r
      );
      localStorage.setItem('orbit_resources', JSON.stringify(updatedResources));
      
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  }, [resources]);

  const markNotificationAsRead = useCallback((notificationId: string) => {
    setNotifications(prev => prev.map(notification =>
      notification.id === notificationId
        ? { ...notification, read: true }
        : notification
    ));
  }, []);

  const getResourceIcon = (type: OrbitResource['type']) => {
    switch (type) {
      case 'document':
        return <FileText className="w-5 h-5" />;
      case 'video':
        return <Video className="w-5 h-5" />;
      case 'code':
        return <Code className="w-5 h-5" />;
      case 'course':
        return <BookOpen className="w-5 h-5" />;
      case 'quiz':
        return <Target className="w-5 h-5" />;
      case 'assignment':
        return <Award className="w-5 h-5" />;
      default:
        return <FileText className="w-5 h-5" />;
    }
  };

  const getDifficultyColor = (difficulty: OrbitResource['difficulty']) => {
    switch (difficulty) {
      case 'beginner':
        return 'text-green-400';
      case 'intermediate':
        return 'text-yellow-400';
      case 'advanced':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  // Render different views
  const renderDashboard = () => (
    <div className="orbit-content">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="orbit-heading-1">
          Welcome back, {user?.name || 'Orbit Explorer'}! 
        </h1>
        <p className="orbit-text">
          Your learning journey continues. Track your progress and explore new resources.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="orbit-stats mb-8">
        <div className="orbit-stat-card">
          <div className="orbit-stat-value">{stats.totalResources}</div>
          <div className="orbit-stat-label">Resources</div>
        </div>
        <div className="orbit-stat-card">
          <div className="orbit-stat-value">{stats.recentDownloads}</div>
          <div className="orbit-stat-label">Downloads</div>
        </div>
        <div className="orbit-stat-card">
          <div className="orbit-stat-value">{stats.favorites}</div>
          <div className="orbit-stat-label">Favorites</div>
        </div>
        <div className="orbit-stat-card">
          <div className="orbit-stat-value">{stats.activeCourses}</div>
          <div className="orbit-stat-label">Active Courses</div>
        </div>
        <div className="orbit-stat-card">
          <div className="orbit-stat-value">{stats.studyStreak}</div>
          <div className="orbit-stat-label">Day Streak</div>
        </div>
        <div className="orbit-stat-card">
          <div className="orbit-stat-value">{stats.averageGrade}%</div>
          <div className="orbit-stat-label">Average Grade</div>
        </div>
      </div>

      {/* Recent Resources */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="orbit-heading-2">Continue Learning</h2>
          <button 
            className="orbit-btn orbit-btn-primary"
            onClick={() => setCurrentView('resources')}
          >
            View All Resources
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        
        <div className="orbit-resource-grid">
          {filteredResources.slice(0, 6).map((resource) => (
            <div key={resource.id} className="orbit-resource-card orbit-card-interactive">
              <div className="orbit-resource-header">
                <div className="orbit-resource-icon">
                  {getResourceIcon(resource.type)}
                </div>
                <div className="orbit-resource-info">
                  <h3 className="orbit-resource-title">{resource.title}</h3>
                  <div className="orbit-resource-meta">
                    <span>{resource.category}</span>
                    <span>·</span>
                    <span>{resource.downloads.toLocaleString()} downloads</span>
                  </div>
                </div>
              </div>
              
              <p className="orbit-resource-description">{resource.description}</p>
              
              <div className="orbit-resource-tags">
                <span className={`orbit-tag ${getDifficultyColor(resource.difficulty)}`}>
                  {resource.difficulty}
                </span>
                {resource.tags.slice(0, 2).map((tag) => (
                  <span key={tag} className="orbit-tag">{tag}</span>
                ))}
              </div>
              
              {resource.progress && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="orbit-text-sm">Progress</span>
                    <span className="orbit-text-sm">{resource.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                      style={{ width: `${resource.progress}%` }}
                    />
                  </div>
                </div>
              )}
              
              <div className="orbit-resource-actions">
                <button 
                  className="orbit-btn orbit-btn-primary"
                  onClick={() => handleDownload(resource)}
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
                <button 
                  className="orbit-btn orbit-btn-ghost"
                  onClick={() => handleFavorite(resource.id)}
                >
                  <Heart className={`w-4 h-4 ${resource.isFavorite ? 'fill-current text-red-500' : ''}`} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderResources = () => (
    <div className="orbit-content">
      <h1 className="orbit-heading-1 mb-8">All Resources</h1>
      
      {filteredResources.length > 0 ? (
        <div className="orbit-resource-grid">
          {filteredResources.map((resource) => (
            <div key={resource.id} className="orbit-resource-card orbit-card-interactive">
              <div className="orbit-resource-header">
                <div className="orbit-resource-icon">
                  {getResourceIcon(resource.type)}
                </div>
                <div className="orbit-resource-info">
                  <h3 className="orbit-resource-title">{resource.title}</h3>
                  <div className="orbit-resource-meta">
                    <span>{resource.category}</span>
                    <span>·</span>
                    <span>{resource.downloads.toLocaleString()} downloads</span>
                  </div>
                </div>
              </div>
              
              <p className="orbit-resource-description">{resource.description}</p>
              
              <div className="orbit-resource-tags">
                <span className={`orbit-tag ${getDifficultyColor(resource.difficulty)}`}>
                  {resource.difficulty}
                </span>
                {resource.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="orbit-tag">{tag}</span>
                ))}
              </div>
              
              <div className="orbit-resource-actions">
                <button 
                  className="orbit-btn orbit-btn-primary"
                  onClick={() => handleDownload(resource)}
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
                <button 
                  className="orbit-btn orbit-btn-ghost"
                  onClick={() => handleFavorite(resource.id)}
                >
                  <Heart className={`w-4 h-4 ${resource.isFavorite ? 'fill-current text-red-500' : ''}`} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="orbit-empty">
          <Search className="orbit-empty-icon" />
          <h3 className="orbit-empty-title">No resources found</h3>
          <p className="orbit-empty-description">
            Try adjusting your search terms or browse all available resources.
          </p>
        </div>
      )}
    </div>
  );

  const renderProfile = () => (
    <div className="orbit-content">
      <h1 className="orbit-heading-1 mb-8">Profile</h1>
      
      {user && (
        <div className="orbit-grid orbit-grid-cols-3 gap-6">
          <div className="orbit-grid-cols-1">
            <div className="orbit-card">
              <div className="text-center mb-6">
                <div className="orbit-avatar mx-auto mb-4">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <h2 className="orbit-heading-2 mb-2">{user.name}</h2>
                <p className="orbit-text-sm">{user.email}</p>
                <p className="orbit-text-xs mt-1">{user.role}</p>
              </div>
              
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="orbit-text-sm">Level</span>
                  <span className="orbit-text-sm font-semibold">{user.level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="orbit-text-sm">Rank</span>
                  <span className="orbit-text-sm font-semibold">#{user.rank}</span>
                </div>
                <div className="flex justify-between">
                  <span className="orbit-text-sm">Study Streak</span>
                  <span className="orbit-text-sm font-semibold">{user.studyStreak} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="orbit-text-sm">Completed Courses</span>
                  <span className="orbit-text-sm font-semibold">{user.completedCourses}</span>
                </div>
                <div className="flex justify-between">
                  <span className="orbit-text-sm">Total Hours</span>
                  <span className="orbit-text-sm font-semibold">{user.totalHours}h</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="orbit-grid-cols-2">
            <div className="orbit-card">
              <h3 className="orbit-heading-3 mb-4">Achievements</h3>
              <div className="space-y-3">
                {user.achievements.map((achievement, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <Award className="w-5 h-5 text-yellow-400" />
                    <span className="orbit-text-sm">{achievement}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderNotifications = () => (
    <div className="orbit-content">
      <h1 className="orbit-heading-1 mb-8">Notifications</h1>
      
      {notifications.length > 0 ? (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div key={notification.id} className={`orbit-card ${!notification.read ? 'border-blue-500' : ''}`}>
              <div className="flex items-start gap-4">
                <div className="orbit-resource-icon">
                  {notification.type === 'achievement' && <Award className="w-5 h-5" />}
                  {notification.type === 'success' && <Star className="w-5 h-5" />}
                  {notification.type === 'info' && <Bell className="w-5 h-5" />}
                  {notification.type === 'warning' && <Zap className="w-5 h-5" />}
                  {notification.type === 'error' && <Shield className="w-5 h-5" />}
                </div>
                
                <div className="flex-1">
                  <h3 className="orbit-heading-4 mb-1">{notification.title}</h3>
                  <p className="orbit-text-sm mb-2">{notification.message}</p>
                  <p className="orbit-text-xs">
                    {notification.timestamp.toLocaleString()}
                  </p>
                  
                  {notification.action && (
                    <button 
                      className="orbit-btn orbit-btn-primary mt-3"
                      onClick={notification.action.handler}
                    >
                      {notification.action.label}
                    </button>
                  )}
                </div>
                
                {!notification.read && (
                  <button 
                    className="orbit-btn orbit-btn-ghost"
                    onClick={() => markNotificationAsRead(notification.id)}
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="orbit-empty">
          <Bell className="orbit-empty-icon" />
          <h3 className="orbit-empty-title">No notifications</h3>
          <p className="orbit-empty-description">
            You're all caught up! Check back later for updates.
          </p>
        </div>
      )}
    </div>
  );

  const renderSettings = () => (
    <div className="orbit-content">
      <h1 className="orbit-heading-1 mb-8">Settings</h1>
      
      <div className="orbit-grid orbit-grid-cols-2 gap-6">
        <div className="orbit-card">
          <h3 className="orbit-heading-3 mb-4">Preferences</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="orbit-text-sm">Dark Mode</span>
              <button className="orbit-btn orbit-btn-ghost">Enabled</button>
            </div>
            <div className="flex justify-between items-center">
              <span className="orbit-text-sm">Notifications</span>
              <button className="orbit-btn orbit-btn-ghost">Enabled</button>
            </div>
            <div className="flex justify-between items-center">
              <span className="orbit-text-sm">Auto-download</span>
              <button className="orbit-btn orbit-btn-ghost">Disabled</button>
            </div>
          </div>
        </div>
        
        <div className="orbit-card">
          <h3 className="orbit-heading-3 mb-4">Account</h3>
          <div className="space-y-4">
            <button className="orbit-btn orbit-btn-ghost w-full text-left">
              <User className="w-4 h-4 mr-2" />
              Edit Profile
            </button>
            <button className="orbit-btn orbit-btn-ghost w-full text-left">
              <Shield className="w-4 h-4 mr-2" />
              Privacy Settings
            </button>
            <button className="orbit-btn orbit-btn-ghost w-full text-left">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="orbit-content">
      <h1 className="orbit-heading-1 mb-8">Analytics</h1>
      
      <div className="orbit-grid orbit-grid-cols-2 gap-6 mb-8">
        <div className="orbit-card">
          <h3 className="orbit-heading-3 mb-4">Learning Progress</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Weekly Progress</span>
                <span>{stats.weeklyProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full"
                  style={{ width: `${stats.weeklyProgress}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Course Completion</span>
                <span>{Math.round((stats.completedLessons / 100) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                  style={{ width: `${(stats.completedLessons / 100) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
        
        <div className="orbit-card">
          <h3 className="orbit-heading-3 mb-4">Study Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="orbit-text-sm">Total Study Hours</span>
              <span className="orbit-text-sm font-semibold">{stats.totalHours}h</span>
            </div>
            <div className="flex justify-between">
              <span className="orbit-text-sm">Average Grade</span>
              <span className="orbit-text-sm font-semibold">{stats.averageGrade}%</span>
            </div>
            <div className="flex justify-between">
              <span className="orbit-text-sm">Resources Downloaded</span>
              <span className="orbit-text-sm font-semibold">{stats.recentDownloads}</span>
            </div>
            <div className="flex justify-between">
              <span className="orbit-text-sm">Active Courses</span>
              <span className="orbit-text-sm font-semibold">{stats.activeCourses}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Loading state
  if (loading) {
    return (
      <div className="orbit-loading">
        <div className="orbit-spinner"></div>
        <span>Loading Orbit...</span>
      </div>
    );
  }

  return (
    <div className="orbit-apple-app" ref={containerRef}>
      {/* Sidebar */}
      <aside className={`orbit-sidebar ${sidebarOpen ? '' : 'orbit-sidebar-collapsed'}`}>
        <div className="orbit-sidebar-header">
          <div className="flex items-center gap-3">
            <div className="orbit-avatar">
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <h2 className="orbit-heading-3">Orbit</h2>
              <p className="orbit-text-xs">Learning Platform</p>
            </div>
          </div>
        </div>
        
        <nav className="orbit-sidebar-nav">
          <a 
            href="#" 
            className={`orbit-nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentView('dashboard');
            }}
          >
            <Home className="orbit-nav-icon" />
            Dashboard
          </a>
          <a 
            href="#" 
            className={`orbit-nav-item ${currentView === 'resources' ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentView('resources');
            }}
          >
            <BookOpen className="orbit-nav-icon" />
            Resources
          </a>
          <a 
            href="#" 
            className={`orbit-nav-item ${currentView === 'analytics' ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentView('analytics');
            }}
          >
            <BarChart3 className="orbit-nav-icon" />
            Analytics
          </a>
          <a 
            href="#" 
            className={`orbit-nav-item ${currentView === 'profile' ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentView('profile');
            }}
          >
            <User className="orbit-nav-icon" />
            Profile
          </a>
          <a 
            href="#" 
            className={`orbit-nav-item ${currentView === 'notifications' ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentView('notifications');
            }}
          >
            <Bell className="orbit-nav-icon" />
            Notifications
            {notifications.filter(n => !n.read).length > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-2 py-1">
                {notifications.filter(n => !n.read).length}
              </span>
            )}
          </a>
          <a 
            href="#" 
            className={`orbit-nav-item ${currentView === 'settings' ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentView('settings');
            }}
          >
            <Settings className="orbit-nav-icon" />
            Settings
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className={`orbit-main ${sidebarOpen ? '' : 'orbit-main-full'}`}>
        {/* Header */}
        <header className="orbit-header">
          <div className="orbit-header-content">
            <div className="flex items-center gap-4">
              <button 
                className="orbit-btn orbit-btn-ghost"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Menu className="w-5 h-5" />
              </button>
              
              <div className="orbit-search">
                <Search className="orbit-search-icon w-5 h-5" />
                <input
                  type="text"
                  className="orbit-search-input"
                  placeholder="Search resources..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button 
                className="orbit-btn orbit-btn-ghost"
                onClick={() => setShowNotifications(!showNotifications)}
              >
                <Bell className="w-5 h-5" />
                {notifications.filter(n => !n.read).length > 0 && (
                  <span className="ml-1 bg-red-500 text-white text-xs rounded-full px-2 py-1">
                    {notifications.filter(n => !n.read).length}
                  </span>
                )}
              </button>
              
              <div className="orbit-profile">
                <div className="orbit-avatar">
                  {user?.name.charAt(0).toUpperCase()}
                </div>
                <div className="orbit-profile-info">
                  <span className="orbit-profile-name">{user?.name}</span>
                  <span className="orbit-profile-role">{user?.role}</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'resources' && renderResources()}
        {currentView === 'profile' && renderProfile()}
        {currentView === 'notifications' && renderNotifications()}
        {currentView === 'settings' && renderSettings()}
        {currentView === 'analytics' && renderAnalytics()}
      </main>

      {/* Notifications Dropdown */}
      {showNotifications && (
        <div className="orbit-notification">
          <div className="orbit-notification-header">
            <h3 className="orbit-notification-title">Notifications</h3>
            <button 
              className="orbit-notification-close"
              onClick={() => setShowNotifications(false)}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="space-y-3">
            {notifications.slice(0, 5).map((notification) => (
              <div key={notification.id} className="text-sm">
                <div className="font-semibold text-white">{notification.title}</div>
                <div className="text-gray-300">{notification.message}</div>
                <div className="text-gray-400 text-xs mt-1">
                  {notification.timestamp.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
          
          <button 
            className="orbit-btn orbit-btn-ghost w-full mt-4"
            onClick={() => {
              setCurrentView('notifications');
              setShowNotifications(false);
            }}
          >
            View All Notifications
          </button>
        </div>
      )}
    </div>
  );
}
