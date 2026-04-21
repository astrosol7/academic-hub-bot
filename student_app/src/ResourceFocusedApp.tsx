import { useEffect, useState, useCallback, useRef } from 'react';
import { Search, Download, Heart, Clock, BookOpen, FileText, Video, Code, Star, TrendingUp, Users } from 'lucide-react';
import { api, type SearchResult } from './api';
import './resource-focused-styles.css';

interface Resource {
  id: string;
  title: string;
  description: string;
  type: 'document' | 'video' | 'code' | 'course';
  category: string;
  tags: string[];
  downloads: number;
  rating: number;
  lastUpdated: string;
  url: string;
}

interface QuickStats {
  totalResources: number;
  recentDownloads: number;
  favorites: number;
  activeCourses: number;
}

export default function ResourceFocusedApp() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<QuickStats>({
    totalResources: 0,
    recentDownloads: 0,
    favorites: 0,
    activeCourses: 0
  });

  const searchTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = () => {
    loadMockData();
    loadCachedData();
    
    const tma = (window as any).Telegram?.WebApp;
    if (tma && tma.initData) {
      tma.ready();
      tma.expand();
    }
  };

  const loadCachedData = () => {
    const cachedFavorites = localStorage.getItem('voyager_favorites');
    const cachedRecent = localStorage.getItem('voyager_recent_searches');
    
    if (cachedFavorites) {
      setFavorites(JSON.parse(cachedFavorites));
    }
    if (cachedRecent) {
      setRecentSearches(JSON.parse(cachedRecent));
    }
  };

  const loadMockData = () => {
    const mockResources: Resource[] = [
      {
        id: '1',
        title: 'Introduction to Web Development',
        description: 'Complete guide to HTML, CSS, and JavaScript fundamentals',
        type: 'course',
        category: 'Web Development',
        tags: ['HTML', 'CSS', 'JavaScript', 'Beginner'],
        downloads: 1250,
        rating: 4.8,
        lastUpdated: '2024-01-15',
        url: '/resources/web-dev-intro'
      },
      {
        id: '2',
        title: 'React Components Tutorial',
        description: 'Learn how to build reusable React components with hooks',
        type: 'video',
        category: 'Frontend',
        tags: ['React', 'Components', 'Hooks', 'Tutorial'],
        downloads: 890,
        rating: 4.9,
        lastUpdated: '2024-01-14',
        url: '/resources/react-components'
      },
      {
        id: '3',
        title: 'Python Data Structures Cheat Sheet',
        description: 'Quick reference for Python data structures and algorithms',
        type: 'document',
        category: 'Programming',
        tags: ['Python', 'Data Structures', 'Algorithms', 'Reference'],
        downloads: 2100,
        rating: 4.7,
        lastUpdated: '2024-01-13',
        url: '/resources/python-cheatsheet'
      },
      {
        id: '4',
        title: 'Machine Learning Basics',
        description: 'Introduction to machine learning concepts and algorithms',
        type: 'course',
        category: 'Data Science',
        tags: ['Machine Learning', 'AI', 'Python', 'Beginner'],
        downloads: 1560,
        rating: 4.6,
        lastUpdated: '2024-01-12',
        url: '/resources/ml-basics'
      },
      {
        id: '5',
        title: 'CSS Grid Layout Examples',
        description: 'Practical examples of CSS Grid layouts for modern web design',
        type: 'code',
        category: 'CSS',
        tags: ['CSS', 'Grid', 'Layout', 'Examples'],
        downloads: 780,
        rating: 4.5,
        lastUpdated: '2024-01-11',
        url: '/resources/css-grid-examples'
      },
      {
        id: '6',
        title: 'JavaScript Async Programming',
        description: 'Master promises, async/await, and asynchronous JavaScript',
        type: 'video',
        category: 'JavaScript',
        tags: ['JavaScript', 'Async', 'Promises', 'Advanced'],
        downloads: 920,
        rating: 4.8,
        lastUpdated: '2024-01-10',
        url: '/resources/js-async'
      },
      {
        id: '7',
        title: 'Database Design Principles',
        description: 'Fundamental concepts of database design and normalization',
        type: 'document',
        category: 'Database',
        tags: ['Database', 'SQL', 'Design', 'Normalization'],
        downloads: 650,
        rating: 4.4,
        lastUpdated: '2024-01-09',
        url: '/resources/database-design'
      },
      {
        id: '8',
        title: 'Node.js REST API Guide',
        description: 'Build RESTful APIs with Node.js, Express, and MongoDB',
        type: 'course',
        category: 'Backend',
        tags: ['Node.js', 'Express', 'API', 'MongoDB'],
        downloads: 1100,
        rating: 4.7,
        lastUpdated: '2024-01-08',
        url: '/resources/nodejs-api'
      }
    ];

    setResources(mockResources);
    setStats({
      totalResources: mockResources.length,
      recentDownloads: 156,
      favorites: 23,
      activeCourses: 3
    });
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
        const results = await api.search(q);
        setSearchResults(results);
        
        setRecentSearches(prev => {
          const updated = [q, ...prev.filter(item => item !== q)].slice(0, 5);
          localStorage.setItem('voyager_recent_searches', JSON.stringify(updated));
          return updated;
        });
      } catch (error) {
        console.error('Search failed:', error);
        // Fallback to local search
        const filtered = resources.filter(resource =>
          resource.title.toLowerCase().includes(q.toLowerCase()) ||
          resource.description.toLowerCase().includes(q.toLowerCase()) ||
          resource.tags.some(tag => tag.toLowerCase().includes(q.toLowerCase()))
        );
        setSearchResults(filtered.map(r => ({
          resource_id: r.id,
          title: r.title,
          course_id: r.category,
          category_slug: r.type,
          week_number: null,
          score: 1.0
        })));
      } finally {
        setLoading(false);
      }
    }, 300);
  }, [resources]);

  const toggleFavorite = useCallback((resourceId: string) => {
    setFavorites(prev => {
      const updated = prev.includes(resourceId)
        ? prev.filter(id => id !== resourceId)
        : [...prev, resourceId];
      localStorage.setItem('voyager_favorites', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const handleDownload = useCallback((resource: Resource) => {
    // Simulate download
    console.log('Downloading:', resource.title);
    // In real app, this would trigger actual download
    window.open(resource.url, '_blank');
  }, []);

  const getResourceIcon = (type: Resource['type']) => {
    switch (type) {
      case 'document':
        return <FileText className="w-6 h-6" />;
      case 'video':
        return <Video className="w-6 h-6" />;
      case 'code':
        return <Code className="w-6 h-6" />;
      case 'course':
        return <BookOpen className="w-6 h-6" />;
      default:
        return <FileText className="w-6 h-6" />;
    }
  };

  const getResourceTypeColor = (type: Resource['type']) => {
    switch (type) {
      case 'document':
        return 'tag-primary';
      case 'video':
        return 'tag-accent';
      case 'code':
        return '';
      case 'course':
        return 'tag-primary';
      default:
        return '';
    }
  };

  const displayResources = searchQuery.length >= 2 
    ? resources.filter(resource =>
        resource.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        resource.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        resource.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : resources;

  return (
    <div className="resource-focused-app">
      {/* Header */}
      <header className="header">
        <div className="fast-access-container">
          <div className="header-content">
            <a href="#" className="logo">
              <div className="logo-icon">
                <BookOpen className="w-5 h-5" />
              </div>
              <span>Orbit Resources</span>
            </a>
            
            <div className="search-container">
              <Search className="search-icon w-5 h-5" />
              <input
                type="text"
                className="search-input"
                placeholder="Search resources, courses, materials..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                autoFocus
              />
              {loading && <div className="search-loading w-5 h-5" />}
            </div>
            
            <div className="quick-actions">
              <button className="btn btn-ghost btn-icon">
                <Heart className="w-5 h-5" />
                {favorites.length > 0 && (
                  <span className="badge bg-primary rounded-pill ms-1">
                    {favorites.length}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="fast-access-container">
          {/* Quick Stats */}
          <div className="stats-bar">
            <div className="stat-card">
              <div className="stat-value">{stats.totalResources}</div>
              <div className="stat-label">Resources</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.recentDownloads}</div>
              <div className="stat-label">Downloads</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.favorites}</div>
              <div className="stat-label">Favorites</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.activeCourses}</div>
              <div className="stat-label">Active Courses</div>
            </div>
          </div>

          {/* Recent Searches */}
          {recentSearches.length > 0 && !searchQuery && (
            <div className="recent-searches">
              <div className="recent-searches-title">Recent Searches</div>
              <div className="recent-searches-list">
                {recentSearches.map((term, index) => (
                  <button
                    key={index}
                    className="recent-search-item"
                    onClick={() => handleSearch(term)}
                  >
                    <Clock className="w-3 h-3 me-1" />
                    {term}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Search Results Header */}
          {searchQuery.length >= 2 && (
            <div className="search-results">
              <div className="search-results-header">
                <h2 className="search-results-title">
                  {displayResources.length > 0 ? 'Search Results' : 'No Results'}
                </h2>
                <span className="search-results-count">
                  {displayResources.length} {displayResources.length === 1 ? 'resource' : 'resources'}
                </span>
              </div>
            </div>
          )}

          {/* Resource Grid */}
          {displayResources.length > 0 ? (
            <div className="resource-grid">
              {displayResources.map((resource) => (
                <div key={resource.id} className="resource-card">
                  <button
                    className={`favorite-btn ${favorites.includes(resource.id) ? 'active' : ''}`}
                    onClick={() => toggleFavorite(resource.id)}
                  >
                    <Heart className="w-4 h-4" />
                  </button>
                  
                  <div className="resource-card-header">
                    <div className="resource-icon">
                      {getResourceIcon(resource.type)}
                    </div>
                    <div className="resource-info">
                      <h3 className="resource-title">{resource.title}</h3>
                      <div className="resource-meta">
                        {resource.category} · {resource.downloads.toLocaleString()} downloads
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-secondary mb-4">{resource.description}</p>
                  
                  <div className="resource-tags">
                    <span className={`tag ${getResourceTypeColor(resource.type)}`}>
                      {resource.type}
                    </span>
                    {resource.tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="tag">
                        {tag}
                      </span>
                    ))}
                  </div>
                  
                  <div className="resource-actions">
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleDownload(resource)}
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                    <button className="btn btn-secondary">
                      <Star className="w-4 h-4" />
                      {resource.rating}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : searchQuery.length >= 2 ? (
            <div className="empty-state">
              <Search className="empty-state-icon" />
              <h3 className="empty-state-title">No resources found</h3>
              <p className="empty-state-description">
                Try different keywords or browse all resources
              </p>
              <button 
                className="btn btn-primary"
                onClick={() => setSearchQuery('')}
              >
                Clear Search
              </button>
            </div>
          ) : (
            <div className="empty-state">
              <BookOpen className="empty-state-icon" />
              <h3 className="empty-state-title">Search for Resources</h3>
              <p className="empty-state-description">
                Enter keywords to find courses, documents, videos, and code examples
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
