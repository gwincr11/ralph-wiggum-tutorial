"""Comic views (routes).

Provides HTML page rendering and JSON API endpoints for Comic generation.
Demonstrates the React Islands pattern where Flask serves HTML with
data-island mount points that React hydrates on the client.
"""
import logging
from flask import Blueprint, render_template, jsonify, request
from pydantic import ValidationError

from ..controllers.comic import ComicController
from ..schemas.comic import ComicGenerateRequest
from ..services.comic_service import (
    ComicServiceError,
    ComicAPIError,
    ComicRateLimitError
)

logger = logging.getLogger(__name__)

comic_bp = Blueprint('comic', __name__)


@comic_bp.route('/comic')
def index():  # type: ignore[no-untyped-def]
    """Render the comic generator page with React island mount point.

    Serves HTML that includes a [data-island="comic-generator"] element
    which the frontend JavaScript will hydrate with React.
    """
    return render_template('comic/index.html')


@comic_bp.route('/api/comic/generate', methods=['POST'])
def api_generate():  # type: ignore[no-untyped-def]
    """Generate a comic strip from a user prompt.

    Request body:
        {"prompt": "Your funny situation or story idea"}

    Returns:
        200: ComicResponse with panels containing images and dialogue
        400: Validation error (empty/invalid prompt)
        429: Rate limit exceeded
        503: API service unavailable
    """
    # Validate request data
    try:
        data = ComicGenerateRequest.model_validate(request.json)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify(error="Validation Error", details=e.errors()), 400

    # Generate comic
    try:
        comic = ComicController.generate(data)
        return jsonify(comic.model_dump(mode='json'))
    except ComicRateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        return jsonify(error="Rate Limit Exceeded", message=str(e)), 429
    except ComicAPIError as e:
        logger.error(f"API error: {e}")
        return jsonify(error="Service Error", message=str(e)), e.status_code
    except ComicServiceError as e:
        logger.error(f"Service error: {e}")
        return jsonify(error="Service Error", message=str(e)), 503
    except Exception as e:
        logger.exception(f"Unexpected error during comic generation: {e}")
        return jsonify(error="Internal Error", message="An unexpected error occurred"), 500
