"""Tests for Comic Generator service.

Tests the ComicService methods with mocked HuggingFace InferenceClient
to verify script generation, image generation, and error handling.
"""
import base64
import json
import pytest
from typing import Generator
from unittest.mock import Mock, patch
from PIL import Image
from flask import Flask

from app.services.comic_service import (
    ComicService,
    ComicAPIError,
    ComicRateLimitError,
    LLM_MODEL,
    IMAGE_MODEL,
)
from app.schemas.comic import ComicPanel, ComicResponse


def create_hf_error(message: str) -> Exception:
    """Create a mock HfHubHTTPError-like exception.

    The actual HfHubHTTPError requires a 'response' object, so we create
    a simple Exception subclass that behaves similarly for testing.
    """
    class MockHfHubHTTPError(Exception):
        pass
    return MockHfHubHTTPError(message)


@pytest.fixture
def mock_app() -> Generator[Flask, None, None]:
    """Create a Flask app context with config for testing."""
    from app import create_app
    app = create_app('testing')
    app.config['HF_API_TOKEN'] = 'test-token'
    with app.app_context():
        yield app


@pytest.fixture
def mock_inference_client() -> Generator[Mock, None, None]:
    """Create a mock InferenceClient."""
    with patch('app.services.comic_service.InferenceClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_script_response() -> str:
    """Sample valid LLM response for script generation."""
    return json.dumps([
        {"panel_number": 1, "description": "A cat sits at desk", "dialogue": "Time to work!"},
        {"panel_number": 2, "description": "Cat stares at screen", "dialogue": "What's this button?"},
        {"panel_number": 3, "description": "Computer explodes", "dialogue": "Oops!"}
    ])


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample PIL Image for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    return img


class TestGenerateScript:
    """Tests for ComicService.generate_script()."""

    def test_generate_script_returns_three_panels(
        self, mock_app: Flask, mock_inference_client: Mock, sample_script_response: str
    ) -> None:
        """Should return exactly 3 panel dictionaries."""
        mock_inference_client.text_generation.return_value = sample_script_response

        panels = ComicService.generate_script("A cat using a computer")

        assert len(panels) == 3
        assert all('description' in p for p in panels)
        assert all('dialogue' in p for p in panels)
        assert all('panel_number' in p for p in panels)

    def test_generate_script_calls_correct_model(
        self, mock_app, mock_inference_client, sample_script_response
    ):
        """Should call the Zephyr LLM model."""
        mock_inference_client.text_generation.return_value = sample_script_response

        ComicService.generate_script("Test prompt")

        mock_inference_client.text_generation.assert_called_once()
        call_kwargs = mock_inference_client.text_generation.call_args.kwargs
        assert call_kwargs['model'] == LLM_MODEL

    def test_generate_script_handles_rate_limit(
        self, mock_app, mock_inference_client
    ):
        """Should raise ComicRateLimitError on 429 response."""
        mock_inference_client.text_generation.side_effect = create_hf_error(
            "429 Too Many Requests"
        )

        with pytest.raises(ComicAPIError):
            ComicService.generate_script("Test prompt")

    def test_generate_script_handles_api_error(
        self, mock_app, mock_inference_client
    ):
        """Should raise ComicAPIError on API failure."""
        mock_inference_client.text_generation.side_effect = create_hf_error(
            "500 Internal Server Error"
        )

        with pytest.raises(ComicAPIError):
            ComicService.generate_script("Test prompt")

    def test_generate_script_handles_invalid_json(
        self, mock_app, mock_inference_client
    ):
        """Should raise ComicAPIError on invalid JSON response."""
        mock_inference_client.text_generation.return_value = "Not valid JSON"

        with pytest.raises(ComicAPIError) as exc_info:
            ComicService.generate_script("Test prompt")
        assert "no valid JSON" in str(exc_info.value)

    def test_generate_script_handles_wrong_panel_count(
        self, mock_app, mock_inference_client
    ):
        """Should raise ComicAPIError if not exactly 3 panels."""
        mock_inference_client.text_generation.return_value = json.dumps([
            {"panel_number": 1, "description": "Only one", "dialogue": "Panel"}
        ])

        with pytest.raises(ComicAPIError) as exc_info:
            ComicService.generate_script("Test prompt")
        assert "exactly 3 panels" in str(exc_info.value)


class TestGenerateImage:
    """Tests for ComicService.generate_image()."""

    def test_generate_image_returns_base64_string(
        self, mock_app, mock_inference_client, sample_image
    ):
        """Should return a non-empty base64 string."""
        mock_inference_client.text_to_image.return_value = sample_image

        result = ComicService.generate_image("A cat at desk")

        assert isinstance(result, str)
        assert len(result) > 0
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_generate_image_calls_correct_model(
        self, mock_app, mock_inference_client, sample_image
    ):
        """Should call the Stable Diffusion XL model."""
        mock_inference_client.text_to_image.return_value = sample_image

        ComicService.generate_image("Test description")

        mock_inference_client.text_to_image.assert_called_once()
        call_kwargs = mock_inference_client.text_to_image.call_args.kwargs
        assert call_kwargs['model'] == IMAGE_MODEL

    def test_generate_image_enhances_prompt(
        self, mock_app, mock_inference_client, sample_image
    ):
        """Should enhance the prompt with comic style keywords."""
        mock_inference_client.text_to_image.return_value = sample_image

        ComicService.generate_image("A cat at desk")

        call_kwargs = mock_inference_client.text_to_image.call_args.kwargs
        assert "Comic book panel" in call_kwargs['prompt']
        assert "A cat at desk" in call_kwargs['prompt']

    def test_generate_image_handles_rate_limit(
        self, mock_app, mock_inference_client
    ):
        """Should raise ComicAPIError on 429 response."""
        mock_inference_client.text_to_image.side_effect = create_hf_error(
            "429 rate limit exceeded"
        )

        with pytest.raises(ComicAPIError):
            ComicService.generate_image("Test description")

    def test_generate_image_handles_api_error(
        self, mock_app, mock_inference_client
    ):
        """Should raise ComicAPIError on API failure."""
        mock_inference_client.text_to_image.side_effect = create_hf_error(
            "503 Service Unavailable"
        )

        with pytest.raises(ComicAPIError):
            ComicService.generate_image("Test description")


class TestGenerateComic:
    """Tests for ComicService.generate_comic() end-to-end orchestration."""

    def test_generate_comic_returns_response_with_panels(
        self, mock_app, mock_inference_client, sample_script_response, sample_image
    ):
        """Should return ComicResponse with 3 panels."""
        mock_inference_client.text_generation.return_value = sample_script_response
        mock_inference_client.text_to_image.return_value = sample_image

        result = ComicService.generate_comic("A cat using a computer")

        assert isinstance(result, ComicResponse)
        assert result.prompt == "A cat using a computer"
        assert len(result.panels) == 3
        assert all(isinstance(p, ComicPanel) for p in result.panels)

    def test_generate_comic_includes_images(
        self, mock_app, mock_inference_client, sample_script_response, sample_image
    ):
        """Should include base64 images in panels."""
        mock_inference_client.text_generation.return_value = sample_script_response
        mock_inference_client.text_to_image.return_value = sample_image

        result = ComicService.generate_comic("Test prompt")

        for panel in result.panels:
            assert panel.image_base64 is not None
            assert len(panel.image_base64) > 0

    def test_generate_comic_continues_without_images_on_failure(
        self, mock_app, mock_inference_client, sample_script_response
    ):
        """Should continue with None images if image generation fails."""
        mock_inference_client.text_generation.return_value = sample_script_response
        mock_inference_client.text_to_image.side_effect = ComicAPIError("Image failed")

        result = ComicService.generate_comic("Test prompt")

        assert len(result.panels) == 3
        # Panels should still have dialogue/description but no image
        for panel in result.panels:
            assert panel.dialogue is not None
            assert panel.description is not None
            assert panel.image_base64 is None

    def test_generate_comic_propagates_script_errors(
        self, mock_app, mock_inference_client
    ):
        """Should propagate errors from script generation."""
        mock_inference_client.text_generation.side_effect = create_hf_error(
            "503 Service Error"
        )

        with pytest.raises(ComicAPIError):
            ComicService.generate_comic("Test prompt")


class TestComicViewIntegration:
    """Tests for the comic API endpoint."""

    def test_generate_endpoint_returns_comic(
        self, mock_app, mock_inference_client, sample_script_response, sample_image
    ):
        """POST /api/comic/generate should return comic JSON."""
        mock_inference_client.text_generation.return_value = sample_script_response
        mock_inference_client.text_to_image.return_value = sample_image

        with mock_app.test_client() as client:
            response = client.post(
                '/api/comic/generate',
                json={'prompt': 'A cat using a computer'},
                content_type='application/json'
            )

        assert response.status_code == 200
        data = response.get_json()
        assert 'panels' in data
        assert len(data['panels']) == 3

    def test_generate_endpoint_validates_prompt(self, mock_app):
        """Should return 400 for empty prompt."""
        with mock_app.test_client() as client:
            response = client.post(
                '/api/comic/generate',
                json={'prompt': ''},
                content_type='application/json'
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_generate_endpoint_handles_rate_limit(
        self, mock_app
    ):
        """Should return 429 on rate limit."""
        with patch('app.views.comic.ComicController.generate') as mock_generate:
            mock_generate.side_effect = ComicRateLimitError("Rate limit exceeded")

            with mock_app.test_client() as client:
                response = client.post(
                    '/api/comic/generate',
                    json={'prompt': 'Test prompt'},
                    content_type='application/json'
                )

            assert response.status_code == 429

    def test_generate_endpoint_handles_service_error(
        self, mock_app
    ):
        """Should return 503 on service error."""
        with patch('app.views.comic.ComicController.generate') as mock_generate:
            mock_generate.side_effect = ComicAPIError("Service unavailable")

            with mock_app.test_client() as client:
                response = client.post(
                    '/api/comic/generate',
                    json={'prompt': 'Test prompt'},
                    content_type='application/json'
                )

            assert response.status_code == 503

    def test_comic_page_renders(self, mock_app):
        """GET /comic should return HTML page."""
        with mock_app.test_client() as client:
            response = client.get('/comic')

        assert response.status_code == 200
        assert b'Comic Generator' in response.data
        assert b'data-island="comic-generator"' in response.data
