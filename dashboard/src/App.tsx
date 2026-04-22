import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bot,
  CheckCircle2,
  ChevronDown,
  Database,
  ExternalLink,
  HardDrive,
  LayoutDashboard,
  Lock,
  LogOut,
  Moon,
  RefreshCw,
  Search,
  Server,
  Settings,
  Sparkles,
  Sun,
  UserRound,
  Users,
  Wifi,
  Wrench,
  XCircle,
  TrendingUp,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  type LucideIcon,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import {
  api,
  AUTH_EXPIRED_EVENT,
  clearStoredSession,
  getConfiguredApiBaseUrl,
  normalizeApiBaseUrl,
  setConfiguredApiBaseUrl,
  type HealthResponse,
  type Incident,
  type IncidentStatus,
  type Overview,
  type QuarantineItem,
  type QuarantineStatus,
  type StudentRow,
  type TelemetryRow,
} from "./api";
import StudentVoyager from "./Voyager";
import {
  getDesktopBridge,
  type DesktopLogEntry,
  type DesktopRuntimeStatus,
  type DesktopServiceName,
} from "./desktop";

type Theme = "night" | "light";
type Density = "spacious" | "dense";
type ColorPreset = "default" | "violet" | "cyan" | "emerald";
type TabId = "control" | "incidents" | "quarantine" | "students" | "intelligence" | "settings";
type StudentFilter = "ALL" | "BOUND" | "UNLINKED" | "CONFLICTED";
type ToastTone = "success" | "warning" | "danger" | "info";

type DesktopRuntimeModel = {
  available: boolean;
  loading: boolean;
  status: DesktopRuntimeStatus | null;
  error: string;
  refresh: () => Promise<void>;
  startService: (service: DesktopServiceName) => Promise<DesktopRuntimeStatus>;
  stopService: (service: DesktopServiceName) => Promise<DesktopRuntimeStatus>;
  restartService: (service: DesktopServiceName) => Promise<DesktopRuntimeStatus>;
  openDataFolder: () => Promise<void>;
  backupDatabase: () => Promise<string>;
};

type ConfigContextValue = {
  theme: Theme;
  setTheme: React.Dispatch<React.SetStateAction<Theme>>;
  density: Density;
  setDensity: React.Dispatch<React.SetStateAction<Density>>;
  colorPreset: ColorPreset;
  setColorPreset: React.Dispatch<React.SetStateAction<ColorPreset>>;
  apiBaseUrl: string;
  setApiBaseUrl: React.Dispatch<React.SetStateAction<string>>;
};

const ConfigContext = createContext<ConfigContextValue | null>(null);

const THEME_KEY = "orbit_theme";
const DENSITY_KEY = "orbit_density";
const COLOR_PRESET_KEY = "orbit_color_preset";
const USERNAME_KEY = "orbit_admin_username";

function useConfig(): ConfigContextValue {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error("Orbit config is not available.");
  }
  return context;
}

function getStoredTheme(): Theme {
  return window.localStorage.getItem(THEME_KEY) === "light" ? "light" : "night";
}

function getStoredDensity(): Density {
  return window.localStorage.getItem(DENSITY_KEY) === "dense" ? "dense" : "spacious";
}

function getStoredColorPreset(): ColorPreset {
  const preset = window.localStorage.getItem(COLOR_PRESET_KEY);
  if (preset === "violet" || preset === "cyan" || preset === "emerald") {
    return preset;
  }
  return "default";
}

