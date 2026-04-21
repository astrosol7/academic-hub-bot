const { app, BrowserWindow, Menu, dialog, ipcMain, shell } = require("electron");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const API_HEALTH_URL = "http://127.0.0.1:8000/api/v1/health";
const LOG_LIMIT = 150;

const managedProcesses = {
  api: null,
  bot: null,
};

const serviceState = {
  api: { name: "api", label: "API Engine", status: "stopped", pid: null, detail: "Not running." },
  bot: { name: "bot", label: "Telegram Bot", status: "stopped", pid: null, detail: "Not running." },
};

const serviceModules = {
  api: "backend.api.main",
  bot: "src.bot.main",
};

let mainWindow = null;
let workspaceRootCache;
let statusPoller = null;
const logBuffer = [];

function emitLog(source, message, level = "info") {
  const lines = String(message)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  for (const line of lines) {
    const entry = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      source,
      level,
      message: line,
      timestamp: new Date().toISOString(),
    };

    logBuffer.unshift(entry);
    if (logBuffer.length > LOG_LIMIT) {
      logBuffer.pop();
    }

    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send("orbit:log", entry);
    }
  }
}

function isWorkspaceRoot(candidate) {
  if (!candidate) {
    return false;
  }

  return (
    fs.existsSync(path.join(candidate, "backend", "api", "main.py")) &&
    fs.existsSync(path.join(candidate, "src", "bot", "main.py"))
  );
}

function getWorkspaceRoot() {
  if (workspaceRootCache !== undefined) {
    return workspaceRootCache;
  }

  const candidates = [
    process.env.ORBIT_WORKSPACE_ROOT,
    path.resolve(__dirname, ".."),
    path.resolve(process.cwd()),
    path.resolve(process.resourcesPath, "..", "..", "..", ".."),
    path.resolve(path.dirname(app.getPath("exe")), "..", "..", ".."),
  ];

  workspaceRootCache = candidates.find((candidate) => isWorkspaceRoot(candidate)) || null;
  return workspaceRootCache;
}

function resolvePythonCommand(workspaceRoot) {
  const candidates = [
    path.join(workspaceRoot, ".venv", "Scripts", "python.exe"),
    path.join(workspaceRoot, "venv", "Scripts", "python.exe"),
    path.join(workspaceRoot, ".venv", "bin", "python"),
    path.join(workspaceRoot, "venv", "bin", "python"),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return { command: candidate, prefixArgs: [] };
    }
  }

  if (process.platform === "win32") {
    return { command: "py", prefixArgs: ["-3"] };
  }

  return { command: "python3", prefixArgs: [] };
}

