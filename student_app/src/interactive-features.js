// Interactive JavaScript Features for Student App
// Modern, industry-standard functionality with psychological UX principles

class StudentAppFeatures {
  constructor() {
    this.isInitialized = false;
    this.userPreferences = this.loadUserPreferences();
    this.theme = this.userPreferences.theme || 'dark';
    this.animationsEnabled = this.userPreferences.animations !== false;
    this.hapticFeedback = this.userPreferences.haptic !== false;
  }

  // Initialize all interactive features
  init() {
    if (this.isInitialized) return;
    
    console.log('🚀 Initializing Student App Features...');
    
    this.setupTheme();
    this.setupMicroInteractions();
    this.setupKeyboardNavigation();
    this.setupGestures();
    this.setupNotifications();
    this.setupPerformanceOptimizations();
    
    this.isInitialized = true;
    console.log('✅ Student App Features Initialized');
  }

  // Theme Management
  setupTheme() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('student-app-theme') || (prefersDark ? 'dark' : 'light');
    
    this.applyTheme(savedTheme);
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('student-app-theme')) {
        this.applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('student-app-theme', theme);
    this.theme = theme;
    
    // Update meta theme color
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
      metaTheme.content = theme === 'dark' ? '#0a0a0f' : '#ffffff';
    }
  }

  // Micro-interactions for better UX
  setupMicroInteractions() {
    if (!this.animationsEnabled) return;

    // Button ripple effects
    document.addEventListener('click', (e) => {
      if (e.target.closest('.btn')) {
        this.createRipple(e.target.closest('.btn'), e);
      }
    });

    // Card hover effects
    document.addEventListener('mouseover', (e) => {
      if (e.target.closest('.card')) {
        this.addHoverEffect(e.target.closest('.card'));
      }
    });

    // Smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  // Create ripple effect on buttons
  createRipple(button, event) {
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    
    button.appendChild(ripple);
    
    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  // Add hover effect to cards
  addHoverEffect(card) {
    card.style.transform = 'translateY(-2px)';
    card.style.transition = 'transform 0.2s ease-out';
  }

  // Keyboard navigation
  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Focus trap for modals
      if (e.key === 'Escape') {
        this.closeModals();
      }
      
      // Arrow key navigation
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        this.handleArrowNavigation(e);
      }
      
      // Search shortcuts
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        this.focusSearch();
      }
    });
  }

  // Handle arrow key navigation
  handleArrowNavigation(e) {
    const focusableElements = document.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const currentIndex = Array.from(focusableElements).indexOf(document.activeElement);
    let nextIndex;
    
    if (e.key === 'ArrowDown') {
      nextIndex = (currentIndex + 1) % focusableElements.length;
    } else if (e.key === 'ArrowUp') {
      nextIndex = currentIndex - 1 < 0 ? focusableElements.length - 1 : currentIndex - 1;
    }
    
    if (nextIndex !== undefined) {
      focusableElements[nextIndex].focus();
      e.preventDefault();
    }
  }

  // Focus search input
  focusSearch() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }

  // Touch gestures for mobile
  setupGestures() {
    let touchStartX = 0;
    let touchStartY = 0;
    
    document.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      const deltaX = touchEndX - touchStartX;
      const deltaY = touchEndY - touchStartY;
      
      // Swipe gestures
      if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY)) {
        if (deltaX > 0) {
          this.handleSwipeRight();
        } else {
          this.handleSwipeLeft();
        }
      }
    });
  }

  // Handle swipe gestures
  handleSwipeRight() {
    // Navigate forward or open menu
    const mobileMenu = document.querySelector('.mobile-menu');
    if (mobileMenu && mobileMenu.classList.contains('open')) {
      // Next menu item
    }
  }

  handleSwipeLeft() {
    // Navigate back or close menu
    const mobileMenu = document.querySelector('.mobile-menu');
    if (mobileMenu && mobileMenu.classList.contains('open')) {
      mobileMenu.classList.remove('open');
    }
  }

  // Notification system
  setupNotifications() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
    
    // Listen for online/offline status
    window.addEventListener('online', () => {
      this.showNotification('Back Online', 'You are now connected to the internet', 'success');
    });
    
    window.addEventListener('offline', () => {
      this.showNotification('Offline', 'You are currently offline', 'warning');
    });
  }

  // Show notification
  showNotification(title, message, type = 'info') {
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: '/favicon.ico',
        tag: 'student-app'
      });
    }
    
    // In-app notification
    this.showInAppNotification(title, message, type);
  }

  // Show in-app notification
  showInAppNotification(title, message, type) {
    const notification = document.createElement('div');
    notification.className = `in-app-notification ${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <h4>${title}</h4>
        <p>${message}</p>
      </div>
      <button class="notification-close" aria-label="Close notification">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => notification.remove(), 300);
    }, 5000);
    
    // Close button
    notification.querySelector('.notification-close').addEventListener('click', () => {
      notification.remove();
    });
  }

  // Performance optimizations
  setupPerformanceOptimizations() {
    // Lazy loading for images
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            imageObserver.unobserve(img);
          }
        });
      });
      
      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
    
    // Preload critical resources
    this.preloadCriticalResources();
    
    // Setup service worker for offline support
    this.setupServiceWorker();
  }

  // Preload critical resources
  preloadCriticalResources() {
    const criticalResources = [
      '/api/v1/public/institutions',
      '/api/v1/public/categories'
    ];
    
    criticalResources.forEach(resource => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = resource;
      document.head.appendChild(link);
    });
  }

  // Setup service worker
  setupServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('Service Worker registered');
        })
        .catch(error => {
          console.log('Service Worker registration failed:', error);
        });
    }
  }

  // Close all modals
  closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
      modal.classList.remove('active');
    });
  }

  // Load user preferences
  loadUserPreferences() {
    const saved = localStorage.getItem('student-app-preferences');
    return saved ? JSON.parse(saved) : {};
  }

  // Save user preferences
  saveUserPreferences(preferences) {
    localStorage.setItem('student-app-preferences', JSON.stringify(preferences));
    this.userPreferences = { ...this.userPreferences, ...preferences };
  }

  // Haptic feedback (for supported devices)
  triggerHaptic(type = 'light') {
    if (!this.hapticFeedback) return;
    
    if ('vibrate' in navigator) {
      switch (type) {
        case 'light':
          navigator.vibrate(10);
          break;
        case 'medium':
          navigator.vibrate(25);
          break;
        case 'heavy':
          navigator.vibrate(50);
          break;
        case 'success':
          navigator.vibrate([10, 50, 10]);
          break;
        case 'error':
          navigator.vibrate([100, 50, 100]);
          break;
      }
    }
    
    // Telegram Web App haptic feedback
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred(type);
    }
  }

  // Analytics and user behavior tracking
  trackEvent(eventName, properties = {}) {
    // Only track in production
    if (window.location.hostname === 'localhost') return;
    
    const event = {
      name: eventName,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        sessionId: this.getSessionId()
      }
    };
    
    // Send to analytics service
    this.sendAnalytics(event);
  }

  // Get session ID
  getSessionId() {
    let sessionId = sessionStorage.getItem('student-app-session');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('student-app-session', sessionId);
    }
    return sessionId;
  }

  // Send analytics data
  sendAnalytics(event) {
    // This would integrate with your analytics service
    console.log('Analytics Event:', event);
    
    // Example: Send to your backend
    fetch('/api/v1/analytics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(event)
    }).catch(error => {
      console.log('Analytics tracking failed:', error);
    });
  }

  // Accessibility features
  setupAccessibility() {
    // Announce page changes to screen readers
    this.setupScreenReaderAnnouncements();
    
    // Focus management
    this.setupFocusManagement();
    
    // High contrast mode
    this.setupHighContrast();
  }

  // Setup screen reader announcements
  setupScreenReaderAnnouncements() {
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
    
    this.announcer = announcer;
  }

  // Announce to screen reader
  announceToScreenReader(message) {
    if (this.announcer) {
      this.announcer.textContent = message;
      setTimeout(() => {
        this.announcer.textContent = '';
      }, 1000);
    }
  }

  // Setup focus management
  setupFocusManagement() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
      }
    });
    
    document.addEventListener('mousedown', () => {
      document.body.classList.remove('keyboard-navigation');
    });
  }

  // Setup high contrast mode
  setupHighContrast() {
    const highContrastToggle = localStorage.getItem('high-contrast') === 'true';
    if (highContrastToggle) {
      document.documentElement.classList.add('high-contrast');
    }
  }

  // Progressive enhancement
  setupProgressiveEnhancement() {
    // Check for modern features
    const features = {
      intersectionObserver: 'IntersectionObserver' in window,
      resizeObserver: 'ResizeObserver' in window,
      webp: this.supportsWebP(),
      serviceWorker: 'serviceWorker' in navigator,
      notifications: 'Notification' in window,
      vibration: 'vibrate' in navigator
    };
    
    // Add feature classes to body for CSS targeting
    Object.entries(features).forEach(([feature, supported]) => {
      document.body.classList.toggle(`supports-${feature}`, supported);
    });
    
    return features;
  }

  // Check WebP support
  supportsWebP() {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }
}

// CSS for ripple effects and other micro-interactions
const style = document.createElement('style');
style.textContent = `
  .ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s ease-out;
    pointer-events: none;
  }
  
  @keyframes ripple-animation {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
  
  .in-app-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--orbit-surface);
    border: 1px solid var(--orbit-border);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
    box-shadow: var(--shadow-xl);
    z-index: 1000;
    max-width: 300px;
    animation: slide-in-right 0.3s ease-out;
  }
  
  .in-app-notification.success {
    border-left: 4px solid var(--orbit-success);
  }
  
  .in-app-notification.warning {
    border-left: 4px solid var(--orbit-warning);
  }
  
  .in-app-notification.error {
    border-left: 4px solid var(--orbit-error);
  }
  
  .in-app-notification.fade-out {
    animation: fade-out 0.3s ease-out forwards;
  }
  
  .notification-close {
    position: absolute;
    top: var(--space-sm);
    right: var(--space-sm);
    background: none;
    border: none;
    color: var(--orbit-fg-secondary);
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-full);
    transition: all var(--transition-fast);
  }
  
  .notification-close:hover {
    background: var(--orbit-error);
    color: white;
  }
  
  @keyframes slide-in-right {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes fade-out {
    from {
      opacity: 1;
      transform: translateX(0);
    }
    to {
      opacity: 0;
      transform: translateX(100%);
    }
  }
  
  .keyboard-navigation *:focus {
    outline: 2px solid var(--orbit-primary);
    outline-offset: 2px;
  }
  
  .high-contrast {
    --orbit-bg: #000000;
    --orbit-surface: #1a1a1a;
    --orbit-border: #ffffff;
    --orbit-fg: #ffffff;
    --orbit-text: #ffffff;
  }
  
  .lazy {
    filter: blur(5px);
    transition: filter 0.3s;
  }
  
  .lazy.loaded {
    filter: blur(0);
  }
  
  .supports-service-worker .offline-banner {
    display: block;
  }
  
  .supports-notifications .notification-badge {
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
  }
`;

document.head.appendChild(style);

// Initialize the features
const studentApp = new StudentAppFeatures();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => studentApp.init());
} else {
  studentApp.init();
}

// Export for use in other modules
window.StudentAppFeatures = StudentAppFeatures;
window.studentApp = studentApp;
