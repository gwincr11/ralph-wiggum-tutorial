"""Comic generation service using Hugging Face APIs.

Provides methods to generate comic scripts and images using:
- HuggingFaceH4/zephyr-7b-beta for script/dialogue generation
- stabilityai/stable-diffusion-xl-base-1.0 for panel image generation
"""
import base64
import json
import logging
import re
from typing import Any
from flask import current_app
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from ..schemas.comic import ComicPanel, ComicResponse

logger = logging.getLogger(__name__)

# Model identifiers
LLM_MODEL = "HuggingFaceH4/zephyr-7b-beta"
IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"


class ComicServiceError(Exception):
    """Base exception for comic service errors."""
    pass


class ComicAPIError(ComicServiceError):
    """Raised when Hugging Face API call fails."""
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


class ComicRateLimitError(ComicServiceError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str = "API rate limit exceeded"):
        super().__init__(message)
        self.status_code = 429


class ComicService:
    """Service for generating comic strips using Hugging Face APIs."""

    @staticmethod
    def _get_client() -> InferenceClient:
        """Get configured InferenceClient with API token."""
        token = current_app.config.get('HF_API_TOKEN')
        return InferenceClient(token=token)

    @staticmethod
    def generate_script(prompt: str) -> list[dict[str, Any]]:
        """Generate a 3-panel comic script from a user prompt.

        Uses the Zephyr-7b-beta LLM to generate panel descriptions and dialogue.

        Args:
            prompt: User's story idea or funny situation

        Returns:
            List of 3 panel dictionaries with 'description' and 'dialogue' keys

        Raises:
            ComicAPIError: If the LLM API call fails
            ComicRateLimitError: If rate limited
        """
        client = ComicService._get_client()

        system_prompt = """You are a comic strip writer. Given a funny situation or story idea,
create a 3-panel comic strip script. Return ONLY valid JSON array with exactly 3 objects.
Each object must have:
- "panel_number": integer 1, 2, or 3
- "description": brief visual description of the scene (max 100 chars)
- "dialogue": character speech or caption (max 150 chars)

Example format:
[
  {"panel_number": 1, "description": "A cat sits at a computer", "dialogue": "Time to check my emails!"},
  {"panel_number": 2, "description": "Cat stares at screen intensely", "dialogue": "Wait... what's this?"},
  {"panel_number": 3, "description": "Cat knocks computer off desk", "dialogue": "Nevermind!"}
]"""

        user_message = f"Create a 3-panel comic about: {prompt}"

        try:
            response = client.text_generation(
                prompt=f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_message}</s>\n<|assistant|>\n",
                model=LLM_MODEL,
                max_new_tokens=500,
                temperature=0.7,
                do_sample=True,
            )

            # Parse JSON from response
            panels = ComicService._parse_script_response(response)
            logger.info(f"Generated script with {len(panels)} panels for prompt: {prompt[:50]}...")
            return panels

        except HfHubHTTPError as e:
            logger.error(f"HF API error during script generation: {e}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise ComicRateLimitError()
            raise ComicAPIError(f"Failed to generate comic script: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during script generation: {e}")
            raise ComicAPIError(f"Script generation failed: {str(e)}")

    @staticmethod
    def _parse_script_response(response: str) -> list[dict[str, Any]]:
        """Parse LLM response to extract panel JSON.

        Args:
            response: Raw LLM text response

        Returns:
            List of panel dictionaries

        Raises:
            ComicAPIError: If parsing fails
        """
        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            logger.error(f"No JSON array found in response: {response[:200]}")
            raise ComicAPIError("Failed to parse comic script - no valid JSON found")

        try:
            panels = json.loads(json_match.group())
            if not isinstance(panels, list) or len(panels) != 3:
                raise ComicAPIError("Script must contain exactly 3 panels")

            # Validate panel structure
            for i, panel in enumerate(panels):
                if 'description' not in panel or 'dialogue' not in panel:
                    raise ComicAPIError(f"Panel {i + 1} missing required fields")
                panel['panel_number'] = i + 1  # Ensure correct numbering

            return panels
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response[:200]}")
            raise ComicAPIError("Failed to parse comic script JSON")

    @staticmethod
    def generate_image(description: str) -> str:
        """Generate a comic panel image from a description.

        Uses Stable Diffusion XL to create a panel image.

        Args:
            description: Visual description of the panel

        Returns:
            Base64-encoded PNG image string

        Raises:
            ComicAPIError: If image generation fails
            ComicRateLimitError: If rate limited
        """
        client = ComicService._get_client()

        # Enhance prompt for comic style
        enhanced_prompt = (
            f"Comic book panel illustration, cartoon style, vibrant colors, "
            f"clear lines, simple background: {description}"
        )

        try:
            image = client.text_to_image(
                prompt=enhanced_prompt,
                model=IMAGE_MODEL,
                num_inference_steps=30,
            )

            # Convert PIL Image to base64
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info(f"Generated image for: {description[:50]}...")
            return image_base64

        except HfHubHTTPError as e:
            logger.error(f"HF API error during image generation: {e}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise ComicRateLimitError()
            raise ComicAPIError(f"Failed to generate panel image: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during image generation: {e}")
            raise ComicAPIError(f"Image generation failed: {str(e)}")

    @staticmethod
    def generate_comic(prompt: str) -> ComicResponse:
        """Generate a complete 3-panel comic strip.

        Orchestrates script generation followed by image generation for each panel.

        Args:
            prompt: User's story idea or funny situation

        Returns:
            ComicResponse with panels containing descriptions, dialogue, and images

        Raises:
            ComicAPIError: If any generation step fails
            ComicRateLimitError: If rate limited
        """
        logger.info(f"Starting comic generation for prompt: {prompt[:50]}...")

        # Step 1: Generate script
        script_panels = ComicService.generate_script(prompt)

        # Step 2: Generate images for each panel
        comic_panels = []
        for panel_data in script_panels:
            try:
                image_base64 = ComicService.generate_image(panel_data['description'])
            except ComicServiceError:
                # If image generation fails, continue without image
                panel_num = panel_data['panel_number']
                logger.warning(f"Image generation failed for panel {panel_num}, continuing without image")
                image_base64 = None

            comic_panel = ComicPanel(
                panel_number=panel_data['panel_number'],
                description=panel_data['description'],
                dialogue=panel_data['dialogue'],
                image_base64=image_base64
            )
            comic_panels.append(comic_panel)

        logger.info(f"Comic generation complete: {len(comic_panels)} panels")
        return ComicResponse(prompt=prompt, panels=comic_panels)
