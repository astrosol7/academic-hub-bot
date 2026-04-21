import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  Search, Download, Heart, BookOpen, FileText, Video, Code,
  Star, Home, User, Bell, Settings, Menu, X, Clock,
  TrendingUp, Users, Award, Zap, Target, Rocket,
  ChevronRight, LogOut, Grid3x3, Filter, BarChart3,
  Activity, Calendar, Shield, Globe, Database,
  Eye, Edit, Trash2, Share2, Bookmark,
  ThumbsUp, MessageSquare, Play, Pause,
  Volume2, VolumeX, Maximize2, Minimize2,
  RefreshCw, MoreVertical, ChevronDown,
  UserPlus, UserCheck, UserX, LogOut as SignOut
} from 'lucide-react';
import { api } from './api';
import './enterprise-styles.css';

// Enterprise-level types for Orbit Control Center integration
interface OrbitResource {
  id: string;
  title: string;
  description: string;
  type: 'document' | 'video' | 'code' | 'course' | 'quiz' | 'assignment' | 'lab' | 'tutorial';
  category: string;
  tags: string[];
  downloads: number;
  rating: number;
  lastUpdated: string;
  url: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  duration?: string;
  instructor?: string;
  progress?: number;
  isFavorite?: boolean;
  isCompleted?: boolean;
  isBookmarked?: boolean;
  views: number;
  likes: number;
  shares: number;
  fileSize: string;
  language: string;
  subtitles: boolean;
  certificate: boolean;
  prerequisites?: string[];
  learningObjectives?: string[];
  materials?: string[];
}

interface OrbitUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'student' | 'instructor' | 'admin' | 'moderator' | 'premium';
  joinDate: string;
  studyStreak: number;
  completedCourses: number;
  totalHours: number;
  rank: number;
  level: string;
  achievements: string[];
  bio?: string;
  location?: string;
  website?: string;
  social?: {
    github?: string;
    linkedin?: string;
    twitter?: string;
  };
  preferences: {
    notifications: boolean;
    darkMode: boolean;
    language: string;
    timezone: string;
  };
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
  monthlyProgress: number;
  yearlyProgress: number;
  globalRank: number;
  localRank: number;
  points: number;
  badges: number;
  certificates: number;
  projects: number;
}

interface OrbitNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'achievement' | 'reminder' | 'update';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  action?: {
    label: string;
    handler: () => void;
  };
  metadata?: any;
}

