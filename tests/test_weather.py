"""Tests for Weather API endpoint.

Tests the /api/weather endpoint which proxies requests to the
National Weather Service API. All external API calls are mocked
to ensure tests are fast, reliable, and don't hit real endpoints.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import requests

from app.services.weather_service import WeatherService


# Sample NWS API responses for mocking
MOCK_POINTS_RESPONSE = {
    "properties": {
        "forecast": "https://api.weather.gov/gridpoints/TOP/31,80/forecast"
    }
}

MOCK_FORECAST_RESPONSE = {
    "properties": {
        "periods": [
            {
                "name": "Today",
                "temperature": 72,
                "temperatureUnit": "F",
                "shortForecast": "Sunny",
                "icon": "https://api.weather.gov/icons/land/day/skc",
                "isDaytime": True
            },
            {
                "name": "Tonight",
                "temperature": 55,
                "temperatureUnit": "F",
                "shortForecast": "Clear",
                "icon": "https://api.weather.gov/icons/land/night/skc",
                "isDaytime": False
            },
            {
                "name": "Tomorrow",
                "temperature": 75,
                "temperatureUnit": "F",
                "shortForecast": "Partly Cloudy",
                "icon": "https://api.weather.gov/icons/land/day/sct",
                "isDaytime": True
            },
            {
                "name": "Tomorrow Night",
                "temperature": 58,
                "temperatureUnit": "F",
                "shortForecast": "Mostly Clear",
                "icon": "https://api.weather.gov/icons/land/night/few",
                "isDaytime": False
            },
            {
                "name": "Wednesday",
                "temperature": 78,
                "temperatureUnit": "F",
                "shortForecast": "Sunny",
                "icon": "https://api.weather.gov/icons/land/day/skc",
                "isDaytime": True
            }
        ]
    }
}


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear weather cache before each test."""
    WeatherService.clear_cache()
    yield
    WeatherService.clear_cache()