function classNames(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

function formatNumber(value: number | undefined): string {
  return new Intl.NumberFormat().format(value ?? 0);
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function toTitleCase(value: string): string {
  return value
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getErrorMessage(error: unknown): string {
  if (typeof error === "string") {
    return error;
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (error && typeof error === "object" && "detail" in error && typeof error.detail === "string") {
    return error.detail;
  }
  return "Something went wrong.";
}

function decodeJwtPayload(token: string | null): Record<string, unknown> | null {
  if (!token) {
    return null;
  }

  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const bytes = Uint8Array.from(window.atob(padded), (char) => char.charCodeAt(0));
    const payload = new TextDecoder().decode(bytes);
    return JSON.parse(payload) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function useDesktopRuntime(): DesktopRuntimeModel {
  const bridge = useMemo(() => getDesktopBridge(), []);
  const [status, setStatus] = useState<DesktopRuntimeStatus | null>(null);
  const [loading, setLoading] = useState(Boolean(bridge));
  const [error, setError] = useState("");

  const refresh = async (): Promise<void> => {
    if (!bridge) {
      return;
    }

    setLoading(true);
    try {
      const next = await bridge.getStatus();
      setStatus(next);
      setError("");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!bridge) {
      return;
    }

    let active = true;

    void bridge
      .getStatus()
      .then((next) => {
        if (!active) {
          return;
        }
        setStatus(next);
        setLoading(false);
      })
      .catch((caught) => {
        if (!active) {
          return;
        }
        setError(getErrorMessage(caught));
        setLoading(false);
      });

    const unsubscribeStatus = bridge.onStatus((next) => {
      if (!active) {
        return;
      }
      setStatus(next);
      setLoading(false);
    });

    const unsubscribeLog = bridge.onLog((entry) => {
      if (!active) {
        return;
      }
      setStatus((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          logs: [entry, ...current.logs.filter((item) => item.id !== entry.id)].slice(0, 60),
        };
      });
    });

    const poller = window.setInterval(() => {
      void bridge
        .getStatus()
        .then((next) => {
          if (active) {
            setStatus(next);
          }
        })
        .catch(() => undefined);
    }, 8000);

    return () => {
      active = false;
      window.clearInterval(poller);
      unsubscribeStatus();
      unsubscribeLog();
    };
  }, [bridge]);

  const runStatusMutation = async (
    operation: (desktopBridge: NonNullable<typeof bridge>) => Promise<DesktopRuntimeStatus>,
  ): Promise<DesktopRuntimeStatus> => {
    if (!bridge) {
      throw new Error("Desktop controls are only available inside the Orbit desktop app.");
    }

    setLoading(true);
    try {
      const next = await operation(bridge);
      setStatus(next);
      setError("");
      return next;
    } catch (caught) {
      const message = getErrorMessage(caught);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  };

  const openDataFolder = async (): Promise<void> => {
    if (!bridge) {
      throw new Error("Desktop controls are only available inside the Orbit desktop app.");
    }

    try {
      await bridge.openDataFolder();
      setError("");
    } catch (caught) {
      const message = getErrorMessage(caught);
      setError(message);
      throw new Error(message);
    }
  };

  const backupDatabase = async (): Promise<string> => {
    if (!bridge) {
      throw new Error("Desktop controls are only available inside the Orbit desktop app.");
    }

    try {
      const backupPath = await bridge.backupDatabase();
      await refresh();
      setError("");
      return backupPath;
    } catch (caught) {
      const message = getErrorMessage(caught);
      setError(message);
      throw new Error(message);
    }
  };

  return {
    available: Boolean(bridge),
    loading,
    status,
    error,
    refresh,
    startService: (service) => runStatusMutation((desktopBridge) => desktopBridge.startService(service)),
    stopService: (service) => runStatusMutation((desktopBridge) => desktopBridge.stopService(service)),
    restartService: (service) => runStatusMutation((desktopBridge) => desktopBridge.restartService(service)),
    openDataFolder,
    backupDatabase,
  };
}

function useToasts() {
  const [toasts, setToasts] = useState<Array<{ id: string; message: string; tone: ToastTone }>>([]);

  const pushToast = (message: string, tone: ToastTone = "info") => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 3200);
  };

  const dismissToast = (id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  };

  return { toasts, pushToast, dismissToast };
}

export default function App() {
  const desktop = useDesktopRuntime();
  const { toasts, pushToast, dismissToast } = useToasts();
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(window.localStorage.getItem("orbit_access_token")));
  const [theme, setTheme] = useState<Theme>(() => getStoredTheme());
  const [density, setDensity] = useState<Density>(() => getStoredDensity());
  const [colorPreset, setColorPreset] = useState<ColorPreset>(() => getStoredColorPreset());
  const [apiBaseUrl, setApiBaseUrl] = useState(() => getConfiguredApiBaseUrl());
  const [activeTab, setActiveTab] = useState<TabId>("control");
  const [adminUsername, setAdminUsername] = useState(() => window.localStorage.getItem(USERNAME_KEY) || "");
  const globalSearchRef = useRef<HTMLInputElement | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [sessionRole, setSessionRole] = useState<string>(() => {
    const payload = decodeJwtPayload(window.localStorage.getItem("orbit_access_token"));
    return String(payload?.role || payload?.scope || "guest");
  });
  const [overview, setOverview] = useState<Overview | null>(null);

  const fetchOverview = async () => {
    if (!isAuthenticated) return;
    try {
      const data = await api.overview();
      setOverview(data);
    } catch (err) {
      console.warn("Failed to fetch overview for sidebar", err);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      void fetchOverview();
      const interval = setInterval(fetchOverview, 30000); // Refresh every 30s
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute("data-density", density);
    window.localStorage.setItem(DENSITY_KEY, density);
  }, [density]);

  useEffect(() => {
    document.documentElement.setAttribute("data-color-preset", colorPreset);
    window.localStorage.setItem(COLOR_PRESET_KEY, colorPreset);
  }, [colorPreset]);

  useEffect(() => {
    window.localStorage.setItem("orbit_api_base_url", apiBaseUrl);
  }, [apiBaseUrl]);

  useEffect(() => {
    const handleAuthExpired = () => {
      setIsAuthenticated(false);
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, []);

  const [setupMode, setSetupMode] = useState(false);
  const [setupRequired, setSetupRequired] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Shift+S triggers setup mode if setup is required
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "s") {
        setSetupMode((prev) => !prev);
      }
      if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const target = e.target as HTMLElement | null;
        if (target?.tagName !== "INPUT" && target?.tagName !== "TEXTAREA") {
          e.preventDefault();
          globalSearchRef.current?.focus();
        }
      }
      if (e.key.toLowerCase() === "g" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const next = (ev: KeyboardEvent) => {
          if (ev.key.toLowerCase() === "i") {
            setActiveTab("incidents");
          }
          if (ev.key.toLowerCase() === "s") {
            setActiveTab("students");
          }
          window.removeEventListener("keydown", next);
        };
        window.addEventListener("keydown", next, { once: true });
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      api.health().then((h) => {
        setSetupRequired(!!h.setup_required);
      }).catch(() => {});
    }
  }, [isAuthenticated]);


  const logout = () => {
    clearStoredSession();
    setIsAuthenticated(false);
    setSessionRole("guest");
    setSetupMode(false);
  };

  const handleAuthSuccess = (accessToken: string, refreshToken: string, username: string) => {
    window.localStorage.setItem("orbit_access_token", accessToken);
    window.localStorage.setItem("orbit_refresh_token", refreshToken);
    window.localStorage.setItem(USERNAME_KEY, username);
    setAdminUsername(username);
    setIsAuthenticated(true);
    setSetupMode(false);
    setSetupRequired(false);
  };

  if (!isAuthenticated) {
    if (setupRequired && setupMode) {
      return (
        <StationIgnition
          apiBaseUrl={apiBaseUrl}
          onSuccess={handleAuthSuccess}
          onCancel={() => setSetupMode(false)}
        />
      );
    }

    return (
      <LoginScreen
        apiBaseUrl={apiBaseUrl}
        setApiBaseUrl={setApiBaseUrl}
        desktop={desktop}
        onLogin={handleAuthSuccess}
      />
    );
  }

  // Removed local navGroups definition from here, we will define it based on role
  const isStudent = sessionRole === "student";
  const isAdmin = ["admin", "super_admin", "operator"].includes(sessionRole);

  const navGroups: Array<{ title: string; items: Array<{ id: TabId; label: string; icon: LucideIcon; badge?: number; badgeTone?: "default" | "warning" }> }> = [
    {
      title: "Main",
      items: [
        { id: "control", label: "Control Center", icon: LayoutDashboard },
        { id: "intelligence", label: "Intelligence", icon: TrendingUp },
        { id: "students", label: "Student Directory", icon: Users },
      ],
    },
    {
      title: "Operations",
      items: [
        { id: "incidents", label: "Incidents", icon: AlertTriangle, badge: overview?.incidents_open, badgeTone: "warning" },
        { id: "quarantine", label: "Quarantine", icon: HardDrive, badge: overview?.quarantine_pending, badgeTone: "warning" },
      ],
    },
  ];

  const secondaryLinks: Array<{ id: TabId; label: string; icon: LucideIcon }> = [
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <ConfigContext.Provider
      value={{
        theme,
        setTheme,
        density,
        setDensity,
        colorPreset,
        setColorPreset,
        apiBaseUrl,
        setApiBaseUrl,
      }}
    >
      <div className="relative flex h-screen overflow-hidden bg-orbit-bg text-orbit-fg">
        {isAdmin && (
          <aside
            className={classNames(
              "relative z-20 hidden shrink-0 border-r border-orbit-border bg-[#0d0d0d] transition-all duration-300 lg:flex lg:flex-col",
              sidebarCollapsed ? "w-16" : "w-64",
            )}
          >
          {/* Profile Header - ChatGPT Style */}
          <div className="p-3">
            <button className={classNames(
              "group flex w-full items-center gap-3 rounded-xl p-2 transition-all duration-200 hover:bg-white/5",
              sidebarCollapsed ? "justify-center" : ""
            )}>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orbit-primary/20 text-orbit-primary ring-1 ring-orbit-primary/30">
                <UserRound className="h-4 w-4" />
              </div>
              {!sidebarCollapsed && (
                <div className="min-w-0 flex-1 text-left">
                  <div className="truncate text-sm font-semibold text-slate-200">{adminUsername || "Orbit Admin"}</div>
                  <div className="text-[0.65rem] font-bold uppercase tracking-widest text-slate-500">{sessionRole}</div>
                </div>
              )}
              {!sidebarCollapsed && <ChevronDown className="h-4 w-4 text-slate-600 transition-colors group-hover:text-slate-400" />}
            </button>
          </div>

          {/* Search - Integrated */}
          {!sidebarCollapsed && (
            <div className="px-4 py-2">
              <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2 ring-1 ring-white/5 focus-within:ring-orbit-primary/40">
                <Search className="h-3.5 w-3.5 text-slate-500" />
                <input
                  ref={globalSearchRef}
                  className="w-full bg-transparent text-xs text-slate-200 outline-none placeholder:text-slate-600"
                  placeholder="Quick search..."
                />
                <span className="text-[10px] font-bold text-slate-600">/</span>
              </div>
            </div>
          )}

          {/* Navigation Groups */}
          <div className="flex-1 overflow-y-auto px-3 py-4">
            <div className="space-y-6">
              {navGroups.map((group) => (
                <div key={group.title}>
                  {!sidebarCollapsed && (
                    <div className="mb-2 px-3 text-[0.65rem] font-black uppercase tracking-[0.2em] text-slate-600">
                      {group.title}
                    </div>
                  )}
                  <nav className="space-y-1">
                    {group.items.map((item) => (
                      <NavButton
                        key={item.id}
                        active={activeTab === item.id}
                        icon={item.icon}
                        label={item.label}
                        collapsed={sidebarCollapsed}
                        badge={item.badge}
                        badgeTone={item.badgeTone}
                        onClick={() => setActiveTab(item.id)}
                      />
                    ))}
                  </nav>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="mt-auto border-t border-white/5 p-3 space-y-1">
            {secondaryLinks.map((item) => (
              <NavButton
                key={item.id}
                active={activeTab === item.id}
                icon={item.icon}
                label={item.label}
                collapsed={sidebarCollapsed}
                onClick={() => setActiveTab(item.id)}
              />
            ))}
            <button
              onClick={logout}
              className={classNames(
                "group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium text-slate-500 transition-all duration-200 hover:bg-rose-500/10 hover:text-rose-400",
                sidebarCollapsed ? "justify-center" : ""
              )}
            >
              <LogOut className="h-4 w-4" />
              {!sidebarCollapsed && <span>End Session</span>}
            </button>
          </div>
        </aside>
      )}

        <main className="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden">
          <header className="border-b border-orbit-border bg-orbit-surface/45 px-4 py-4 backdrop-blur-xl lg:px-8">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setMobileSidebarOpen((v) => !v)}
                  className="inline-flex items-center justify-center rounded-xl border border-orbit-border bg-orbit-bg/40 p-2 text-slate-300 lg:hidden"
                >
                  <Menu className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setSidebarCollapsed((v) => !v)}
                  className="hidden items-center justify-center rounded-xl border border-orbit-border bg-orbit-bg/40 p-2 text-slate-300 lg:inline-flex"
                >
                  {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
                </button>
                <h2 className="text-xl font-semibold tracking-tight text-white">Orbit Admin Console</h2>
              </div>
              <div className="flex flex-wrap items-center justify-end gap-3">
                <StatusChip
                  tone={desktop.status?.services.api.status === "running" ? "success" : "warning"}
                  label={
                    desktop.status?.services.api.status === "running"
                      ? "Local API Ready"
                      : "API Waiting"
                  }
                />
                <div className="hidden max-w-[18rem] truncate rounded-full border border-orbit-border bg-orbit-bg/50 px-4 py-2 text-xs font-semibold text-slate-300 md:block">
                  {apiBaseUrl}
                </div>
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-8 lg:py-8">
            <div className="mx-auto max-w-7xl">
              <AnimatePresence mode="wait">
                <motion.div
                  key={isStudent ? "student" : activeTab}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -16 }}
                  transition={{ duration: 0.2 }}
                >
                  {isStudent ? (
                    <StudentVoyager studentName={adminUsername} isAuthenticated={isAuthenticated} />
                  ) : (
                    <>
                      {activeTab === "control" && (
                        <ControlCenterPanel
                          desktop={desktop}
                          sessionRole={sessionRole}
                          adminUsername={adminUsername}
                          overview={overview}
                          onRefresh={fetchOverview}
                        />
                      )}
                      {activeTab === "incidents" && <IncidentsPanel />}
                      {activeTab === "quarantine" && <QuarantinePanel />}
                      {activeTab === "students" && <StudentsPanel pushToast={pushToast} />}
                      {activeTab === "intelligence" && <IntelligencePanel />}
                      {activeTab === "settings" && (
                        <SettingsPanel
                          adminUsername={adminUsername}
                          sessionRole={sessionRole}
                          desktop={desktop}
                          logout={logout}
                        />
                      )}
                    </>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </main>
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-50 flex lg:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setMobileSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative flex w-72 flex-col bg-[#0d0d0d] p-4 shadow-2xl"
            >
              <div className="mb-6 flex items-center justify-between px-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orbit-primary/20 text-orbit-primary ring-1 ring-orbit-primary/30">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <span className="text-lg font-black tracking-tight text-white">Orbit</span>
                </div>
                <button onClick={() => setMobileSidebarOpen(false)} className="text-slate-500 hover:text-white">
                  <PanelLeftClose className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 space-y-6 overflow-y-auto px-2">
                {navGroups.map((group) => (
                  <div key={group.title}>
                    <div className="mb-2 px-3 text-[0.65rem] font-black uppercase tracking-[0.2em] text-slate-600">
                      {group.title}
                    </div>
                    <div className="space-y-1">
                      {group.items.map((item) => (
                        <NavButton
                          key={item.id}
                          active={activeTab === item.id}
                          icon={item.icon}
                          label={item.label}
                          badge={item.badge}
                          badgeTone={item.badgeTone}
                          onClick={() => {
                            setActiveTab(item.id);
                            setMobileSidebarOpen(false);
                          }}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-auto border-t border-white/5 pt-4 space-y-1">
                {secondaryLinks.map((item) => (
                  <NavButton
                    key={item.id}
                    active={activeTab === item.id}
                    icon={item.icon}
                    label={item.label}
                    onClick={() => {
                      setActiveTab(item.id);
                      setMobileSidebarOpen(false);
                    }}
                  />
                ))}
              </div>
            </motion.aside>
          </div>
        )}
        <ToastStack toasts={toasts} onDismiss={dismissToast} />
      </div>
    </ConfigContext.Provider>
  );
}

function LoginScreen({
  onLogin,
  apiBaseUrl,
  setApiBaseUrl,
  desktop,
}: {
  onLogin: (accessToken: string, refreshToken: string, username: string) => void;
  apiBaseUrl: string;
  setApiBaseUrl: React.Dispatch<React.SetStateAction<string>>;
  desktop: DesktopRuntimeModel;
}) {
  const [username, setUsername] = useState(() => window.localStorage.getItem(USERNAME_KEY) || "");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const normalizedApiBase = setConfiguredApiBaseUrl(apiBaseUrl);
      const tokenSet = await api.login(username, password, normalizedApiBase);
      onLogin(tokenSet.access_token, tokenSet.refresh_token, username);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  const checkConnection = async () => {
    setTesting(true);
    setError("");
    try {
      const normalizedApiBase = normalizeApiBaseUrl(apiBaseUrl);
      const nextHealth = await api.health(normalizedApiBase);
      setHealth(nextHealth);
      setApiBaseUrl(normalizedApiBase);
    } catch (caught) {
      setError(getErrorMessage(caught));
      setHealth(null);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-orbit-bg px-4 py-10 text-orbit-fg">

      <div className="grid w-full max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/65 p-8 backdrop-blur-xl lg:p-12">
          <div className="mb-10">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-orbit-primary/20 bg-orbit-primary/10 px-4 py-2 text-xs font-black uppercase tracking-[0.3em] text-orbit-accent">
              <Sparkles className="h-4 w-4" />
              Orbit Control Center
            </div>
            <h1 className="text-4xl font-black tracking-tight text-white lg:text-5xl">
              Administrative access for the live system.
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
              Sign in to triage incidents, resolve student identity conflicts, manage quarantine, and control
              the local Orbit services from one place.
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-3">
            <SummaryCard
              icon={Server}
              label="Backend"
              value={desktop.status?.services.api.status === "running" ? "Online" : "Waiting"}
              note="FastAPI admin endpoints"
              tone={desktop.status?.services.api.status === "running" ? "success" : "warning"}
            />
            <SummaryCard
              icon={Bot}
              label="Bot"
              value={desktop.status?.services.bot.status === "running" ? "Polling" : "Idle"}
              note="Telegram delivery engine"
              tone={desktop.status?.services.bot.status === "running" ? "success" : "default"}
            />
            <SummaryCard
              icon={Wifi}
              label="API Target"
              value={health?.version || "Ready"}
              note={normalizeApiBaseUrl(apiBaseUrl)}
              tone={health ? "success" : "default"}
            />
          </div>

          {desktop.available && (
            <div className="mt-8 rounded-[2rem] border border-orbit-border bg-orbit-bg/35 p-6">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-white">Local desktop controls</h2>
                  <p className="text-sm text-slate-400">
                    Start the API if you want to sign in against the local workspace.
                  </p>
                </div>
                <button
                  onClick={() => {
                    void desktop.refresh();
                  }}
                  className="rounded-2xl border border-orbit-border bg-orbit-surface/70 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-orbit-primary/50 hover:text-white"
                >
                  Refresh
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <CompactServiceCard
                  label="API Engine"
                  detail={desktop.status?.services.api.detail || "No runtime data yet."}
                  status={desktop.status?.services.api.status || "unknown"}
                  onStart={() => {
                    void desktop.startService("api");
                  }}
                  onRestart={() => {
                    void desktop.restartService("api");
                  }}
                  onStop={() => {
                    void desktop.stopService("api");
                  }}
                />
                <CompactServiceCard
                  label="Telegram Bot"
                  detail={desktop.status?.services.bot.detail || "No runtime data yet."}
                  status={desktop.status?.services.bot.status || "unknown"}
                  onStart={() => {
                    void desktop.startService("bot");
                  }}
                  onRestart={() => {
                    void desktop.restartService("bot");
                  }}
                  onStop={() => {
                    void desktop.stopService("bot");
                  }}
                />
              </div>

              <div className="mt-4 rounded-2xl border border-dashed border-orbit-border px-4 py-3 text-sm text-slate-400">
                Workspace: {desktop.status?.workspaceRoot || "Orbit workspace not detected yet."}
              </div>
            </div>
          )}
        </section>

        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-[2rem] border border-orbit-border bg-orbit-surface/65 p-8 backdrop-blur-xl lg:p-10"
        >
          <div className="mb-8 flex items-center gap-4">
            <div className="orbit-glow flex h-16 w-16 items-center justify-center rounded-[1.5rem] border border-orbit-primary/30 bg-orbit-primary/10">
              <Lock className="h-8 w-8 text-orbit-primary" />
            </div>
            <div>
              <h2 className="text-3xl font-black tracking-tight text-white">Secure Sign-In</h2>
              <p className="text-sm text-slate-400">Admin credentials or Student School ID.</p>
            </div>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <label className="block">
              <span className="mb-2 block text-xs font-black uppercase tracking-[0.25em] text-slate-400">
                Identity Identifier
              </span>
              <input
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white outline-none transition focus:border-orbit-primary"
                placeholder="Admin username or Student ID"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-xs font-black uppercase tracking-[0.25em] text-slate-400">
                Password
              </span>
              <input
                required
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white outline-none transition focus:border-orbit-primary"
                placeholder="••••••••"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-xs font-black uppercase tracking-[0.25em] text-slate-400">
                API Endpoint
              </span>
              <input
                required
                value={apiBaseUrl}
                onChange={(event) => setApiBaseUrl(event.target.value)}
                className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white outline-none transition focus:border-orbit-primary"
                placeholder="http://127.0.0.1:8000"
              />
            </label>

            {(error || desktop.error) && (
              <ErrorBanner message={error || desktop.error} />
            )}

            {health && !error && (
              <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
                Connected to Orbit {health.version} ({health.release}).
              </div>
            )}

            <div className="flex flex-col gap-3 pt-2 sm:flex-row">
              <button
                type="submit"
                disabled={loading}
                className="orbit-glow flex flex-1 items-center justify-center gap-2 rounded-2xl bg-orbit-primary px-5 py-4 text-sm font-black uppercase tracking-[0.2em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Lock className="h-4 w-4" />}
                Authenticate
              </button>
              <button
                type="button"
                onClick={() => {
                  void checkConnection();
                }}
                disabled={testing}
                className="flex items-center justify-center gap-2 rounded-2xl border border-orbit-border bg-orbit-surface/70 px-5 py-4 text-sm font-semibold text-slate-200 transition hover:border-orbit-primary/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                {testing ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Wifi className="h-4 w-4" />}
                Test Endpoint
              </button>
            </div>
          </form>
        </motion.section>
      </div>
    </div>
  );
}

function ControlCenterPanel({
  desktop,
  sessionRole,
  adminUsername,
  overview,
  onRefresh,
}: {
  desktop: DesktopRuntimeModel;
  sessionRole: string;
  adminUsername: string;
  overview: Overview | null;
  onRefresh: () => Promise<void>;
}) {
  const { apiBaseUrl } = useConfig();
  const [localHealth, setLocalHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(!overview);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionBusy, setActionBusy] = useState("");
  const [period, setPeriod] = useState<"7d" | "30d" | "90d">("7d");

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const [healthResult] = await Promise.allSettled([api.health()]);
      if (healthResult.status === "fulfilled") {
        setLocalHealth(healthResult.value);
      }
      await onRefresh();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!overview) {
      void load();
    } else {
      setLoading(false);
    }
  }, []);

  const runDesktopAction = async (
    key: string,
    action: () => Promise<DesktopRuntimeStatus | string | void>,
    successMessage?: string,
  ) => {
    setActionBusy(key);
    setActionMessage("");
    try {
      const result = await action();
      if (typeof result === "string") {
        setActionMessage(result);
      } else if (successMessage) {
        setActionMessage(successMessage);
      }
    } catch (caught) {
      setActionMessage(getErrorMessage(caught));
    } finally {
      setActionBusy("");
    }
  };

  return (
    <div className="space-y-8">
      <PanelIntro
        eyebrow="Operations"
        title="Control Center"
        description="Keep the local services healthy, watch the live admin surface, and verify the institutional data layer."
        action={
          <button
            onClick={() => {
              void load();
              void desktop.refresh();
            }}
            className="inline-flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-surface/70 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-orbit-primary/60 hover:text-white"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        }
      />

      {(error || desktop.error || actionMessage) && (
        <ErrorBanner message={actionMessage || error || desktop.error} />
      )}

      <div className="grid gap-4 xl:grid-cols-4">
        <SummaryCard
          icon={Users}
          label="Students"
          value={formatNumber(overview?.students_total)}
          note="Institution records loaded"
          tone="default"
        />
        <SummaryCard
          icon={Activity}
          label="Identity Links"
          value={formatNumber(overview?.links_total)}
          note="Telegram to student bindings"
          tone="success"
        />
        <SummaryCard
          icon={AlertTriangle}
          label="Open Incidents"
          value={formatNumber(overview?.incidents_open)}
          note="Needs admin attention"
          tone={overview?.incidents_open ? "warning" : "default"}
        />
        <SummaryCard
          icon={HardDrive}
          label="Quarantine"
          value={formatNumber(overview?.quarantine_pending)}
          note="Pending recovery decisions"
          tone={overview?.quarantine_pending ? "warning" : "default"}
        />
      </div>

      <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-xl font-black tracking-tight text-white">Performance Trends</h3>
            <p className="text-sm text-slate-400">Hover cards and quick period switcher for operator awareness.</p>
          </div>
          <div className="flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-bg/40 p-1">
            {(["7d", "30d", "90d"] as const).map((item) => (
              <button
                key={item}
                onClick={() => setPeriod(item)}
                className={classNames(
                  "rounded-xl px-3 py-1.5 text-xs font-semibold uppercase",
                  period === item ? "bg-orbit-primary text-white" : "text-slate-300",
                )}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <HoverMetricCard
            icon={TrendingUp}
            title="Answer velocity"
            subtitle={`Median first response (${period})`}
            value={period === "7d" ? "3.2h" : period === "30d" ? "4.1h" : "4.8h"}
            trend="+12%"
          />
          <HoverMetricCard
            icon={BarChart3}
            title="Resolved incidents"
            subtitle={`Workflow closure (${period})`}
            value={period === "7d" ? "46" : period === "30d" ? "182" : "498"}
            trend="+8%"
          />
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-black tracking-tight text-white">Desktop operations</h3>
              <p className="text-sm text-slate-400">
                Orbit running as {desktop.status?.packaged ? "packaged desktop app" : "local development shell"}.
              </p>
            </div>
            {localHealth && (
              <StatusChip tone="success" label={`API ${localHealth.version}`} />
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <ServiceCard
              icon={Server}
              label="API Engine"
              service={desktop.status?.services.api}
              loading={actionBusy === "start:api" || actionBusy === "restart:api" || actionBusy === "stop:api"}
              onStart={() => {
                void runDesktopAction("start:api", () => desktop.startService("api"));
              }}
              onRestart={() => {
                void runDesktopAction("restart:api", () => desktop.restartService("api"));
              }}
              onStop={() => {
                void runDesktopAction("stop:api", () => desktop.stopService("api"));
              }}
            />
            <ServiceCard
              icon={Bot}
              label="Telegram Bot"
              service={desktop.status?.services.bot}
              loading={actionBusy === "start:bot" || actionBusy === "restart:bot" || actionBusy === "stop:bot"}
              onStart={() => {
                void runDesktopAction("start:bot", () => desktop.startService("bot"));
              }}
              onRestart={() => {
                void runDesktopAction("restart:bot", () => desktop.restartService("bot"));
              }}
              onStop={() => {
                void runDesktopAction("stop:bot", () => desktop.stopService("bot"));
              }}
            />
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <InfoTile
              icon={Database}
              label="Workspace Root"
              value={desktop.status?.workspaceRoot || "Not detected"}
              note="Desktop controls are enabled when the Orbit repository is present."
            />
            <InfoTile
              icon={Wifi}
              label="Connected API"
              value={apiBaseUrl}
              note="The renderer can target local or remote Orbit deployments."
            />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <ActionButton
              label="Open Data Folder"
              variant="secondary"
              disabled={!desktop.available || !desktop.status?.workspaceDetected || actionBusy !== ""}
              onClick={() => {
                void runDesktopAction("open-data", () => desktop.openDataFolder(), "Opened the Orbit data folder.");
              }}
            />
            <ActionButton
              label="Backup Database"
              variant="secondary"
              disabled={!desktop.available || !desktop.status?.workspaceDetected || actionBusy !== ""}
              onClick={() => {
                void runDesktopAction("backup-db", () => desktop.backupDatabase());
              }}
            />
          </div>
        </section>

        <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-black tracking-tight text-white">Operator log</h3>
              <p className="text-sm text-slate-400">
                Live process output from the desktop shell and local Orbit services.
              </p>
            </div>
            <StatusChip
              tone={desktop.status?.workspaceDetected ? "success" : "warning"}
              label={desktop.status?.workspaceDetected ? "Workspace Found" : "Workspace Missing"}
            />
          </div>

          <div className="max-h-[29rem] space-y-3 overflow-y-auto pr-1">
            {desktop.status?.logs.length ? (
              desktop.status.logs.map((entry) => (
                <LogRow key={entry.id} entry={entry} />
              ))
            ) : (
              <EmptyState
                icon={Activity}
                title={loading ? "Waiting for live status" : "No log messages yet"}
                description="Start a local service or refresh the desktop shell to populate the activity stream."
              />
            )}
          </div>
        </section>
      </div>

      <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-black tracking-tight text-white">Current admin context</h3>
            <p className="text-sm text-slate-400">
              Signed in as {adminUsername || "Orbit Admin"} with {toTitleCase(sessionRole)} privileges.
            </p>
          </div>
          <a
            href={`${apiBaseUrl}/docs`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-bg/40 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-orbit-primary/60 hover:text-white"
          >
            API Docs
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <InfoTile
            icon={UserRound}
            label="Role"
            value={toTitleCase(sessionRole)}
            note="JWT-derived admin privilege level"
          />
          <InfoTile
            icon={Server}
            label="Release"
            value={localHealth ? `${localHealth.release} ${localHealth.version}` : "Unavailable"}
            note="Backend health endpoint response"
          />
          <InfoTile
            icon={Sparkles}
            label="Conflicts"
            value={overview ? formatNumber(overview.conflicts_total) : "0"}
            note="Identity records needing manual review"
          />
        </div>
      </section>
    </div>
  );
}

function IncidentsPanel() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [drafts, setDrafts] = useState<Record<string, { status: IncidentStatus; note: string }>>({});
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState("");
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkStatus, setBulkStatus] = useState<IncidentStatus>("IN_PROGRESS");
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<"ALL" | IncidentStatus>("ALL");
  const [view, setView] = useState<"triage" | "active" | "closed">("triage");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const next = await api.incidents();
      setIncidents(next);
      setDrafts((current) => {
        const updated = { ...current };
        for (const incident of next) {
          updated[incident.id] = {
            status: current[incident.id]?.status || incident.status,
            note: current[incident.id]?.note ?? incident.resolution_note ?? "",
          };
        }
        return updated;
      });
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const filteredIncidents = useMemo(() => {
    const byView = incidents.filter((incident) => {
      if (view === "active") {
        return incident.status === "OPEN" || incident.status === "IN_PROGRESS";
      }
      if (view === "closed") {
        return incident.status === "RESOLVED" || incident.status === "REJECTED";
      }
      return true;
    });
    if (filter === "ALL") {
      return byView;
    }
    return byView.filter((incident) => incident.status === filter);
  }, [filter, incidents, view]);

  const counts = useMemo(
    () => ({
      OPEN: incidents.filter((incident) => incident.status === "OPEN").length,
      IN_PROGRESS: incidents.filter((incident) => incident.status === "IN_PROGRESS").length,
      RESOLVED: incidents.filter((incident) => incident.status === "RESOLVED").length,
      REJECTED: incidents.filter((incident) => incident.status === "REJECTED").length,
    }),
    [incidents],
  );

  const saveIncident = async (incident: Incident) => {
    const draft = drafts[incident.id];
    if (!draft) {
      return;
    }

    setSavingId(incident.id);
    setError("");
    try {
      const updated = await api.updateIncident(incident.id, draft.status, draft.note);
      setIncidents((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setSavingId("");
    }
  };

  const toggleSelected = (id: string) => {
    setSelectedIds((current) => (current.includes(id) ? current.filter((x) => x !== id) : [...current, id]));
  };

  const selectedIncidents = useMemo(
    () => incidents.filter((incident) => selectedIds.includes(incident.id)),
    [incidents, selectedIds],
  );

  const applyBulkStatus = async () => {
    setBulkBusy(true);
    setError("");
    try {
      for (const incident of selectedIncidents) {
        const note = drafts[incident.id]?.note || incident.resolution_note || "";
        const updated = await api.updateIncident(incident.id, bulkStatus, note);
        setIncidents((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      }
      setSelectedIds([]);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBulkBusy(false);
    }
  };

  return (
    <div className="space-y-8">
      <PanelIntro
        eyebrow="Triage"
        title="Incidents"
        description="Review student-reported issues, move them through the response workflow, and document the resolution."
        action={
          <button
            onClick={() => {
              void load();
            }}
            className="inline-flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-surface/70 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-orbit-primary/60 hover:text-white"
          >
            <RefreshCw className="h-4 w-4" />
            Reload
          </button>
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard icon={AlertTriangle} label="Open" value={String(counts.OPEN)} note="Awaiting first response" tone="warning" />
        <SummaryCard icon={Wrench} label="In Progress" value={String(counts.IN_PROGRESS)} note="Under investigation" tone="default" />
        <SummaryCard icon={CheckCircle2} label="Resolved" value={String(counts.RESOLVED)} note="Closed successfully" tone="success" />
        <SummaryCard icon={XCircle} label="Rejected" value={String(counts.REJECTED)} note="Dismissed after review" tone="danger" />
      </div>

      <div className="flex flex-wrap gap-3">
        {([
          { id: "triage", label: "Triage Queue" },
          { id: "active", label: "Active Work" },
          { id: "closed", label: "Closed" },
        ] as const).map((item) => (
          <FilterChip key={item.id} active={view === item.id} label={item.label} onClick={() => setView(item.id)} />
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        {(["ALL", "OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"] as const).map((status) => (
          <FilterChip
            key={status}
            active={filter === status}
            label={status === "ALL" ? "All incidents" : toTitleCase(status)}
            onClick={() => setFilter(status)}
          />
        ))}
      </div>

      {selectedIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-blue-500/30 bg-blue-500/10 px-4 py-3">
          <div className="text-sm text-blue-100">{selectedIds.length} incident(s) selected</div>
          <select
            value={bulkStatus}
            onChange={(event) => setBulkStatus(event.target.value as IncidentStatus)}
            className="rounded-xl border border-orbit-border bg-orbit-bg/60 px-3 py-2 text-sm text-white outline-none"
          >
            {(["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"] as IncidentStatus[]).map((option) => (
              <option key={option} value={option}>
                {toTitleCase(option)}
              </option>
            ))}
          </select>
          <ActionButton
            label={bulkBusy ? "Applying..." : "Apply to selected"}
            disabled={bulkBusy}
            onClick={() => {
              void applyBulkStatus();
            }}
          />
          <ActionButton label="Clear" variant="secondary" onClick={() => setSelectedIds([])} />
        </div>
      )}

      {loading ? (
        <LoadingState label="Loading incident queue..." />
      ) : filteredIncidents.length ? (
        <div className="grid gap-5 xl:grid-cols-2">
          {filteredIncidents.map((incident) => {
            const draft = drafts[incident.id] ?? {
              status: incident.status,
              note: incident.resolution_note ?? "",
            };

            const changed =
              draft.status !== incident.status || draft.note !== (incident.resolution_note ?? "");

            return (
              <article
                key={incident.id}
                className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl"
              >
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <label className="mb-2 inline-flex items-center gap-2 text-xs text-slate-400">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(incident.id)}
                        onChange={() => toggleSelected(incident.id)}
                      />
                      Select
                    </label>
                    <div className="mb-2 flex flex-wrap gap-2">
                      <StatusChip tone={statusTone(incident.status)} label={toTitleCase(incident.status)} />
                      <StatusChip tone="default" label={incident.category} />
                    </div>
                    <h3 className="text-xl font-bold text-white">{incident.description}</h3>
                    <p className="mt-2 text-sm text-slate-400">
                      Telegram ID: {incident.telegram_id} {incident.course_id ? `• Course ${incident.course_id}` : ""}
                    </p>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <div>{formatDateTime(incident.created_at)}</div>
                    <div className="mt-1">Updated {formatDateTime(incident.updated_at)}</div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
                  <label className="block">
                    <span className="mb-2 block text-xs font-black uppercase tracking-[0.25em] text-slate-400">
                      Next status
                    </span>
                    <select
                      value={draft.status}
                      onChange={(event) =>
                        setDrafts((current) => ({
                          ...current,
                          [incident.id]: {
                            ...draft,
                            status: event.target.value as IncidentStatus,
                          },
                        }))
                      }
                      className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-4 py-3 text-white outline-none transition focus:border-orbit-primary"
                    >
                      {(["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"] as IncidentStatus[]).map((option) => (
                        <option key={option} value={option}>
                          {toTitleCase(option)}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-xs font-black uppercase tracking-[0.25em] text-slate-400">
                      Resolution note
                    </span>
                    <textarea
                      value={draft.note}
                      onChange={(event) =>
                        setDrafts((current) => ({
                          ...current,
                          [incident.id]: {
                            ...draft,
                            note: event.target.value,
                          },
                        }))
                      }
                      rows={3}
                      className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-4 py-3 text-white outline-none transition focus:border-orbit-primary"
                      placeholder="Capture what changed, who handled it, or why it was dismissed."
                    />
                  </label>
                </div>

                <div className="mt-5 flex items-center justify-between gap-4">
                  <div className="text-sm text-slate-400">
                    {changed ? "Unsaved changes ready to commit." : "No unsaved changes."}
                  </div>
                  <ActionButton
                    label={savingId === incident.id ? "Saving..." : "Save Update"}
                    disabled={!changed || savingId === incident.id}
                    onClick={() => {
                      void saveIncident(incident);
                    }}
                  />
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={CheckCircle2}
          title="No incidents in this view"
          description="Change the filter or wait for new student reports to arrive."
        />
      )}
    </div>
  );
}

function QuarantinePanel() {
  const [items, setItems] = useState<QuarantineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setItems(await api.quarantine());
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const updateStatus = async (item: QuarantineItem, status: QuarantineStatus) => {
    setBusyId(item.id);
    setError("");
    try {
      await api.updateQuarantine(item.id, status);
      setItems((current) => current.filter((entry) => entry.id !== item.id));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBusyId("");
    }
  };

  return (
    <div className="space-y-8">
      <PanelIntro
        eyebrow="Recovery"
        title="Quarantine"
        description="Review ingestion anomalies before they re-enter the academic content pipeline."
        action={
          <button
            onClick={() => {
              void load();
            }}
            className="inline-flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-surface/70 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-orbit-primary/60 hover:text-white"
          >
            <RefreshCw className="h-4 w-4" />
            Reload
          </button>
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard icon={HardDrive} label="Pending" value={String(items.length)} note="Records waiting for action" tone={items.length ? "warning" : "default"} />
        <SummaryCard icon={CheckCircle2} label="Recoverable" value={String(items.filter((item) => item.severity !== "error").length)} note="Likely safe to restore" tone="success" />
        <SummaryCard icon={AlertTriangle} label="High Severity" value={String(items.filter((item) => item.severity === "error").length)} note="Needs careful inspection" tone="danger" />
      </div>

      {loading ? (
        <LoadingState label="Loading quarantine queue..." />
      ) : items.length ? (
        <div className="grid gap-5 xl:grid-cols-2">
          {items.map((item) => (
            <article
              key={item.id}
              className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl"
            >
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <div className="mb-2 flex flex-wrap gap-2">
                    <StatusChip tone="warning" label={toTitleCase(item.status)} />
                    <StatusChip tone={item.severity === "error" ? "danger" : "default"} label={item.severity || "unknown"} />
                  </div>
                  <h3 className="text-lg font-bold text-white">{item.reason}</h3>
                  <p className="mt-2 break-all text-sm text-slate-400">{item.file_path}</p>
                </div>
                <div className="text-xs text-slate-500">{formatDateTime(item.detected_at)}</div>
              </div>

              <div className="flex flex-wrap gap-3">
                <ActionButton
                  label={busyId === item.id ? "Working..." : "Recover"}
                  disabled={busyId === item.id}
                  onClick={() => {
                    void updateStatus(item, "RECOVERED");
                  }}
                />
                <ActionButton
                  label="Ignore"
                  variant="secondary"
                  disabled={busyId === item.id}
                  onClick={() => {
                    void updateStatus(item, "IGNORED");
                  }}
                />
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={CheckCircle2}
          title="Quarantine is clear"
          description="There are no pending ingestion anomalies right now."
        />
      )}
    </div>
  );
}

function StudentsPanel({ pushToast }: { pushToast: (message: string, tone?: ToastTone) => void }) {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [filter, setFilter] = useState<StudentFilter>("ALL");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState<"student_id" | "full_name" | "telegram">("student_id");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [view, setView] = useState<"all" | "needs_action" | "healthy">("all");

  const load = async (nextQuery = query) => {
    setLoading(true);
    setError("");
    try {
      setStudents(await api.students(nextQuery || undefined));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    void api
      .students()
      .then((rows) => {
        if (active) {
          setStudents(rows);
        }
      })
      .catch((caught) => {
        if (active) {
          setError(getErrorMessage(caught));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const filteredStudents = useMemo(() => {
    const byView = students.filter((student) => {
      if (view === "needs_action") {
        return !student.telegram_id || student.is_conflicted;
      }
      if (view === "healthy") {
        return Boolean(student.telegram_id) && !student.is_conflicted;
      }
      return true;
    });
    switch (filter) {
      case "BOUND":
        return byView.filter((student) => Boolean(student.telegram_id));
      case "UNLINKED":
        return byView.filter((student) => !student.telegram_id);
      case "CONFLICTED":
        return byView.filter((student) => student.is_conflicted);
      default:
        return byView;
    }
  }, [filter, students, view]);

  const stats = useMemo(
    () => ({
      bound: students.filter((student) => Boolean(student.telegram_id)).length,
      unlinked: students.filter((student) => !student.telegram_id).length,
      conflicted: students.filter((student) => student.is_conflicted).length,
    }),
    [students],
  );

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setQuery(input.trim());
    await load(input.trim());
  };

  const handleUnbind = async (student: StudentRow) => {
    setBusyId(student.student_id);
    setError("");
    try {
      await api.unbind(student.student_id, student.telegram_id || undefined);
      setStudents((current) =>
        current.map((row) =>
          row.student_id === student.student_id
            ? { ...row, telegram_id: null, is_conflicted: false }
            : row,
        ),
      );
      pushToast(`Unbound ${student.student_id}`, "success");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBusyId("");
    }
  };

  const selectedStudents = useMemo(
    () => filteredStudents.filter((student) => selectedIds.includes(student.student_id)),
    [filteredStudents, selectedIds],
  );

  const canBulkUnbind = selectedStudents.some((student) => Boolean(student.telegram_id) || student.is_conflicted);

  const toggleSelected = (studentId: string) => {
    setSelectedIds((current) =>
      current.includes(studentId) ? current.filter((id) => id !== studentId) : [...current, studentId],
    );
  };

  const toggleSelectAllVisible = () => {
    const visibleIds = filteredStudents.map((student) => student.student_id);
    const allSelected = visibleIds.length > 0 && visibleIds.every((id) => selectedIds.includes(id));
    if (allSelected) {
      setSelectedIds((current) => current.filter((id) => !visibleIds.includes(id)));
      return;
    }
    setSelectedIds((current) => Array.from(new Set([...current, ...visibleIds])));
  };

  const runBulkUnbind = async () => {
    setBulkBusy(true);
    setError("");
    try {
      for (const student of selectedStudents) {
        if (!student.telegram_id && !student.is_conflicted) {
          continue;
        }
        await api.unbind(student.student_id, student.telegram_id || undefined);
      }
      setStudents((current) =>
        current.map((row) =>
          selectedIds.includes(row.student_id) ? { ...row, telegram_id: null, is_conflicted: false } : row,
        ),
      );
      pushToast(`Bulk unbound ${selectedStudents.length} student record(s).`, "success");
      setSelectedIds([]);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBulkBusy(false);
    }
  };

  const setSort = (next: "student_id" | "full_name" | "telegram") => {
    if (next === sortBy) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortBy(next);
    setSortDir("asc");
  };

  const sortedStudents = useMemo(() => {
    const factor = sortDir === "asc" ? 1 : -1;
    const rows = [...filteredStudents];
    rows.sort((a, b) => {
      const av =
        sortBy === "student_id"
          ? a.student_id
          : sortBy === "full_name"
            ? a.full_name
            : a.telegram_id || "";
      const bv =
        sortBy === "student_id"
          ? b.student_id
          : sortBy === "full_name"
            ? b.full_name
            : b.telegram_id || "";
      return av.localeCompare(bv) * factor;
    });
    return rows;
  }, [filteredStudents, sortBy, sortDir]);

  return (
    <div className="space-y-8">
      <PanelIntro
        eyebrow="Identity"
        title="Student Directory"
        description="Search institutional records, review binding health, and manually clear problematic linkages."
      />

      {error && <ErrorBanner message={error} />}

      <form onSubmit={handleSearch} className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-5 backdrop-blur-xl">
        <div className="flex flex-col gap-3 lg:flex-row">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            className="flex-1 rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white outline-none transition focus:border-orbit-primary"
            placeholder="Search by student ID or full name"
          />
          <ActionButton label={loading ? "Searching..." : "Search"} disabled={loading} type="submit" />
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          {([
            { id: "all", label: "All Records" },
            { id: "needs_action", label: "Needs Action" },
            { id: "healthy", label: "Healthy Links" },
          ] as const).map((item) => (
            <FilterChip key={item.id} active={view === item.id} label={item.label} onClick={() => setView(item.id)} />
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-3">
          {(["ALL", "BOUND", "UNLINKED", "CONFLICTED"] as StudentFilter[]).map((item) => (
            <FilterChip
              key={item}
              active={filter === item}
              label={item === "ALL" ? "All" : toTitleCase(item)}
              onClick={() => setFilter(item)}
            />
          ))}
        </div>
      </form>

      {selectedIds.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-500/30 bg-blue-500/10 px-4 py-3">
          <div className="text-sm text-blue-100">
            {selectedIds.length} selected
            {canBulkUnbind ? " - bulk action available." : " - no linked records in selection."}
          </div>
          <div className="flex gap-2">
            <ActionButton
              label={bulkBusy ? "Applying..." : "Bulk unbind"}
              disabled={!canBulkUnbind || bulkBusy}
              onClick={() => {
                void runBulkUnbind();
              }}
            />
            <ActionButton label="Clear" variant="secondary" onClick={() => setSelectedIds([])} />
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard icon={Users} label="Loaded" value={String(students.length)} note={query ? `Search: ${query}` : "Current view"} tone="default" />
        <SummaryCard icon={CheckCircle2} label="Bound" value={String(stats.bound)} note="Has Telegram mapping" tone="success" />
        <SummaryCard icon={XCircle} label="Unlinked" value={String(stats.unlinked)} note="Missing Telegram link" tone="warning" />
        <SummaryCard icon={AlertTriangle} label="Conflicted" value={String(stats.conflicted)} note="Needs admin repair" tone="danger" />
      </div>

      {loading ? (
        <LoadingState label="Loading student records..." />
      ) : sortedStudents.length ? (
        <div className="overflow-hidden rounded-[2rem] border border-orbit-border bg-orbit-surface/60 backdrop-blur-xl">
          <div className="sticky top-0 z-10 hidden grid-cols-[0.45fr_1fr_1.2fr_1fr_0.8fr_0.8fr] gap-4 border-b border-orbit-border bg-orbit-surface/95 px-6 py-4 text-xs font-black uppercase tracking-[0.25em] text-slate-400 lg:grid">
            <button type="button" onClick={toggleSelectAllVisible} className="text-left">
              {sortedStudents.length > 0 && sortedStudents.every((row) => selectedIds.includes(row.student_id))
                ? "Clear"
                : "All"}
            </button>
            <button type="button" onClick={() => setSort("student_id")} className="text-left">Student ID</button>
            <button type="button" onClick={() => setSort("full_name")} className="text-left">Name</button>
            <button type="button" onClick={() => setSort("telegram")} className="text-left">Telegram</button>
            <div>Status</div>
            <div>Action</div>
          </div>

          <div className="divide-y divide-orbit-border">
            {sortedStudents.map((student) => (
              <div
                key={student.student_id}
                className="grid gap-4 px-6 py-5 lg:grid-cols-[0.45fr_1fr_1.2fr_1fr_0.8fr_0.8fr] lg:items-center"
              >
                <label className="inline-flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(student.student_id)}
                    onChange={() => toggleSelected(student.student_id)}
                  />
                  <span className="lg:hidden">Select</span>
                </label>
                <div>
                  <div className="text-xs uppercase tracking-[0.25em] text-slate-500 lg:hidden">Student ID</div>
                  <div className="font-semibold text-white">{student.student_id}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-[0.25em] text-slate-500 lg:hidden">Name</div>
                  <div className="font-semibold text-white">{student.full_name}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-[0.25em] text-slate-500 lg:hidden">Telegram</div>
                  <div className="break-all text-slate-300">{student.telegram_id || "Not linked"}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {student.telegram_id ? (
                    <StatusChip tone="success" label="Linked" />
                  ) : (
                    <StatusChip tone="warning" label="Unlinked" />
                  )}
                  {student.is_conflicted && <StatusChip tone="danger" label="Conflict" />}
                </div>
                <div>
                  <ActionButton
                    label={busyId === student.student_id ? "Working..." : "Unbind"}
                    variant="secondary"
                    disabled={(!student.telegram_id && !student.is_conflicted) || busyId === student.student_id}
                    onClick={() => {
                      void handleUnbind(student);
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState
          icon={Users}
          title="No students matched"
          description="Try a different search term or clear the current identity filter."
        />
      )}
    </div>
  );
}

function IntelligencePanel() {
  const [topQueries, setTopQueries] = useState<TelemetryRow[]>([]);
  const [failedQueries, setFailedQueries] = useState<TelemetryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [period, setPeriod] = useState<"7d" | "30d" | "90d">("7d");

  const load = async () => {
    setLoading(true);
    setError("");

    const [topResult, failedResult] = await Promise.allSettled([api.telemetryTop(), api.telemetryFailed()]);

    if (topResult.status === "fulfilled") {
      setTopQueries(topResult.value);
    } else {
      setTopQueries([]);
    }

    if (failedResult.status === "fulfilled") {
      setFailedQueries(failedResult.value);
    } else {
      setFailedQueries([]);
    }

    if (topResult.status === "rejected" && failedResult.status === "rejected") {
      setError(getErrorMessage(topResult.reason));
    }

    setLoading(false);
  };

  useEffect(() => {
    let active = true;

    void Promise.allSettled([api.telemetryTop(), api.telemetryFailed()]).then(([topResult, failedResult]) => {
      if (!active) {
        return;
      }

      if (topResult.status === "fulfilled") {
        setTopQueries(topResult.value);
      } else {
        setTopQueries([]);
      }

      if (failedResult.status === "fulfilled") {
        setFailedQueries(failedResult.value);
      } else {
        setFailedQueries([]);
      }

      if (topResult.status === "rejected" && failedResult.status === "rejected") {
        setError(getErrorMessage(topResult.reason));
      }

      setLoading(false);
    });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-8">
      <PanelIntro
        eyebrow="Signals"
        title="Search Intelligence"
        description="Track what students are asking for most, and surface the searches that still fail to match the knowledge base."
        action={
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-bg/40 p-1">
              {(["7d", "30d", "90d"] as const).map((item) => (
                <button
                  key={item}
                  onClick={() => setPeriod(item)}
                  className={classNames(
                    "rounded-xl px-3 py-1.5 text-xs font-semibold uppercase",
                    period === item ? "bg-orbit-primary text-white" : "text-slate-300",
                  )}
                >
                  {item}
                </button>
              ))}
            </div>
            <button
              onClick={() => {
                void load();
              }}
              className="inline-flex items-center gap-2 rounded-2xl border border-orbit-border bg-orbit-surface/70 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-orbit-primary/60 hover:text-white"
            >
              <RefreshCw className="h-4 w-4" />
              Reload
            </button>
          </div>
        }
      />

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <LoadingState label="Reading telemetry..." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-2">
          <TelemetryCard
            title={`Top search queries (${period})`}
            description="What students successfully search for most often."
            icon={Search}
            items={topQueries}
            accent="success"
            emptyTitle="No search traffic yet"
            emptyDescription="Once students start searching, the hottest topics will appear here."
          />
          <TelemetryCard
            title={`Failed search queries (${period})`}
            description="Requests that did not match the indexed content."
            icon={AlertTriangle}
            items={failedQueries}
            accent="warning"
            emptyTitle="No failed searches"
            emptyDescription="This view stays empty when the content index is satisfying student demand."
          />
        </div>
      )}
    </div>
  );
}

function SettingsPanel({
  adminUsername,
  sessionRole,
  desktop,
  logout,
}: {
  adminUsername: string;
  sessionRole: string;
  desktop: DesktopRuntimeModel;
  logout: () => void;
}) {
  const { theme, setTheme, density, setDensity, colorPreset, setColorPreset, apiBaseUrl, setApiBaseUrl } = useConfig();
  const [draftApiBaseUrl, setDraftApiBaseUrl] = useState(apiBaseUrl);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setDraftApiBaseUrl(apiBaseUrl);
  }, [apiBaseUrl]);

  const saveApiBaseUrl = () => {
    const normalized = normalizeApiBaseUrl(draftApiBaseUrl);
    setApiBaseUrl(normalized);
    setMessage(`Saved API target: ${normalized}`);
  };

  const testApiBaseUrl = async () => {
    setTesting(true);
    setMessage("");
    try {
      const normalized = normalizeApiBaseUrl(draftApiBaseUrl);
      const health = await api.health(normalized);
      setDraftApiBaseUrl(normalized);
      setMessage(`Connected to Orbit ${health.version} at ${normalized}`);
    } catch (caught) {
      setMessage(getErrorMessage(caught));
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-8">
      <PanelIntro
        eyebrow="Preferences"
        title="Settings"
        description="Tune the interface, manage the API target, and review how this admin session is running."
      />

      {message && <ErrorBanner message={message} tone="info" />}

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
          <h3 className="text-xl font-black tracking-tight text-white">Appearance</h3>
          <p className="mt-2 text-sm text-slate-400">Choose how the admin panel feels during long review sessions.</p>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <ChoiceCard
              active={theme === "night"}
              icon={Moon}
              title="Deep Night"
              description="High contrast for operations-heavy work."
              onClick={() => setTheme("night")}
            />
            <ChoiceCard
              active={theme === "light"}
              icon={Sun}
              title="Solar Day"
              description="Bright mode for office and presentation use."
              onClick={() => setTheme("light")}
            />
            <ChoiceCard
              active={density === "spacious"}
              icon={LayoutDashboard}
              title="Spacious"
              description="More room between modules and cards."
              onClick={() => setDensity("spacious")}
            />
            <ChoiceCard
              active={density === "dense"}
              icon={Database}
              title="Dense"
              description="Pack more signal into the same screen."
              onClick={() => setDensity("dense")}
            />
          </div>

          <div className="mt-6">
            <div className="mb-3 text-xs font-black uppercase tracking-[0.25em] text-slate-400">Color preset</div>
            <div className="grid gap-3 sm:grid-cols-4">
              {([
                { id: "default", label: "Blue" },
                { id: "violet", label: "Violet" },
                { id: "cyan", label: "Cyan" },
                { id: "emerald", label: "Emerald" },
              ] as Array<{ id: ColorPreset; label: string }>).map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => setColorPreset(preset.id)}
                  className={classNames(
                    "rounded-xl border px-3 py-2 text-sm font-semibold transition",
                    colorPreset === preset.id
                      ? "border-orbit-primary bg-orbit-primary/15 text-white"
                      : "border-orbit-border bg-orbit-bg/35 text-slate-300 hover:border-orbit-primary/50",
                  )}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
          <h3 className="text-xl font-black tracking-tight text-white">API target</h3>
          <p className="mt-2 text-sm text-slate-400">
            Point Orbit to a local backend or a hosted admin API.
          </p>

          <div className="mt-6 space-y-4">
            <input
              value={draftApiBaseUrl}
              onChange={(event) => setDraftApiBaseUrl(event.target.value)}
              className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white outline-none transition focus:border-orbit-primary"
              placeholder="http://127.0.0.1:8000"
            />
            <div className="flex flex-wrap gap-3">
              <ActionButton label="Save endpoint" onClick={saveApiBaseUrl} />
              <ActionButton
                label={testing ? "Testing..." : "Test connection"}
                variant="secondary"
                disabled={testing}
                onClick={() => {
                  void testApiBaseUrl();
                }}
              />
            </div>
          </div>
        </section>
      </div>

      <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
        <div className="grid gap-4 md:grid-cols-3">
          <InfoTile
            icon={UserRound}
            label="Signed in as"
            value={adminUsername || "Orbit Admin"}
            note="Local session username"
          />
          <InfoTile
            icon={Sparkles}
            label="Role"
            value={toTitleCase(sessionRole)}
            note="Derived from the current access token"
          />
          <InfoTile
            icon={Server}
            label="Desktop mode"
            value={
              desktop.status
                ? desktop.status.packaged
                  ? "Packaged desktop"
                  : "Development shell"
                : "Browser session"
            }
            note={desktop.status?.workspaceRoot || "No local workspace connected"}
          />
        </div>

        <div className="mt-6">
          <ActionButton label="Sign out" variant="danger" onClick={logout} />
        </div>
      </section>
    </div>
  );
}

function NavButton({
  active,
  icon: Icon,
  label,
  collapsed = false,
  onClick,
  badge,
  badgeTone = "default",
}: {
  active: boolean;
  icon: LucideIcon;
  label: string;
  collapsed?: boolean;
  onClick: () => void;
  badge?: number;
  badgeTone?: "default" | "warning";
}) {
  return (
    <button
      onClick={onClick}
      className={classNames(
        "group relative flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium transition-all duration-200",
        active
          ? "bg-white/10 text-white"
          : "text-slate-400 hover:bg-white/5 hover:text-slate-200",
      )}
    >
      {active && <div className="sidebar-active-indicator" />}
      <Icon className={classNames("h-4 w-4 shrink-0 transition-colors", active ? "text-orbit-primary" : "text-slate-500 group-hover:text-slate-300")} />
      {!collapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {badge !== undefined && badge > 0 && (
            <SidebarBadge count={badge} tone={badgeTone} />
          )}
        </>
      )}
    </button>
  );
}

function SidebarBadge({ count, tone = "default" }: { count: number; tone?: "default" | "warning" }) {
  if (count <= 0) return null;
  return (
    <span className={classNames(
      "sidebar-badge",
      tone === "warning" && "sidebar-badge-warning"
    )}>
      {count > 99 ? "99+" : count}
    </span>
  );
}

function PanelIntro({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <div className="text-[0.7rem] font-black uppercase tracking-[0.35em] text-orbit-accent">{eyebrow}</div>
        <h2 className="mt-2 text-4xl font-black tracking-tight text-white">{title}</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-400">{description}</p>
      </div>
      {action}
    </div>
  );
}

function StationIgnition({
  apiBaseUrl,
  onSuccess,
  onCancel,
}: {
  apiBaseUrl: string;
  onSuccess: (at: string, rt: string, u: string) => void;
  onCancel: () => void;
}) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [masterSecret, setMasterSecret] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleIgnition = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const normalizedBase = normalizeApiBaseUrl(apiBaseUrl);
      // We use the masterSecret as the 'password' for the bootstrap endpoint
      const tokens = await api.bootstrap(username, masterSecret, normalizedBase);
      onSuccess(tokens.access_token, tokens.refresh_token, username);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-orbit-bg px-4 py-10 text-orbit-fg">
      <div className="absolute inset-0 bg-rose-500/5 animate-pulse pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-xl rounded-[2.5rem] border border-rose-500/30 bg-orbit-surface/80 p-10 backdrop-blur-2xl shadow-2xl shadow-rose-500/10"
      >
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border border-rose-500/40 bg-rose-500/10 text-rose-400">
            <Lock className="h-8 w-8" />
          </div>
          <h2 className="text-3xl font-black tracking-tight text-white">Station Ignition</h2>
          <p className="mt-3 text-slate-400">First-time system initialization required.</p>
        </div>

        {error && <ErrorBanner message={error} />}

        <form onSubmit={handleIgnition} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-widest text-slate-500">Desired Admin Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white placeholder-slate-600 focus:border-rose-500/50 focus:outline-none"
                placeholder="e.g. admin"
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-widest text-slate-500">Desired Admin Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-2xl border border-orbit-border bg-orbit-bg/50 px-5 py-4 text-white placeholder-slate-600 focus:border-rose-500/50 focus:outline-none"
                placeholder="Secure password"
                required
              />
            </div>
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5">
              <label className="mb-2 block text-xs font-black uppercase tracking-widest text-rose-400">Master Bootstrap Secret</label>
              <input
                type="password"
                value={masterSecret}
                onChange={(e) => setMasterSecret(e.target.value)}
                className="w-full rounded-xl border border-rose-500/30 bg-orbit-bg/60 px-4 py-3 text-white placeholder-rose-900/50 focus:border-rose-500 focus:outline-none"
                placeholder="From .env file"
                required
              />
              <p className="mt-3 text-[10px] uppercase tracking-wider text-rose-500/60 font-bold">Requires server-side file access</p>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 rounded-2xl border border-orbit-border bg-transparent py-4 text-sm font-bold text-slate-400 transition hover:bg-orbit-surface"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-[2] rounded-2xl bg-rose-600 py-4 text-sm font-bold text-white transition hover:bg-rose-500 hover:shadow-lg hover:shadow-rose-500/20 disabled:opacity-50"
            >
              {loading ? "Igniting..." : "Start Station Ignition"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  note,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  note: string;
  tone: "default" | "success" | "warning" | "danger";
}) {
  const toneClasses =
    tone === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : tone === "warning"
        ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
        : tone === "danger"
          ? "border-rose-500/30 bg-rose-500/10 text-rose-300"
          : "border-orbit-border bg-orbit-bg/35 text-orbit-primary";

  return (
    <div className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-5 backdrop-blur-xl">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className={classNames("flex h-12 w-12 items-center justify-center rounded-2xl border", toneClasses)}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="text-[0.7rem] font-black uppercase tracking-[0.3em] text-slate-500">{label}</div>
      </div>
      <div className="text-4xl font-black tracking-tight text-white">{value}</div>
      <div className="mt-2 text-sm text-slate-400">{note}</div>
    </div>
  );
}

function StatusChip({
  label,
  tone,
}: {
  label: string;
  tone: "default" | "success" | "warning" | "danger" | "info";
}) {
  const toneClasses =
    tone === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : tone === "warning"
        ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
        : tone === "danger"
          ? "border-rose-500/30 bg-rose-500/10 text-rose-300"
          : tone === "info"
            ? "border-blue-500/30 bg-blue-500/10 text-blue-300"
            : "border-orbit-border bg-orbit-bg/40 text-slate-300";

  return (
    <span className={classNames("inline-flex items-center rounded-full border px-3 py-1 text-xs font-black uppercase tracking-[0.2em]", toneClasses)}>
      {label}
    </span>
  );
}

function ActionButton({
  label,
  onClick,
  disabled = false,
  variant = "primary",
  type = "button",
}: {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "danger";
  type?: "button" | "submit";
}) {
  const classes =
    variant === "secondary"
      ? "border border-orbit-border bg-orbit-surface/70 text-slate-100 hover:border-orbit-primary/60"
      : variant === "danger"
        ? "border border-rose-500/30 bg-rose-500/10 text-rose-200 hover:border-rose-400/60"
        : "bg-orbit-primary text-white hover:brightness-110";

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={classNames(
        "inline-flex items-center justify-center rounded-2xl px-4 py-3 text-sm font-semibold transition",
        classes,
        disabled && "cursor-not-allowed opacity-60",
      )}
    >
      {label}
    </button>
  );
}

function FilterChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={classNames(
        "rounded-full px-4 py-2 text-sm font-semibold transition",
        active
          ? "bg-orbit-primary text-white"
          : "border border-orbit-border bg-orbit-surface/60 text-slate-300 hover:border-orbit-primary/50 hover:text-white",
      )}
    >
      {label}
    </button>
  );
}

function LoadingState({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center rounded-[2rem] border border-orbit-border bg-orbit-surface/50 px-6 py-16 text-slate-300">
      <RefreshCw className="mr-3 h-5 w-5 animate-spin" />
      {label}
    </div>
  );
}

function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-[2rem] border border-dashed border-orbit-border bg-orbit-surface/35 px-8 py-14 text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border border-orbit-border bg-orbit-bg/50 text-orbit-primary">
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="text-xl font-bold text-white">{title}</h3>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400">{description}</p>
    </div>
  );
}

function ErrorBanner({
  message,
  tone = "error",
}: {
  message: string;
  tone?: "error" | "info";
}) {
  const classes =
    tone === "info"
      ? "border-blue-500/30 bg-blue-500/10 text-blue-200"
      : "border-rose-500/30 bg-rose-500/10 text-rose-200";

  return (
    <div className={classNames("rounded-2xl border px-4 py-3 text-sm", classes)}>
      {message}
    </div>
  );
}

function statusTone(status: string): "default" | "success" | "warning" | "danger" {
  if (status === "RESOLVED" || status === "running") {
    return "success";
  }
  if (status === "OPEN" || status === "PENDING" || status === "starting") {
    return "warning";
  }
  if (status === "REJECTED" || status === "error") {
    return "danger";
  }
  return "default";
}

function ServiceCard({
  icon: Icon,
  label,
  service,
  loading,
  onStart,
  onRestart,
  onStop,
}: {
  icon: LucideIcon;
  label: string;
  service: DesktopRuntimeStatus["services"]["api"] | undefined;
  loading: boolean;
  onStart: () => void;
  onRestart: () => void;
  onStop: () => void;
}) {
  return (
    <div className="rounded-[1.75rem] border border-orbit-border bg-orbit-bg/35 p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-orbit-border bg-orbit-surface/70 text-orbit-primary">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-bold text-white">{label}</h4>
            <div className="text-sm text-slate-400">{service?.detail || "No status yet."}</div>
          </div>
        </div>
        <StatusChip tone={statusTone(service?.status || "unknown")} label={toTitleCase(service?.status || "unknown")} />
      </div>

      <div className="text-xs uppercase tracking-[0.25em] text-slate-500">
        PID {service?.pid || "—"}
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <ActionButton label={loading ? "Working..." : "Start"} disabled={loading} onClick={onStart} />
        <ActionButton label="Restart" variant="secondary" disabled={loading} onClick={onRestart} />
        <ActionButton label="Stop" variant="secondary" disabled={loading} onClick={onStop} />
      </div>
    </div>
  );
}

function CompactServiceCard({
  label,
  detail,
  status,
  onStart,
  onRestart,
  onStop,
}: {
  label: string;
  detail: string;
  status: string;
  onStart: () => void;
  onRestart: () => void;
  onStop: () => void;
}) {
  return (
    <div className="rounded-[1.5rem] border border-orbit-border bg-orbit-bg/35 p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="font-bold text-white">{label}</div>
        <StatusChip tone={statusTone(status)} label={toTitleCase(status)} />
      </div>
      <p className="text-sm text-slate-400">{detail}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <ActionButton label="Start" onClick={onStart} />
        <ActionButton label="Restart" variant="secondary" onClick={onRestart} />
        <ActionButton label="Stop" variant="secondary" onClick={onStop} />
      </div>
    </div>
  );
}

function InfoTile({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-[1.75rem] border border-orbit-border bg-orbit-bg/35 p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-orbit-border bg-orbit-surface/70 text-orbit-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div className="text-xs font-black uppercase tracking-[0.25em] text-slate-500">{label}</div>
      </div>
      <div className="break-all text-lg font-semibold text-white">{value}</div>
      <div className="mt-2 text-sm text-slate-400">{note}</div>
    </div>
  );
}

function LogRow({ entry }: { entry: DesktopLogEntry }) {
  return (
    <div className="rounded-2xl border border-orbit-border bg-orbit-bg/35 p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip tone={entry.level === "error" ? "danger" : entry.level === "warn" ? "warning" : "default"} label={entry.source} />
          <span className="text-xs uppercase tracking-[0.2em] text-slate-500">{entry.level}</span>
        </div>
        <span className="text-xs text-slate-500">{formatDateTime(entry.timestamp)}</span>
      </div>
      <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-slate-200">{entry.message}</pre>
    </div>
  );
}

function TelemetryCard({
  title,
  description,
  icon: Icon,
  items,
  accent,
  emptyTitle,
  emptyDescription,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
  items: TelemetryRow[];
  accent: "success" | "warning";
  emptyTitle: string;
  emptyDescription: string;
}) {
  return (
    <section className="rounded-[2rem] border border-orbit-border bg-orbit-surface/60 p-6 backdrop-blur-xl">
      <div className="mb-6 flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-orbit-border bg-orbit-bg/40 text-orbit-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-xl font-black tracking-tight text-white">{title}</h3>
          <p className="mt-2 text-sm text-slate-400">{description}</p>
        </div>
      </div>

      {items.length ? (
        <div className="space-y-4">
          {items.map((item, index) => {
            const leader = items[0]?.count || 1;
            const width = Math.max(8, Math.round((item.count / leader) * 100));
            return (
              <div key={`${item.query}-${index}`} className="space-y-2">
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="truncate font-semibold text-white">{item.query}</span>
                  <span className="font-mono text-slate-400">{item.count}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-orbit-bg">
                  <div
                    className={classNames(
                      "h-full rounded-full",
                      accent === "success" ? "bg-emerald-400" : "bg-amber-400",
                    )}
                    style={{ width: `${width}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState icon={Icon} title={emptyTitle} description={emptyDescription} />
      )}
    </section>
  );
}

function ChoiceCard({
  active,
  icon: Icon,
  title,
  description,
  onClick,
}: {
  active: boolean;
  icon: LucideIcon;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={classNames(
        "rounded-[1.75rem] border p-5 text-left transition",
        active
          ? "border-orbit-primary bg-orbit-primary/10 text-white orbit-glow"
          : "border-orbit-border bg-orbit-bg/35 text-slate-300 hover:border-orbit-primary/40 hover:text-white",
      )}
    >
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl border border-current/20 bg-current/10">
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-lg font-bold">{title}</div>
      <div className="mt-2 text-sm leading-6 text-slate-400">{description}</div>
    </button>
  );
}

function HoverMetricCard({
  icon: Icon,
  title,
  subtitle,
  value,
  trend,
}: {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  value: string;
  trend: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.16 }}
      className="rounded-[1.5rem] border border-orbit-border bg-orbit-bg/40 p-5"
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-orbit-primary/40 bg-orbit-primary/10 text-orbit-primary">
          <Icon className="h-5 w-5" />
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
          {trend}
        </span>
      </div>
      <div className="text-sm text-slate-400">{title}</div>
      <div className="mt-1 text-3xl font-black text-white">{value}</div>
      <div className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-500">{subtitle}</div>
    </motion.div>
  );
}

function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: Array<{ id: string; message: string; tone: ToastTone }>;
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          onClick={() => onDismiss(toast.id)}
          className={classNames(
            "pointer-events-auto rounded-2xl border px-4 py-3 text-left text-sm shadow-lg backdrop-blur",
            toast.tone === "success"
              ? "border-emerald-500/40 bg-emerald-500/20 text-emerald-100"
              : toast.tone === "warning"
                ? "border-amber-500/40 bg-amber-500/20 text-amber-100"
                : toast.tone === "danger"
                  ? "border-rose-500/40 bg-rose-500/20 text-rose-100"
                  : "border-blue-500/40 bg-blue-500/20 text-blue-100",
          )}
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}
