const { app, BrowserWindow, Menu, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const axios = require('axios');

let mainWindow;
let apiProcess;
let botProcess;

// Keep a global reference of the window object
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'icon.ico'),
    show: false,
    frame: true,
    titleBarStyle: 'default'
  });

  // Load the app
  const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, '../build/index.html')}`;
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    // Cleanup processes
    if (apiProcess) apiProcess.kill();
    if (botProcess) botProcess.kill();
  });

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// Create custom menu
function createMenu() {
  const template = [
    {
      label: 'System Control',
      submenu: [
        {
          label: 'Start API Server',
          click: () => startAPIServer(),
          accelerator: 'CmdOrCtrl+Shift+A'
        },
        {
          label: 'Start Telegram Bot',
          click: () => startTelegramBot(),
          accelerator: 'CmdOrCtrl+Shift+B'
        },
        {
          label: 'Stop All Services',
          click: () => stopAllServices(),
          accelerator: 'CmdOrCtrl+Shift+S'
        },
        { type: 'separator' },
        {
          label: 'System Status',
          click: () => mainWindow.webContents.send('system-status-request')
        }
      ]
    },
    {
      label: 'Database',
      submenu: [
        {
          label: 'Initialize Database',
          click: () => initializeDatabase()
        },
        {
          label: 'Sync Resources',
          click: () => syncResources()
        },
        {
          label: 'Backup Database',
          click: () => backupDatabase()
        },
        { type: 'separator' },
        {
          label: 'Open Data Folder',
          click: () => shell.openPath(path.join(__dirname, '../../data'))
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About Orbit Control',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Orbit Control Center',
              message: 'Orbit Control Center v1.0',
              detail: 'Ultimate System Control for Academic Hub\n\nBuilt with Electron and React'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// System Control Functions
function startAPIServer() {
  if (apiProcess) {
    mainWindow.webContents.send('log-message', 'API Server already running');
    return;
  }

  const apiPath = path.join(__dirname, '../../');
  apiProcess = spawn('python', ['-m', 'backend.api.main'], {
    cwd: apiPath,
    stdio: 'pipe'
  });

  apiProcess.stdout.on('data', (data) => {
    mainWindow.webContents.send('log-message', `API: ${data.toString()}`);
  });

  apiProcess.stderr.on('data', (data) => {
    mainWindow.webContents.send('log-message', `API Error: ${data.toString()}`);
  });

  apiProcess.on('close', (code) => {
    mainWindow.webContents.send('log-message', `API Process exited with code ${code}`);
    apiProcess = null;
  });

  mainWindow.webContents.send('service-status', { api: 'starting' });
}

function startTelegramBot() {
  if (botProcess) {
    mainWindow.webContents.send('log-message', 'Telegram Bot already running');
    return;
  }

  const botPath = path.join(__dirname, '../../');
  botProcess = spawn('python', ['-m', 'academic_hub.app'], {
    cwd: botPath,
    stdio: 'pipe'
  });

  botProcess.stdout.on('data', (data) => {
    mainWindow.webContents.send('log-message', `Bot: ${data.toString()}`);
  });

  botProcess.stderr.on('data', (data) => {
    mainWindow.webContents.send('log-message', `Bot Error: ${data.toString()}`);
  });

  botProcess.on('close', (code) => {
    mainWindow.webContents.send('log-message', `Bot Process exited with code ${code}`);
    botProcess = null;
  });

  mainWindow.webContents.send('service-status', { bot: 'starting' });
}

function stopAllServices() {
  if (apiProcess) {
    apiProcess.kill();
    apiProcess = null;
  }
  if (botProcess) {
    botProcess.kill();
    botProcess = null;
  }
  mainWindow.webContents.send('service-status', { api: 'stopped', bot: 'stopped' });
  mainWindow.webContents.send('log-message', 'All services stopped');
}

async function initializeDatabase() {
  try {
    const dbPath = path.join(__dirname, '../../backend/api/database_sqlite.py');
    const { spawn } = require('child_process');
    
    const result = spawn('python', ['-c', `
import sys
sys.path.append('${path.join(__dirname, '../../')}')
from backend.api.database_sqlite import init_database
init_database()
print("Database initialized successfully")
`], {
      cwd: path.join(__dirname, '../../'),
      stdio: 'pipe'
    });

    result.stdout.on('data', (data) => {
      mainWindow.webContents.send('log-message', `DB Init: ${data.toString()}`);
    });

    result.stderr.on('data', (data) => {
      mainWindow.webContents.send('log-message', `DB Init Error: ${data.toString()}`);
    });

  } catch (error) {
    mainWindow.webContents.send('log-message', `DB Init Error: ${error.message}`);
  }
}

function syncResources() {
  const syncPath = path.join(__dirname, '../../');
  const syncProcess = spawn('python', ['-m', 'backend.sync.sync_service'], {
    cwd: syncPath,
    stdio: 'pipe'
  });

  syncProcess.stdout.on('data', (data) => {
    mainWindow.webContents.send('log-message', `Sync: ${data.toString()}`);
  });

  syncProcess.stderr.on('data', (data) => {
    mainWindow.webContents.send('log-message', `Sync Error: ${data.toString()}`);
  });
}

function backupDatabase() {
  const dataPath = path.join(__dirname, '../../data');
  const backupPath = path.join(dataPath, `backup_${new Date().toISOString().replace(/[:.]/g, '-')}.db`);
  
  try {
    if (fs.existsSync(path.join(dataPath, 'academic_hub.db'))) {
      fs.copyFileSync(path.join(dataPath, 'academic_hub.db'), backupPath);
      mainWindow.webContents.send('log-message', `Database backed up to ${backupPath}`);
    } else {
      mainWindow.webContents.send('log-message', 'Database file not found');
    }
  } catch (error) {
    mainWindow.webContents.send('log-message', `Backup Error: ${error.message}`);
  }
}

// IPC Handlers
ipcMain.handle('get-system-status', async () => {
  try {
    const apiResponse = await axios.get('http://localhost:8000/api/v1/health', { timeout: 2000 });
    return {
      api: apiResponse.data.status === 'operational' ? 'running' : 'error',
      bot: botProcess ? 'running' : 'stopped',
      uptime: process.uptime()
    };
  } catch (error) {
    return {
      api: 'stopped',
      bot: botProcess ? 'running' : 'stopped',
      uptime: process.uptime()
    };
  }
});

ipcMain.handle('get-logs', async () => {
  const logPath = path.join(__dirname, '../../data');
  if (fs.existsSync(logPath)) {
    const files = fs.readdirSync(logPath).filter(f => f.endsWith('.log'));
    return files.map(f => ({
      name: f,
      content: fs.readFileSync(path.join(logPath, f), 'utf8')
    }));
  }
  return [];
});

// App Events
app.whenReady().then(() => {
  createWindow();
  createMenu();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});
