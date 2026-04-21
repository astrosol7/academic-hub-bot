const { contextBridge, ipcRenderer } = require("electron");

function subscribe(channel, listener) {
  const wrapped = (_event, payload) => {
    listener(payload);
  };

  ipcRenderer.on(channel, wrapped);
  return () => {
    ipcRenderer.removeListener(channel, wrapped);
  };
}

contextBridge.exposeInMainWorld("orbitDesktop", {
  getStatus: () => ipcRenderer.invoke("orbit:get-status"),
  startService: (service) => ipcRenderer.invoke("orbit:start-service", service),
  stopService: (service) => ipcRenderer.invoke("orbit:stop-service", service),
  restartService: (service) => ipcRenderer.invoke("orbit:restart-service", service),
  openDataFolder: () => ipcRenderer.invoke("orbit:open-data-folder"),
  backupDatabase: () => ipcRenderer.invoke("orbit:backup-database"),
  onStatus: (listener) => subscribe("orbit:status", listener),
  onLog: (listener) => subscribe("orbit:log", listener),
});
