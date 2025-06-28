"""
TTS Service - Text-to-Speech Conversion using Kokoro

This module provides the TtsService class, which is responsible for
converting text to speech using the Kokoro TTS service. It supports
streaming audio for minimal perceived latency.

Author: Rip Jonesy
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, AsyncGenerator, BinaryIO

import aiohttp
import aiofiles
from fastapi.responses import StreamingResponse

from backend.app.core.config import settings

# Logger for this module
logger = logging.getLogger("chatchonk.services.tts")

class TtsService:
    """
    Service for text-to-speech conversion using Kokoro.
    
    This service connects to a Kokoro-FastAPI instance to convert text to speech.
    It supports streaming audio chunks for minimal perceived latency.
    """
    
    def __init__(self):
        """Initialize the TtsService."""
        self._initialized = False
        self._kokoro_base_url = os.environ.get("KOKORO_TTS_BASE_URL", "http://localhost:8880")
        self._audio_output_dir = Path(settings.TEMP_DIR) / "audio"
        self._audio_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("TtsService initialized")
    
    async def initialize(self):
        """
        Initialize the TtsService.
        
        This method should be called once at application startup.
        """
        # Check if the Kokoro service is available
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self._kokoro_base_url}/health") as response:
                    if response.status == 200:
                        logger.info(f"Kokoro TTS service is available at {self._kokoro_base_url}")
                    else:
                        logger.warning(f"Kokoro TTS service health check failed: {response.status}")
        except Exception as e:
            logger.error(f"Failed to connect to Kokoro TTS service: {str(e)}")
        
        self._initialized = True
        logger.info("TtsService fully initialized")
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice_id: str = "af_bella",
        streaming: bool = False
    ) -> str:
        """
        Convert text to speech.
        
        This is a placeholder implementation that will be expanded in future phases.
        In the full implementation, this will connect to the Kokoro TTS service.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            streaming: Whether to return a streaming response
            
        Returns:
            Path to the generated audio file
        """
        if not self._initialized:
            logger.warning("TtsService used before initialization")
            await self.initialize()
        
        logger.info(f"Synthesizing speech for text: '{text[:50]}...' with voice: {voice_id}")
        
        # This is a placeholder. In the future, this will call the Kokoro TTS service.
        # For now, we'll just return a placeholder path.
        audio_path = self._audio_output_dir / f"{uuid.uuid4()}.mp3"
        
        return str(audio_path)
    
    async def stream_speech(
        self, 
        text: str, 
        voice_id: str = "af_bella"
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks from text.
        
        This method will be implemented in Phase 3 to provide streaming audio
        directly from the Kokoro TTS service to minimize perceived latency.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            
        Yields:
            Audio data chunks
        """
        if not self._initialized:
            logger.warning("TtsService used before initialization")
            await self.initialize()
        
        logger.info(f"Streaming speech for text: '{text[:50]}...' with voice: {voice_id}")
        
        endpoint = f"{self._kokoro_base_url}/v1/audio/speech"

        # Payload expected by Kokoro-FastAPI
        payload = {
            "text": text,
            "voice_id": voice_id,
            # We explicitly ask for streaming so Kokoro starts sending
            # audio chunks as soon as they are generated.
            "stream": True,
            # Default settings – feel free to tune / expose via params later
            "format": "mp3",
        }

        headers = {
            "Content-Type": "application/json",
            # Let the server know we can accept a stream of bytes
            "Accept": "application/octet-stream",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        # Log and stop streaming if Kokoro returned an error
                        error_msg = await resp.text()
                        logger.error(
                            "Kokoro TTS error %s: %s", resp.status, error_msg[:200]
                        )
                        return

                    # Stream the response in manageable chunks
                    async for chunk in resp.content.iter_chunked(4096):
                        if chunk:
                            yield chunk
        except aiohttp.ClientError as e:
            logger.error("Failed to stream from Kokoro TTS: %s", str(e))
            return
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get a list of available voices from the Kokoro TTS service.
        
        Returns:
            Dictionary containing available voices
        """
        if not self._initialized:
            logger.warning("TtsService used before initialization")
            await self.initialize()
        
        # This is a placeholder. In the future, this will call the Kokoro TTS service.
        return {
            "voices": [
                {"id": "af_bella", "name": "Bella"},
                {"id": "af_sky", "name": "Sky"},
                {"id": "af_heart", "name": "Heart"}
            ]
        }
