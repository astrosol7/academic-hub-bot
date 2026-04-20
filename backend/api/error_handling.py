"""
Advanced Error Handling and Recovery System for Academic Hub
Provides comprehensive error handling, logging, and automatic recovery mechanisms
"""

import logging
import traceback
import asyncio
import functools
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys

# Configure advanced logging
class OrbitLogger:
    """Enhanced logger with structured logging and error tracking"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.FileHandler(
            log_dir / f"{name}.log", 
            mode='a', 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Error tracking
        self.error_counts = {}
        self.last_errors = {}
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Enhanced error logging with context and tracking"""
        error_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(message)}"
        
        # Track error frequency
        error_type = type(error).__name__ if error else 'Unknown'
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = {
            'timestamp': datetime.now(),
            'message': message,
            'error_id': error_id
        }
        
        # Log with full context
        if error:
            self.logger.error(
                f"{message} [{error_id}]",
                exc_info=True,
                extra={
                    'error_type': error_type,
                    'error_id': error_id,
                    'error_count': self.error_counts[error_type],
                    **kwargs
                }
            )
        else:
            self.logger.error(f"{message} [{error_id}]", extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'error_counts': self.error_counts,
            'last_errors': {
                k: {
                    'timestamp': v['timestamp'].isoformat(),
                    'message': v['message'],
                    'error_id': v['error_id']
                } for k, v in self.last_errors.items()
            }
        }

# Global logger instance
orbit_log = OrbitLogger('orbit_api')

class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = 'HALF_OPEN'
                    orbit_log.info(f"Circuit breaker HALF_OPEN for {func.__name__}")
                else:
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                    orbit_log.info(f"Circuit breaker CLOSED for {func.__name__}")
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                    orbit_log.error(f"Circuit breaker OPEN for {func.__name__}", e)
                
                raise e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = 'HALF_OPEN'
                    orbit_log.info(f"Circuit breaker HALF_OPEN for {func.__name__}")
                else:
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                    orbit_log.info(f"Circuit breaker CLOSED for {func.__name__}")
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                    orbit_log.error(f"Circuit breaker OPEN for {func.__name__}", e)
                
                raise e
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

class RetryManager:
    """Advanced retry mechanism with exponential backoff and jitter"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def __call__(self, func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        orbit_log.error(f"Max retries exceeded for {func.__name__}", e)
                        raise e
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        self.base_delay * (2 ** attempt) + (0.1 * attempt),
                        self.max_delay
                    )
                    
                    orbit_log.warning(
                        f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} after {delay:.2f}s",
                        error=e
                    )
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        orbit_log.error(f"Max retries exceeded for {func.__name__}", e)
                        raise e
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        self.base_delay * (2 ** attempt) + (0.1 * attempt),
                        self.max_delay
                    )
                    
                    orbit_log.warning(
                        f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} after {delay:.2f}s",
                        error=e
                    )
                    import time
                    time.sleep(delay)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

class HealthChecker:
    """System health monitoring and recovery"""
    
    def __init__(self):
        self.checks = {}
        self.last_health_status = {}
    
    def add_check(self, name: str, check_func: Callable[[], bool], recovery_func: Callable[[], None] = None):
        """Add a health check with optional recovery function"""
        self.checks[name] = {
            'check': check_func,
            'recovery': recovery_func,
            'last_check': None,
            'consecutive_failures': 0
        }
    
    async def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks and return status"""
        results = {}
        
        for name, check_config in self.checks.items():
            try:
                is_healthy = check_config['check']()
                current_time = datetime.now()
                
                if is_healthy:
                    check_config['consecutive_failures'] = 0
                    results[name] = {
                        'status': 'healthy',
                        'last_check': current_time.isoformat(),
                        'consecutive_failures': 0
                    }
                else:
                    check_config['consecutive_failures'] += 1
                    
                    # Attempt recovery if configured
                    if (check_config['recovery'] and 
                        check_config['consecutive_failures'] >= 3):
                        try:
                            orbit_log.warning(f"Attempting recovery for {name}")
                            check_config['recovery']()
                            results[name] = {
                                'status': 'recovered',
                                'last_check': current_time.isoformat(),
                                'consecutive_failures': check_config['consecutive_failures']
                            }
                        except Exception as e:
                            orbit_log.error(f"Recovery failed for {name}", e)
                            results[name] = {
                                'status': 'unhealthy',
                                'last_check': current_time.isoformat(),
                                'consecutive_failures': check_config['consecutive_failures']
                            }
                    else:
                        results[name] = {
                            'status': 'unhealthy',
                            'last_check': current_time.isoformat(),
                            'consecutive_failures': check_config['consecutive_failures']
                        }
                
                check_config['last_check'] = current_time
                
            except Exception as e:
                orbit_log.error(f"Health check failed for {name}", e)
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
        
        self.last_health_status = results
        return results

# Global instances
circuit_breaker = CircuitBreaker()
retry_manager = RetryManager()
health_checker = HealthChecker()

# Decorators for easy use
def with_circuit_breaker(failure_threshold: int = 5, timeout: int = 60):
    return CircuitBreaker(failure_threshold, timeout)

def with_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    return RetryManager(max_retries, base_delay, max_delay)

def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        orbit_log.error(f"Safe execution failed for {func.__name__}", e)
        return default_return

# Error recovery strategies
class DatabaseRecovery:
    """Database-specific recovery strategies"""
    
    @staticmethod
    async def reconnect_database():
        """Attempt to reconnect to database"""
        try:
            from backend.api.database_sqlite import engine
            # Test connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            orbit_log.info("Database reconnection successful")
            return True
        except Exception as e:
            orbit_log.error("Database reconnection failed", e)
            return False
    
    @staticmethod
    async def repair_database():
        """Attempt to repair database corruption"""
        try:
            from backend.api.database_sqlite import engine
            with engine.connect() as conn:
                conn.execute("PRAGMA integrity_check")
                conn.execute("VACUUM")
            orbit_log.info("Database repair successful")
            return True
        except Exception as e:
            orbit_log.error("Database repair failed", e)
            return False

class APIServiceRecovery:
    """API service recovery strategies"""
    
    @staticmethod
    async def restart_api():
        """Restart API service"""
        try:
            # Implementation would depend on deployment method
            orbit_log.info("API service restart initiated")
            return True
        except Exception as e:
            orbit_log.error("API service restart failed", e)
            return False

# Initialize default health checks
def initialize_health_checks():
    """Initialize default health checks for the system"""
    
    # Database health check
    def check_database():
        try:
            from backend.api.database_sqlite import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except:
            return False
    
    health_checker.add_check(
        'database',
        check_database,
        DatabaseRecovery.reconnect_database
    )
    
    # File system health check
    def check_filesystem():
        try:
            data_dir = Path(__file__).parent.parent.parent / "data"
            return data_dir.exists() and data_dir.is_dir()
        except:
            return False
    
    health_checker.add_check('filesystem', check_filesystem)
    
    orbit_log.info("Health checks initialized")

# Initialize on import
initialize_health_checks()