export default function EnterpriseApp() {
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
    weeklyProgress: 0,
    monthlyProgress: 0,
    yearlyProgress: 0,
    globalRank: 0,
    localRank: 0,
    points: 0,
    badges: 0,
    certificates: 0,
    projects: 0
  });
  const [notifications, setNotifications] = useState<OrbitNotification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [particles, setParticles] = useState<Array<{id: number, x: number, y: number, size: number, duration: number}>>([]);

  // Refs
  const searchTimeoutRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize app with enterprise-level features
  useEffect(() => {
    initializeEnterpriseApp();
    generateParticles();
    
    // Add keyboard shortcuts
    const handleKeyboardShortcuts = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'k':
            e.preventDefault();
            document.querySelector('.orbit-search-input')?.focus();
            break;
          case 'p':
            e.preventDefault();
            setShowProfileDropdown(!showProfileDropdown);
            break;
          case 'n':
            e.preventDefault();
            setCurrentView('notifications');
            break;
          case '/':
            e.preventDefault();
            setCurrentView('resources');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyboardShortcuts);
    return () => window.removeEventListener('keydown', handleKeyboardShortcuts);
  }, [showProfileDropdown]);

  const generateParticles = () => {
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: 15 + Math.random() * 10
    }));
    setParticles(newParticles);
  };

  const initializeEnterpriseApp = async () => {
    setLoading(true);
    
    try {
      // Initialize Telegram Web App with enterprise settings
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

      // Load data from Orbit Control Center API
      await Promise.all([
        loadUserData(),
        loadResources(),
        loadStats(),
        loadNotifications()
      ]);
      
    } catch (error) {
      console.error('Failed to initialize Enterprise app:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserData = async () => {
    try {
      // In production, fetch from Orbit Control Center API
      const tma = (window as any).Telegram?.WebApp;
      const userData: OrbitUser = {
        id: tma?.initDataUnsafe?.user?.id || '1',
        name: tma?.initDataUnsafe?.user?.first_name || 'Enterprise User',
        email: tma?.initDataUnsafe?.user?.id ? `user${tma.initDataUnsafe.user.id}@orbit.enterprise` : 'enterprise@orbit.edu',
        role: 'premium',
        joinDate: new Date().toISOString(),
        studyStreak: 42,
        completedCourses: 12,
        totalHours: 342,
        rank: 156,
        level: 'Expert',
        achievements: ['First Steps', 'Week Streak', 'Quick Learner', 'Problem Solver', 'Team Player', 'Innovation Award', 'Excellence', 'Leadership'],
        bio: 'Passionate learner and technology enthusiast',
        location: 'San Francisco, CA',
        website: 'https://orbit.enterprise',
        social: {
          github: 'orbit-user',
          linkedin: 'orbit-user',
          twitter: '@orbit_user'
        },
        preferences: {
          notifications: true,
          darkMode: true,
          language: 'en',
          timezone: 'UTC'
        }
      };
      
      setUser(userData);
      localStorage.setItem('orbit_user_enterprise', JSON.stringify(userData));
      
    } catch (error) {
      console.error('Failed to load user data:', error);
      const cachedUser = localStorage.getItem('orbit_user_enterprise');
      if (cachedUser) {
        setUser(JSON.parse(cachedUser));
      }
    }
  };

  const loadResources = async () => {
    try {
      // In production, fetch from Orbit Control Center API
      const mockResources: OrbitResource[] = [
        {
          id: '1',
          title: 'Advanced Enterprise Architecture Patterns',
          description: 'Master enterprise-level architecture patterns including microservices, event-driven architecture, and distributed systems design with real-world case studies from Fortune 500 companies',
          type: 'course',
          category: 'Enterprise Architecture',
          tags: ['Microservices', 'Distributed Systems', 'Cloud Native', 'DevOps', 'Kubernetes', 'Docker'],
          downloads: 12420,
          rating: 4.9,
          lastUpdated: '2024-01-15',
          url: '/orbit/resources/enterprise-architecture',
          difficulty: 'expert',
          duration: '12 weeks',
          instructor: 'Dr. Sarah Johnson',
          progress: 78,
          isFavorite: true,
          isCompleted: false,
          views: 45680,
          likes: 3420,
          shares: 890,
          fileSize: '2.4 GB',
          language: 'English',
          subtitles: true,
          certificate: true,
          prerequisites: ['Basic programming', 'System design fundamentals'],
          learningObjectives: ['Design scalable systems', 'Implement microservices', 'Master cloud deployment'],
          materials: ['Video lectures', 'Code examples', 'Design templates', 'Case studies']
        },
        {
          id: '2',
          title: 'Machine Learning at Scale',
          description: 'Build and deploy production-ready ML systems handling millions of requests with advanced optimization techniques and MLOps best practices',
          type: 'course',
          category: 'Data Science',
          tags: ['Machine Learning', 'MLOps', 'TensorFlow', 'PyTorch', 'Production', 'Scaling'],
          downloads: 8920,
          rating: 4.8,
          lastUpdated: '2024-01-14',
          url: '/orbit/resources/ml-scale',
          difficulty: 'advanced',
          duration: '10 weeks',
          instructor: 'Prof. Michael Chen',
          progress: 62,
          isFavorite: false,
          isCompleted: false,
          views: 32450,
          likes: 2890,
          shares: 567,
          fileSize: '1.8 GB',
          language: 'English',
          subtitles: true,
          certificate: true,
          prerequisites: ['Python programming', 'Basic ML concepts'],
          learningObjectives: ['Scale ML models', 'Implement MLOps', 'Optimize performance'],
          materials: ['Jupyter notebooks', 'Datasets', 'Cloud templates']
        },
        {
          id: '3',
          title: 'Enterprise Security & Compliance',
          description: 'Comprehensive guide to enterprise security including zero-trust architecture, compliance frameworks, and advanced threat detection',
          type: 'document',
          category: 'Security',
          tags: ['Security', 'Compliance', 'Zero Trust', 'GDPR', 'SOC2', 'ISO27001'],
          downloads: 15680,
          rating: 4.7,
          lastUpdated: '2024-01-13',
          url: '/orbit/resources/enterprise-security',
          difficulty: 'advanced',
          views: 67890,
          likes: 4560,
          shares: 1234,
          fileSize: '45 MB',
          language: 'English',
          subtitles: false,
          certificate: false,
          isFavorite: true,
          isCompleted: false
        },
        {
          id: '4',
          title: 'Advanced Cloud Native Development',
          description: 'Master cloud-native development with Kubernetes, service meshes, and advanced orchestration patterns for enterprise applications',
          type: 'course',
          category: 'Cloud Computing',
          tags: ['Kubernetes', 'Docker', 'Service Mesh', 'Istio', 'Helm', 'Terraform'],
          downloads: 9870,
          rating: 4.9,
          lastUpdated: '2024-01-12',
          url: '/orbit/resources/cloud-native',
          difficulty: 'expert',
          duration: '8 weeks',
          instructor: 'Emily Rodriguez',
          progress: 45,
          isFavorite: false,
          isCompleted: false,
          views: 28900,
          likes: 2340,
          shares: 456,
          fileSize: '3.1 GB',
          language: 'English',
          subtitles: true,
          certificate: true,
          prerequisites: ['Docker basics', 'Linux fundamentals'],
          learningObjectives: ['Master Kubernetes', 'Implement service mesh', 'Deploy cloud apps'],
          materials: ['Video tutorials', 'Lab exercises', 'YAML templates']
        }
      ];
      
      setResources(mockResources);
      setFilteredResources(mockResources);
      localStorage.setItem('orbit_resources_enterprise', JSON.stringify(mockResources));
      
    } catch (error) {
      console.error('Failed to load resources:', error);
      const cachedResources = localStorage.getItem('orbit_resources_enterprise');
      if (cachedResources) {
        const resources = JSON.parse(cachedResources);
        setResources(resources);
        setFilteredResources(resources);
      }
    }
  };

  const loadStats = async () => {
    try {
      // In production, fetch from Orbit Control Center API
      const mockStats: OrbitStats = {
        totalResources: 1247,
        recentDownloads: 156,
        favorites: 89,
        activeCourses: 5,
        studyStreak: 42,
        completedLessons: 234,
        averageGrade: 94.5,
        totalHours: 342,
        weeklyProgress: 87,
        monthlyProgress: 92,
        yearlyProgress: 78,
        globalRank: 156,
        localRank: 12,
        points: 45670,
        badges: 23,
        certificates: 8,
        projects: 15
      };
      
      setStats(mockStats);
      localStorage.setItem('orbit_stats_enterprise', JSON.stringify(mockStats));
      
    } catch (error) {
      console.error('Failed to load stats:', error);
      const cachedStats = localStorage.getItem('orbit_stats_enterprise');
      if (cachedStats) {
        setStats(JSON.parse(cachedStats));
      }
    }
  };

  const loadNotifications = async () => {
    try {
      // In production, fetch from Orbit Control Center API
      const mockNotifications: OrbitNotification[] = [
        {
          id: '1',
          type: 'achievement',
          title: 'Expert Level Achieved! ',
          message: 'Congratulations! You\'ve reached Expert level with 45,670 points',
          timestamp: new Date(Date.now() - 3600000),
          read: false,
          priority: 'high',
          action: {
            label: 'View Profile',
            handler: () => setCurrentView('profile')
          }
        },
        {
          id: '2',
          type: 'info',
          title: 'New Enterprise Course Available',
          message: 'Advanced Cloud Security Patterns is now available for premium users',
          timestamp: new Date(Date.now() - 7200000),
          read: false,
          priority: 'medium',
          action: {
            label: 'Explore Course',
            handler: () => setCurrentView('resources')
          }
        },
        {
          id: '3',
          type: 'success',
          title: 'Project Completed Successfully',
          message: 'Your microservices project has been reviewed and approved',
          timestamp: new Date(Date.now() - 86400000),
          read: true,
          priority: 'medium'
        },
        {
          id: '4',
          type: 'reminder',
          title: 'Study Session Reminder',
          message: 'Your scheduled study session starts in 30 minutes',
          timestamp: new Date(Date.now() - 1800000),
          read: false,
          priority: 'low'
        }
      ];
      
      setNotifications(mockNotifications);
      
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  // Enterprise search with advanced features
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (query.length < 2) {
      setFilteredResources(resources);
      return;
    }
    
    // Advanced search with multiple criteria
    searchTimeoutRef.current = window.setTimeout(() => {
      const filtered = resources.filter(resource => {
        const searchFields = [
          resource.title,
          resource.description,
          resource.category,
          ...resource.tags,
          resource.instructor || '',
          resource.type,
          resource.difficulty,
          resource.language
        ].join(' ').toLowerCase();
        
        return searchFields.includes(query.toLowerCase());
      });
      
      setFilteredResources(filtered);
      
      // Track search analytics
      console.log('Enterprise search performed:', {
        query,
        results: filtered.length,
        timestamp: new Date().toISOString()
      });
      
    }, 300);
  }, [resources]);

  // Enterprise resource interactions
  const handleDownload = useCallback(async (resource: OrbitResource) => {
    try {
      // Haptic feedback
      const tma = (window as any).Telegram?.WebApp;
      try {
        tma?.HapticFeedback?.notificationOccurred?.('success');
      } catch (e) {
        // Haptic feedback failed
      }
      
      // Track download
      console.log('Enterprise download initiated:', {
        resourceId: resource.id,
        title: resource.title,
        timestamp: new Date().toISOString()
      });
      
      // Update stats
      setStats(prev => ({
        ...prev,
        recentDownloads: prev.recentDownloads + 1
      }));
      
      // Update resource stats
      setResources(prev => prev.map(r =>
        r.id === resource.id
          ? { ...r, downloads: r.downloads + 1 }
          : r
      ));
      
      setFilteredResources(prev => prev.map(r =>
        r.id === resource.id
          ? { ...r, downloads: r.downloads + 1 }
          : r
      ));
      
      // Open resource
      window.open(resource.url, '_blank');
      
      // Show success notification
      const newNotification: OrbitNotification = {
        id: Date.now().toString(),
        type: 'success',
        title: 'Download Started',
        message: `${resource.title} (${resource.fileSize}) is being downloaded`,
        timestamp: new Date(),
        read: false,
        priority: 'medium'
      };
      
      setNotifications(prev => [newNotification, ...prev].slice(0, 20));
      
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
      localStorage.setItem('orbit_resources_enterprise', JSON.stringify(updatedResources));
      
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  }, [resources]);

  const handleBookmark = useCallback(async (resourceId: string) => {
    try {
      setResources(prev => prev.map(resource =>
        resource.id === resourceId
          ? { ...resource, isBookmarked: !resource.isBookmarked }
          : resource
      ));
      
      setFilteredResources(prev => prev.map(resource =>
        resource.id === resourceId
          ? { ...resource, isBookmarked: !resource.isBookmarked }
          : resource
      ));
      
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
    }
  }, []);

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
      case 'lab':
        return <Database className="w-5 h-5" />;
      case 'tutorial':
        return <Play className="w-5 h-5" />;
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
        return 'text-orange-400';
      case 'expert':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  // Render enterprise dashboard
  const renderDashboard = () => (
    <div className="orbit-content">
      {/* Welcome Section */}
      <div className="mb-12">
        <h1 className="orbit-heading-1">
          Welcome back, {user?.name || 'Enterprise User'}! 
        </h1>
        <p className="orbit-text-base">
          Your enterprise learning journey continues. Track your progress and explore new opportunities.
        </p>
      </div>

      {/* Enterprise Stats Grid */}
      <div className="orbit-stats mb-12">
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.totalResources.toLocaleString()}</div>
          <div className="orbit-stat-label">Total Resources</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.recentDownloads}</div>
          <div className="orbit-stat-label">Recent Downloads</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.favorites}</div>
          <div className="orbit-stat-label">Favorites</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.activeCourses}</div>
          <div className="orbit-stat-label">Active Courses</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.studyStreak}</div>
          <div className="orbit-stat-label">Day Streak</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.averageGrade}%</div>
          <div className="orbit-stat-label">Average Grade</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">#{stats.globalRank}</div>
          <div className="orbit-stat-label">Global Rank</div>
        </div>
        <div className="orbit-stat-card orbit-micro-hover">
          <div className="orbit-stat-value">{stats.points.toLocaleString()}</div>
          <div className="orbit-stat-label">Points</div>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="orbit-grid orbit-grid-cols-3 gap-8 mb-12">
        <div className="orbit-card orbit-micro-hover">
          <h3 className="orbit-heading-3 mb-6">Learning Progress</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="orbit-text-sm">Weekly Progress</span>
                <span className="orbit-text-sm font-semibold">{stats.weeklyProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 h-3 rounded-full"
                  style={{ width: `${stats.weeklyProgress}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="orbit-text-sm">Monthly Progress</span>
                <span className="orbit-text-sm font-semibold">{stats.monthlyProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full"
                  style={{ width: `${stats.monthlyProgress}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="orbit-text-sm">Yearly Progress</span>
                <span className="orbit-text-sm font-semibold">{stats.yearlyProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full"
                  style={{ width: `${stats.yearlyProgress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
        
        <div className="orbit-card orbit-micro-hover">
          <h3 className="orbit-heading-3 mb-6">Achievements</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400 mb-2">{stats.badges}</div>
              <div className="orbit-text-sm">Badges</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400 mb-2">{stats.certificates}</div>
              <div className="orbit-text-sm">Certificates</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400 mb-2">{stats.projects}</div>
              <div className="orbit-text-sm">Projects</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400 mb-2">{stats.completedLessons}</div>
              <div className="orbit-text-sm">Lessons</div>
            </div>
          </div>
        </div>
        
        <div className="orbit-card orbit-micro-hover">
          <h3 className="orbit-heading-3 mb-6">Quick Actions</h3>
          <div className="space-y-3">
            <button className="orbit-btn orbit-btn-primary w-full">
              <BookOpen className="w-4 h-4" />
              Browse Courses
            </button>
            <button className="orbit-btn orbit-btn-secondary w-full">
              <Target className="w-4 h-4" />
              Take Quiz
            </button>
            <button className="orbit-btn orbit-btn-accent w-full">
              <Award className="w-4 h-4" />
              View Achievements
            </button>
          </div>
        </div>
      </div>

      {/* Recent Resources */}
      <div>
        <div className="flex justify-between items-center mb-8">
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
                <div className="orbit-resource-icon orbit-micro-rotate">
                  {getResourceIcon(resource.type)}
                </div>
                <div className="orbit-resource-info">
                  <h3 className="orbit-resource-title">{resource.title}</h3>
                  <div className="orbit-resource-meta">
                    <span>{resource.category}</span>
                    <span>·</span>
                    <span>{resource.downloads.toLocaleString()} downloads</span>
                    <span>·</span>
                    <span>{resource.views.toLocaleString()} views</span>
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
                  <div className="flex justify-between text-sm mb-2">
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
              
              <div className="flex justify-between items-center mb-4">
                <div className="flex gap-4">
                  <span className="flex items-center gap-1 orbit-text-sm">
                    <Star className="w-4 h-4 text-yellow-400" />
                    {resource.rating}
                  </span>
                  <span className="flex items-center gap-1 orbit-text-sm">
                    <ThumbsUp className="w-4 h-4 text-green-400" />
                    {resource.likes}
                  </span>
                  <span className="flex items-center gap-1 orbit-text-sm">
                    <Share2 className="w-4 h-4 text-blue-400" />
                    {resource.shares}
                  </span>
                </div>
                <span className="orbit-text-sm">{resource.fileSize}</span>
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
                <button 
                  className="orbit-btn orbit-btn-ghost"
                  onClick={() => handleBookmark(resource.id)}
                >
                  <Bookmark className={`w-4 h-4 ${resource.isBookmarked ? 'fill-current text-blue-500' : ''}`} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Render other views (resources, profile, etc.) would go here...
  const renderResources = () => (
    <div className="orbit-content">
      <h1 className="orbit-heading-1 mb-8">All Resources</h1>
      
      {filteredResources.length > 0 ? (
        <div className="orbit-resource-grid">
          {filteredResources.map((resource) => (
            <div key={resource.id} className="orbit-resource-card orbit-card-interactive">
              {/* Resource card content */}
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

  // Loading state
  if (loading) {
    return (
      <div className="orbit-loading">
        <div className="orbit-spinner"></div>
        <div className="orbit-loading-text">Loading Enterprise Platform...</div>
        <div className="orbit-loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    );
  }

  return (
    <div className="orbit-enterprise-app" ref={containerRef}>
      {/* Enterprise Particle Effects */}
      <div className="orbit-particles">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="orbit-particle"
            style={{
              left: `${particle.x}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animationDelay: `${Math.random() * 10}s`,
              animationDuration: `${particle.duration}s`
            }}
          />
        ))}
      </div>

      {/* Enterprise Sidebar */}
      <aside className={`orbit-sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
        <div className="orbit-sidebar-header">
          <div className="flex items-center gap-4">
            <div className="orbit-avatar">
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <h2 className="orbit-heading-3">Orbit Enterprise</h2>
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

      {/* Enterprise Main Content */}
      <main className={`orbit-main ${sidebarOpen ? '' : 'full-width'}`}>
        {/* Enterprise Header */}
        <header className="orbit-header">
          <div className="orbit-header-content">
            <div className="flex items-center gap-6">
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
                  placeholder="Search resources, courses, instructors... (Ctrl+K)"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex items-center gap-4">
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
              
              {/* Enterprise Profile Dropdown */}
              <div className={`orbit-profile ${showProfileDropdown ? 'active' : ''}`}>
                <div className="flex items-center gap-3" onClick={() => setShowProfileDropdown(!showProfileDropdown)}>
                  <div className="orbit-avatar orbit-micro-scale">
                    {user?.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="orbit-profile-info">
                    <span className="orbit-profile-name">{user?.name}</span>
                    <span className="orbit-profile-role">{user?.role}</span>
                  </div>
                  <ChevronDown className="w-4 h-4" />
                </div>
                
                {/* Quick Profile Dropdown */}
                <div className="orbit-profile-dropdown">
                  <div className="orbit-profile-header">
                    <div className="orbit-avatar">
                      {user?.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold">{user?.name}</div>
                      <div className="orbit-text-sm">{user?.email}</div>
                      <div className="orbit-text-xs text-yellow-400">{user?.level} Level</div>
                    </div>
                  </div>
                  
                  <div className="orbit-profile-body">
                    <button className="orbit-btn orbit-btn-ghost w-full text-left">
                      <User className="w-4 h-4 mr-3" />
                      View Profile
                    </button>
                    <button className="orbit-btn orbit-btn-ghost w-full text-left">
                      <Award className="w-4 h-4 mr-3" />
                      Achievements
                    </button>
                    <button className="orbit-btn orbit-btn-ghost w-full text-left">
                      <Settings className="w-4 h-4 mr-3" />
                      Settings
                    </button>
                  </div>
                  
                  <div className="orbit-profile-footer">
                    <button className="orbit-btn orbit-btn-outline w-full text-left">
                      <SignOut className="w-4 h-4 mr-3" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'resources' && renderResources()}
        {currentView === 'profile' && <div className="orbit-content"><h1 className="orbit-heading-1">Profile</h1></div>}
        {currentView === 'notifications' && <div className="orbit-content"><h1 className="orbit-heading-1">Notifications</h1></div>}
        {currentView === 'settings' && <div className="orbit-content"><h1 className="orbit-heading-1">Settings</h1></div>}
        {currentView === 'analytics' && <div className="orbit-content"><h1 className="orbit-heading-1">Analytics</h1></div>}
      </main>

      {/* Enterprise Notifications */}
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
                <div className="orbit-text-sm">{notification.message}</div>
                <div className="orbit-text-xs mt-1">
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
