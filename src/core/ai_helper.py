"""
AI Helper Service for Academic Hub - Honest Study Assistant
"""

import json
import logging
import os
from typing import Optional, Dict, Any, AsyncGenerator
import httpx

from .config import load_config
from api.models import Question, Answer
from sqlalchemy.orm import sessionmaker
from api.database import get_engine

log = logging.getLogger(__name__)

class AIHelper:
    """AI-powered study assistant using GROQ Llama 3"""
    
    def __init__(self):
        self.config = load_config()
        self.client = None
        self.system_prompt = self._build_system_prompt()
        
        # Prepare Database Session for community context
        try:
            self._engine = get_engine()
            self._Session = sessionmaker(bind=self._engine)
        except Exception:
            self._Session = None

    def _get_community_context(self, query: str) -> str:
        """Search the database for relevant student Q&A"""
        if not self._Session:
            return ""
        
        try:
            with self._Session() as session:
                # Search for questions containing key terms from the query
                q_list = session.query(Question).filter(Question.title.ilike(f"%{query[:20]}%")).limit(3).all()
                if not q_list:
                    return ""
                
                context = "\n\n**COMMUNITY Q&A CONTEXT:**\n"
                for q in q_list:
                    context += f"- Q: {q.title}\n"
                    # Get the top answer for this question
                    top_a = session.query(Answer).filter(Answer.question_id == q.id).first()
                    if top_a:
                        context += f"  A: {top_a.body[:100]}...\n"
                return context
        except Exception:
            return ""
        
    def _build_system_prompt(self) -> str:
        """Build the honest system prompt for the study assistant"""
        return f"""You are a study assistant for SIT students.

**CONSTRAINTS:**
- Answer questions directly and concisely.
- Do not hallucinate links. Use the provided links if relevant:
  * Exam Prep: <a href="https://t.me/c/3653709098/1034">Resource Index</a>
  * Subjects: <a href="https://t.me/c/3653709098/5">Maths</a>, <a href="https://t.me/c/3653709098/7">Physics</a>, <a href="https://t.me/c/3653709098/766">Programming</a>.
  * Official: <a href="https://{self.config.institution_website}">{self.config.institution_website}</a>.
- Format responses cleanly using standard markdown where applicable.
"""

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client"""
        key = self.config.groq_api_key
        return httpx.AsyncClient(
            base_url="https://api.groq.com/openai/v1",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30.0
        )

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chunks from GROQ API with Community Context"""
        if not self.config.groq_api_key or not getattr(self.config, 'ai_helper_enabled', True):
            yield "AI Assistant is currently disabled or missing API key."
            return

        try:
            # Inject Community Context from Database
            last_user_msg = messages[-1]["content"] if messages else ""
            community_context = self._get_community_context(last_user_msg)
            if community_context:
                messages[0]["content"] += community_context

            client = await self._get_client()
            async with client as active_client:
                async with active_client.stream(
                    "POST",
                    "/chat/completions",
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.5,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        error_msg = f"❌ GROQ ERROR {response.status_code}: {error_detail.decode()}"
                        print(f"\n{error_msg}\n") 
                        log.error(error_msg)
                        yield f"Sorry, I'm having trouble connecting right now. (Error: {response.status_code})"
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(data_str)
                            chunk = data["choices"][0]["delta"].get("content", "")
                            if chunk:
                                yield chunk
                        except (KeyError, json.JSONDecodeError):
                            continue

        except Exception as e:
            log.error(f"GROQ Stream failed: {e}")
            yield "Connection error. Let me try to reconnect."

    async def _call_groq(self, messages: list[dict[str, str]]) -> Optional[str]:
        """Make simple API call to GROQ"""
        if not self.config.groq_api_key or not getattr(self.config, 'ai_helper_enabled', True):
            return None
            
        try:
            client = await self._get_client()
            async with client as active_client:
                response = await active_client.post(
                    "/chat/completions",
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": messages,
                        "max_tokens": 100,
                        "temperature": 0.5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    log.warning(f"GROQ API error: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            log.error(f"GROQ API call failed: {e}")
            return None

    async def close(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()

# Global instance
_ai_helper = None

def get_ai_helper() -> AIHelper:
    """Get global AI helper instance"""
    global _ai_helper
    if _ai_helper is None:
        _ai_helper = AIHelper()
    return _ai_helper
