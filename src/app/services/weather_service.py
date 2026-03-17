"""Weather service for NWS API integration.

Handles communication with the National Weather Service API to fetch
weather forecasts. Uses a backend proxy pattern because NWS requires
a custom User-Agent header which browsers block for security reasons.
"""
import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# NWS API requires User-Agent identification
NWS_USER_AGENT = '(RalphWiggumTutorial, tutorial@example.com)'
NWS_API_BASE = 'https://api.weather.gov'
REQUEST_TIMEOUT = 5  # seconds

# Simple in-memory cache with TTL to respect NWS rate limits
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL = 300  # 5 minutes


class WeatherServiceError(Exception):
    """Base exception for weather service errors."""
    pass


class WeatherValidationError(WeatherServiceError):
    """Raised when coordinates are invalid."""
    pass


class WeatherAPIError(WeatherServiceError):
    """Raised when NWS API returns an error."""
    pass


class WeatherService:
    """Service for fetching weather data from NWS API."""

    @staticmethod
    def _get_cached(key: str) -> dict[str, Any] | None:
        """Get cached value if not expired."""
        if key in _cache:
            timestamp, data = _cache[key]
            if time.time() - timestamp < CACHE_TTL:
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                del _cache[key]
        return None

    @staticmethod
    def _set_cache(key: str, data: dict[str, Any]) -> None:
        """Store value in cache with timestamp."""
        _cache[key] = (time.time(), data)

    @staticmethod
    def _make_request(url: str) -> dict[str, Any]:
        """Make a request to the NWS API with proper headers.

        Args:
            url: Full URL to request

        Returns:
            JSON response as dict

        Raises:
            WeatherAPIError: If request fails or returns non-200
        """
        headers = {'User-Agent': NWS_USER_AGENT, 'Accept': 'application/json'}
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.Timeout as e:
            logger.error(f"NWS API timeout: {url}")
            raise WeatherAPIError(f"Weather service timeout: {e}") from e
        except requests.RequestException as e:
            logger.error(f"NWS API error: {e}")
            raise WeatherAPIError(f"Weather service error: {e}") from e

    @staticmethod
    def validate_coordinates(lat: float, lng: float) -> None:
        """Validate latitude and longitude ranges.

        Args:
            lat: Latitude (-90 to 90)
            lng: Longitude (-180 to 180)

        Raises:
            WeatherValidationError: If coordinates are out of range
        """
        if not -90 <= lat <= 90:
            raise WeatherValidationError(f"Latitude must be between -90 and 90, got {lat}")
        if not -180 <= lng <= 180:
            raise WeatherValidationError(f"Longitude must be between -180 and 180, got {lng}")

    @classmethod
    def get_forecast(cls, lat: float, lng: float) -> dict[str, Any]:
        """Fetch weather forecast for a location.

        Uses the NWS API two-step process:
        1. GET /points/{lat},{lng} to get the forecast URL
        2. GET the forecast URL to get actual weather data

        Args:
            lat: Latitude of location
            lng: Longitude of location

        Returns:
            Simplified weather data structure:
            {
                'current': {
                    'name': str,
                    'temperature': int,
                    'unit': str,
                    'shortForecast': str,
                    'icon': str,
                    'isDaytime': bool
                },
                'periods': [...]  # Next 5 periods for forecast strip
            }

        Raises:
            WeatherValidationError: If coordinates are invalid
            WeatherAPIError: If NWS API fails
        """
        cls.validate_coordinates(lat, lng)

        # Check cache first
        cache_key = f"{lat:.4f},{lng:.4f}"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached

        # Step 1: Get the forecast URL from points endpoint
        # Round to 4 decimal places (NWS requirement)
        points_url = f"{NWS_API_BASE}/points/{lat:.4f},{lng:.4f}"
        logger.info(f"Fetching NWS points: {points_url}")

        points_data = cls._make_request(points_url)

        forecast_url = points_data.get('properties', {}).get('forecast')
        if not forecast_url:
            raise WeatherAPIError("No forecast URL in NWS response")

        # Step 2: Get the forecast data
        logger.info(f"Fetching NWS forecast: {forecast_url}")
        forecast_data = cls._make_request(forecast_url)

        # Parse and simplify the response
        periods = forecast_data.get('properties', {}).get('periods', [])
        if not periods:
            raise WeatherAPIError("No forecast periods in NWS response")

        # Build simplified response
        result = {
            'current': cls._simplify_period(periods[0]),
            'periods': [cls._simplify_period(p) for p in periods[1:6]]  # Next 5 periods
        }

        # Cache the result
        cls._set_cache(cache_key, result)

        return result

    @staticmethod
    def _simplify_period(period: dict[str, Any]) -> dict[str, Any]:
        """Convert NWS period to simplified structure.

        Args:
            period: NWS forecast period object

        Returns:
            Simplified period dict
        """
        return {
            'name': period.get('name', ''),
            'temperature': period.get('temperature', 0),
            'unit': period.get('temperatureUnit', 'F'),
            'shortForecast': period.get('shortForecast', ''),
            'icon': period.get('icon', ''),
            'isDaytime': period.get('isDaytime', True)
        }
