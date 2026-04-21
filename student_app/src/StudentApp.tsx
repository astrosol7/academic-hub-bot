import { startTransition, useDeferredValue, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowRight,
  BadgeCheck,
  Bookmark,
  BookmarkCheck,
  Bot,
  Building2,
  ChevronRight,
  Clock3,
  Compass,
  Copy,
  Flame,
  GraduationCap,
  Home,
  Layers3,
  LibraryBig,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react'
import { api, type Course, type Institution, type MaterialCategory, type SearchResult } from './api'

type StudentView = 'overview' | 'search' | 'courses' | 'profile'
type AuthState = 'checking' | 'verified' | 'preview' | 'failed'

interface SavedResource extends SearchResult {
  saved_at: string
}

interface ToastState {
  kind: 'success' | 'error'
  message: string
}

const STORAGE_KEYS = {
  savedResources: 'student_app_saved_resources',
  recentSearches: 'student_app_recent_searches',
  selectedInstitution: 'student_app_selected_institution',
}

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function writeStored<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value))
}

function emitImpact(style: 'light' | 'medium' = 'light') {
  try {
    (window as any).Telegram?.WebApp?.HapticFeedback?.impactOccurred?.(style)
  } catch {
    // Ignore Telegram preview failures.
  }
}

function emitNotification(type: 'success' | 'error' | 'warning') {
  try {
    (window as any).Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.(type)
  } catch {
    // Ignore Telegram preview failures.
  }
}

function formatCategoryLabel(slug: string, categories: MaterialCategory[]) {
  const match = categories.find((category) => category.slug === slug)
  if (match) {
    return match.name
  }

  return slug
    .split(/[_-]/g)
    .filter(Boolean)
    .map((segment) => segment[0]?.toUpperCase() + segment.slice(1))
    .join(' ')
}

function formatSearchEngine(engine: string) {
  if (engine === 'tsquery_hit') {
    return 'Full-text match'
  }

  if (engine === 'trigram_hit') {
    return 'Fuzzy match'
  }

  return 'Suggestion mode'
}

function formatAuthLabel(authState: AuthState) {
  if (authState === 'verified') {
    return 'Telegram verified'
  }

  if (authState === 'failed') {
    return 'Verification pending'
  }

  if (authState === 'preview') {
    return 'Browser preview'
  }

  return 'Checking Telegram'
}

