"""Vision Solver Agent - Simplified version.

Provides a VisionParser for analyzing math problem images using a vision-capable LLM.
"""

import json
import logging
import re
from typing import Any, AsyncGenerator

from app.config import get_settings
from app.llm.openai_compatible import OpenAICompatibleClient
from app.agents.multimodal import format_vision_message

logger = logging.getLogger(__name__)


class VisionParser:
    """Agent for analyzing math problem images."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """Initialize the Vision Parser.

        Args:
            api_key: API key for LLM provider
            base_url: Base URL for LLM API
        """
        self.settings = get_settings()
        self.client = OpenAICompatibleClient(self.settings)
        self.api_key = api_key

    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks."""
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, response)
        
        if matches:
            json_str = matches[0]
        else:
            json_str = response

        # Remove JSON comments
        json_str = re.sub(r"//.*?$", "", json_str, flags=re.MULTILINE)
        json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try fixing common issues
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # Remove trailing commas
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"JSON parsing failed, response: {response[:500]}...")
                return {}

    async def parse_image(
        self,
        base64_img: str,
        text_prompt: str,
        model: str = "deepseek-v4-pro"
    ) -> dict[str, Any]:
        """Parse an image and text prompt, returning a structured JSON output.
        
        Args:
            base64_img: Base64 encoded image string (with or without data: prefix)
            text_prompt: Prompt for the vision model
            model: Model name to use
            
        Returns:
            Dictionary extracted from JSON output
        """
        message = format_vision_message(
            prompt=text_prompt,
            base64_image=base64_img,
            provider="openai"
        )
        
        response = await self.client.chat_completion(
            messages=[message],  # type: ignore
            api_key=self.api_key,
            model=model
        )
        
        if not response:
            return {}
            
        return self._extract_json_from_response(response)

    async def stream_parse_image(
        self,
        base64_img: str,
        text_prompt: str,
        model: str = "deepseek-v4-pro"
    ) -> AsyncGenerator[str, None]:
        """Stream the parsing analysis for an image and text prompt.
        
        Args:
            base64_img: Base64 encoded image string (with or without data: prefix)
            text_prompt: Prompt for the vision model
            model: Model name to use
            
        Yields:
            Response text chunks
        """
        message = format_vision_message(
            prompt=text_prompt,
            base64_image=base64_img,
            provider="openai"
        )
        
        async for chunk in self.client.stream(
            messages=[message],  # type: ignore
            api_key=self.api_key,
            model=model
        ):
            yield chunk
