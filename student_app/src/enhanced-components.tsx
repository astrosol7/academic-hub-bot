import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, BookOpen, User, ArrowLeft, Loader2, Download,
  Award, Zap, Eye, Heart, Clock, Sparkles, TrendingUp,
  Filter, Settings, Bell, Menu, X, Home, ChevronRight,
  Star, Calendar, FileText, Video, Headphones, Code,
  Database, Globe, Shield, BarChart3, Users, MessageSquare
} from 'lucide-react';

// Enhanced Search Component with Advanced Features
export const EnhancedSearch = ({ onSearch, recentSearches, loading }: any) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    onSearch(value);
    
    // Generate suggestions based on input
    if (value.length > 2) {
      const mockSuggestions = [
        `${value} for beginners`,
        `Advanced ${value}`,
        `${value} tutorial`,
        `${value} examples`,
        `${value} guide`
      ];
      setSuggestions(mockSuggestions.slice(0, 3));
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  return (
    <div className="enhanced-search-container">
      <div className="search-input-wrapper">
        <Search className="search-icon" />
        <input
          type="text"
          className="enhanced-search-input"
          placeholder="Search courses, materials, topics..."
          value={query}
          onChange={handleInputChange}
          autoFocus
        />
        {loading && (
          <div className="search-loading">
            <Loader2 className="animate-spin" />
          </div>
        )}
        
        {/* Search Filters */}
        <button className="search-filters-btn">
          <Filter className="w-4 h-4" />
        </button>
      </div>

      {/* Search Suggestions */}
      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="search-suggestions"
          >
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-item"
                onClick={() => {
                  setQuery(suggestion);
                  onSearch(suggestion);
                  setShowSuggestions(false);
                }}
              >
                <Search className="w-3 h-3" />
                {suggestion}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recent Searches */}
      {recentSearches.length > 0 && !query && (
        <div className="recent-searches">
          <h3>Recent Searches</h3>
          <div className="recent-search-tags">
            {recentSearches.map((term: string, index: number) => (
              <button
                key={index}
                className="recent-search-tag"
                onClick={() => {
                  setQuery(term);
                  onSearch(term);
                }}
              >
                <Clock className="w-3 h-3" />
                {term}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced Course Card Component
export const EnhancedCourseCard = ({ course, onFavorite, isFavorite, onDownload }: any) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      className="enhanced-course-card"
      whileHover={{ y: -4, scale: 1.02 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      <div className="card-header">
        <div className="course-icon">
          <BookOpen className="w-6 h-6" />
        </div>
        <div className="course-info">
          <h3 className="course-title">{course.title}</h3>
          <p className="course-meta">
            <Calendar className="w-3 h-3" />
            {course.week_count || 12} weeks
          </p>
        </div>
        <button
          className={`favorite-btn ${isFavorite ? 'active' : ''}`}
          onClick={() => onFavorite(course.id)}
        >
          <Heart className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} />
        </button>
      </div>

      <div className="card-content">
        <p className="course-description">
          {course.description || 'Master this comprehensive course with hands-on projects and real-world applications.'}
        </p>
        
        <div className="course-stats">
          <div className="stat">
            <Users className="w-4 h-4" />
            <span>{course.students || Math.floor(Math.random() * 1000 + 100)}</span>
          </div>
          <div className="stat">
            <Star className="w-4 h-4" />
            <span>{course.rating || (4.5 + Math.random() * 0.5).toFixed(1)}</span>
          </div>
          <div className="stat">
            <Clock className="w-4 h-4" />
            <span>{course.duration || Math.floor(Math.random() * 20 + 10)}h</span>
          </div>
        </div>
      </div>

      <div className="card-actions">
        <button className="btn btn-primary" onClick={() => onDownload(course)}>
          <Download className="w-4 h-4" />
          Download
        </button>
        <button className="btn btn-secondary">
          <Eye className="w-4 h-4" />
          Preview
        </button>
      </div>

      {/* Hover Effect Overlay */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="card-hover-overlay"
          >
            <div className="overlay-content">
              <h4>Quick Actions</h4>
              <div className="overlay-actions">
                <button className="overlay-btn">
                  <Video className="w-4 h-4" />
                  Videos
                </button>
                <button className="overlay-btn">
                  <FileText className="w-4 h-4" />
                  Notes
                </button>
                <button className="overlay-btn">
                  <Headphones className="w-4 h-4" />
                  Audio
                </button>
                <button className="overlay-btn">
                  <Code className="w-4 h-4" />
                  Code
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Enhanced Stats Dashboard Component
export const EnhancedStatsDashboard = ({ stats }: any) => {
  const statItems = [
    {
      icon: Download,
      label: 'Downloads',
      value: stats.totalDownloads,
      color: 'from-blue-400 to-blue-600',
      trend: '+12%',
      description: 'This month'
    },
    {
      icon: Heart,
      label: 'Favorites',
      value: stats.favoriteCount,
      color: 'from-red-400 to-pink-600',
      trend: '+5%',
      description: 'This week'
    },
    {
      icon: Zap,
      label: 'Study Streak',
      value: stats.studyStreak,
      color: 'from-yellow-400 to-orange-600',
      trend: 'Active',
      description: 'Keep it up!'
    },
    {
      icon: Award,
      label: 'Completed',
      value: stats.completedCourses,
      color: 'from-green-400 to-emerald-600',
      trend: '+2',
      description: 'This month'
    }
  ];

  return (
    <div className="enhanced-stats-dashboard">
      <div className="stats-grid">
        {statItems.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="stat-card"
          >
            <div className={`stat-icon-wrapper bg-gradient-to-r ${stat.color}`}>
              <stat.icon className="w-6 h-6 text-white" />
            </div>
            
            <div className="stat-content">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
              <div className="stat-trend">
                <TrendingUp className="w-3 h-3" />
                <span>{stat.trend}</span>
                <span className="stat-description">{stat.description}</span>
              </div>
            </div>

            {/* Progress Ring */}
            <div className="stat-progress">
              <svg className="progress-ring" viewBox="0 0 36 36">
                <path
                  className="progress-ring-bg"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="progress-ring-fill"
                  stroke-dasharray={`${(stat.value / 100) * 100}, 100`}
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Enhanced Notification Component
export const EnhancedNotifications = ({ notifications, onMarkAsRead, onDismiss }: any) => {
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');

  const filteredNotifications = notifications.filter((notif: any) => {
    if (filter === 'unread') return !notif.read;
    if (filter === 'read') return notif.read;
    return true;
  });

  return (
    <div className="enhanced-notifications">
      <div className="notifications-header">
        <h2>Notifications</h2>
        <div className="notification-filters">
          {(['all', 'unread', 'read'] as const).map((filterType) => (
            <button
              key={filterType}
              className={`filter-btn ${filter === filterType ? 'active' : ''}`}
              onClick={() => setFilter(filterType)}
            >
              {filterType.charAt(0).toUpperCase() + filterType.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="notifications-list">
        <AnimatePresence>
          {filteredNotifications.map((notification: any) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className={`notification-item ${notification.type} ${!notification.read ? 'unread' : ''}`}
            >
              <div className="notification-icon">
                {notification.type === 'success' && <Award className="w-5 h-5" />}
                {notification.type === 'warning' && <Bell className="w-5 h-5" />}
                {notification.type === 'error' && <Shield className="w-5 h-5" />}
                {notification.type === 'info' && <MessageSquare className="w-5 h-5" />}
              </div>
              
              <div className="notification-content">
                <h4>{notification.title}</h4>
                <p>{notification.message}</p>
                <span className="notification-time">
                  {new Date(notification.timestamp).toLocaleString()}
                </span>
              </div>

              <div className="notification-actions">
                {!notification.read && (
                  <button
                    className="mark-read-btn"
                    onClick={() => onMarkAsRead(notification.id)}
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
                <button
                  className="dismiss-btn"
                  onClick={() => onDismiss(notification.id)}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {filteredNotifications.length === 0 && (
          <div className="empty-state">
            <Bell className="w-12 h-12 opacity-50" />
            <p>No notifications</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Quick Actions Component
export const EnhancedQuickActions = ({ onAction }: any) => {
  const actions = [
    {
      icon: Search,
      label: 'Search Resources',
      description: 'Find exactly what you need',
      color: 'from-blue-500 to-cyan-600',
      action: 'search'
    },
    {
      icon: BookOpen,
      label: 'Browse Courses',
      description: 'Explore all available content',
      color: 'from-purple-500 to-pink-600',
      action: 'browse'
    },
    {
      icon: User,
      label: 'My Profile',
      description: 'View your progress',
      color: 'from-green-500 to-emerald-600',
      action: 'profile'
    },
    {
      icon: Database,
      label: 'Downloads',
      description: 'Access your files',
      color: 'from-orange-500 to-red-600',
      action: 'downloads'
    },
    {
      icon: BarChart3,
      label: 'Analytics',
      description: 'Track your progress',
      color: 'from-indigo-500 to-purple-600',
      action: 'analytics'
    },
    {
      icon: Settings,
      label: 'Settings',
      description: 'Customize your experience',
      color: 'from-gray-500 to-slate-600',
      action: 'settings'
    }
  ];

  return (
    <div className="enhanced-quick-actions">
      <h2 className="section-title">Quick Actions</h2>
      <div className="actions-grid">
        {actions.map((action, index) => (
          <motion.button
            key={action.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -4, scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`action-card bg-gradient-to-r ${action.color}`}
            onClick={() => onAction(action.action)}
          >
            <div className="action-icon">
              <action.icon className="w-8 h-8 text-white" />
            </div>
            <div className="action-content">
              <h3>{action.label}</h3>
              <p>{action.description}</p>
            </div>
            <ChevronRight className="action-arrow" />
          </motion.button>
        ))}
      </div>
    </div>
  );
};

// Enhanced Activity Feed Component
export const EnhancedActivityFeed = ({ activities }: any) => {
  return (
    <div className="enhanced-activity-feed">
      <h2 className="section-title">Recent Activity</h2>
      <div className="activity-timeline">
        <AnimatePresence>
          {activities.map((activity: any, index: number) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="activity-item"
            >
              <div className="activity-timeline-dot" />
              <div className="activity-content">
                <div className="activity-header">
                  <div className={`activity-icon ${activity.type}`}>
                    {activity.type === 'download' && <Download className="w-4 h-4" />}
                    {activity.type === 'favorite' && <Heart className="w-4 h-4" />}
                    {activity.type === 'complete' && <Award className="w-4 h-4" />}
                    {activity.type === 'search' && <Search className="w-4 h-4" />}
                  </div>
                  <div className="activity-info">
                    <h4>{activity.title}</h4>
                    <p>{activity.description}</p>
                  </div>
                  <span className="activity-time">
                    {new Date(activity.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {activities.length === 0 && (
          <div className="empty-state">
            <Clock className="w-12 h-12 opacity-50" />
            <p>No recent activity</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Loading Component
export const EnhancedLoading = ({ message = 'Loading...' }: any) => {
  return (
    <div className="enhanced-loading">
      <div className="loading-container">
        <div className="loading-animation">
          <div className="loading-orbit">
            <div className="loading-planet" />
          </div>
        </div>
        <div className="loading-text">
          <h3>{message}</h3>
          <div className="loading-dots">
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Empty State Component
export const EnhancedEmptyState = ({ 
  icon, 
  title, 
  description, 
  action 
}: any) => {
  const IconComponent = icon;

  return (
    <div className="enhanced-empty-state">
      <div className="empty-state-content">
        <div className="empty-state-icon">
          <IconComponent className="w-16 h-16" />
        </div>
        <h3>{title}</h3>
        <p>{description}</p>
        {action && (
          <button className="btn btn-primary" onClick={action.onClick}>
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
};