function formatSyncTime(timestamp: string | null) {
  if (!timestamp) {
    return 'Waiting for first sync'
  }

  return `Synced ${new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

export default function StudentApp() {
  const [view, setView] = useState<StudentView>('overview')
  const [authState, setAuthState] = useState<AuthState>('checking')
  const [studentName, setStudentName] = useState('SIT Student')
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [categories, setCategories] = useState<MaterialCategory[]>([])
  const [selectedInstitution, setSelectedInstitution] = useState<Institution | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [savedResources, setSavedResources] = useState<SavedResource[]>([])
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const deferredQuery = useDeferredValue(searchQuery.trim())
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchEngine, setSearchEngine] = useState('none')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [bootLoading, setBootLoading] = useState(true)
  const [searchLoading, setSearchLoading] = useState(false)
  const [coursesLoading, setCoursesLoading] = useState(false)
  const [surfaceError, setSurfaceError] = useState<string | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [coursesError, setCoursesError] = useState<string | null>(null)
  const [toast, setToast] = useState<ToastState | null>(null)
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null)
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const savedResourceIds = new Set(savedResources.map((resource) => resource.resource_id))
  const filteredResults =
    selectedCategory === 'all'
      ? searchResults
      : searchResults.filter((result) => result.category_slug === selectedCategory)

  function showToast(kind: ToastState['kind'], message: string) {
    setToast({ kind, message })
  }

  function changeView(nextView: StudentView) {
    emitImpact('light')
    startTransition(() => {
      setView(nextView)
    })
  }

  async function loadCoursesForInstitution(
    institution: Institution,
    options?: { focusView?: boolean; silent?: boolean },
  ) {
    const focusView = options?.focusView ?? true
    const silent = options?.silent ?? false

    if (!silent) {
      emitImpact('light')
    }

    setSelectedInstitution(institution)
    setCoursesError(null)
    setCoursesLoading(true)
    writeStored(STORAGE_KEYS.selectedInstitution, institution.slug)

    if (focusView) {
      startTransition(() => {
        setView('courses')
      })
    }

    try {
      const nextCourses = await api.getCourses(institution.slug)
      setCourses(nextCourses)
      setLastSyncAt(new Date().toISOString())
    } catch {
      setCourses([])
      setCoursesError('Unable to load courses for this institution right now.')
      showToast('error', 'Course sync failed')
      emitNotification('error')
    } finally {
      setCoursesLoading(false)
    }
  }

  function handleSaveResource(result: SearchResult) {
    emitImpact('light')
    setSavedResources((current) => {
      const exists = current.some((resource) => resource.resource_id === result.resource_id)
      const nextSaved = exists
        ? current.filter((resource) => resource.resource_id !== result.resource_id)
        : [{ ...result, saved_at: new Date().toISOString() }, ...current].slice(0, 16)

      writeStored(STORAGE_KEYS.savedResources, nextSaved)
      return nextSaved
    })

    const isSaved = savedResourceIds.has(result.resource_id)
    showToast('success', isSaved ? 'Saved resource removed' : 'Saved resource pinned')
    emitNotification('success')
  }

  async function handleCopyReference(result: SearchResult) {
    const reference = `${result.title} | ${result.course_id} | ${result.resource_id}`

    try {
      await navigator.clipboard.writeText(reference)
      showToast('success', 'Resource reference copied')
      emitNotification('success')
    } catch {
      showToast('error', 'Clipboard is unavailable in this browser')
      emitNotification('error')
    }
  }

  function handleSuggestionClick(term: string) {
    emitImpact('light')
    startTransition(() => {
      setView('search')
      setSearchQuery(term)
    })
  }

  useEffect(() => {
    const storedResources = readStored<SavedResource[]>(STORAGE_KEYS.savedResources, [])
    const storedRecentSearches = readStored<string[]>(STORAGE_KEYS.recentSearches, [])

    setSavedResources(storedResources)
    setRecentSearches(storedRecentSearches)

    let cancelled = false

    async function bootstrap() {
      const tma = (window as any).Telegram?.WebApp
      const initData = tma?.initData
      const firstName = tma?.initDataUnsafe?.user?.first_name

      if (firstName) {
        setStudentName(firstName)
      }

      if (initData) {
        try {
          tma.ready?.()
          tma.expand?.()
          tma.setHeaderColor?.('#0c1020')
          tma.setBackgroundColor?.('#081119')
          await api.loginWithTelegram(initData)
          if (!cancelled) {
            setAuthState('verified')
          }
        } catch {
          if (!cancelled) {
            setAuthState('failed')
          }
        }
      } else {
        setAuthState('preview')
      }

      const [institutionsResult, categoriesResult] = await Promise.allSettled([
        api.getInstitutions(),
        api.getCategories(),
      ])

      if (cancelled) {
        return
      }

      if (institutionsResult.status === 'fulfilled') {
        setInstitutions(institutionsResult.value)

        const storedSlug = readStored<string | null>(STORAGE_KEYS.selectedInstitution, null)
        const restoredInstitution = institutionsResult.value.find(
          (institution) => institution.slug === storedSlug,
        )

        if (restoredInstitution) {
          void loadCoursesForInstitution(restoredInstitution, {
            focusView: false,
            silent: true,
          })
        }
      }

      if (categoriesResult.status === 'fulfilled') {
        setCategories(categoriesResult.value)
      }

      if (
        institutionsResult.status === 'rejected' &&
        categoriesResult.status === 'rejected'
      ) {
        setSurfaceError('The student index is unavailable. Check that the API is running.')
      } else if (institutionsResult.status === 'rejected') {
        setSurfaceError('Institution discovery is unavailable right now.')
      } else if (categoriesResult.status === 'rejected') {
        setSurfaceError('Category metadata could not be loaded, but search still works.')
      }

      setLastSyncAt(new Date().toISOString())
      setBootLoading(false)
    }

    void bootstrap()

    return () => {
      cancelled = true
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!toast) {
      return
    }

    const timeout = setTimeout(() => {
      setToast(null)
    }, 2400)

    return () => clearTimeout(timeout)
  }, [toast])

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (deferredQuery.length < 2) {
      setSearchLoading(false)
      setSearchError(null)
      setSearchResults([])
      setSearchEngine('none')
      setSuggestions([])
      return
    }

    setSearchLoading(true)
    setSearchError(null)

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await api.search(deferredQuery)

        startTransition(() => {
          setSearchResults(response.results)
          setSearchEngine(response.engine)
          setSuggestions(response.suggestions)
        })

        setRecentSearches((current) => {
          const nextSearches = [deferredQuery, ...current.filter((item) => item !== deferredQuery)].slice(0, 8)
          writeStored(STORAGE_KEYS.recentSearches, nextSearches)
          return nextSearches
        })

        setLastSyncAt(new Date().toISOString())
      } catch {
        setSearchError('Search could not reach the backend. Try again in a moment.')
        setSearchResults([])
        setSearchEngine('none')
        setSuggestions([])
      } finally {
        setSearchLoading(false)
      }
    }, 320)

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [deferredQuery])

  if (bootLoading) {
    return (
      <div className="student-shell">
        <div className="student-backdrop" />
        <main className="student-loading">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.4, repeat: Infinity, ease: 'linear' }}
            className="student-loading-ring"
          >
            <Sparkles />
          </motion.div>
          <p className="student-loading-kicker">Orbit Student Deck</p>
          <h1 className="student-loading-title">Syncing your student workspace</h1>
          <p className="student-loading-copy">
            Checking Telegram identity, loading institutions, and warming up search.
          </p>
        </main>
      </div>
    )
  }

  return (
    <div className="student-shell">
      <div className="student-backdrop" />
      <div className="student-app">
        <motion.header
          className="topbar"
          initial={{ opacity: 0, y: -24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <div>
            <p className="eyebrow">SIT Academic Hub</p>
            <h1 className="topbar-title">Orbit Student Deck</h1>
          </div>

          <div className="topbar-meta">
            <StatusPill
              icon={<ShieldCheck className="w-4 h-4" />}
              label={formatAuthLabel(authState)}
              tone={authState === 'verified' ? 'success' : authState === 'failed' ? 'warning' : 'neutral'}
            />
            <StatusPill
              icon={<RefreshCw className="w-4 h-4" />}
              label={formatSyncTime(lastSyncAt)}
              tone="neutral"
            />
          </div>
        </motion.header>

        {surfaceError ? (
          <motion.div
            className="system-banner"
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {surfaceError}
          </motion.div>
        ) : null}

        <AnimatePresence mode="wait">
          <motion.main
            key={view}
            className="view-stack"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -18 }}
            transition={{ duration: 0.28 }}
          >
            {view === 'overview' ? (
              <>
                <section className="panel hero-panel">
                  <div className="hero-copy-block">
                    <p className="eyebrow">Student command layer</p>
                    <h2 className="hero-title">
                      Search materials fast, keep your course stream close, and hand off clean references.
                    </h2>
                    <p className="hero-copy">
                      {studentName}, this student app now rides the real API. Institutions, courses, categories, and search suggestions all sync from the backend instead of mock data.
                    </p>
                    <div className="action-row">
                      <button type="button" className="btn btn-primary" onClick={() => changeView('search')}>
                        Search resources
                        <ArrowRight className="w-4 h-4" />
                      </button>
                      <button type="button" className="btn btn-secondary" onClick={() => changeView('courses')}>
                        Browse institutions
                        <Compass className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="hero-aside">
                    <p className="mini-label">Current lane</p>
                    <h3>{selectedInstitution?.name ?? 'Choose an institution'}</h3>
                    <p>
                      {selectedInstitution
                        ? `${coursesLoading ? 'Loading' : courses.length} courses indexed for ${selectedInstitution.slug}.`
                        : 'Pick an institution once and the app will remember it here.'}
                    </p>
                    {selectedInstitution ? (
                      <button type="button" className="btn btn-ghost" onClick={() => changeView('courses')}>
                        Open course list
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    ) : null}
                  </div>
                </section>

                <section className="stats-grid">
                  <StatCard icon={<Building2 className="w-5 h-5" />} label="Institutions" value={institutions.length.toString()} />
                  <StatCard icon={<Layers3 className="w-5 h-5" />} label="Categories" value={categories.length.toString()} />
                  <StatCard icon={<BookmarkCheck className="w-5 h-5" />} label="Saved resources" value={savedResources.length.toString()} />
                  <StatCard
                    icon={<ShieldCheck className="w-5 h-5" />}
                    label="Access mode"
                    value={authState === 'verified' ? 'Live' : 'Preview'}
                  />
                </section>

                <section className="overview-grid">
                  <div className="panel section-card">
                    <SectionHeading kicker="Jump Back In" title="Saved resources" />
                    {savedResources.length > 0 ? (
                      <div className="saved-list">
                        {savedResources.slice(0, 4).map((resource) => (
                          <button
                            key={resource.resource_id}
                            type="button"
                            className="saved-item"
                            onClick={() => {
                              setSearchQuery(resource.title)
                              changeView('search')
                            }}
                          >
                            <div>
                              <p className="saved-item-title">{resource.title}</p>
                              <p className="saved-item-meta">
                                {resource.course_id} · {formatCategoryLabel(resource.category_slug, categories)}
                              </p>
                            </div>
                            <BookmarkCheck className="w-4 h-4" />
                          </button>
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        title="No saved references yet"
                        copy="Pin useful search results here so you can jump back into them later."
                      />
                    )}
                  </div>

                  <div className="panel section-card">
                    <SectionHeading kicker="Quick Filters" title="Material categories" />
                    <div className="chip-row">
                      {categories.length > 0 ? (
                        categories.slice(0, 8).map((category) => (
                          <button
                            key={category.slug}
                            type="button"
                            className="chip"
                            onClick={() => {
                              setSelectedCategory(category.slug)
                              changeView('search')
                            }}
                          >
                            {category.name}
                          </button>
                        ))
                      ) : (
                        <p className="muted-copy">Categories will appear here once the backend responds.</p>
                      )}
                    </div>

                    <div className="profile-note">
                      <Flame className="w-4 h-4" />
                      <span>
                        Recent searches: {recentSearches.length > 0 ? recentSearches.join(', ') : 'none yet'}
                      </span>
                    </div>
                  </div>
                </section>
              </>
            ) : null}

            {view === 'search' ? (
              <>
                <section className="panel section-card">
                  <SectionHeading kicker="Search" title="Query the academic index" />
                  <label className="search-field">
                    <Search className="w-5 h-5" />
                    <input
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      placeholder="Try data structures, physics exam, or week 3..."
                    />
                  </label>

                  <div className="search-summary">
                    <span>
                      {deferredQuery.length < 2
                        ? 'Type at least two characters to start searching.'
                        : `${filteredResults.length} visible results for "${deferredQuery}"`}
                    </span>
                    <span className="engine-pill">{formatSearchEngine(searchEngine)}</span>
                  </div>
                </section>

                {recentSearches.length > 0 ? (
                  <section className="panel section-card">
                    <SectionHeading kicker="Quick Repeat" title="Recent searches" />
                    <div className="chip-row">
                      {recentSearches.map((term) => (
                        <button key={term} type="button" className="chip" onClick={() => handleSuggestionClick(term)}>
                          {term}
                        </button>
                      ))}
                    </div>
                  </section>
                ) : null}

                <section className="panel section-card">
                  <SectionHeading kicker="Refine" title="Material filters" />
                  <div className="chip-row">
                    <button
                      type="button"
                      className={`chip ${selectedCategory === 'all' ? 'active' : ''}`}
                      onClick={() => setSelectedCategory('all')}
                    >
                      All categories
                    </button>
                    {categories.map((category) => (
                      <button
                        key={category.slug}
                        type="button"
                        className={`chip ${selectedCategory === category.slug ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(category.slug)}
                      >
                        {category.name}
                      </button>
                    ))}
                  </div>
                </section>

                {suggestions.length > 0 && !searchLoading ? (
                  <section className="panel section-card">
                    <SectionHeading kicker="Suggestions" title="Closest matches" />
                    <div className="chip-row">
                      {suggestions.map((term) => (
                        <button key={term} type="button" className="chip" onClick={() => handleSuggestionClick(term)}>
                          {term}
                        </button>
                      ))}
                    </div>
                  </section>
                ) : null}

                {searchError ? (
                  <div className="panel section-card">
                    <EmptyState title="Search is temporarily unavailable" copy={searchError} />
                  </div>
                ) : null}

                {searchLoading ? (
                  <section className="result-list">
                    {Array.from({ length: 3 }).map((_, index) => (
                      <div key={index} className="panel result-card skeleton-card">
                        <div className="skeleton-line skeleton-line-short" />
                        <div className="skeleton-line" />
                        <div className="skeleton-line skeleton-line-mid" />
                      </div>
                    ))}
                  </section>
                ) : filteredResults.length > 0 ? (
                  <section className="result-list">
                    {filteredResults.map((result) => (
                      <article key={result.resource_id} className="panel result-card">
                        <div className="result-header">
                          <div className="result-badges">
                            <span>{formatCategoryLabel(result.category_slug, categories)}</span>
                            <span>{result.course_id}</span>
                            {result.week_number ? <span>Week {result.week_number}</span> : null}
                          </div>
                          <button
                            type="button"
                            className="icon-button"
                            onClick={() => handleSaveResource(result)}
                            aria-label={savedResourceIds.has(result.resource_id) ? 'Remove saved resource' : 'Save resource'}
                          >
                            {savedResourceIds.has(result.resource_id) ? (
                              <BookmarkCheck className="w-4 h-4" />
                            ) : (
                              <Bookmark className="w-4 h-4" />
                            )}
                          </button>
                        </div>

                        <h3 className="result-title">{result.title}</h3>

                        <div className="result-footer">
                          <div className="result-score">
                            <Clock3 className="w-4 h-4" />
                            <span>{Math.max(1, Math.round(result.score * 100))}% relevance</span>
                          </div>

                          <div className="result-actions">
                            <button type="button" className="btn btn-ghost compact" onClick={() => handleCopyReference(result)}>
                              Copy ref
                              <Copy className="w-4 h-4" />
                            </button>
                            <button type="button" className="btn btn-secondary compact" onClick={() => handleSaveResource(result)}>
                              {savedResourceIds.has(result.resource_id) ? 'Saved' : 'Save'}
                            </button>
                          </div>
                        </div>
                      </article>
                    ))}
                  </section>
                ) : (
                  <div className="panel section-card">
                    <EmptyState
                      title={deferredQuery.length < 2 ? 'Search is ready' : 'No results in this filter'}
                      copy={
                        deferredQuery.length < 2
                          ? 'Ask for a course, resource, week, or topic to start building a result list.'
                          : 'Try a broader query or switch back to all categories.'
                      }
                    />
                  </div>
                )}
              </>
            ) : null}

            {view === 'courses' ? (
              <section className="course-layout">
                <div className="panel section-card">
                  <SectionHeading kicker="Institutions" title="Pick your campus stream" />
                  <div className="institution-grid">
                    {institutions.map((institution) => (
                      <button
                        key={institution.id}
                        type="button"
                        className={`institution-card ${selectedInstitution?.id === institution.id ? 'active' : ''}`}
                        onClick={() => {
                          void loadCoursesForInstitution(institution)
                        }}
                      >
                        <div className="institution-card-top">
                          <Building2 className="w-5 h-5" />
                          <span>{institution.slug}</span>
                        </div>
                        <strong>{institution.name}</strong>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="panel section-card">
                  <SectionHeading
                    kicker={selectedInstitution ? selectedInstitution.slug.toUpperCase() : 'Course index'}
                    title={selectedInstitution ? selectedInstitution.name : 'Courses will land here'}
                  />

                  {coursesError ? <p className="error-copy">{coursesError}</p> : null}

                  {coursesLoading ? (
                    <div className="saved-list">
                      {Array.from({ length: 4 }).map((_, index) => (
                        <div key={index} className="course-item skeleton-card">
                          <div className="skeleton-line skeleton-line-short" />
                          <div className="skeleton-line skeleton-line-mid" />
                        </div>
                      ))}
                    </div>
                  ) : selectedInstitution ? (
                    courses.length > 0 ? (
                      <div className="course-list">
                        {courses.map((course) => (
                          <article key={course.id} className="course-item">
                            <div>
                              <p className="mini-label">{course.id}</p>
                              <h3>{course.title}</h3>
                            </div>
                            <div className="course-pill">
                              <GraduationCap className="w-4 h-4" />
                              <span>{course.week_count ?? 'N/A'} weeks</span>
                            </div>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        title="No courses indexed yet"
                        copy="This institution is connected, but the course catalog has not been populated."
                      />
                    )
                  ) : (
                    <EmptyState
                      title="Choose an institution"
                      copy="Once you pick a school, its course catalog will appear here and stay pinned to your overview lane."
                    />
                  )}
                </div>
              </section>
            ) : null}

            {view === 'profile' ? (
              <section className="profile-layout">
                <div className="panel section-card identity-card">
                  <div className="identity-orb">
                    <UserRound className="w-10 h-10" />
                  </div>
                  <div>
                    <p className="eyebrow">Identity</p>
                    <h2 className="profile-title">{studentName}</h2>
                    <p className="muted-copy">
                      {authState === 'verified'
                        ? 'Telegram identity is confirmed and ready for bot handoff.'
                        : authState === 'failed'
                          ? 'Telegram was detected, but verification did not complete. The UI still runs in preview mode.'
                          : 'You are previewing the student app outside Telegram.'}
                    </p>
                  </div>

                  <div className="identity-metrics">
                    <StatusPill icon={<Bot className="w-4 h-4" />} label={formatAuthLabel(authState)} tone="neutral" />
                    <StatusPill
                      icon={<BadgeCheck className="w-4 h-4" />}
                      label={selectedInstitution ? selectedInstitution.slug : 'No institution pinned'}
                      tone="neutral"
                    />
                  </div>
                </div>

                <div className="panel section-card">
                  <SectionHeading kicker="Memory" title="Recent searches" />
                  {recentSearches.length > 0 ? (
                    <div className="saved-list">
                      {recentSearches.map((term) => (
                        <button
                          key={term}
                          type="button"
                          className="saved-item"
                          onClick={() => handleSuggestionClick(term)}
                        >
                          <div>
                            <p className="saved-item-title">{term}</p>
                            <p className="saved-item-meta">Tap to rerun this search in the live index.</p>
                          </div>
                          <Search className="w-4 h-4" />
                        </button>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="No recent searches" copy="Run a few searches and this timeline will become your quick replay list." />
                  )}
                </div>

                <div className="panel section-card">
                  <SectionHeading kicker="Library" title="Saved references" />
                  {savedResources.length > 0 ? (
                    <div className="saved-list">
                      {savedResources.map((resource) => (
                        <article key={resource.resource_id} className="saved-item static">
                          <div>
                            <p className="saved-item-title">{resource.title}</p>
                            <p className="saved-item-meta">
                              {resource.course_id} · {formatCategoryLabel(resource.category_slug, categories)}
                            </p>
                          </div>
                          <button
                            type="button"
                            className="icon-button"
                            onClick={() => handleSaveResource(resource)}
                            aria-label="Remove saved resource"
                          >
                            <BookmarkCheck className="w-4 h-4" />
                          </button>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Your library is empty" copy="Save resources from search results to build a reusable study stack here." />
                  )}
                </div>
              </section>
            ) : null}
          </motion.main>
        </AnimatePresence>

        <nav className="bottom-dock" aria-label="Student app navigation">
          <DockButton
            active={view === 'overview'}
            icon={<Home className="w-4 h-4" />}
            label="Overview"
            onClick={() => changeView('overview')}
          />
          <DockButton
            active={view === 'search'}
            icon={<Search className="w-4 h-4" />}
            label="Search"
            onClick={() => changeView('search')}
          />
          <DockButton
            active={view === 'courses'}
            icon={<LibraryBig className="w-4 h-4" />}
            label="Courses"
            onClick={() => changeView('courses')}
          />
          <DockButton
            active={view === 'profile'}
            icon={<UserRound className="w-4 h-4" />}
            label="Profile"
            onClick={() => changeView('profile')}
          />
        </nav>

        <AnimatePresence>
          {toast ? (
            <motion.div
              className={`toast ${toast.kind}`}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 18 }}
            >
              {toast.message}
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  )
}

function SectionHeading(props: { kicker: string; title: string }) {
  return (
    <div className="section-heading">
      <p className="eyebrow">{props.kicker}</p>
      <h2>{props.title}</h2>
    </div>
  )
}

function StatusPill(props: {
  icon: React.ReactNode
  label: string
  tone: 'success' | 'warning' | 'neutral'
}) {
  return (
    <div className={`status-pill ${props.tone}`}>
      {props.icon}
      <span>{props.label}</span>
    </div>
  )
}

function StatCard(props: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="panel stat-card">
      <div className="stat-icon">{props.icon}</div>
      <div>
        <p className="mini-label">{props.label}</p>
        <h3>{props.value}</h3>
      </div>
    </div>
  )
}

function DockButton(props: {
  active: boolean
  icon: React.ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button type="button" className={`dock-button ${props.active ? 'active' : ''}`} onClick={props.onClick}>
      {props.icon}
      <span>{props.label}</span>
    </button>
  )
}

function EmptyState(props: { title: string; copy: string }) {
  return (
    <div className="empty-state">
      <Sparkles className="w-5 h-5" />
      <h3>{props.title}</h3>
      <p>{props.copy}</p>
    </div>
  )
}
