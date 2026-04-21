import { startTransition, useDeferredValue, useEffect, useRef, useState } from 'react';
import type { ComponentType } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowUpRight,
  BadgeCheck,
  BookOpen,
  Building2,
  Clock3,
  Code2,
  Copy,
  FileText,
  Filter,
  Flame,
  Grid3x3,
  Heart,
  Layers3,
  LibraryBig,
  Link2,
  LoaderCircle,
  Rocket,
  Search,
  Sparkles,
  Video,
} from 'lucide-react';
import {
  api,
  type Course,
  type Institution,
  type MaterialCategory,
  type PublicResource,
  type ResourceFilters,
  type SearchResult,
} from './api';
import './interactive-modern-styles.css';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        initDataUnsafe?: {
          user?: {
            first_name?: string;
          };
        };
        ready?: () => void;
        expand?: () => void;
        setHeaderColor?: (color: string) => void;
        setBackgroundColor?: (color: string) => void;
        HapticFeedback?: {
          impactOccurred?: (style: string) => void;
          notificationOccurred?: (type: string) => void;
        };
      };
    };
    studentApp?: {
      showNotification?: (
        title: string,
        message: string,
        type?: 'info' | 'success' | 'warning' | 'error'
      ) => void;
      triggerHaptic?: (type?: string) => void;
    };
  }
}

type AppMode = 'discover' | 'saved';

interface DisplayResource {
  id: string;
  title: string;
  courseId: string;
  courseTitle: string;
  institutionSlug: string;
  institutionName: string;
  categorySlug: string;
  categoryName: string;
  weekNumber?: number;
  topicGroup?: string;
  tags: string[];
  sourceType: string;
  createdAt?: string;
  accessUrl?: string | null;
  availableInWeb: boolean;
  score?: number;
}

interface SavedResource extends DisplayResource {
  savedAt: string;
}

interface SearchSuggestion {
  id: string;
  text: string;
  type: 'recent' | 'suggestion' | 'course' | 'category';
  icon: ComponentType<{ className?: string }>;
}

const STORAGE_KEYS = {
  favorites: 'orbit_student_saved_resources',
  recentSearches: 'orbit_student_recent_searches',
  institution: 'orbit_student_institution',
};

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeStored<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value));
}

function toDisplayResource(resource: PublicResource | SearchResult): DisplayResource {
  if ('resource_id' in resource) {
    return {
      id: resource.resource_id,
      title: resource.title,
      courseId: resource.course_id,
      courseTitle: resource.course_title,
      institutionSlug: resource.institution_slug,
      institutionName: resource.institution_name,
      categorySlug: resource.category_slug,
      categoryName: resource.category_name,
      weekNumber: resource.week_number,
      topicGroup: resource.topic_group,
      tags: resource.tags ?? [],
      sourceType: resource.source_type,
      createdAt: resource.created_at,
      accessUrl: resource.access_url,
      availableInWeb: resource.available_in_web,
      score: resource.score,
    };
  }

  return {
    id: resource.id,
    title: resource.title,
    courseId: resource.course_id,
    courseTitle: resource.course_title,
    institutionSlug: resource.institution_slug,
    institutionName: resource.institution_name,
    categorySlug: resource.category_slug,
    categoryName: resource.category_name,
    weekNumber: resource.week_number,
    topicGroup: resource.topic_group,
    tags: resource.tags ?? [],
    sourceType: resource.source_type,
    createdAt: resource.created_at,
    accessUrl: resource.access_url,
    availableInWeb: resource.available_in_web,
  };
}

function formatSourceLabel(sourceType: string): string {
  if (sourceType === 'drive') {
    return 'Dashboard upload';
  }

  if (sourceType === 'admin') {
    return 'Admin curated';
  }

  if (sourceType === 'system') {
    return 'System sync';
  }

  return sourceType.replace(/[_-]/g, ' ');
}

function formatSearchEngine(engine: string): string {
  if (engine === 'tsquery_hit') {
    return 'Full-text search';
  }

  if (engine === 'trigram_hit') {
    return 'Fuzzy match';
  }

  return 'Live browse';
}

function formatAuthMode(authMode: 'checking' | 'verified' | 'preview' | 'failed'): string {
  if (authMode === 'verified') {
    return 'Telegram verified';
  }

  if (authMode === 'failed') {
    return 'Verification pending';
  }

  if (authMode === 'preview') {
    return 'Browser preview';
  }

  return 'Checking Telegram';
}

