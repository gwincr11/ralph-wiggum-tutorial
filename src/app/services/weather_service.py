"""Weather service for National Weather Service API integration.

Provides weather forecast data by:
1. Using browser geolocation coordinates (lat/lng)
2. Calling NWS /points endpoint to get forecast URL
3. Calling forecast URL to get weather data
4. Returning simplified weather data structure

The NWS API requires a User-Agent header identifying the application.
"""
import time
from typing import TypedDict, Optional
import requests


class WeatherPeriod(TypedDict):
    """A single forecast period (e.g., 'Today', 'Tonight', 'Tuesday')."""
    name: str
    temperature: int
    unit: str
    shortForecast: str
    icon: str
    isDaytime: bool


class WeatherData(TypedDict):
    """Complete weather data with current conditions and forecast periods."""
    current: WeatherPeriod
    periods: list[WeatherPeriod]


class WeatherServiceError(Exception):
    """Base exception for weather service errors."""
    pass


class InvalidCoordinatesError(WeatherServiceError):
    """Raised when coordinates are out of valid range."""
    pass


class UpstreamAPIError(WeatherServiceError):
    """Raised when the NWS API returns an error or is unreachable."""
    pass


# Simple in-memory cache with TTL
_cache: dict[str, tuple[float, WeatherData]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


class WeatherService:
    """Service for fetching weather forecasts from the National Weather Service API.

    Uses a backend proxy pattern because:
    - NWS API requires a custom User-Agent header (blocked by browsers for security)
    - Enables caching to respect NWS rate limits
    - Centralizes error handling
    """

    USER_AGENT = '(RalphWiggumTutorial, tutorial@example.com)'
    NWS_BASE_URL = 'https://api.weather.gov'
    REQUEST_TIMEOUT = 5  # seconds

    @classmethod
    def get_forecast(cls, lat: float, lng: float) -> WeatherData:
        """Get weather forecast for the given coordinates.

        Args:
            lat: Latitude (-90 to 90)
            lng: Longitude (-180 to 180)

        Returns:
            WeatherData with current conditions and forecast periods

        Raises:
            InvalidCoordinatesError: If lat/lng are out of valid range
            UpstreamAPIError: If NWS API fails or times out
        """
        cls._validate_coordinates(lat, lng)

        cache_key = f"{lat:.4f},{lng:.4f}"
        cached = cls._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            forecast_data = cls._fetch_forecast(lat, lng)
            cls._set_cache(cache_key, forecast_data)
            return forecast_data
        except requests.Timeout:
            raise UpstreamAPIError("Weather service timed out")
        except requests.RequestException as e:
            raise UpstreamAPIError(f"Weather service unavailable: {str(e)}")

    @classmethod
    def _validate_coordinates(cls, lat: float, lng: float) -> None:
        """Validate that coordinates are within valid ranges."""
        if not (-90 <= lat <= 90):
            raise InvalidCoordinatesError(
                f"Latitude must be between -90 and 90, got {lat}"
            )
        if not (-180 <= lng <= 180):
            raise InvalidCoordinatesError(
                f"Longitude must be between -180 and 180, got {lng}"
            )

    @classmethod
    def _fetch_forecast(cls, lat: float, lng: float) -> WeatherData:
        """Fetch forecast from NWS API."""
        headers = {'User-Agent': cls.USER_AGENT}

        # Step 1: Get the forecast URL from /points endpoint
        points_url = f"{cls.NWS_BASE_URL}/points/{lat},{lng}"
        points_response = requests.get(
            points_url,
            headers=headers,
            timeout=cls.REQUEST_TIMEOUT
        )

        if points_response.status_code != 200:
            raise UpstreamAPIError(
                f"NWS points API returned {points_response.status_code}"
            )

        points_data = points_response.json()
        forecast_url = points_data.get('properties', {}).get('forecast')

        if not forecast_url:
            raise UpstreamAPIError("No forecast URL in NWS response")

        # Step 2: Get the actual forecast data
        forecast_response = requests.get(
            forecast_url,
            headers=headers,
            timeout=cls.REQUEST_TIMEOUT
        )

        if forecast_response.status_code != 200:
            raise UpstreamAPIError(
                f"NWS forecast API returned {forecast_response.status_code}"
            )

        forecast_data = forecast_response.json()
        return cls._parse_forecast(forecast_data)

    @classmethod
    def _parse_forecast(cls, data: dict) -> WeatherData:  # type: ignore[type-arg]
        """Parse NWS forecast response into simplified structure."""
        periods_raw = data.get('properties', {}).get('periods', [])

        if not periods_raw:
            raise UpstreamAPIError("No forecast periods in NWS response")

        periods: list[WeatherPeriod] = []
        for p in periods_raw[:14]:  # Limit to ~7 days (14 periods)
            periods.append({
                'name': p.get('name', ''),
                'temperature': p.get('temperature', 0),
                'unit': p.get('temperatureUnit', 'F'),
                'shortForecast': p.get('shortForecast', ''),
                'icon': p.get('icon', ''),
                'isDaytime': p.get('isDaytime', True),
            })

        return {
            'current': periods[0],
            'periods': periods[1:],  # Rest of the periods after current
        }

    @classmethod
    def _get_from_cache(cls, key: str) -> Optional[WeatherData]:
        """Get value from cache if not expired."""
        if key in _cache:
            timestamp, data = _cache[key]
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                return data
            del _cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, data: WeatherData) -> None:
        """Store value in cache with current timestamp."""
        _cache[key] = (time.time(), data)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the entire cache. Useful for testing."""
        _cache.clear()
