"""
Coach Service - Central Coordinator for AI Coach Interactions

This module provides the CoachService class, which coordinates all interactions
with the AI Coach (Sara). It handles request processing, persona management,
text-to-speech conversion, and maintains conversation history.

Author: Rip Jonesy
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.app.automodel import TaskType
from backend.app.automodel.automodel import AutoModel, ProcessRequest
from backend.app.core.config import settings
from backend.app.services.database_service import supabase
from backend.app.services.persona_service import PersonaService
from backend.app.services.tts_service import TtsService

# Logger for this module
logger = logging.getLogger("chatchonk.services.coach")

class CoachService:
    """
    Central service for handling AI Coach (Sara) interactions.
    
    This service coordinates between:
    - PersonaService: Manages Sara's personality and voice
    - AutoModel: Processes language and generates responses
    - TtsService: Converts text responses to speech
    
    It also maintains conversation history and handles command routing.
    """
    
    def __init__(self):
        """Initialize the CoachService."""
        self._initialized = False
        self._persona_service = None
        self._tts_service = None
        logger.info("CoachService initialized")
    
    async def initialize(self):
        """
        Initialize the CoachService and its dependencies.
        
        This method should be called once at application startup.
        """
        # Get references to the other services
        from backend.app.main import persona_service, tts_service
        self._persona_service = persona_service
        self._tts_service = tts_service
        
        self._initialized = True
        logger.info("CoachService fully initialized")
    
    async def handle_request(
        self, 
        user_id: str, 
        text_input: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle a request from the user to the AI Coach.
        
        Args:
            user_id: ID of the user making the request
            text_input: Text of the user's request (transcribed from voice or typed)
            session_id: Optional session ID for continuing a conversation
            context: Optional context about the current UI state
            
        Returns:
            Sara's response as text
        """
        if not self._initialized:
            logger.warning("CoachService used before initialization")
            await self.initialize()
        
        logger.info(f"Handling coach request from user {user_id}: '{text_input}'")
        
        # Step 1: Retrieve or create a conversation session
        if not session_id:
            # Create a new conversation
            conversation_data = {
                "user_id": user_id,
                "metadata": context or {}
            }
            try:
                result = supabase.table("coach_conversations").insert(conversation_data).execute()
                session_id = result.data[0]["id"]
                logger.info(f"Created new conversation session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to create conversation: {e}")
                # Fallback to a temporary session ID if database operation fails
                session_id = str(uuid.uuid4())
        
        # Step 2: Save the user's message to the database
        user_message = {
            "conversation_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": text_input
        }
        try:
            supabase.table("coach_messages").insert(user_message).execute()
            logger.info(f"Saved user message to conversation {session_id}")
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
        
        # Step 3: Generate Sara's response using AutoModel
        try:
            # Get the active persona for this user (default to sara_default)
            persona = await self._persona_service.get_persona("sara_default")
            
            # Retrieve conversation history to provide context
            history = await self.get_conversation_history(user_id, session_id, limit=5)
            history_text = "\n".join([f"{'User' if msg['role'] == 'user' else 'Sara'}: {msg['content']}" 
                                     for msg in history])
            
            # Create a prompt that includes conversation history and the system prompt
            prompt = f"{persona['system_prompt']}\n\n"
            if history:
                prompt += f"Previous conversation:\n{history_text}\n\n"
            prompt += f"User: {text_input}\nSara:"
            
            # Process with AutoModel
            request = ProcessRequest(
                task_type=TaskType.TEXT_GENERATION,
                content=prompt,
                temperature=0.7,
                max_tokens=300
            )
            response = await AutoModel.process(request)
            
            # Extract Sara's response
            sara_response = response.content
            if isinstance(sara_response, str):
                # Clean up the response if needed
                sara_response = sara_response.strip()
            else:
                sara_response = str(sara_response)
                
            # Step 4: Generate audio for Sara's response (placeholder for now)
            audio_url = await self._tts_service.synthesize_speech(
                text=sara_response,
                voice_id=persona["voice_config"]["voice_id"]
            )
            
            # Step 5: Save Sara's response to the database
            assistant_message = {
                "conversation_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": sara_response,
                "audio_url": audio_url
            }
            try:
                supabase.table("coach_messages").insert(assistant_message).execute()
                logger.info(f"Saved assistant message to conversation {session_id}")
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")
            
            return sara_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            # Fallback response in case of error
            return "I'm sorry, I encountered an issue while processing your request. Please try again."
    
    async def get_conversation_history(
        self, 
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a user.
        
        Args:
            user_id: ID of the user
            session_id: Optional session ID to filter by
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        try:
            query = supabase.table("coach_messages").select("*").eq("user_id", user_id).order("created_at", desc=False)
            
            # Filter by conversation ID if provided
            if session_id:
                query = query.eq("conversation_id", session_id)
            
            # Limit the number of messages
            query = query.limit(limit)
            
            # Execute the query
            result = query.execute()
            
            # Return the messages
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    async def process_command(
        self,
        user_id: str,
        command: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a system command detected in the user's request.
        
        Args:
            user_id: ID of the user
            command: The command to execute (e.g., "export", "change_voice")
            params: Parameters for the command
            
        Returns:
            Result of the command execution
        """
        # Placeholder - will be implemented in Phase 4
        return {"success": False, "message": "Commands not yet implemented"}