function formatTimestamp(timestamp?: string): string {
  if (!timestamp) {
    return 'Just now';
  }

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return 'Recently synced';
  }

  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function buildReference(resource: DisplayResource): string {
  return `${resource.title} | ${resource.courseId} | ${resource.id}`;
}

function buildResourceDescription(resource: DisplayResource): string {
  const details = [
    resource.courseTitle,
    resource.weekNumber ? `Week ${resource.weekNumber}` : resource.topicGroup || 'Flexible structure',
    formatSourceLabel(resource.sourceType),
  ];
  return details.join(' · ');
}

function getSourceTone(sourceType: string): string {
  if (sourceType === 'drive') {
    return 'tag-secondary';
  }

  if (sourceType === 'admin') {
    return 'tag-accent';
  }

  return 'tag-primary';
}

function matchesResource(resource: DisplayResource, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return true;
  }

  return [
    resource.title,
    resource.courseId,
    resource.courseTitle,
    resource.institutionName,
    resource.categoryName,
    resource.topicGroup || '',
    resource.tags.join(' '),
  ]
    .join(' ')
    .toLowerCase()
    .includes(normalized);
}

function getResourceIcon(resource: DisplayResource) {
  const slug = resource.categorySlug.toLowerCase();

  if (slug.includes('video') || slug.includes('lecture')) {
    return <Video className="w-6 h-6" />;
  }

  if (slug.includes('code') || slug.includes('lab') || slug.includes('project')) {
    return <Code2 className="w-6 h-6" />;
  }

  if (slug.includes('book') || slug.includes('exam') || slug.includes('sheet') || slug.includes('note')) {
    return <FileText className="w-6 h-6" />;
  }

  return <BookOpen className="w-6 h-6" />;
}

async function copyText(value: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = value;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
}

