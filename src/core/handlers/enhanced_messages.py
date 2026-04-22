"""
Enhanced Telegram Bot Message Handlers with Modern UX and Micro-interactions
Provides rich, interactive user experience with haptic feedback and animations
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from src.bot.services.message_service import MessageService
from src.bot.services.user_service import UserService
from src.bot.keyboards.enhanced_main import create_enhanced_main_keyboard
from src.bot.keyboards.interactive_search import create_search_keyboard
from src.bot.keyboards.profile_menu import create_profile_keyboard

router = Router()
log = logging.getLogger(__name__)

class MessageHandler:
    """Enhanced message handler with rich interactions"""
    
    def __init__(self, message_service: MessageService, user_service: UserService):
        self.message_service = message_service
        self.user_service = user_service
        self.user_states = {}  # Track user interaction states
        self.search_history = {}  # Store search history per user
        self.favorite_resources = {}  # User favorites
    
    async def send_typing_action(self, chat_id: int):
        """Show typing indicator for better UX"""
        await self.message_service.bot.send_chat_action(chat_id, 'typing')
        await asyncio.sleep(0.5)  # Simulate processing
    
    async def send_with_reaction(self, chat_id: int, text: str, reaction: str = None):
        """Send message with optional reaction animation"""
        if reaction:
            # Send reaction animation
            await self.message_service.bot.send_message(
                chat_id, 
                f"{reaction} {text}",
                parse_mode='HTML'
            )
        else:
            await self.message_service.bot.send_message(chat_id, text)
    
    async def send_loading_animation(self, chat_id: int, message: str = "Searching..."):
        """Send animated loading message"""
        loading_frames = ["⏳", "⌛", "🔄", "⚡"]
        
        sent_message = await self.message_service.bot.send_message(chat_id, f"{loading_frames[0]} {message}")
        
        for i in range(1, len(loading_frames)):
            await asyncio.sleep(0.3)
            try:
                await self.message_service.bot.edit_message_text(
                    chat_id, 
                    sent_message.message_id, 
                    f"{loading_frames[i]} {message}"
                )
            except:
                pass  # Message might be deleted
    
    async def send_search_results(self, chat_id: int, results: List[Dict], query: str):
        """Send search results with rich formatting and interactions"""
        if not results:
            await self.send_not_found_response(chat_id, query)
            return
        
        # Store search history
        user_id = str(chat_id)
        if user_id not in self.search_history:
            self.search_history[user_id] = []
        self.search_history[user_id].insert(0, {
            'query': query,
            'timestamp': datetime.now(),
            'results_count': len(results)
        })
        
        # Keep only last 10 searches
        self.search_history[user_id] = self.search_history[user_id][:10]
        
        # Create rich response
        response_text = f"🔍 <b>Found {len(results)} results for:</b> <code>{query}</code>\n\n"
        
        # Create inline keyboard for results
        builder = InlineKeyboardBuilder()
        
        for i, result in enumerate(results[:5]):  # Show first 5 results
            title = result.get('title', 'Unknown Title')[:40]
            description = result.get('description', '')[:60]
            resource_id = result.get('id', 'unknown')
            
            # Add emoji based on resource type
            emoji = self.get_resource_emoji(result.get('category', ''))
            
            button_text = f"{emoji} {title}"
            if description:
                button_text += f"\n{description}"
            
            builder.row(
                types.InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"resource:{resource_id}"
                )
            )
        
        # Add navigation buttons
        if len(results) > 5:
            builder.row(
                types.InlineKeyboardButton(
                    text="📄 Show more results...",
                    callback_data=f"more_results:{query}:{5}"
                )
            )
        
        # Add search again button
        builder.row(
            types.InlineKeyboardButton(
                text="🔍 New Search",
                callback_data="new_search"
            )
        )
        
        await self.message_service.bot.send_message(
            chat_id,
            response_text,
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
    
    async def send_not_found_response(self, chat_id: int, query: str):
        """Send enhanced not found response with suggestions"""
        suggestions = [
            "Try different keywords",
            "Check spelling",
            "Browse by institution",
            "Use filters"
        ]
        
        response = f"😔 <b>No results found for:</b> <code>{query}</code>\n\n"
        response += "<b>💡 Suggestions:</b>\n"
        response += "\n".join(f"• {suggestion}" for suggestion in suggestions)
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🏫 Browse Institutions", callback_data="browse_institutions"),
            types.InlineKeyboardButton(text="🔍 Try New Search", callback_data="new_search")
        )
        
        await self.message_service.bot.send_message(
            chat_id,
            response,
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
    
    def get_resource_emoji(self, category: str) -> str:
        """Get emoji for resource category"""
        emoji_map = {
            'pdf': '📄',
            'video': '🎥',
            'audio': '🎵',
            'image': '🖼️',
            'link': '🔗',
            'document': '📋',
            'presentation': '📊',
            'spreadsheet': '📈',
            'archive': '🗜️'
        }
        return emoji_map.get(category.lower(), '📄')
    
    async def send_resource_details(self, chat_id: int, resource: Dict):
        """Send detailed resource view with rich interactions"""
        title = resource.get('title', 'Unknown Title')
        description = resource.get('description', 'No description available')
        category = resource.get('category', 'document')
        file_size = resource.get('file_size', 'Unknown size')
        download_count = resource.get('download_count', 0)
        rating = resource.get('rating', 0)
        
        # Create rich formatted response
        response = f"📚 <b>{title}</b>\n\n"
        response += f"📝 <b>Description:</b> {description}\n\n"
        response += f"📁 <b>Category:</b> {self.get_resource_emoji(category)} {category}\n"
        response += f"💾 <b>Size:</b> {file_size}\n"
        response += f"⬇️ <b>Downloads:</b> {download_count}\n"
        
        if rating > 0:
            stars = "⭐" * int(rating)
            response += f"⭐ <b>Rating:</b> {stars} ({rating}/5)\n"
        
        response += f"📅 <b>Added:</b> {resource.get('created_at', 'Unknown')}"
        
        # Create action buttons
        builder = InlineKeyboardBuilder()
        
        # Favorite button
        user_id = str(chat_id)
        is_favorite = resource.get('id') in self.favorite_resources.get(user_id, set())
        favorite_text = "❤️ Remove from Favorites" if is_favorite else "🤍 Add to Favorites"
        favorite_callback = f"remove_favorite:{resource.get('id')}" if is_favorite else f"add_favorite:{resource.get('id')}"
        
        builder.row(
            types.InlineKeyboardButton(text=f"⬇️ Download", callback_data=f"download:{resource.get('id')}"),
            types.InlineKeyboardButton(text=favorite_text, callback_data=favorite_callback)
        )
        
        builder.row(
            types.InlineKeyboardButton(text="🔗 Share", callback_data=f"share:{resource.get('id')}"),
            types.InlineKeyboardButton(text="📊 Report Issue", callback_data=f"report:{resource.get('id')}")
        )
        
        builder.row(
            types.InlineKeyboardButton(text="⬅️ Back to Results", callback_data="back_to_results"),
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        )
        
        await self.message_service.bot.send_message(
            chat_id,
            response,
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
    
    async def send_user_profile(self, chat_id: int, user_data: Dict):
        """Send enhanced user profile with statistics"""
        username = user_data.get('username', 'Unknown')
        join_date = user_data.get('join_date', datetime.now())
        total_searches = len(self.search_history.get(str(chat_id), []))
        total_downloads = user_data.get('download_count', 0)
        favorite_count = len(self.favorite_resources.get(str(chat_id), []))
        
        # Calculate user level based on activity
        user_level = self.calculate_user_level(total_searches, total_downloads)
        
        response = f"👤 <b>{username}</b>\n\n"
        response += f"🎯 <b>Level:</b> {user_level['emoji']} {user_level['name']}\n"
        response += f"📅 <b>Member Since:</b> {join_date.strftime('%B %d, %Y')}\n\n"
        
        response += "<b>📊 Statistics:</b>\n"
        response += f"🔍 Searches: {total_searches}\n"
        response += f"⬇️ Downloads: {total_downloads}\n"
        response += f"❤️ Favorites: {favorite_count}\n"
        
        # Recent activity
        recent_searches = self.search_history.get(str(chat_id), [])[:3]
        if recent_searches:
            response += f"\n<b>🕒 Recent Searches:</b>\n"
            for search in recent_searches:
                response += f"• {search['query']}\n"
        
        # Create profile menu
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="❤️ My Favorites", callback_data="view_favorites"),
            types.InlineKeyboardButton(text="📈 Statistics", callback_data="detailed_stats")
        )
        builder.row(
            types.InlineKeyboardButton(text="🔍 Search History", callback_data="search_history"),
            types.InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")
        )
        builder.row(
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        )
        
        await self.message_service.bot.send_message(
            chat_id,
            response,
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
    
    def calculate_user_level(self, searches: int, downloads: int) -> Dict:
        """Calculate user level based on activity"""
        score = searches + (downloads * 2)
        
        if score < 10:
            return {"name": "Beginner", "emoji": "🌱"}
        elif score < 50:
            return {"name": "Explorer", "emoji": "🌿"}
        elif score < 100:
            return {"name": "Scholar", "emoji": "📚"}
        elif score < 200:
            return {"name": "Expert", "emoji": "🎓"}
        else:
            return {"name": "Master", "emoji": "🏆"}

@router.message(Command("start"))
async def handle_start(message: types.Message):
    """Enhanced start command with welcome animation"""
    user_id = message.from_user.id
    username = message.from_user.first_name or "Voyager"
    
    # Send typing indicator
    await message.bot.send_chat_action(message.chat.id, 'typing')
    await asyncio.sleep(0.5)
    
    # Enhanced welcome message
    welcome_text = f"""
