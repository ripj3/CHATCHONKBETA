"""
Persona Service - Manages AI Coach Personas

This module provides the PersonaService class, which is responsible for
loading, managing, and providing access to the AI coach's personas.
Each persona defines the coach's personality, tone, and voice configuration.

Author: Rip Jonesy
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from backend.app.core.config import settings

# Logger for this module
logger = logging.getLogger("chatchonk.services.persona")

class PersonaService:
    """
    Service for managing AI coach personas.
    
    This service loads persona configurations from YAML files in the
    templates/personas/ directory. Each persona defines the coach's
    personality, system prompt, and voice configuration.
    """
    
    def __init__(self):
        """Initialize the PersonaService."""
        self._personas = {}
        self._personas_dir = Path(settings.TEMPLATES_DIR) / "personas"
        self._initialized = False
        logger.info("PersonaService initialized")
    
    async def initialize(self):
        """
        Initialize the PersonaService by loading all available personas.
        
        This method should be called once at application startup.
        """
        # This is a placeholder. In the future, this will load all persona
        # YAML files from the templates/personas/ directory.
        self._initialized = True
        logger.info("PersonaService fully initialized")
    
    async def get_persona(self, persona_id: str) -> Dict[str, Any]:
        """
        Get a persona by its ID.
        
        Args:
            persona_id: ID of the persona to retrieve
            
        Returns:
            Dictionary containing the persona configuration
        """
        if not self._initialized:
            logger.warning("PersonaService used before initialization")
            await self.initialize()
        
        # This is a placeholder implementation that returns a hardcoded persona.
        # In the future, this will load the persona from a YAML file.
        if persona_id == "sara_default":
            return {
                "id": "sara_default",
                "name": "Sara",
                "tone_description": "Helpful, clear, and slightly playful.",
                "system_prompt": "You are Sara, a helpful AI coach for ChatChonk. You help users navigate the application, understand its features, and get the most out of their experience. You are friendly, concise, and focused on reducing cognitive load for the user.",
                "voice_config": {
                    "provider": "kokoro",
                    "voice_id": "af_bella",  # Default Kokoro voice
                }
            }
        else:
            logger.warning(f"Persona {persona_id} not found, using default")
            return {
                "id": "sara_default",
                "name": "Sara",
                "tone_description": "Helpful, clear, and slightly playful.",
                "system_prompt": "You are Sara, a helpful AI coach for ChatChonk. You help users navigate the application, understand its features, and get the most out of their experience. You are friendly, concise, and focused on reducing cognitive load for the user.",
                "voice_config": {
                    "provider": "kokoro",
                    "voice_id": "af_bella",  # Default Kokoro voice
                }
            }
    
    async def list_personas(self) -> List[Dict[str, Any]]:
        """
        List all available personas.
        
        Returns:
            List of persona configurations
        """
        # Placeholder - will be implemented in future phases
        return [await self.get_persona("sara_default")]
    
    async def create_persona(self, persona_config: Dict[str, Any]) -> bool:
        """
        Create a new persona.
        
        Args:
            persona_config: Configuration for the new persona
            
        Returns:
            True if the persona was created successfully, False otherwise
        """
        # Placeholder - will be implemented in future phases
        return False
    
    async def update_persona(self, persona_id: str, persona_config: Dict[str, Any]) -> bool:
        """
        Update an existing persona.
        
        Args:
            persona_id: ID of the persona to update
            persona_config: New configuration for the persona
            
        Returns:
            True if the persona was updated successfully, False otherwise
        """
        # Placeholder - will be implemented in future phases
        return False
    
    async def delete_persona(self, persona_id: str) -> bool:
        """
        Delete a persona.
        
        Args:
            persona_id: ID of the persona to delete
            
        Returns:
            True if the persona was deleted successfully, False otherwise
        """
        # Placeholder - will be implemented in future phases
        return False
