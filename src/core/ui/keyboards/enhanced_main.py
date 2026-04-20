"""
Enhanced Interactive Keyboards for Telegram Bot
Modern, responsive keyboards with rich interactions and animations
"""

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton, KeyboardButton
from typing import List, Dict, Any

def create_enhanced_main_keyboard() -> ReplyKeyboardRemove:
    """Create enhanced main keyboard with modern design"""
    builder = ReplyKeyboardBuilder()
    
    # First row - Main actions
    builder.row(
        KeyboardButton(text="🔍 Search Resources"),
        KeyboardButton(text="🏫 Browse All")
    )
    
    # Second row - Personal features
    builder.row(
        KeyboardButton(text="❤️ My Favorites"),
        KeyboardButton(text="👤 Profile")
    )
    
    # Third row - Quick access
    builder.row(
        KeyboardButton(text="📊 Statistics"),
        KeyboardButton(text="⚙️ Settings")
    )
    
    # Fourth row - Help
    builder.row(
        KeyboardButton(text="❓ Help & Guide")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_search_keyboard() -> ReplyKeyboardRemove:
    """Create search-specific keyboard with suggestions"""
    builder = ReplyKeyboardBuilder()
    
    # Popular search categories
    builder.row(
        KeyboardButton(text="📚 Lecture Notes"),
        KeyboardButton(text="🎥 Video Tutorials")
    )
    
    builder.row(
        KeyboardButton(text="📄 Past Papers"),
        KeyboardButton(text="🔬 Lab Reports")
    )
    
    builder.row(
        KeyboardButton(text="📐 Assignments"),
        KeyboardButton(text="💡 Study Guides")
    )
    
    # Navigation
    builder.row(
        KeyboardButton(text="🔍 Custom Search"),
        KeyboardButton(text="⬅️ Back to Menu")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_browse_keyboard(institutions: List[Dict]) -> ReplyKeyboardRemove:
    """Create browse keyboard with institutions"""
    builder = ReplyKeyboardBuilder()
    
    # Display institutions in rows of 2
    for i in range(0, len(institutions), 2):
        row_buttons = []
        if i < len(institutions):
            row_buttons.append(KeyboardButton(text=f"🏫 {institutions[i]['name']}"))
        if i + 1 < len(institutions):
            row_buttons.append(KeyboardButton(text=f"🏫 {institutions[i+1]['name']}"))
        builder.row(*row_buttons)
    
    # Navigation
    builder.row(
        KeyboardButton(text="🔍 Search"),
        KeyboardButton(text="⬅️ Main Menu")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_profile_keyboard() -> ReplyKeyboardRemove:
    """Create profile management keyboard"""
    builder = ReplyKeyboardBuilder()
    
    # Profile sections
    builder.row(
        KeyboardButton(text="📈 My Statistics"),
        KeyboardButton(text="❤️ Favorites")
    )
    
    builder.row(
        KeyboardButton(text="🕒 Search History"),
        KeyboardButton(text="📊 Activity Log")
    )
    
    builder.row(
        KeyboardButton(text="⚙️ Settings"),
        KeyboardButton(text="🔔 Notifications")
    )
    
    builder.row(
        KeyboardButton(text="⬅️ Back to Menu")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_settings_keyboard() -> ReplyKeyboardRemove:
    """Create settings management keyboard"""
    builder = ReplyKeyboardBuilder()
    
    # Settings categories
    builder.row(
        KeyboardButton(text="🌐 Language"),
        KeyboardButton(text="🎨 Theme")
    )
    
    builder.row(
        KeyboardButton(text="🔔 Notifications"),
        KeyboardButton(text="🔐 Privacy")
    )
    
    builder.row(
        KeyboardButton(text="📊 Data Usage"),
        KeyboardButton(text="💾 Backup Data")
    )
    
    builder.row(
        KeyboardButton(text="ℹ️ About"),
        KeyboardButton(text="⬅️ Back to Menu")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_resource_actions_keyboard(resource_id: str, is_favorite: bool = False) -> InlineKeyboardBuilder:
    """Create inline keyboard for resource actions"""
    builder = InlineKeyboardBuilder()
    
    # Action buttons
    favorite_text = "❤️ Remove from Favorites" if is_favorite else "🤍 Add to Favorites"
    favorite_callback = f"remove_favorite:{resource_id}" if is_favorite else f"add_favorite:{resource_id}"
    
    builder.row(
        InlineKeyboardButton(text="⬇️ Download", callback_data=f"download:{resource_id}"),
        InlineKeyboardButton(text=favorite_text, callback_data=favorite_callback)
    )
    
    # Share and report
    builder.row(
        InlineKeyboardButton(text="🔗 Share", callback_data=f"share:{resource_id}"),
        InlineKeyboardButton(text="🚨 Report Issue", callback_data=f"report:{resource_id}")
    )
    
    # Navigation
    builder.row(
        InlineKeyboardButton(text="📄 Full Details", callback_data=f"details:{resource_id}"),
        InlineKeyboardButton(text="⬅️ Back to Results", callback_data="back_to_search")
    )
    
    return builder

def create_search_results_keyboard(query: str, has_more: bool = True) -> InlineKeyboardBuilder:
    """Create keyboard for search results"""
    builder = InlineKeyboardBuilder()
    
    # Search actions
    builder.row(
        InlineKeyboardButton(text="🔍 Refine Search", callback_data=f"refine_search:{query}"),
        InlineKeyboardButton(text="🏫 Browse Instead", callback_data="browse_institutions")
    )
    
    # More results
    if has_more:
        builder.row(
            InlineKeyboardButton(text="📄 Show More Results", callback_data=f"more_results:{query}")
        )
    
    # New search
    builder.row(
        InlineKeyboardButton(text="🔍 New Search", callback_data="new_search"),
        InlineKeyboardButton(text="⬅️ Main Menu", callback_data="main_menu")
    )
    
    return builder

def create_favorites_keyboard(favorites: List[Dict]) -> InlineKeyboardBuilder:
    """Create keyboard for favorites management"""
    builder = InlineKeyboardBuilder()
    
    # List favorites
    for i, favorite in enumerate(favorites[:5]):  # Show first 5
        title = favorite.get('title', 'Unknown')[:30]
        resource_id = favorite.get('id', 'unknown')
        
        builder.row(
            InlineKeyboardButton(text=f"❤️ {title}", callback_data=f"resource:{resource_id}")
        )
    
    # Management options
    builder.row(
        InlineKeyboardButton(text="🗑️ Clear All", callback_data="clear_favorites"),
        InlineKeyboardButton(text="📊 View Stats", callback_data="favorites_stats")
    )
    
    # Navigation
    builder.row(
        InlineKeyboardButton(text="⬅️ Back to Profile", callback_data="back_to_profile"),
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
    )
    
    return builder

def create_statistics_keyboard() -> ReplyKeyboardRemove:
    """Create statistics viewing keyboard"""
    builder = ReplyKeyboardBuilder()
    
    # Statistics categories
    builder.row(
        KeyboardButton(text="📈 Usage Stats"),
        KeyboardButton(text="🔍 Search Stats")
    )
    
    builder.row(
        KeyboardButton(text="⬇️ Download Stats"),
        KeyboardButton(text="❤️ Favorite Stats")
    )
    
    builder.row(
        KeyboardButton(text="🏆 Leaderboard"),
        KeyboardButton(text="📅 Activity Timeline")
    )
    
    builder.row(
        KeyboardButton(text="⬅️ Back to Profile")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_help_keyboard() -> ReplyKeyboardRemove:
    """Create help and guidance keyboard"""
    builder = ReplyKeyboardBuilder()
    
    # Help categories
    builder.row(
        KeyboardButton(text="📖 User Guide"),
        KeyboardButton(text="🎮 How to Use")
    )
    
    builder.row(
        KeyboardButton(text="❓ FAQ"),
        KeyboardButton(text="💬 Contact Support")
    )
    
    builder.row(
        KeyboardButton(text="🔍 Search Tips"),
        KeyboardButton(text="⚙️ Advanced Features")
    )
    
    builder.row(
        KeyboardButton(text="📊 System Status"),
        KeyboardButton(text="⬅️ Back to Menu")
    )
    
    return builder.as_markup(resize_keyboard=True)

def create_confirmation_keyboard(action: str, item: str = "") -> InlineKeyboardBuilder:
    """Create confirmation keyboard for actions"""
    builder = InlineKeyboardBuilder()
    
    # Confirmation text
    confirm_text = f"✅ Yes, {action}"
    if item:
        confirm_text = f"✅ Yes, {action} {item}"
    
    builder.row(
        InlineKeyboardButton(text=confirm_text, callback_data=f"confirm:{action}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
    )
    
    return builder

def create_pagination_keyboard(current_page: int, total_pages: int, action_prefix: str) -> InlineKeyboardBuilder:
    """Create pagination keyboard"""
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons
    if current_page > 0:
        builder.row(
            InlineKeyboardButton(text="⬅️ Previous", callback_data=f"{action_prefix}:page:{current_page-1}")
        )
    
    if current_page < total_pages - 1:
        builder.row(
            InlineKeyboardButton(text="➡️ Next", callback_data=f"{action_prefix}:page:{current_page+1}")
        )
    
    # Page indicator
    builder.row(
        InlineKeyboardButton(text=f"📄 Page {current_page + 1}/{total_pages}", callback_data="noop")
    )
    
    return builder

# Interactive animations and micro-interactions
def create_loading_keyboard() -> InlineKeyboardBuilder:
    """Create loading animation keyboard"""
    builder = InlineKeyboardBuilder()
    
    # Animated loading buttons
    loading_texts = ["⏳ Processing...", "⌛ Loading...", "🔄 Searching..."]
    
    for text in loading_texts:
        builder.row(
            InlineKeyboardButton(text=text, callback_data="loading")
        )
    
    return builder

def create_quick_reply_keyboard(replies: List[str]) -> ReplyKeyboardRemove:
    """Create quick reply keyboard from suggestions"""
    builder = ReplyKeyboardBuilder()
    
    # Add replies in rows of 2
    for i in range(0, len(replies), 2):
        row_buttons = []
        if i < len(replies):
            row_buttons.append(KeyboardButton(text=replies[i]))
        if i + 1 < len(replies):
            row_buttons.append(KeyboardButton(text=replies[i+1]))
        builder.row(*row_buttons)
    
    # Add "Custom" option
    builder.row(
        KeyboardButton(text="✏️ Custom Input"),
        KeyboardButton(text="❌ Cancel")
    )
    
    return builder.as_markup(resize_keyboard=True)

# Context-aware keyboards
def create_context_keyboard(context: Dict[str, Any]) -> ReplyKeyboardRemove:
    """Create keyboard based on user context"""
    user_level = context.get('level', 'beginner')
    last_action = context.get('last_action', 'none')
    
    builder = ReplyKeyboardBuilder()
    
    # Adaptive suggestions based on user level
    if user_level == 'beginner':
        builder.row(
            KeyboardButton(text="🎓 Getting Started"),
            KeyboardButton(text="🔍 Basic Search")
        )
    elif user_level == 'expert':
        builder.row(
            KeyboardButton(text="🔬 Advanced Search"),
            KeyboardButton(text="📊 Analytics")
        )
    
    # Recent actions
    if last_action == 'search':
        builder.row(
            KeyboardButton(text="🔍 Search Again"),
            KeyboardButton(text="🏫 Browse Categories")
        )
    elif last_action == 'browse':
        builder.row(
            KeyboardButton(text="📚 View Courses"),
            KeyboardButton(text="👤 Profile")
        )
    
    # Always include main menu
    builder.row(
        KeyboardButton(text="🏠 Main Menu")
    )
    
    return builder.as_markup(resize_keyboard=True)
