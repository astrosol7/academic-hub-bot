export type DesktopServiceName = "api" | "bot";
export type DesktopServiceState = "running" | "stopped" | "starting" | "error" | "unknown";
export type DesktopLogLevel = "info" | "warn" | "error";
export type DesktopLogSource = "system" | "api" | "bot";

export type DesktopLogEntry = {
  id: string;
  source: DesktopLogSource;
  level: DesktopLogLevel;
  message: string;
  timestamp: string;
};

export type DesktopServiceStatus = {
  name: DesktopServiceName;
  label: string;
  status: DesktopServiceState;
  pid: number | null;
  detail: string;
};

export type DesktopRuntimeStatus = {
  available: boolean;
  packaged: boolean;
  workspaceRoot: string | null;
  dataDirectory: string | null;
  apiBaseUrl: string;
  workspaceDetected: boolean;
  canControlServices: boolean;
  services: Record<DesktopServiceName, DesktopServiceStatus>;
  logs: DesktopLogEntry[];
};

export type OrbitDesktopBridge = {
  getStatus: () => Promise<DesktopRuntimeStatus>;
  startService: (service: DesktopServiceName) => Promise<DesktopRuntimeStatus>;
  stopService: (service: DesktopServiceName) => Promise<DesktopRuntimeStatus>;
  restartService: (service: DesktopServiceName) => Promise<DesktopRuntimeStatus>;
  openDataFolder: () => Promise<void>;
  backupDatabase: () => Promise<string>;
  onStatus: (listener: (status: DesktopRuntimeStatus) => void) => () => void;
  onLog: (listener: (entry: DesktopLogEntry) => void) => () => void;
};

export function getDesktopBridge(): OrbitDesktopBridge | null {
  return window.orbitDesktop ?? null;
}
