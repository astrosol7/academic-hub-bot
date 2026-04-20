import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Monitor, Server, Database, Users, Activity, AlertTriangle, 
  Settings, Power, RefreshCw, Download, Upload, Shield, 
  Zap, Globe, Terminal, FileText, BarChart3, Lock, Eye,
  Play, Square, RotateCcw, HardDrive, Wifi, Cpu, MemoryStick
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import './App.css';

const { ipcRenderer } = window.require('electron');

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [systemStatus, setSystemStatus] = useState({
    api: 'stopped',
    bot: 'stopped',
    uptime: 0
  });
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Request initial system status
    updateSystemStatus();
    
    // Set up IPC listeners
    ipcRenderer.on('log-message', (event, message) => {
      setLogs(prev => [...prev.slice(-100), { 
        id: Date.now(), 
        message: message.toString().trim(),
        timestamp: new Date()
      }]);
    });

    ipcRenderer.on('service-status', (event, status) => {
      setSystemStatus(prev => ({ ...prev, ...status }));
    });

    // Auto-refresh system status
    const interval = setInterval(updateSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const updateSystemStatus = async () => {
    try {
      const status = await ipcRenderer.invoke('get-system-status');
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to get system status:', error);
    }
  };

  const startService = async (service) => {
    setIsLoading(true);
    try {
      if (service === 'api') {
        await ipcRenderer.send('start-api-server');
      } else if (service === 'bot') {
        await ipcRenderer.send('start-telegram-bot');
      }
      toast.success(`${service.toUpperCase()} service starting...`);
    } catch (error) {
      toast.error(`Failed to start ${service} service`);
    }
    setTimeout(() => setIsLoading(false), 2000);
  };

  const stopService = async () => {
    setIsLoading(true);
    try {
      await ipcRenderer.send('stop-all-services');
      toast.success('All services stopped');
    } catch (error) {
      toast.error('Failed to stop services');
    }
    setTimeout(() => setIsLoading(false), 2000);
  };

  const initializeDatabase = async () => {
    setIsLoading(true);
    try {
      await ipcRenderer.send('initialize-database');
      toast.success('Database initialization started');
    } catch (error) {
      toast.error('Failed to initialize database');
    }
    setTimeout(() => setIsLoading(false), 2000);
  };

  const syncResources = async () => {
    setIsLoading(true);
    try {
      await ipcRenderer.send('sync-resources');
      toast.success('Resource synchronization started');
    } catch (error) {
      toast.error('Failed to sync resources');
    }
    setTimeout(() => setIsLoading(false), 2000);
  };

  const backupDatabase = async () => {
    setIsLoading(true);
    try {
      await ipcRenderer.send('backup-database');
      toast.success('Database backup created');
    } catch (error) {
      toast.error('Failed to backup database');
    }
    setTimeout(() => setIsLoading(false), 2000);
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-400';
      case 'starting': return 'text-yellow-400';
      case 'stopped': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Play className="w-4 h-4" />;
      case 'starting': return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'stopped': return <Square className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex">
      {/* Sidebar */}
      <motion.aside 
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        className="w-64 bg-gray-800 border-r border-gray-700 p-6"
      >
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
            <Monitor className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Orbit Control</h1>
            <p className="text-xs text-gray-400">System Management</p>
          </div>
        </div>

        <nav className="space-y-2">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 className="w-5 h-5" /> },
            { id: 'services', label: 'Services', icon: <Server className="w-5 h-5" /> },
            { id: 'database', label: 'Database', icon: <Database className="w-5 h-5" /> },
            { id: 'logs', label: 'Logs', icon: <Terminal className="w-5 h-5" /> },
            { id: 'monitoring', label: 'Monitoring', icon: <Activity className="w-5 h-5" /> },
            { id: 'settings', label: 'Settings', icon: <Settings className="w-5 h-5" /> }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                activeTab === tab.id 
                  ? 'bg-blue-500 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'dashboard' && (
              <DashboardView 
                systemStatus={systemStatus} 
                formatUptime={formatUptime}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            )}
            
            {activeTab === 'services' && (
              <ServicesView 
                systemStatus={systemStatus}
                startService={startService}
                stopService={stopService}
                isLoading={isLoading}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            )}
            
            {activeTab === 'database' && (
              <DatabaseView 
                initializeDatabase={initializeDatabase}
                syncResources={syncResources}
                backupDatabase={backupDatabase}
                isLoading={isLoading}
              />
            )}
            
            {activeTab === 'logs' && <LogsView logs={logs} />}
            
            {activeTab === 'monitoring' && <MonitoringView />}
            
            {activeTab === 'settings' && <SettingsView />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

// Dashboard Component
function DashboardView({ systemStatus, formatUptime, getStatusColor, getStatusIcon }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">System Dashboard</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          Uptime: {formatUptime(systemStatus.uptime)}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="API Server"
          status={systemStatus.api}
          icon={<Server className="w-6 h-6" />}
          color={getStatusColor(systemStatus.api)}
          statusIcon={getStatusIcon(systemStatus.api)}
        />
        <StatusCard
          title="Telegram Bot"
          status={systemStatus.bot}
          icon={<Globe className="w-6 h-6" />}
          color={getStatusColor(systemStatus.bot)}
          statusIcon={getStatusIcon(systemStatus.bot)}
        />
        <StatusCard
          title="Database"
          status="running"
          icon={<Database className="w-6 h-6" />}
          color="text-green-400"
          statusIcon={<Play className="w-4 h-4" />}
        />
        <StatusCard
          title="System Health"
          status="operational"
          icon={<Shield className="w-6 h-6" />}
          color="text-green-400"
          statusIcon={<Check className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            System Performance
          </h3>
          <div className="space-y-4">
            <MetricBar label="CPU Usage" value={45} color="blue" />
            <MetricBar label="Memory" value={62} color="green" />
            <MetricBar label="Disk I/O" value={23} color="yellow" />
            <MetricBar label="Network" value={78} color="purple" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-green-400" />
            User Activity
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Active Users</span>
              <span className="text-2xl font-bold">127</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">API Requests</span>
              <span className="text-2xl font-bold">1,842</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Bot Messages</span>
              <span className="text-2xl font-bold">3,291</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Resource Downloads</span>
              <span className="text-2xl font-bold">847</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Services Component
function ServicesView({ systemStatus, startService, stopService, isLoading, getStatusColor, getStatusIcon }) {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Service Management</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ServiceCard
          title="API Server"
          description="FastAPI backend server for all API endpoints"
          status={systemStatus.api}
          port={8000}
          onStart={() => startService('api')}
          isLoading={isLoading}
          getStatusColor={getStatusColor}
          getStatusIcon={getStatusIcon}
        />
        
        <ServiceCard
          title="Telegram Bot"
          description="Telegram bot for student interactions"
          status={systemStatus.bot}
          port={null}
          onStart={() => startService('bot')}
          isLoading={isLoading}
          getStatusColor={getStatusColor}
          getStatusIcon={getStatusIcon}
        />
      </div>

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Power className="w-5 h-5 text-red-400" />
          System Control
        </h3>
        <div className="flex gap-4">
          <button
            onClick={stopService}
            disabled={isLoading}
            className="px-6 py-3 bg-red-500 hover:bg-red-600 disabled:bg-gray-600 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <Square className="w-4 h-4" />
            Stop All Services
          </button>
        </div>
      </div>
    </div>
  );
}

// Database Component
function DatabaseView({ initializeDatabase, syncResources, backupDatabase, isLoading }) {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Database Management</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ActionCard
          title="Initialize Database"
          description="Create and setup database schema"
          icon={<Database className="w-8 h-8" />}
          action={initializeDatabase}
          isLoading={isLoading}
          color="blue"
        />
        
        <ActionCard
          title="Sync Resources"
          description="Synchronize file system with database"
          icon={<RefreshCw className="w-8 h-8" />}
          action={syncResources}
          isLoading={isLoading}
          color="green"
        />
        
        <ActionCard
          title="Backup Database"
          description="Create database backup"
          icon={<Download className="w-8 h-8" />}
          action={backupDatabase}
          isLoading={isLoading}
          color="purple"
        />
      </div>

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <HardDrive className="w-5 h-5 text-yellow-400" />
          Database Information
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Database Type</p>
            <p className="text-xl font-semibold">SQLite</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Size</p>
            <p className="text-xl font-semibold">24.7 MB</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Last Backup</p>
            <p className="text-xl font-semibold">2 hours ago</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Total Records</p>
            <p className="text-xl font-semibold">1,847</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Logs Component
function LogsView({ logs }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">System Logs</h2>
        <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
          Clear Logs
        </button>
      </div>
      
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div className="bg-gray-900 px-4 py-2 border-b border-gray-700">
          <span className="text-sm font-mono text-gray-400">Real-time System Output</span>
        </div>
        <div className="h-96 overflow-y-auto p-4 font-mono text-sm space-y-1">
          {logs.length === 0 ? (
            <div className="text-gray-500 text-center py-8">No logs available</div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex gap-2 text-gray-300">
                <span className="text-gray-500">
                  {log.timestamp.toLocaleTimeString()}
                </span>
                <span className="flex-1">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// Monitoring Component
function MonitoringView() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">System Monitoring</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-400" />
            Resource Usage
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">CPU</span>
                <span className="text-sm">45%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '45%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">Memory</span>
                <span className="text-sm">62%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '62%' }}></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Wifi className="w-5 h-5 text-green-400" />
            Network Status
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Upload Speed</span>
              <span className="font-semibold">12.4 Mbps</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Download Speed</span>
              <span className="font-semibold">45.7 Mbps</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Latency</span>
              <span className="font-semibold">23 ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Settings Component
function SettingsView() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Settings</h2>
      
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Application Settings</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Auto-start Services</p>
              <p className="text-sm text-gray-400">Start services automatically on launch</p>
            </div>
            <button className="w-12 h-6 bg-blue-500 rounded-full relative">
              <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5"></div>
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Enable Notifications</p>
              <p className="text-sm text-gray-400">Show system notifications</p>
            </div>
            <button className="w-12 h-6 bg-gray-600 rounded-full relative">
              <div className="w-5 h-5 bg-white rounded-full absolute left-0.5 top-0.5"></div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function StatusCard({ title, status, icon, color, statusIcon }) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-gray-700 rounded-lg">{icon}</div>
        <div className={`flex items-center gap-2 ${color}`}>
          {statusIcon}
          <span className="text-sm font-medium capitalize">{status}</span>
        </div>
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
    </div>
  );
}

function ServiceCard({ title, description, status, port, onStart, isLoading, getStatusColor, getStatusIcon }) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className={`flex items-center gap-2 ${getStatusColor(status)}`}>
          {getStatusIcon(status)}
          <span className="text-sm font-medium capitalize">{status}</span>
        </div>
      </div>
      <p className="text-gray-400 mb-4">{description}</p>
      {port && <p className="text-sm text-gray-500 mb-4">Port: {port}</p>}
      <button
        onClick={onStart}
        disabled={isLoading || status === 'running'}
        className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
      >
        <Play className="w-4 h-4" />
        {status === 'running' ? 'Running' : 'Start Service'}
      </button>
    </div>
  );
}

function ActionCard({ title, description, icon, action, isLoading, color }) {
  const colorClasses = {
    blue: 'bg-blue-500 hover:bg-blue-600',
    green: 'bg-green-500 hover:bg-green-600',
    purple: 'bg-purple-500 hover:bg-purple-600'
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className={`w-16 h-16 rounded-xl flex items-center justify-center mb-4 bg-gray-700`}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 mb-4">{description}</p>
      <button
        onClick={action}
        disabled={isLoading}
        className={`w-full px-4 py-2 ${colorClasses[color]} disabled:bg-gray-600 rounded-lg font-medium transition-colors`}
      >
        {isLoading ? 'Processing...' : 'Execute'}
      </button>
    </div>
  );
}

function MetricBar({ label, value, color }) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    purple: 'bg-purple-500'
  };

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-sm font-medium">{value}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div 
          className={`${colorClasses[color]} h-2 rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        ></div>
      </div>
    </div>
  );
}

export default App;