async function probeApiHealth() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 1800);

  try {
    const response = await fetch(API_HEALTH_URL, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const body = await response.json();
    return {
      online: true,
      detail: `Healthy (${body.version || "unknown version"})`,
    };
  } catch {
    return {
      online: false,
      detail: "Not responding on http://127.0.0.1:8000",
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

function getBaseRuntimeStatus() {
  const workspaceRoot = getWorkspaceRoot();
  return {
    available: true,
    packaged: app.isPackaged,
    workspaceRoot,
    dataDirectory: workspaceRoot ? path.join(workspaceRoot, "data") : null,
    apiBaseUrl: process.env.ORBIT_API_BASE_URL || "http://127.0.0.1:8000",
    workspaceDetected: Boolean(workspaceRoot),
    canControlServices: Boolean(workspaceRoot),
  };
}

async function getRuntimeStatus() {
  const base = getBaseRuntimeStatus();
  const apiHealth = await probeApiHealth();

  const apiStatus = {
    ...serviceState.api,
    status: apiHealth.online
      ? "running"
      : managedProcesses.api
        ? serviceState.api.status === "error"
          ? "error"
          : "starting"
        : "stopped",
    detail: apiHealth.online ? apiHealth.detail : serviceState.api.detail || apiHealth.detail,
    pid: managedProcesses.api ? managedProcesses.api.pid || null : null,
  };

  const botStatus = {
    ...serviceState.bot,
    status: managedProcesses.bot ? serviceState.bot.status : "stopped",
    pid: managedProcesses.bot ? managedProcesses.bot.pid || null : null,
    detail: managedProcesses.bot ? serviceState.bot.detail : "Not running.",
  };

  return {
    ...base,
    services: {
      api: apiStatus,
      bot: botStatus,
    },
    logs: logBuffer.slice(0, 60),
  };
}

function setServiceState(name, patch) {
  serviceState[name] = {
    ...serviceState[name],
    ...patch,
  };
}

async function broadcastStatus() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  try {
    const status = await getRuntimeStatus();
    mainWindow.webContents.send("orbit:status", status);
  } catch (error) {
    emitLog("system", `Status update failed: ${error.message}`, "warn");
  }
}

function loadRenderer(window) {
  const bundledRenderer = path.join(__dirname, "dashboard-dist", "index.html");
  const devServerUrl = process.env.ELECTRON_START_URL || "http://127.0.0.1:5173";

  if (app.isPackaged || process.env.ELECTRON_USE_LOCAL_BUILD === "1") {
    return window.loadFile(bundledRenderer);
  }

  return window.loadURL(devServerUrl);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1560,
    height: 980,
    minWidth: 1320,
    minHeight: 780,
    backgroundColor: "#05070a",
    show: false,
    title: "Orbit Control Center",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  loadRenderer(mainWindow).catch((error) => {
    dialog.showErrorBox(
      "Orbit Control Center",
      `The admin dashboard could not be loaded.\n\n${error.message}`,
    );
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    void broadcastStatus();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.webContents.on("will-navigate", (event, url) => {
    const isLocalDev = !app.isPackaged && url.startsWith("http://127.0.0.1:5173");
    const isBundledFile = url.startsWith("file://");
    if (!isLocalDev && !isBundledFile) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

async function killProcessTree(childProcess) {
  if (!childProcess || !childProcess.pid) {
    return;
  }

  if (process.platform === "win32") {
    await new Promise((resolve) => {
      const killer = spawn("taskkill", ["/PID", String(childProcess.pid), "/T", "/F"], {
        windowsHide: true,
      });
      killer.on("close", () => resolve());
      killer.on("error", () => resolve());
    });
    return;
  }

  try {
    childProcess.kill("SIGTERM");
  } catch {
    return;
  }
}

function attachChildLogging(name, childProcess) {
  childProcess.stdout.on("data", (chunk) => emitLog(name, chunk.toString(), "info"));
  childProcess.stderr.on("data", (chunk) => emitLog(name, chunk.toString(), "error"));

  childProcess.on("error", (error) => {
    managedProcesses[name] = null;
    setServiceState(name, {
      status: "error",
      detail: error.message,
      pid: null,
    });
    emitLog("system", `${serviceState[name].label} failed to start: ${error.message}`, "error");
    void broadcastStatus();
  });

  childProcess.on("close", (code) => {
    managedProcesses[name] = null;
    setServiceState(name, {
      status: "stopped",
      detail: code === 0 || code === null ? "Stopped." : `Exited with code ${code}.`,
      pid: null,
    });
    emitLog("system", `${serviceState[name].label} exited${code === null ? "" : ` with code ${code}`}.`, code === 0 || code === null ? "info" : "warn");
    void broadcastStatus();
  });
}

async function startService(name) {
  if (managedProcesses[name]) {
    return getRuntimeStatus();
  }

  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    throw new Error(
      "Orbit workspace not detected. Set ORBIT_WORKSPACE_ROOT or launch the desktop build from inside the repository.",
    );
  }

  const python = resolvePythonCommand(workspaceRoot);
  const args = [...python.prefixArgs, "-m", serviceModules[name]];
  const childProcess = spawn(python.command, args, {
    cwd: workspaceRoot,
    env: {
      ...process.env,
      PYTHONPATH: workspaceRoot,
    },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });

  managedProcesses[name] = childProcess;
  setServiceState(name, {
    status: name === "api" ? "starting" : "running",
    detail: name === "api" ? "Launching backend API..." : "Bot polling has started.",
    pid: childProcess.pid || null,
  });

  emitLog("system", `Starting ${serviceState[name].label}...`);
  attachChildLogging(name, childProcess);

  if (name === "api") {
    setTimeout(() => {
      void broadcastStatus();
    }, 1200);
  } else {
    void broadcastStatus();
  }

  return getRuntimeStatus();
}

async function stopService(name) {
  const childProcess = managedProcesses[name];
  if (!childProcess) {
    if (name === "api") {
      const apiHealth = await probeApiHealth();
      if (apiHealth.online) {
        emitLog("system", "A local API is running, but it was not started by Orbit Control Center.", "warn");
      }
    }
    return getRuntimeStatus();
  }

  emitLog("system", `Stopping ${serviceState[name].label}...`);
  await killProcessTree(childProcess);
  managedProcesses[name] = null;
  setServiceState(name, {
    status: "stopped",
    detail: "Stopped.",
    pid: null,
  });

  await broadcastStatus();
  return getRuntimeStatus();
}

async function restartService(name) {
  await stopService(name);
  return startService(name);
}

async function openDataFolder() {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    throw new Error("Orbit workspace not detected.");
  }

  const target = path.join(workspaceRoot, "data");
  const errorMessage = await shell.openPath(target);
  if (errorMessage) {
    throw new Error(errorMessage);
  }
}

async function backupDatabase() {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    throw new Error("Orbit workspace not detected.");
  }

  const dataDirectory = path.join(workspaceRoot, "data");
  const sourcePath = path.join(dataDirectory, "academic_hub.db");
  if (!fs.existsSync(sourcePath)) {
    throw new Error("Database file not found at data/academic_hub.db.");
  }

  const fileName = `academic_hub_backup_${new Date().toISOString().replace(/[:.]/g, "-")}.db`;
  const destinationPath = path.join(dataDirectory, fileName);
  fs.copyFileSync(sourcePath, destinationPath);
  emitLog("system", `Database backup created: ${fileName}`);
  return destinationPath;
}

async function stopManagedProcesses() {
  await Promise.allSettled(
    Object.keys(managedProcesses).map((name) => stopService(name)),
  );
}

function showMenuError(error) {
  dialog.showErrorBox("Orbit Control Center", error.message);
}

function createMenu() {
  const runAction = (action) => {
    action().catch((error) => showMenuError(error));
  };

  const template = [
    {
      label: "Orbit",
      submenu: [
        {
          label: "Refresh Status",
          click: () => runAction(() => broadcastStatus()),
          accelerator: "CmdOrCtrl+R",
        },
        { type: "separator" },
        {
          label: "Quit",
          role: "quit",
        },
      ],
    },
    {
      label: "Services",
      submenu: [
        {
          label: "Start API Engine",
          click: () => runAction(() => startService("api")),
        },
        {
          label: "Restart API Engine",
          click: () => runAction(() => restartService("api")),
        },
        {
          label: "Start Telegram Bot",
          click: () => runAction(() => startService("bot")),
        },
        {
          label: "Restart Telegram Bot",
          click: () => runAction(() => restartService("bot")),
        },
        { type: "separator" },
        {
          label: "Stop API Engine",
          click: () => runAction(() => stopService("api")),
        },
        {
          label: "Stop Telegram Bot",
          click: () => runAction(() => stopService("bot")),
        },
      ],
    },
    {
      label: "Data",
      submenu: [
        {
          label: "Open Data Folder",
          click: () => runAction(() => openDataFolder()),
        },
        {
          label: "Backup Database",
          click: () => runAction(() => backupDatabase()),
        },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

ipcMain.handle("orbit:get-status", async () => getRuntimeStatus());
ipcMain.handle("orbit:start-service", async (_event, service) => startService(service));
ipcMain.handle("orbit:stop-service", async (_event, service) => stopService(service));
ipcMain.handle("orbit:restart-service", async (_event, service) => restartService(service));
ipcMain.handle("orbit:open-data-folder", async () => openDataFolder());
ipcMain.handle("orbit:backup-database", async () => backupDatabase());

app.whenReady().then(() => {
  createWindow();
  createMenu();
  statusPoller = setInterval(() => {
    void broadcastStatus();
  }, 8000);
});

app.on("before-quit", () => {
  if (statusPoller) {
    clearInterval(statusPoller);
    statusPoller = null;
  }
  void stopManagedProcesses();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
