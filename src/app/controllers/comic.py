"""Comic controller with business logic.

Encapsulates comic generation logic for the view layer.
Views call controller methods rather than services directly.
"""
from ..schemas.comic import ComicGenerateRequest, ComicResponse
from ..services.comic_service import ComicService


class ComicController:
    """Controller for Comic generation operations."""

    @staticmethod
    def generate(data: ComicGenerateRequest) -> ComicResponse:
        """Generate a comic strip from a user prompt.

        Args:
            data: Validated ComicGenerateRequest with prompt

        Returns:
            ComicResponse with generated panels

        Raises:
            ComicServiceError: If generation fails
        """
        return ComicService.generate_comic(data.prompt)