class TestWeatherAPI:
    """Tests for the /api/weather endpoint."""

    def test_weather_missing_params(self, client):
        """GET /api/weather without lat/lng returns 400."""
        response = client.get('/api/weather')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'lat' in data['error'].lower() or 'lng' in data['error'].lower()

    def test_weather_missing_lat(self, client):
        """GET /api/weather with only lng returns 400."""
        response = client.get('/api/weather?lng=-122.4194')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_weather_missing_lng(self, client):
        """GET /api/weather with only lat returns 400."""
        response = client.get('/api/weather?lat=37.7749')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_weather_invalid_params(self, client):
        """GET /api/weather with non-numeric params returns 400."""
        response = client.get('/api/weather?lat=abc&lng=def')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'number' in data['error'].lower()

    def test_weather_out_of_range_lat(self, client):
        """GET /api/weather with lat > 90 returns 400."""
        response = client.get('/api/weather?lat=999&lng=-122.4194')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'latitude' in data['error'].lower()

    def test_weather_out_of_range_lng(self, client):
        """GET /api/weather with lng > 180 returns 400."""
        response = client.get('/api/weather?lat=37.7749&lng=999')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'longitude' in data['error'].lower()

    @patch('app.services.weather_service.requests.get')
    def test_weather_success(self, mock_get, client):
        """GET /api/weather with valid coords returns weather data."""
        # Setup mock responses
        mock_points_response = MagicMock()
        mock_points_response.status_code = 200
        mock_points_response.json.return_value = MOCK_POINTS_RESPONSE

        mock_forecast_response = MagicMock()
        mock_forecast_response.status_code = 200
        mock_forecast_response.json.return_value = MOCK_FORECAST_RESPONSE

        mock_get.side_effect = [mock_points_response, mock_forecast_response]

        # Make request
        response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
        assert response.status_code == 200

        data = json.loads(response.data)

        # Verify response structure
        assert 'current' in data
        assert 'periods' in data

        # Verify current weather
        assert data['current']['name'] == 'Today'
        assert data['current']['temperature'] == 72
        assert data['current']['unit'] == 'F'
        assert data['current']['shortForecast'] == 'Sunny'
        assert data['current']['isDaytime'] is True

        # Verify forecast periods (excluding current)
        assert len(data['periods']) == 4
        assert data['periods'][0]['name'] == 'Tonight'

    @patch('app.services.weather_service.requests.get')
    def test_weather_upstream_failure(self, mock_get, client):
        """GET /api/weather returns 502 when NWS API fails."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
        assert response.status_code == 502
        data = json.loads(response.data)
        assert 'error' in data

    @patch('app.services.weather_service.requests.get')
    def test_weather_timeout(self, mock_get, client):
        """GET /api/weather returns 502 when NWS API times out."""
        mock_get.side_effect = requests.Timeout("Connection timed out")

        response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
        assert response.status_code == 502
        data = json.loads(response.data)
        assert 'error' in data
        assert 'timed out' in data['error'].lower()

    @patch('app.services.weather_service.requests.get')
    def test_weather_connection_error(self, mock_get, client):
        """GET /api/weather returns 502 when NWS API is unreachable."""
        mock_get.side_effect = requests.ConnectionError("Failed to connect")

        response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
        assert response.status_code == 502
        data = json.loads(response.data)
        assert 'error' in data

    @patch('app.services.weather_service.requests.get')
    def test_weather_caching(self, mock_get, client):
        """Weather data should be cached to reduce API calls."""
        mock_points_response = MagicMock()
        mock_points_response.status_code = 200
        mock_points_response.json.return_value = MOCK_POINTS_RESPONSE

        mock_forecast_response = MagicMock()
        mock_forecast_response.status_code = 200
        mock_forecast_response.json.return_value = MOCK_FORECAST_RESPONSE

        mock_get.side_effect = [mock_points_response, mock_forecast_response]

        # First request should hit the API
        response1 = client.get('/api/weather?lat=37.7749&lng=-122.4194')
        assert response1.status_code == 200
        assert mock_get.call_count == 2  # points + forecast

        # Second request should use cache
        response2 = client.get('/api/weather?lat=37.7749&lng=-122.4194')
        assert response2.status_code == 200
        assert mock_get.call_count == 2  # Still 2, not 4

        # Verify same data returned
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        assert data1 == data2


class TestWeatherService:
    """Unit tests for WeatherService class."""

    def test_validate_coordinates_valid(self):
        """Valid coordinates should not raise exception."""
        # Should not raise
        WeatherService._validate_coordinates(37.7749, -122.4194)
        WeatherService._validate_coordinates(0, 0)
        WeatherService._validate_coordinates(-90, -180)
        WeatherService._validate_coordinates(90, 180)

    def test_validate_coordinates_invalid_lat(self):
        """Invalid latitude should raise InvalidCoordinatesError."""
        from app.services.weather_service import InvalidCoordinatesError

        with pytest.raises(InvalidCoordinatesError):
            WeatherService._validate_coordinates(91, 0)

        with pytest.raises(InvalidCoordinatesError):
            WeatherService._validate_coordinates(-91, 0)

    def test_validate_coordinates_invalid_lng(self):
        """Invalid longitude should raise InvalidCoordinatesError."""
        from app.services.weather_service import InvalidCoordinatesError

        with pytest.raises(InvalidCoordinatesError):
            WeatherService._validate_coordinates(0, 181)

        with pytest.raises(InvalidCoordinatesError):
            WeatherService._validate_coordinates(0, -181)

    def test_parse_forecast(self):
        """Forecast parsing should extract correct data structure."""
        result = WeatherService._parse_forecast(MOCK_FORECAST_RESPONSE)

        assert 'current' in result
        assert 'periods' in result
        assert result['current']['name'] == 'Today'
        assert len(result['periods']) == 4  # 5 total - 1 current = 4

    @patch('app.services.weather_service.requests.get')
    def test_user_agent_header(self, mock_get):
        """Requests to NWS API should include User-Agent header."""
        mock_points_response = MagicMock()
        mock_points_response.status_code = 200
        mock_points_response.json.return_value = MOCK_POINTS_RESPONSE

        mock_forecast_response = MagicMock()
        mock_forecast_response.status_code = 200
        mock_forecast_response.json.return_value = MOCK_FORECAST_RESPONSE

        mock_get.side_effect = [mock_points_response, mock_forecast_response]

        WeatherService.get_forecast(37.7749, -122.4194)

        # Verify User-Agent header was sent
        assert mock_get.call_count == 2
        for call in mock_get.call_args_list:
            headers = call.kwargs.get('headers', {})
            assert 'User-Agent' in headers
            assert 'RalphWiggumTutorial' in headers['User-Agent']
