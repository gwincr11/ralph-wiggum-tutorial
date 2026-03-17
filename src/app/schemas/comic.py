"""Pydantic schemas for Comic generation.

Defines request validation and response serialization schemas
for the Comic Generator API endpoints.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class ComicGenerateRequest(BaseModel):
    """Schema for requesting comic generation.

    Validates incoming request data for POST /api/comic/generate.
    """
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="A funny situation or story idea for the comic"
    )


class ComicPanel(BaseModel):
    """Schema for a single comic panel.

    Each panel has a description, dialogue, and optionally a base64 image.
    """
    panel_number: int = Field(..., ge=1, le=6, description="Panel number (1-6)")
    description: str = Field(..., description="Visual description of the panel")
    dialogue: str = Field(..., description="Character dialogue or caption")
    image_base64: Optional[str] = Field(None, description="Base64-encoded panel image")

    model_config = ConfigDict(from_attributes=True)


class ComicResponse(BaseModel):
    """Schema for comic generation response.

    Contains the original prompt, generated panels, and timestamp.
    """
    prompt: str = Field(..., description="Original user prompt")
    panels: list[ComicPanel] = Field(..., description="List of generated comic panels")
    created_at: datetime = Field(default_factory=_utc_now, description="Generation timestamp")

    model_config = ConfigDict(from_attributes=True)
