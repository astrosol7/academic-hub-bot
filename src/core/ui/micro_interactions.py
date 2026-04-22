"""
Micro-interactions System for Academic Hub
Industry-standard animations, haptic feedback, and interactive elements
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

log = logging.getLogger(__name__)

class AnimationType(str, Enum):
    """Types of micro-interactions"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    LOADING = "loading"
    HAPTIC_LIGHT = "haptic_light"
    HAPTIC_MEDIUM = "haptic_medium"
    HAPTIC_HEAVY = "haptic_heavy"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    BOUNCE = "bounce"
    PULSE = "pulse"
    SHAKE = "shake"
    ROTATE = "rotate"

class MicroInteraction:
    """Micro-interaction manager with industry-standard feedback"""
    
    def __init__(self):
        self.animation_queue = []
        self.current_animations = {}
        self.haptic_queue = []
        self.sound_queue = []
    
    async def trigger_animation(self, element_id: str, animation_type: AnimationType, 
                           duration_ms: int = 300, properties: Dict[str, Any] = None):
        """Trigger visual animation with haptic feedback"""
        try:
            # Queue animation
            animation_data = {
                'element_id': element_id,
                'type': animation_type.value,
                'duration': duration_ms,
                'properties': properties or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.animation_queue.append(animation_data)
            
            # Trigger haptic feedback
            haptic_type = self.get_haptic_type(animation_type)
            if haptic_type:
                await self.trigger_haptic(haptic_type)
            
            log.info(f"Animation triggered: {animation_type.value} on {element_id}")
            return True
            
        except Exception as e:
            log.error(f"Animation trigger failed: {e}")
            return False
    
    async def trigger_haptic(self, haptic_type: str, intensity: float = 1.0):
        """Trigger haptic feedback"""
        try:
            # Queue haptic feedback
            haptic_data = {
                'type': haptic_type,
                'intensity': intensity,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.haptic_queue.append(haptic_data)
            log.info(f"Haptic feedback triggered: {haptic_type} (intensity: {intensity})")
            return True
            
        except Exception as e:
            log.error(f"Haptic trigger failed: {e}")
            return False
    
    async def play_sound(self, sound_type: str, volume: float = 0.5):
        """Play sound effect"""
        try:
            sound_data = {
                'type': sound_type,
                'volume': volume,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.sound_queue.append(sound_data)
            log.info(f"Sound played: {sound_type} (volume: {volume})")
            return True
            
        except Exception as e:
            log.error(f"Sound play failed: {e}")
            return False
    
    def get_haptic_type(self, animation_type: AnimationType) -> Optional[str]:
        """Map animation types to haptic feedback"""
        haptic_mapping = {
            AnimationType.SUCCESS: AnimationType.HAPTIC_LIGHT,
            AnimationType.WARNING: AnimationType.HAPTIC_MEDIUM,
            AnimationType.ERROR: AnimationType.HAPTIC_HEAVY,
            AnimationType.LOADING: AnimationType.HAPTIC_LIGHT,
        }
        return haptic_mapping.get(animation_type)
    
    def create_loading_animation(self, element_id: str, steps: List[str]) -> Dict[str, Any]:
        """Create multi-step loading animation"""
        return {
            'element_id': element_id,
            'animation_type': AnimationType.LOADING.value,
            'steps': steps,
            'current_step': 0,
            'duration_per_step': 500,
            'properties': {
                'loop': True,
                'easing': 'ease-in-out'
            }
        }
    
    def create_success_animation(self, element_id: str, message: str) -> Dict[str, Any]:
        """Create success feedback animation"""
        return {
            'element_id': element_id,
            'animation_type': AnimationType.SUCCESS.value,
            'message': message,
            'properties': {
                'color': '#10b981',
                'scale': 1.1,
                'duration': 800
            }
        }
    
    def create_error_animation(self, element_id: str, error_message: str) -> Dict[str, Any]:
        """Create error feedback animation"""
        return {
            'element_id': element_id,
            'animation_type': AnimationType.ERROR.value,
            'error_message': error_message,
            'properties': {
                'color': '#ef4444',
                'shake_intensity': 0.5,
                'duration': 600
            }
        }
    
    def get_animation_queue(self) -> List[Dict[str, Any]]:
        """Get all queued animations"""
        return self.animation_queue.copy()
    
    def get_haptic_queue(self) -> List[Dict[str, Any]]:
        """Get all queued haptic feedback"""
        return self.haptic_queue.copy()
    
    def get_sound_queue(self) -> List[Dict[str, Any]]:
        """Get all queued sounds"""
        return self.sound_queue.copy()
    
    def clear_queues(self):
        """Clear all interaction queues"""
        self.animation_queue.clear()
        self.haptic_queue.clear()
        self.sound_queue.clear()
        log.info("Interaction queues cleared")

class InteractionRenderer:
    """Renders micro-interactions with industry-standard animations"""
    
    def __init__(self):
        self.active_animations = {}
        self.animation_handlers = {
            AnimationType.SLIDE_UP: self._render_slide_animation,
            AnimationType.SLIDE_DOWN: self._render_slide_animation,
            AnimationType.SLIDE_LEFT: self._render_slide_animation,
            AnimationType.SLIDE_RIGHT: self._render_slide_animation,
            AnimationType.FADE_IN: self._render_fade_animation,
            AnimationType.FADE_OUT: self._render_fade_animation,
            AnimationType.BOUNCE: self._render_bounce_animation,
            AnimationType.PULSE: self._render_pulse_animation,
            AnimationType.SHAKE: self._render_shake_animation,
            AnimationType.ROTATE: self._render_rotate_animation
        }
    
    async def render_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render animation based on type and properties"""
        try:
            animation_type = AnimationType(animation_data['animation_type'])
            handler = self.animation_handlers.get(animation_type)
            
            if handler:
                self.active_animations[animation_data['element_id']] = animation_data
                return await handler(animation_data)
            else:
                log.warning(f"No handler for animation type: {animation_type}")
                return False
                
        except Exception as e:
            log.error(f"Animation render failed: {e}")
            return False
    
    def _render_slide_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render slide animation"""
        try:
            element_id = animation_data['element_id']
            direction = animation_data['properties'].get('direction', 'up')
            duration = animation_data['duration_per_step']
            
            # Create slide animation CSS
            css_animation = f"""
                #{element_id} {{
                    transform: translateX({direction === 'left' ? '-100%' : direction === 'right' ? '100%' : '0'});
                    transition: transform {duration}ms ease-in-out;
                }}
            """
            
            # Apply animation
            await self.apply_css_animation(element_id, css_animation, duration)
            return True
            
        except Exception as e:
            log.error(f"Slide animation failed: {e}")
            return False
    
    def _render_fade_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render fade animation"""
        try:
            element_id = animation_data['element_id']
            duration = animation_data['properties'].get('duration', 500)
            
            # Create fade animation CSS
            css_animation = f"""
                #{element_id} {{
                    opacity: 0;
                    transition: opacity {duration}ms ease-in-out;
                }}
                
                #{element_id}.fade-in {{
                    opacity: 1;
                }}
            """
            
            # Apply animation
            await self.apply_css_animation(element_id, css_animation, duration)
            return True
            
        except Exception as e:
            log.error(f"Fade animation failed: {e}")
            return False
    
    def _render_bounce_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render bounce animation"""
        try:
            element_id = animation_data['element_id']
            duration = animation_data['properties'].get('duration', 600)
            intensity = animation_data['properties'].get('bounce_intensity', 0.5)
            
            # Create bounce animation CSS
            css_animation = f"""
                #{element_id} {{
                    animation: bounce {duration}ms ease-in-out;
                    transform-origin: center bottom;
                }}
                
                @keyframes bounce {{
                    0%, 20%, 53%, 80%, 100% {{
                        transform: translateY(0);
                        animation-timing-function: cubic-bezier(0.215, 0.610, 0.355, 1.000);
                    }}
                    40% {{
                        transform: translateY(-{30 * intensity}px);
                    }}
                    43% {{
                        transform: translateY(0);
                    }}
                    70% {{
                        transform: translateY(-{15 * intensity}px);
                    }}
                    80% {{
                        transform: translateY(0);
                    }}
                    90% {{
                        transform: translateY(0);
                    }}
                }}
            """
            
            # Apply animation
            await self.apply_css_animation(element_id, css_animation, duration)
            return True
            
        except Exception as e:
            log.error(f"Bounce animation failed: {e}")
            return False
    
    def _render_pulse_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render pulse animation"""
        try:
            element_id = animation_data['element_id']
            duration = animation_data['properties'].get('duration', 1000)
            
            # Create pulse animation CSS
            css_animation = f"""
                #{element_id} {{
                    animation: pulse {duration}ms ease-in-out infinite;
                    transform-origin: center;
                }}
                
                @keyframes pulse {{
                    0% {{
                        transform: scale(1);
                        opacity: 1;
                    }}
                    50% {{
                        transform: scale(1.05);
                        opacity: 0.8;
                    }}
                    100% {{
                        transform: scale(1);
                        opacity: 1;
                    }}
                }}
            """
            
            # Apply animation
            await self.apply_css_animation(element_id, css_animation, duration)
            return True
            
        except Exception as e:
            log.error(f"Pulse animation failed: {e}")
            return False
    
    def _render_shake_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render shake animation"""
        try:
            element_id = animation_data['element_id']
            duration = animation_data['properties'].get('duration', 500)
            intensity = animation_data['properties'].get('shake_intensity', 0.5)
            
            # Create shake animation CSS
            css_animation = f"""
                #{element_id} {{
                    animation: shake {duration}ms ease-in-out;
                    transform-origin: center;
                }}
                
                @keyframes shake {{
                    0%, 100% {{
                        transform: translateX(0);
                    }}
                    10%, 30%, 50%, 70%, 90% {{
                        transform: translateX({-10 * intensity}px);
                    }}
                    20%, 40%, 60%, 80% {{
                        transform: translateX({10 * intensity}px);
                    }}
                    30%, 50%, 70%, 90%, 100% {{
                        transform: translateX(0);
                    }}
                }}
            """
            
            # Apply animation
            await self.apply_css_animation(element_id, css_animation, duration)
            return True
            
        except Exception as e:
            log.error(f"Shake animation failed: {e}")
            return False
    
    def _render_rotate_animation(self, animation_data: Dict[str, Any]) -> bool:
        """Render rotate animation"""
        try:
            element_id = animation_data['element_id']
            duration = animation_data['properties'].get('duration', 500)
            degrees = animation_data['properties'].get('degrees', 360)
            
            # Create rotate animation CSS
            css_animation = f"""
                #{element_id} {{
                    animation: rotate {degrees}deg linear {duration}ms;
                    transform-origin: center;
                }}
            """
            
            # Apply animation
            await self.apply_css_animation(element_id, css_animation, duration)
            return True
            
        except Exception as e:
            log.error(f"Rotate animation failed: {e}")
            return False
    
    async def apply_css_animation(self, element_id: str, css_animation: str, duration: int):
        """Apply CSS animation to element"""
        try:
            # This would integrate with the frontend framework
            # For now, return the CSS for manual application
            log.info(f"CSS animation ready for {element_id}: {css_animation}")
            return {
                'css': css_animation,
                'duration': duration,
                'element_id': element_id
            }
            
        except Exception as e:
            log.error(f"CSS application failed: {e}")
            return {'error': str(e)}
    
    def get_active_animations(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active animations"""
        return self.active_animations.copy()
    
    def remove_animation(self, element_id: str) -> bool:
        """Remove animation from active animations"""
        if element_id in self.active_animations:
            del self.active_animations[element_id]
            log.info(f"Animation removed from {element_id}")
            return True
        return False

class ProgressIndicator:
    """Animated progress indicators with micro-interactions"""
    
    def __init__(self):
        self.progress_bars = {}
        self.loading_animations = {}
    
    def create_progress_bar(self, element_id: str, initial_value: float = 0.0, 
                        max_value: float = 100.0, animated: bool = True) -> Dict[str, Any]:
        """Create animated progress bar"""
        progress_data = {
            'element_id': element_id,
            'current_value': initial_value,
            'max_value': max_value,
            'animated': animated,
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.progress_bars[element_id] = progress_data
        
        if animated:
            self.loading_animations[element_id] = True
        
        log.info(f"Progress bar created: {element_id} ({initial_value}/{max_value})")
        return progress_data
    
    def update_progress(self, element_id: str, new_value: float) -> Dict[str, Any]:
        """Update progress bar value"""
        if element_id in self.progress_bars:
            self.progress_bars[element_id]['current_value'] = new_value
            self.progress_bars[element_id]['updated_at'] = datetime.utcnow().isoformat()
            
            # Trigger success animation if complete
            if new_value >= self.progress_bars[element_id]['max_value']:
                self.progress_bars[element_id]['completed'] = True
            
            log.info(f"Progress updated: {element_id} = {new_value}/{self.progress_bars[element_id]['max_value']}")
            return self.progress_bars[element_id]
        return None
    
    def get_progress_status(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Get progress bar status"""
        return self.progress_bars.get(element_id)
    
    def remove_progress_bar(self, element_id: str) -> bool:
        """Remove progress bar"""
        if element_id in self.progress_bars:
            del self.progress_bars[element_id]
            log.info(f"Progress bar removed: {element_id}")
            return True
        return False

class NotificationSystem:
    """Advanced notification system with micro-interactions"""
    
    def __init__(self):
        self.notifications = []
        self.notification_queue = []
        self.display_handlers = {
            'toast': self._display_toast,
            'modal': self._display_modal,
            'banner': self._display_banner,
            'tooltip': self._display_tooltip
        }
    
    async def create_notification(self, notification_type: str, title: str, 
                            message: str, duration_ms: int = 3000,
                            display_type: str = 'toast', 
                            priority: str = 'medium',
                            actions: List[Dict[str, Any]] = None) -> str:
        """Create notification with micro-interactions"""
        try:
            notification_data = {
                'id': f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'type': notification_type,
                'title': title,
                'message': message,
                'duration': duration_ms,
                'display_type': display_type,
                'priority': priority,
                'actions': actions or [],
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.notification_queue.append(notification_data)
            
            # Trigger haptic feedback
            await self.trigger_haptic(AnimationType.HAPTIC_MEDIUM, intensity=0.5)
            
            log.info(f"Notification created: {notification_type} - {title}")
            return notification_data['id']
            
        except Exception as e:
            log.error(f"Notification creation failed: {e}")
            return None
    
    async def display_notification(self, notification_id: str) -> bool:
        """Display notification using appropriate handler"""
        try:
            # Find notification in queue
            notification = None
            for i, notif in enumerate(self.notification_queue):
                if notif['id'] == notification_id:
                    notification = notif
                    break
            
            if not notification:
                log.error(f"Notification {notification_id} not found")
                return False
            
            handler = self.display_handlers.get(notification['display_type'])
            if handler:
                result = await handler(notification)
                if result:
                    # Remove from queue
                    self.notification_queue.remove(notification)
                    log.info(f"Notification displayed: {notification_id}")
                return result
            
            return False
            
        except Exception as e:
            log.error(f"Notification display failed: {e}")
            return False
    
    def _display_toast(self, notification: Dict[str, Any]) -> bool:
        """Display toast notification"""
        try:
            # Create toast element with animation
            toast_css = f"""
                .toast-{notification['id']} {{
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: rgba(0, 0, 0, 0.9);
                    color: white;
                    padding: 16px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    z-index: 1000;
                    transform: translateY(100px);
                    transition: all 0.3s ease;
                    max-width: 300px;
                }}
                
                .toast-{notification['id']}.show {{
                    transform: translateY(0);
                    opacity: 1;
                }}
                
                .toast-{notification['id']}.hide {{
                    transform: translateY(100px);
                    opacity: 0;
                }}
            """
            
            log.info(f"Toast notification ready: {notification['id']}")
            return {
                'css': toast_css,
                'html': self._generate_toast_html(notification),
                'duration': notification['duration']
            }
            
        except Exception as e:
            log.error(f"Toast creation failed: {e}")
            return {'error': str(e)}
    
    def _display_modal(self, notification: Dict[str, Any]) -> bool:
        """Display modal notification"""
        try:
            # Create modal overlay with animation
            modal_css = f"""
                .modal-overlay-{notification['id']} {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }}
                
                .modal-content-{notification['id']} {{
                    background: white;
                    border-radius: 12px;
                    padding: 24px;
                    max-width: 500px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
                    transform: scale(0.9);
                    transition: transform 0.3s ease;
                }}
                
                .modal-overlay-{notification['id']}.show {{
                    opacity: 1;
                }}
                
                .modal-overlay-{notification['id']}.show .modal-content-{notification['id']} {{
                    transform: scale(1);
                }}
            """
            
            log.info(f"Modal notification ready: {notification['id']}")
            return {
                'css': modal_css,
                'html': self._generate_modal_html(notification)
            }
            
        except Exception as e:
            log.error(f"Modal creation failed: {e}")
            return {'error': str(e)}
    
    def _display_banner(self, notification: Dict[str, Any]) -> bool:
        """Display banner notification"""
        try:
            # Create banner with slide animation
            banner_css = f"""
                .banner-{notification['id']} {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    background: linear-gradient(135deg, #3b82f6, #2563eb);
                    color: white;
                    padding: 16px;
                    text-align: center;
                    z-index: 999;
                    transform: translateY(-100%);
                    transition: transform 0.3s ease;
                }}
                
                .banner-{notification['id']}.show {{
                    transform: translateY(0);
                }}
            """
            
            log.info(f"Banner notification ready: {notification['id']}")
            return {
                'css': banner_css,
                'html': self._generate_banner_html(notification)
            }
            
        except Exception as e:
            log.error(f"Banner creation failed: {e}")
            return {'error': str(e)}
    
    def _generate_toast_html(self, notification: Dict[str, Any]) -> str:
        """Generate toast notification HTML"""
        return f"""
            <div class="toast-{notification['id']}" id="{notification['id']}">
                <div class="toast-header">
                    <strong>{notification['title']}</strong>
                    <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
                <div class="toast-body">
                    {notification['message']}
                </div>
                {self._generate_action_buttons(notification['actions'])}
            </div>
        """
    
    def _generate_modal_html(self, notification: Dict[str, Any]) -> str:
        """Generate modal notification HTML"""
        return f"""
            <div class="modal-overlay-{notification['id']}" id="{notification['id']}">
                <div class="modal-content-{notification['id']}">
                    <div class="modal-header">
                        <h3>{notification['title']}</h3>
                        <button class="modal-close" onclick="document.getElementById('{notification['id']}').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        {notification['message']}
                    </div>
                    {self._generate_action_buttons(notification['actions'])}
                </div>
            </div>
        """
    
    def _generate_banner_html(self, notification: Dict[str, Any]) -> str:
        """Generate banner notification HTML"""
        return f"""
            <div class="banner-{notification['id']}" id="{notification['id']}">
                <div class="banner-content">
                    <strong>{notification['title']}</strong>
                    <p>{notification['message']}</p>
                    {self._generate_action_buttons(notification['actions'])}
                </div>
                <button class="banner-close" onclick="document.getElementById('{notification['id']}').remove()">×</button>
            </div>
        """
    
    def _generate_action_buttons(self, actions: List[Dict[str, Any]]) -> str:
        """Generate action buttons for notifications"""
        if not actions:
            return ""
        
        buttons_html = '<div class="notification-actions">'
        for action in actions:
            buttons_html += f'''
                <button class="notification-action" data-action="{action['id']}" onclick="handleNotificationAction('{action['id']}')">
                    {action.get('text', action['id'])}
                </button>
            '''
        
        buttons_html += '</div>'
        return buttons_html

class GestureHandler:
    """Advanced gesture recognition and handling"""
    
    def __init__(self):
        self.gesture_patterns = {}
        self.gesture_handlers = {}
    
    def register_gesture(self, gesture_name: str, pattern: Dict[str, Any], handler: Callable):
        """Register custom gesture pattern"""
        self.gesture_patterns[gesture_name] = pattern
        self.gesture_handlers[gesture_name] = handler
        log.info(f"Gesture registered: {gesture_name}")
    
    def detect_gesture(self, gesture_data: Dict[str, Any]) -> Optional[str]:
        """Detect gesture from input data"""
        try:
            for gesture_name, pattern in self.gesture_patterns.items():
                if self._matches_pattern(gesture_data, pattern):
                    handler = self.gesture_handlers.get(gesture_name)
                    if handler:
                        return gesture_name
            return None
            
        except Exception as e:
            log.error(f"Gesture detection failed: {e}")
            return None
    
    def _matches_pattern(self, gesture_data: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """Check if gesture data matches pattern"""
        try:
            for key, expected_value in pattern.items():
                actual_value = gesture_data.get(key)
                if actual_value is not None and actual_value != expected_value:
                    return False
            return True
            
        except Exception as e:
            log.error(f"Pattern matching failed: {e}")
            return False

# Industry-standard micro-interaction factory
def create_interaction_system() -> MicroInteraction:
    """Create industry-standard micro-interaction system"""
    return MicroInteraction()

def create_progress_system() -> ProgressIndicator:
    """Create animated progress indicator system"""
    return ProgressIndicator()

def create_notification_system() -> NotificationSystem:
    """Create advanced notification system"""
    return NotificationSystem()

def create_gesture_handler() -> GestureHandler:
    """Create advanced gesture handler"""
    return GestureHandler()
