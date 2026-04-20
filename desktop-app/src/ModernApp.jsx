import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Monitor, Server, Database, Users, Activity, Shield, Settings,
  Power, RefreshCw, Square, Play, Download, Upload,
  Zap, TrendingUp, AlertTriangle, CheckCircle, XCircle,
  Clock, HardDrive, Wifi, Cpu, MemoryStick, Globe,
  Search, Menu, X, ChevronRight, ChevronDown, Filter,
  BarChart3, PieChart, Activity as ActivityIcon, Eye,
  Heart, Share2, MoreVertical, Bell, User, LogOut,
  Home, Layers, Package, FileText, Link
} from 'lucide-react';
import './ModernApp.css';

const ModernApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [systemStatus, setSystemStatus] = useState({
    api: 'running',
    bot: 'running', 
    database: 'healthy',
    uptime: '48h 32m'
  });
  const [metrics, setMetrics] = useState({
    cpu: 45,
    memory: 62,
    disk: 23,
    network: 78,
    activeUsers: 127
  });
  const [alerts, setAlerts] = useState([
    { id: 1, severity: 'high', message: 'Database connection pool optimized', time: '2 min ago', resolved: true },
    { id: 2, severity: 'medium', message: 'High API traffic detected', time: '15 min ago', resolved: false },
    { id: 3, severity: 'low', message: 'Scheduled maintenance completed', time: '1 hour ago', resolved: true }
  ]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'services', label: 'Services', icon: Server },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  const serviceActions = {
    api: { 
      status: systemStatus.api,
      color: systemStatus.api === 'running' ? 'green' : 'red',
      icon: systemStatus.api === 'running' ? Play : Square,
      label: systemStatus.api === 'running' ? 'Running' : 'Stopped'
    },
    bot: { 
      status: systemStatus.bot,
      color: systemStatus.bot === 'running' ? 'green' : 'red',
      icon: systemStatus.bot === 'running' ? Play : Square,
      label: systemStatus.bot === 'running' ? 'Running' : 'Stopped'
    }
  };

  const handleServiceAction = (service, action) => {
    // Handle service start/stop/restart
    console.log(`${action} ${service} service`);
    setSystemStatus(prev => ({
      ...prev,
      [service]: action === 'start' ? 'running' : 'stopped'
    }));
  };

  const handleAlertResolve = (alertId) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, resolved: true } : alert
    ));
  };

  const Sidebar = () => (
    <motion.div 
      className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}
      initial={{ width: 280 }}
      animate={{ width: sidebarCollapsed ? 80 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      <div className="sidebar-header">
        <div className="logo">
          <Monitor className="logo-icon" />
          <span className={`logo-text ${sidebarCollapsed ? 'hidden' : ''}`}>
            Orbit Control
          </span>
        </div>
        <button 
          className="collapse-btn"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          <Menu className="collapse-icon" />
        </button>
      </div>

      <nav className="sidebar-nav">
        {tabs.map(tab => (
          <motion.button
            key={tab.id}
            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <tab.icon className="nav-icon" />
            {!sidebarCollapsed && <span className="nav-label">{tab.label}</span>}
          </motion.button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            <User />
          </div>
          {!sidebarCollapsed && (
            <div className="user-info">
              <div className="user-name">System Admin</div>
              <div className="user-role">Super Admin</div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );

  const Dashboard = () => (
    <div className="dashboard">
      <motion.div 
        className="dashboard-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="page-title">System Dashboard</h1>
        <div className="dashboard-subtitle">Real-time system monitoring and control</div>
      </motion.div>

      <div className="metrics-grid">
        <motion.div 
          className="metric-card cpu"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <div className="metric-header">
            <Cpu className="metric-icon cpu" />
            <span className="metric-label">CPU Usage</span>
          </div>
          <div className="metric-value">
            <span className="value">{metrics.cpu}%</span>
            <div className="progress-bar">
              <div className="progress-fill cpu" style={{ width: `${metrics.cpu}%` }}></div>
            </div>
          </div>
        </motion.div>

        <motion.div 
          className="metric-card memory"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="metric-header">
            <MemoryStick className="metric-icon memory" />
            <span className="metric-label">Memory</span>
          </div>
          <div className="metric-value">
            <span className="value">{metrics.memory}%</span>
            <div className="progress-bar">
              <div className="progress-fill memory" style={{ width: `${metrics.memory}%` }}></div>
            </div>
          </div>
        </motion.div>

        <motion.div 
          className="metric-card disk"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="metric-header">
            <HardDrive className="metric-icon disk" />
            <span className="metric-label">Disk Usage</span>
          </div>
          <div className="metric-value">
            <span className="value">{metrics.disk}%</span>
            <div className="progress-bar">
              <div className="progress-fill disk" style={{ width: `${metrics.disk}%` }}></div>
            </div>
          </div>
        </motion.div>

        <motion.div 
          className="metric-card network"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <div className="metric-header">
            <Wifi className="metric-icon network" />
            <span className="metric-label">Network</span>
          </div>
          <div className="metric-value">
            <span className="value">{metrics.network}%</span>
            <div className="progress-bar">
              <div className="progress-fill network" style={{ width: `${metrics.network}%` }}></div>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="dashboard-grid">
        <motion.div 
          className="card services-card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="card-header">
            <h3>Services Status</h3>
            <Shield className="card-icon" />
          </div>
          <div className="services-grid">
            {Object.entries(serviceActions).map(([service, action]) => (
              <div key={service} className={`service-item ${action.color}`}>
                <div className="service-info">
                  <action.icon className="service-icon" />
                  <div>
                    <div className="service-name">{service.toUpperCase()}</div>
                    <div className="service-status">{action.label}</div>
                  </div>
                </div>
                <div className="service-controls">
                  <button 
                    className={`control-btn ${action.status === 'running' ? 'stop' : 'start'}`}
                    onClick={() => handleServiceAction(service, action.status === 'running' ? 'stop' : 'start')}
                  >
                    {action.status === 'running' ? <Square /> : <Play />}
                  </button>
                  <button className="control-btn restart">
                    <RefreshCw />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div 
          className="card alerts-card"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <div className="card-header">
            <h3>System Alerts</h3>
            <Bell className="card-icon" />
          </div>
          <div className="alerts-list">
            <AnimatePresence>
              {alerts.map(alert => (
                <motion.div
                  key={alert.id}
                  className={`alert-item ${alert.severity} ${alert.resolved ? 'resolved' : ''}`}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="alert-content">
                    <div className="alert-header">
                      {alert.severity === 'high' && <AlertTriangle className="alert-icon high" />}
                      {alert.severity === 'medium' && <AlertTriangle className="alert-icon medium" />}
                      {alert.severity === 'low' && <CheckCircle className="alert-icon low" />}
                      <div className="alert-info">
                        <div className="alert-message">{alert.message}</div>
                        <div className="alert-time">{alert.time}</div>
                      </div>
                    </div>
                    <div className="alert-actions">
                      {!alert.resolved && (
                        <button 
                          className="resolve-btn"
                          onClick={() => handleAlertResolve(alert.id)}
                        >
                          <CheckCircle />
                          Resolve
                        </button>
                      )}
                      {alert.resolved && (
                        <span className="resolved-badge">Resolved</span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        <motion.div 
          className="card activity-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <div className="card-header">
            <h3>Recent Activity</h3>
            <ActivityIcon className="card-icon" />
          </div>
          <div className="activity-list">
            {[
              { icon: Download, text: 'API server started', time: '2 min ago', type: 'success' },
              { icon: Users, text: '127 active users', time: '5 min ago', type: 'info' },
              { icon: Database, text: 'Database optimized', time: '15 min ago', type: 'success' },
              { icon: Upload, text: 'Resource uploaded', time: '1 hour ago', type: 'info' }
            ].map((activity, index) => (
              <motion.div
                key={index}
                className="activity-item"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
              >
                <div className={`activity-icon ${activity.type}`}>
                  <activity.icon />
                </div>
                <div className="activity-content">
                  <div className="activity-text">{activity.text}</div>
                  <div className="activity-time">{activity.time}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );

  const Services = () => (
    <div className="services">
      <motion.div 
        className="page-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="page-title">Service Management</h1>
        <div className="page-subtitle">Start, stop and monitor all system services</div>
      </motion.div>

      <div className="services-container">
        <motion.div 
          className="service-control-panel"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="service-header">
            <Server className="service-large-icon api" />
            <div className="service-details">
              <h2>API Server</h2>
              <p className="service-description">FastAPI backend server handling all API requests</p>
              <div className="service-status-large running">
                <div className="status-indicator"></div>
                <span>Running on port 8000</span>
              </div>
            </div>
          </div>
          <div className="service-actions">
            <button className="action-btn primary">
              <Power />
              Stop Service
            </button>
            <button className="action-btn secondary">
              <RefreshCw />
              Restart
            </button>
            <button className="action-btn tertiary">
              <Settings />
              Configure
            </button>
          </div>
        </motion.div>

        <motion.div 
          className="service-control-panel"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="service-header">
            <Globe className="service-large-icon bot" />
            <div className="service-details">
              <h2>Telegram Bot</h2>
              <p className="service-description">Student interaction bot with enhanced UX features</p>
              <div className="service-status-large running">
                <div className="status-indicator"></div>
                <span>Connected and active</span>
              </div>
            </div>
          </div>
          <div className="service-actions">
            <button className="action-btn primary">
              <Power />
              Stop Bot
            </button>
            <button className="action-btn secondary">
              <RefreshCw />
              Restart
            </button>
            <button className="action-btn tertiary">
              <Users />
              User Stats
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'services':
        return <Services />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="modern-app">
      <Sidebar />
      <div className={`main-content ${sidebarCollapsed ? 'expanded' : ''}`}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            className="content-wrapper"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ModernApp;
