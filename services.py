import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from .models import (
    CategoryDefinition,
    CourseManifest,
    ResourceFile,
    ScreenView,
    SearchQuery,
    SearchResolution,
    SearchResult,
    SearchStatus,
)

log = logging.getLogger(__name__)

class ButtonLabels:
    BACK = "◀ Back"
    MAIN = "⌂ Main menu"
    RESOURCES = "📚 Resources"
    EXAMS = "📝 Exams"
    NOTES = "📘 Lecture notes"
    SYLLABUS = "📄 Syllabus"
    WEEKS = "🗓 By week"
    OVERVIEW = "✨ Overview"
    MORE = "📂 More files"

class NavigationStatus:
    SENDING = "sending"
    TRANSIENT_IDS = "transient_ids"

class NavigationService:
    """Manages FSM state transitions and transient message cleanup."""
    
    @staticmethod
    async def clear_transient(state: FSMContext, bot: Bot, chat_id: int):
        data = await state.get_data()
        msg_ids = data.get("transient_ids", [])
        for mid in msg_ids:
            try:
                await bot.delete_message(chat_id, mid)
            except Exception:
                pass
        await state.update_data(transient_ids=[])

    @staticmethod
    async def track_transient(state: FSMContext, message_id: int):
        data = await state.get_data()
        ids = data.get("transient_ids", [])
        ids.append(message_id)
        await state.update_data(transient_ids=ids)

class DeliveryService:
    """Handles rate-limited file sending with interrupt support."""
    
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_bundle(
        self, 
        chat_id: int, 
        files: List[Path], 
        captions: List[str],
        state: FSMContext
    ):
        await state.update_data(sending=True)
        sent_count = 0
        
        for path, caption in zip(files, captions):
            # HARD KILL SWITCH check
            data = await state.get_data()
            if not data.get("sending"):
                log.info("Delivery interrupted by user.")
                break

            try:
                await self.bot.send_document(
                    chat_id, 
                    types.FSInputFile(path), 
                    caption=caption
                )
                sent_count += 1
                # Rate limiting
                await asyncio.sleep(0.35) 
            except Exception as e:
                log.error(f"Failed to send {path}: {e}")
                # Store failure for retry logic
        
        await state.update_data(sending=False)
        return sent_count

class SearchService:
    """In-memory alias-aware search indexer."""
    
    def __init__(self, courses: Dict[str, CourseManifest]):
        self.courses = courses
        self.index: Dict[str, List[str]] = {} # token -> course_ids
        self._build_index()

    def _build_index(self):
        for cid, course in self.courses.items():
            tokens = set()
            tokens.add(course.title.lower())
            for alias in course.aliases:
                tokens.add(alias.lower())
            
            for t in tokens:
                # Simple normalization
                clean = t.replace(" ", "")
                self.index.setdefault(clean, []).append(cid)

    def resolve(self, query: str) -> List[SearchResult]:
        query = query.lower().replace(" ", "")
        matches = self.index.get(query, [])
        return [SearchResult(course_id=cid, score=1.0) for cid in matches]