🚀 <b>Welcome to Academic Hub, {username}!</b>

🎓 Your personal knowledge gateway is now active!

✨ <b>What I can help you find:</b>
• 📚 Academic Resources
• 🎥 Video Lectures  
• 📄 Study Materials
• 🔍 Research Papers
• 💡 Quick Answers

🎮 <b>Try these commands:</b>
/🔍 Search for anything
/🏫 Browse by institution
/👤 Your profile
/❤️ Your favorites

Let's start your learning journey! 🚀
    """
    
    # Create enhanced main keyboard
    keyboard = await create_enhanced_main_keyboard()
    
    await message.bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    # Store user session
    user_service = UserService()
    await user_service.create_or_update_user(user_id, username, message.from_user.username)

@router.message(Command("search"))
async def handle_search_command(message: types.Message):
    """Enhanced search command with interactive keyboard"""
    keyboard = await create_search_keyboard()
    await message.bot.send_message(
        message.chat.id,
        "🔍 <b>Search Mode Activated</b>\n\n"
        "Type what you're looking for or use the buttons below:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@router.message(F.text & ~Command())
async def handle_text_search(message: types.Message, state: FSMContext):
    """Handle text search with rich interactions"""
    handler = MessageHandler(message_service, user_service)
    query = message.text.strip()
    
    if len(query) < 2:
        await message.bot.send_message(
            message.chat.id,
            "⚠️ Please enter at least 2 characters to search",
            parse_mode='HTML'
        )
        return
    
    # Send loading animation
    await handler.send_loading_animation(message.chat.id, "Searching resources...")
    
    try:
        # Perform search (mock implementation)
        results = await message_service.search_resources(query)
        
        # Send results with rich formatting
        await handler.send_search_results(message.chat.id, results, query)
        
    except Exception as e:
        log.error(f"Search failed: {e}")
        await message.bot.send_message(
            message.chat.id,
            "😔 <b>Search temporarily unavailable</b>\nPlease try again later.",
            parse_mode='HTML'
        )

@router.callback_query(lambda c: c.data.startswith("resource:"))
async def handle_resource_callback(callback: types.CallbackQuery):
    """Handle resource selection with enhanced details"""
    resource_id = callback.data.split(":")[1]
    
    await callback.bot.answer_callback_query(callback.id, show_alert=False)
    
    try:
        # Get resource details
        message_service = MessageService()
        resource = await message_service.get_resource_details(resource_id)
        
        handler = MessageHandler(message_service, user_service)
        await handler.send_resource_details(callback.message.chat.id, resource)
        
    except Exception as e:
        log.error(f"Resource details failed: {e}")
        await callback.bot.send_message(
            callback.message.chat.id,
            "❌ Resource not found or unavailable",
            parse_mode='HTML'
        )

@router.callback_query(lambda c: c.data.startswith("add_favorite:"))
async def handle_add_favorite(callback: types.CallbackQuery):
    """Handle adding resource to favorites with animation"""
    resource_id = callback.data.split(":")[1]
    user_id = str(callback.from_user.id)
    
    handler = MessageHandler(message_service, user_service)
    
    # Add to favorites
    if user_id not in handler.favorite_resources:
        handler.favorite_resources[user_id] = set()
    handler.favorite_resources[user_id].add(resource_id)
    
    await callback.bot.answer_callback_query(
        callback.id, 
        text="❤️ Added to favorites!",
        show_alert=True
    )
    
    # Update message
    await callback.bot.edit_message_text(
        callback.message.chat.id,
        callback.message.message_id,
        callback.message.html_text + "\n\n❤️ <b>Added to Favorites</b>",
        parse_mode='HTML'
    )

@router.callback_query(lambda c: c.data.startswith("download:"))
async def handle_download(callback: types.CallbackQuery):
    """Handle resource download with progress indication"""
    resource_id = callback.data.split(":")[1]
    
    await callback.bot.answer_callback_query(
        callback.id,
        text="⬇️ Preparing download...",
        show_alert=True
    )
    
    try:
        # Get download link
        message_service = MessageService()
        download_info = await message_service.get_download_link(resource_id)
        
        # Send download with progress
        await callback.bot.send_message(
            callback.message.chat.id,
            f"⬇️ <b>Download Ready!</b>\n\n"
            f"📁 {download_info['title']}\n"
            f"🔗 {download_info['url']}\n\n"
            f"⏱️ Link expires in 10 minutes",
            parse_mode='HTML'
        )
        
        # Track download
        user_service = UserService()
        await user_service.track_download(callback.from_user.id, resource_id)
        
    except Exception as e:
        log.error(f"Download failed: {e}")
        await callback.bot.send_message(
            callback.message.chat.id,
            "❌ Download failed. Please try again.",
            parse_mode='HTML'
        )

# Initialize enhanced message handler
def create_enhanced_message_handler(message_service: MessageService, user_service: UserService) -> MessageHandler:
    """Factory function to create enhanced message handler"""
    return MessageHandler(message_service, user_service)