export default function InteractiveModernApp() {
  const [searchQuery, setSearchQuery] = useState('');
  const deferredQuery = useDeferredValue(searchQuery.trim());
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; size: number }>>([]);
  const [appMode, setAppMode] = useState<AppMode>('discover');
  const [showFilters, setShowFilters] = useState(true);
  const [studentName, setStudentName] = useState('Student');
  const [authMode, setAuthMode] = useState<'checking' | 'verified' | 'preview' | 'failed'>('checking');
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [categories, setCategories] = useState<MaterialCategory[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedInstitutionSlug, setSelectedInstitutionSlug] = useState('');
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [selectedCategorySlug, setSelectedCategorySlug] = useState('all');
  const [browseResources, setBrowseResources] = useState<DisplayResource[]>([]);
  const [searchResults, setSearchResults] = useState<DisplayResource[]>([]);
  const [searchEngine, setSearchEngine] = useState('none');
  const [apiSuggestions, setApiSuggestions] = useState<string[]>([]);
  const [savedResources, setSavedResources] = useState<SavedResource[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [bootLoading, setBootLoading] = useState(true);
  const [coursesLoading, setCoursesLoading] = useState(false);
  const [resourcesLoading, setResourcesLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [surfaceError, setSurfaceError] = useState<string | null>(null);
  const [coursesError, setCoursesError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null);
  const searchTimeoutRef = useRef<number | null>(null);

  const savedResourceIds = new Set(savedResources.map((resource) => resource.id));
  const selectedInstitution =
    institutions.find((institution) => institution.slug === selectedInstitutionSlug) ?? null;
  const selectedCourse = courses.find((course) => course.id === selectedCourseId) ?? null;

  const activeFilters: ResourceFilters = {
    institutionSlug: selectedInstitutionSlug || undefined,
    courseId: selectedCourseId || undefined,
    categorySlug: selectedCategorySlug !== 'all' ? selectedCategorySlug : undefined,
    limit: 18,
  };

  const discoverResources = deferredQuery.length >= 2 ? searchResults : browseResources;
  const visibleResources =
    appMode === 'saved'
      ? savedResources.filter((resource) => {
          const matchesFilters =
            (!selectedInstitutionSlug || resource.institutionSlug === selectedInstitutionSlug) &&
            (!selectedCourseId || resource.courseId === selectedCourseId) &&
            (selectedCategorySlug === 'all' || resource.categorySlug === selectedCategorySlug);

          return matchesFilters && matchesResource(resource, deferredQuery);
        })
      : discoverResources;

  const latestUploadCount = browseResources.filter((resource) =>
    ['drive', 'admin'].includes(resource.sourceType)
  ).length;

  const suggestionItems = createSuggestionItems({
    query: searchQuery,
    recentSearches,
    apiSuggestions,
    categories,
    courses,
  });

  useEffect(() => {
    const newParticles = Array.from({ length: 36 }, (_, index) => ({
      id: index,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 1,
    }));
    setParticles(newParticles);
  }, []);

  useEffect(() => {
    const storedResources = readStored<SavedResource[]>(STORAGE_KEYS.favorites, []);
    const storedSearches = readStored<string[]>(STORAGE_KEYS.recentSearches, []);
    const storedInstitution = readStored<string>(STORAGE_KEYS.institution, '');

    setSavedResources(storedResources);
    setRecentSearches(storedSearches);
    setSelectedInstitutionSlug(storedInstitution);

    let cancelled = false;

    async function bootstrap() {
      const tma = window.Telegram?.WebApp;
      const initData = tma?.initData;
      const firstName = tma?.initDataUnsafe?.user?.first_name;

      if (firstName) {
        setStudentName(firstName);
      }

      if (initData) {
        try {
          tma?.ready?.();
          tma?.expand?.();
          tma?.setHeaderColor?.('#0f172a');
          tma?.setBackgroundColor?.('#0f172a');
          await api.loginWithTelegram(initData);
          if (!cancelled) {
            setAuthMode('verified');
          }
        } catch {
          if (!cancelled) {
            setAuthMode('failed');
          }
        }
      } else {
        setAuthMode('preview');
      }

      const [institutionsResult, categoriesResult] = await Promise.allSettled([
        api.getInstitutions(),
        api.getCategories(),
      ]);

      if (cancelled) {
        return;
      }

      if (institutionsResult.status === 'fulfilled') {
        const nextInstitutions = institutionsResult.value;
        setInstitutions(nextInstitutions);

        if (!storedInstitution && nextInstitutions.length === 1) {
          const singleInstitution = nextInstitutions[0];
          setSelectedInstitutionSlug(singleInstitution.slug);
          writeStored(STORAGE_KEYS.institution, singleInstitution.slug);
        }
      }

      if (categoriesResult.status === 'fulfilled') {
        setCategories(categoriesResult.value);
      }

      if (
        institutionsResult.status === 'rejected' &&
        categoriesResult.status === 'rejected'
      ) {
        setSurfaceError('The live student index is offline. Start the API and try again.');
      } else if (institutionsResult.status === 'rejected') {
        setSurfaceError('Institutions could not be loaded, but the live resource feed may still work.');
      } else if (categoriesResult.status === 'rejected') {
        setSurfaceError('Category metadata is delayed, but resources can still sync.');
      } else {
        setSurfaceError(null);
      }

      setBootLoading(false);
    }

    void bootstrap();

    return () => {
      cancelled = true;
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!selectedInstitutionSlug) {
      setCourses([]);
      setCoursesError(null);
      setSelectedCourseId('');
      return;
    }

    let cancelled = false;
    setCoursesLoading(true);
    setCoursesError(null);

    api
      .getCourses(selectedInstitutionSlug)
      .then((nextCourses) => {
        if (cancelled) {
          return;
        }

        setCourses(nextCourses);
        setSelectedCourseId((current) =>
          nextCourses.some((course) => course.id === current) ? current : ''
        );
        setLastSyncAt(new Date().toISOString());
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        setCourses([]);
        setSelectedCourseId('');
        setCoursesError('Course sync is delayed for this institution right now.');
      })
      .finally(() => {
        if (!cancelled) {
          setCoursesLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedInstitutionSlug]);

  useEffect(() => {
    if (appMode === 'saved' || deferredQuery.length >= 2) {
      return;
    }

    let cancelled = false;
    setResourcesLoading(true);
    setSearchError(null);

    api
      .getResources(activeFilters)
      .then((items) => {
        if (cancelled) {
          return;
        }

        startTransition(() => {
          setBrowseResources(items.map(toDisplayResource));
          setSearchEngine('none');
        });
        setLastSyncAt(new Date().toISOString());
        setSurfaceError((current) =>
          current === 'The live feed could not refresh. Check the backend connection.' ||
          current === 'The live student index is offline. Start the API and try again.'
            ? null
            : current
        );
      })
      .catch(() => {
        if (!cancelled) {
          setSurfaceError('The live feed could not refresh. Check the backend connection.');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setResourcesLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [appMode, deferredQuery, selectedInstitutionSlug, selectedCourseId, selectedCategorySlug]);

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (appMode === 'saved' || deferredQuery.length < 2) {
      setSearchLoading(false);
      setSearchError(null);
      setSearchResults([]);
      setApiSuggestions([]);
      setSearchEngine('none');
      return;
    }

    setSearchLoading(true);
    setSearchError(null);

    searchTimeoutRef.current = window.setTimeout(async () => {
      try {
        const response = await api.search(deferredQuery, activeFilters);

        startTransition(() => {
          setSearchResults(response.results.map(toDisplayResource));
          setSearchEngine(response.engine);
          setApiSuggestions(response.suggestions);
        });

        setRecentSearches((current) => {
          const nextSearches = [deferredQuery, ...current.filter((item) => item !== deferredQuery)].slice(0, 8);
          writeStored(STORAGE_KEYS.recentSearches, nextSearches);
          return nextSearches;
        });
        setLastSyncAt(new Date().toISOString());
      } catch {
        setSearchResults([]);
        setApiSuggestions([]);
        setSearchEngine('none');
        setSearchError('Search could not reach the backend. The browse feed is still available.');
      } finally {
        setSearchLoading(false);
      }
    }, 280);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [appMode, deferredQuery, selectedInstitutionSlug, selectedCourseId, selectedCategorySlug]);

  function triggerImpact(style: string = 'light') {
    if (window.studentApp?.triggerHaptic) {
      window.studentApp.triggerHaptic(style);
      return;
    }

    try {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred?.(style);
    } catch {
      // Ignore environments without haptics.
    }
  }

  function emitNotification(
    title: string,
    message: string,
    type: 'success' | 'warning' | 'error' | 'info' = 'success'
  ) {
    window.studentApp?.showNotification?.(title, message, type);

    try {
      if (type === 'success') {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success');
      }
    } catch {
      // Ignore Telegram preview errors.
    }
  }

  function changeInstitution(slug: string) {
    triggerImpact('light');
    setSelectedInstitutionSlug(slug);
    setSelectedCourseId('');
    writeStored(STORAGE_KEYS.institution, slug);
    startTransition(() => {
      setAppMode('discover');
    });
  }

  function changeCategory(slug: string) {
    triggerImpact('light');
    setSelectedCategorySlug(slug);
    startTransition(() => {
      setAppMode('discover');
    });
  }

  function openDiscoverMode() {
    triggerImpact('light');
    startTransition(() => {
      setAppMode('discover');
    });
  }

  function openSavedMode() {
    triggerImpact('light');
    startTransition(() => {
      setAppMode('saved');
    });
  }

  function resetToLatestUploads() {
    triggerImpact('medium');
    setSearchQuery('');
    setSearchResults([]);
    setApiSuggestions([]);
    startTransition(() => {
      setAppMode('discover');
    });
  }

  function toggleSavedResource(resource: DisplayResource) {
    triggerImpact('light');
    setSavedResources((current) => {
      const exists = current.some((item) => item.id === resource.id);
      const nextSaved = exists
        ? current.filter((item) => item.id !== resource.id)
        : [{ ...resource, savedAt: new Date().toISOString() }, ...current].slice(0, 18);

      writeStored(STORAGE_KEYS.favorites, nextSaved);
      emitNotification(
        exists ? 'Removed from saved deck' : 'Added to saved deck',
        exists
          ? 'This resource has been removed from your quick-return list.'
          : 'This resource is now pinned in your saved study stack.',
        'success'
      );
      return nextSaved;
    });
  }

  async function handleCopyReference(resource: DisplayResource) {
    try {
      await copyText(buildReference(resource));
      emitNotification(
        'Reference copied',
        'You can paste the resource reference into the bot or another workflow.',
        'success'
      );
    } catch {
      emitNotification(
        'Copy failed',
        'Clipboard access is unavailable in this browser.',
        'error'
      );
    }
  }

  async function handlePrimaryAction(resource: DisplayResource) {
    if (resource.availableInWeb && resource.accessUrl) {
      triggerImpact('medium');
      window.open(resource.accessUrl, '_blank', 'noopener,noreferrer');
      emitNotification(
        'Opening resource',
        'A direct link is available for this item, so it is opening in a new tab.',
        'success'
      );
      return;
    }

    await handleCopyReference(resource);
  }

  function selectSuggestion(text: string) {
    triggerImpact('light');
    setSearchQuery(text);
    setShowSuggestions(false);
    startTransition(() => {
      setAppMode('discover');
    });
  }

  if (bootLoading) {
    return (
      <div className="interactive-modern-app">
        <div className="cosmic-background" />
        <div className="particles-container">
          {particles.map((particle) => (
            <div
              key={particle.id}
              className="particle"
              style={{
                left: `${particle.x}%`,
                width: `${particle.size}px`,
                height: `${particle.size}px`,
                animationDelay: `${Math.random() * 10}s`,
                animationDuration: `${10 + Math.random() * 10}s`,
              }}
            />
          ))}
        </div>

        <main className="main-content">
          <div className="loading-state">
            <div className="loading-spinner" />
            <p className="recent-searches-title">Orbit Student Surface</p>
            <h2 className="empty-state-title">Warming up the live student experience</h2>
            <p className="empty-state-description">
              Loading institutions, categories, Telegram state, and the latest active resources.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="interactive-modern-app">
      <div className="cosmic-background" />

      <div className="particles-container">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="particle"
            style={{
              left: `${particle.x}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animationDelay: `${Math.random() * 10}s`,
              animationDuration: `${10 + Math.random() * 10}s`,
            }}
          />
        ))}
      </div>

      <header className="header">
        <div className="header-content">
          <motion.button
            type="button"
            className="logo logo-button"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={resetToLatestUploads}
          >
            <div className="logo-icon">
              <Sparkles className="w-6 h-6" />
            </div>
            <span>Orbit Student</span>
          </motion.button>

          <div className="search-container">
            <div className="search-wrapper">
              <Search className="search-icon w-5 h-5" />
              <input
                type="text"
                className="search-input"
                placeholder="Search uploaded resources, courses, weeks, or categories..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => {
                  window.setTimeout(() => setShowSuggestions(false), 120);
                }}
              />
              {searchLoading && <LoaderCircle className="search-loading w-5 h-5" />}
            </div>

            <AnimatePresence>
              {showSuggestions && suggestionItems.length > 0 ? (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="search-suggestions"
                >
                  {suggestionItems.map((suggestion) => (
                    <button
                      key={suggestion.id}
                      type="button"
                      className="suggestion-item"
                      onClick={() => selectSuggestion(suggestion.text)}
                    >
                      <suggestion.icon className="suggestion-icon w-4 h-4" />
                      <span>{suggestion.text}</span>
                      <small className="suggestion-pill">{suggestion.type}</small>
                    </button>
                  ))}
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>

          <div className="quick-actions">
            <motion.button
              type="button"
              className="btn btn-ghost btn-icon"
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={() => {
                triggerImpact('light');
                setShowFilters((current) => !current);
              }}
              aria-label="Toggle filters"
            >
              <Filter className="w-5 h-5" />
            </motion.button>
            <motion.button
              type="button"
              className={`btn ${appMode === 'discover' ? 'btn-secondary' : 'btn-ghost'} btn-icon`}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={openDiscoverMode}
              aria-label="Open live feed"
            >
              <Grid3x3 className="w-5 h-5" />
            </motion.button>
            <motion.button
              type="button"
              className={`btn ${appMode === 'saved' ? 'btn-accent' : 'btn-ghost'} btn-icon`}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={openSavedMode}
              aria-label="Open saved resources"
            >
              <Heart className="w-5 h-5" />
              {savedResources.length > 0 ? (
                <span className="quick-action-badge">{savedResources.length}</span>
              ) : null}
            </motion.button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <motion.section
          className="hero-panel card"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="hero-copy">
            <p className="recent-searches-title">Psych-first student surface</p>
            <h1 className="hero-title">
              Live, motion-rich student UX with real admin uploads behind it.
            </h1>
            <p className="hero-description">
              {studentName}, this surface is now wired so ACTIVE resources from the backend can
              land here automatically. The search, saved deck, filters, and direct-open behavior
              all operate on live API data instead of mock cards.
            </p>

            <div className="hero-actions">
              <button type="button" className="btn btn-primary" onClick={resetToLatestUploads}>
                <Rocket className="w-4 h-4" />
                Latest uploads
              </button>
              <button type="button" className="btn btn-secondary" onClick={openSavedMode}>
                <Heart className="w-4 h-4" />
                Saved deck
              </button>
            </div>

            <div className="hero-proof-list">
              <div className="hero-proof-item">
                <BadgeCheck className="w-4 h-4" />
                <span>{formatAuthMode(authMode)}</span>
              </div>
              <div className="hero-proof-item">
                <Flame className="w-4 h-4" />
                <span>{latestUploadCount} recent dashboard/system items in feed</span>
              </div>
              <div className="hero-proof-item">
                <Clock3 className="w-4 h-4" />
                <span>{lastSyncAt ? `Last sync ${formatTimestamp(lastSyncAt)}` : 'Awaiting first sync'}</span>
              </div>
            </div>
          </div>

          <div className="hero-side">
            <p className="mini-label">Active lane</p>
            <h2>{selectedInstitution?.name ?? 'All institutions'}</h2>
            <p className="hero-side-copy">
              {selectedCourse
                ? `${selectedCourse.title} is selected, so the feed is narrowed to that course.`
                : 'Keep the feed wide or pick a course to create a more focused learning lane.'}
            </p>
            <div className="hero-side-stack">
              <div className="hero-side-row">
                <span>Institution</span>
                <strong>{selectedInstitution?.slug ?? 'Global feed'}</strong>
              </div>
              <div className="hero-side-row">
                <span>Course</span>
                <strong>{selectedCourse?.id ?? 'All courses'}</strong>
              </div>
              <div className="hero-side-row">
                <span>Category</span>
                <strong>
                  {selectedCategorySlug === 'all'
                    ? 'All materials'
                    : categories.find((category) => category.slug === selectedCategorySlug)?.name ||
                      selectedCategorySlug}
                </strong>
              </div>
            </div>
          </div>
        </motion.section>

        {surfaceError ? <div className="surface-banner">{surfaceError}</div> : null}
        {coursesError ? <div className="surface-banner secondary">{coursesError}</div> : null}
        {searchError ? <div className="surface-banner secondary">{searchError}</div> : null}

        <div className="stats-bar">
          {[
            {
              label: 'Visible Resources',
              value: visibleResources.length,
              icon: Layers3,
            },
            {
              label: 'Institutions',
              value: institutions.length,
              icon: Building2,
            },
            {
              label: 'Course Catalog',
              value: selectedInstitution ? courses.length : institutions.length > 0 ? 'Pick one' : 0,
              icon: LibraryBig,
            },
            {
              label: 'Saved Deck',
              value: savedResources.length,
              icon: Heart,
            },
            {
              label: 'Live Uploads',
              value: latestUploadCount,
              icon: Flame,
            },
            {
              label: 'Search Memory',
              value: recentSearches.length,
              icon: Clock3,
            },
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={stat.label}
                className="stat-card card"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 * index }}
                whileHover={{ y: -4, scale: 1.02 }}
              >
                <Icon className="w-6 h-6 mb-2" style={{ color: 'var(--primary)' }} />
                <div className="stat-value">{stat.value}</div>
                <div className="stat-label">{stat.label}</div>
              </motion.div>
            );
          })}
        </div>

        {showFilters ? (
          <motion.section
            className="filter-panel card"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="filter-header">
              <div>
                <p className="recent-searches-title">Dynamic controls</p>
                <h2 className="filter-title">Browse the live stream your way</h2>
              </div>
              <div className="filter-status">
                <span className="filter-status-pill">{formatSearchEngine(searchEngine)}</span>
              </div>
            </div>

            <div className="filter-group">
              <span className="filter-label">Institution</span>
              <div className="chip-row">
                <button
                  type="button"
                  className={`chip ${selectedInstitutionSlug === '' ? 'active' : ''}`}
                  onClick={() => changeInstitution('')}
                >
                  All campuses
                </button>
                {institutions.map((institution) => (
                  <button
                    key={institution.id}
                    type="button"
                    className={`chip ${selectedInstitutionSlug === institution.slug ? 'active' : ''}`}
                    onClick={() => changeInstitution(institution.slug)}
                  >
                    {institution.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-grid">
              <div className="filter-group">
                <span className="filter-label">Course</span>
                <label className="select-shell">
                  <LibraryBig className="w-4 h-4" />
                  <select
                    className="select-control"
                    value={selectedCourseId}
                    onChange={(event) => {
                      triggerImpact('light');
                      setSelectedCourseId(event.target.value);
                      startTransition(() => {
                        setAppMode('discover');
                      });
                    }}
                    disabled={!selectedInstitutionSlug || coursesLoading}
                  >
                    <option value="">
                      {selectedInstitutionSlug
                        ? coursesLoading
                          ? 'Loading courses...'
                          : 'All courses'
                        : 'Pick an institution first'}
                    </option>
                    {courses.map((course) => (
                      <option key={course.id} value={course.id}>
                        {course.id} · {course.title}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="filter-group">
                <span className="filter-label">Category</span>
                <div className="chip-row compact">
                  <button
                    type="button"
                    className={`chip ${selectedCategorySlug === 'all' ? 'active' : ''}`}
                    onClick={() => changeCategory('all')}
                  >
                    All materials
                  </button>
                  {categories.map((category) => (
                    <button
                      key={category.slug}
                      type="button"
                      className={`chip ${selectedCategorySlug === category.slug ? 'active' : ''}`}
                      onClick={() => changeCategory(category.slug)}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.section>
        ) : null}

        {recentSearches.length > 0 && !searchQuery ? (
          <motion.div
            className="recent-searches"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="recent-searches-title">Recent Searches</div>
            <div className="recent-searches-list">
              {recentSearches.map((term, index) => (
                <motion.button
                  key={term}
                  type="button"
                  className="recent-search-item"
                  onClick={() => selectSuggestion(term)}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.24 + index * 0.05 }}
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                >
                  <Clock3 className="w-3 h-3" />
                  {term}
                </motion.button>
              ))}
            </div>
          </motion.div>
        ) : null}

        <section className="resource-section-header">
          <div>
            <p className="recent-searches-title">
              {appMode === 'saved'
                ? 'Saved stack'
                : deferredQuery.length >= 2
                  ? 'Search results'
                  : 'Live resource feed'}
            </p>
            <h2 className="resource-section-title">
              {appMode === 'saved'
                ? 'Pinned resources that you can jump back into fast'
                : deferredQuery.length >= 2
                  ? `Dynamic results for "${deferredQuery}"`
                  : 'Fresh resources flowing from the active backend index'}
            </h2>
            <p className="resource-section-copy">
              {appMode === 'saved'
                ? 'Saved items stay local to the student app, but they still respect your active institution, course, category, and search filters.'
                : deferredQuery.length >= 2
                  ? `Using ${formatSearchEngine(searchEngine).toLowerCase()} with your current filters to find the best matching resources.`
                  : 'Anything ACTIVE and exposed by the public API can appear here, including admin or dashboard-ingested uploads.'}
            </p>
          </div>
          <div className="resource-count-pill">{visibleResources.length} visible</div>
        </section>

        {resourcesLoading || searchLoading ? (
          <div className="loading-state">
            <div className="loading-spinner" />
            <p className="recent-searches-title">
              {searchLoading ? 'Searching the live index' : 'Refreshing the feed'}
            </p>
            <p className="empty-state-description">
              {searchLoading
                ? 'Looking for exact and fuzzy matches across active resources.'
                : 'Pulling the latest resources from the backend so uploaded items can surface here.'}
            </p>
          </div>
        ) : visibleResources.length > 0 ? (
          <div className="resource-grid">
            {visibleResources.map((resource, index) => (
              <motion.article
                key={resource.id}
                className="resource-card card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(index * 0.05, 0.4) }}
                whileHover={{ y: -6, scale: 1.015 }}
              >
                <motion.button
                  type="button"
                  className={`favorite-btn ${savedResourceIds.has(resource.id) ? 'active' : ''}`}
                  onClick={() => toggleSavedResource(resource)}
                  whileHover={{ scale: 1.15, rotate: 12 }}
                  whileTap={{ scale: 0.9 }}
                  aria-label={savedResourceIds.has(resource.id) ? 'Remove from saved deck' : 'Save resource'}
                >
                  <Heart className="w-4 h-4" />
                </motion.button>

                <div className="resource-card-header">
                  <motion.div
                    className="resource-icon"
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.5 }}
                  >
                    {getResourceIcon(resource)}
                  </motion.div>
                  <div className="resource-info">
                    <div className="resource-title-row">
                      <h3 className="resource-title">{resource.title}</h3>
                      {resource.score ? (
                        <span className="resource-score-pill">
                          {Math.max(1, Math.round(resource.score * 100))}% match
                        </span>
                      ) : null}
                    </div>
                    <div className="resource-meta">
                      <Building2 className="w-4 h-4" />
                      <span>{resource.institutionName || resource.institutionSlug}</span>
                      <span>·</span>
                      <span>{resource.categoryName}</span>
                    </div>
                    <div className="resource-meta">
                      <LibraryBig className="w-4 h-4" />
                      <span>{resource.courseTitle}</span>
                      <span>·</span>
                      <span>{resource.courseId}</span>
                    </div>
                  </div>
                </div>

                <p className="resource-description">{buildResourceDescription(resource)}</p>

                <div className="resource-tags">
                  <span className={`tag ${getSourceTone(resource.sourceType)}`}>
                    {formatSourceLabel(resource.sourceType)}
                  </span>
                  {resource.weekNumber ? <span className="tag">Week {resource.weekNumber}</span> : null}
                  {resource.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="resource-supporting">
                  <div className="resource-meta">
                    <Clock3 className="w-4 h-4" />
                    <span>{formatTimestamp(resource.createdAt)}</span>
                  </div>

                  {!resource.availableInWeb ? (
                    <div className="resource-link-note">
                      <Link2 className="w-4 h-4" />
                      <span>
                        No direct web URL yet. Copy the reference for bot handoff or internal retrieval.
                      </span>
                    </div>
                  ) : null}
                </div>

                <div className="resource-actions">
                  <motion.button
                    type="button"
                    className="btn btn-primary"
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => {
                      void handlePrimaryAction(resource);
                    }}
                  >
                    {resource.availableInWeb ? (
                      <>
                        <ArrowUpRight className="w-4 h-4" />
                        Open resource
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy ref
                      </>
                    )}
                  </motion.button>

                  <motion.button
                    type="button"
                    className={savedResourceIds.has(resource.id) ? 'btn btn-accent' : 'btn btn-secondary'}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => toggleSavedResource(resource)}
                  >
                    <Heart className="w-4 h-4" />
                    {savedResourceIds.has(resource.id) ? 'Saved' : 'Save'}
                  </motion.button>
                </div>
              </motion.article>
            ))}
          </div>
        ) : (
          <motion.div
            className="empty-state"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="empty-state-icon" style={{ position: 'relative' }}>
              <Sparkles className="w-full h-full" />
            </div>
            <h3 className="empty-state-title">
              {appMode === 'saved'
                ? 'Your saved deck is empty in this filter'
                : deferredQuery.length >= 2
                  ? 'No live results matched that query'
                  : 'The live feed is ready for content'}
            </h3>
            <p className="empty-state-description">
              {appMode === 'saved'
                ? 'Save a few resources from the live feed and they will show up here for quick return.'
                : deferredQuery.length >= 2
                  ? 'Try broadening the query, clearing a filter, or waiting for more resources to be uploaded.'
                  : 'Once resources are uploaded and ACTIVE in the backend, they will surface here automatically.'}
            </p>
            <div className="empty-action-row">
              <button type="button" className="btn btn-primary" onClick={resetToLatestUploads}>
                <Rocket className="w-4 h-4" />
                Show live feed
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setSearchQuery('')}>
                <Search className="w-4 h-4" />
                Clear search
              </button>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}

function createSuggestionItems(input: {
  query: string;
  recentSearches: string[];
  apiSuggestions: string[];
  categories: MaterialCategory[];
  courses: Course[];
}): SearchSuggestion[] {
  const items: SearchSuggestion[] = [];
  const seen = new Set<string>();
  const normalizedQuery = input.query.trim().toLowerCase();

  function push(text: string, type: SearchSuggestion['type'], icon: ComponentType<{ className?: string }>) {
    const normalized = text.trim().toLowerCase();
    if (!normalized || seen.has(normalized)) {
      return;
    }

    seen.add(normalized);
    items.push({
      id: `${type}-${normalized}`,
      text,
      type,
      icon,
    });
  }

  input.recentSearches.slice(0, 3).forEach((term) => push(term, 'recent', Clock3));
  input.apiSuggestions.slice(0, 3).forEach((term) => push(term, 'suggestion', Sparkles));

  if (normalizedQuery) {
    input.categories
      .filter((category) => category.name.toLowerCase().includes(normalizedQuery))
      .slice(0, 2)
      .forEach((category) => push(category.name, 'category', Layers3));

    input.courses
      .filter(
        (course) =>
          course.title.toLowerCase().includes(normalizedQuery) ||
          course.id.toLowerCase().includes(normalizedQuery)
      )
      .slice(0, 2)
      .forEach((course) => push(course.title, 'course', LibraryBig));
  }

  return items.slice(0, 8);
}
