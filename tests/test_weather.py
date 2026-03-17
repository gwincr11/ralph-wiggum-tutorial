"""Tests for Weather API routes.

Tests the /api/weather endpoint which proxies requests to the NWS API.
All NWS API calls are mocked to avoid external dependencies in tests.
"""
import json
from unittest.mock import patch, MagicMock

import requests


class TestWeatherAPI:
    """Tests for the Weather JSON API."""

    def test_weather_missing_params(self, client):
        """GET /api/weather without lat/lng should return 400."""
        response = client.get('/api/weather')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'lat' in data['error'].lower() or 'lng' in data['error'].lower()

    def test_weather_missing_lat(self, client):
        """GET /api/weather with only lng should return 400."""
        response = client.get('/api/weather?lng=-122.4194')
        assert response.status_code == 400

    def test_weather_missing_lng(self, client):
        """GET /api/weather with only lat should return 400."""
        response = client.get('/api/weather?lat=37.7749')
        assert response.status_code == 400

    def test_weather_invalid_params(self, client):
        """GET /api/weather with non-numeric params should return 400."""
        response = client.get('/api/weather?lat=abc&lng=def')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_weather_out_of_range_lat(self, client):
        """GET /api/weather with lat > 90 should return 400."""
        response = client.get('/api/weather?lat=999&lng=-122.4194')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Latitude' in data['error']

    def test_weather_out_of_range_lng(self, client):
        """GET /api/weather with lng > 180 should return 400."""
        response = client.get('/api/weather?lat=37.7749&lng=999')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Longitude' in data['error']

    def test_weather_success(self, client):
        """GET /api/weather with valid params should return forecast data."""
        # Mock NWS API responses
        mock_points_response = MagicMock()
        mock_points_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/MTR/84,105/forecast'
            }
        }
        mock_points_response.raise_for_status = MagicMock()

        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
            'properties': {
                'periods': [
                    {
                        'name': 'Today',
                        'temperature': 72,
                        'temperatureUnit': 'F',
                        'shortForecast': 'Sunny',
                        'icon': 'https://api.weather.gov/icons/land/day/few',
                        'isDaytime': True
                    },
                    {
                        'name': 'Tonight',
                        'temperature': 55,
                        'temperatureUnit': 'F',
                        'shortForecast': 'Clear',
                        'icon': 'https://api.weather.gov/icons/land/night/few',
                        'isDaytime': False
                    },
                    {
                        'name': 'Tuesday',
                        'temperature': 75,
                        'temperatureUnit': 'F',
                        'shortForecast': 'Mostly Sunny',
                        'icon': 'https://api.weather.gov/icons/land/day/sct',
                        'isDaytime': True
                    }
                ]
            }
        }
        mock_forecast_response.raise_for_status = MagicMock()

        with patch('app.services.weather_service.requests.get') as mock_get:
            mock_get.side_effect = [mock_points_response, mock_forecast_response]

            response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert 'current' in data
            assert 'periods' in data

            # Verify current conditions
            current = data['current']
            assert current['name'] == 'Today'
            assert current['temperature'] == 72
            assert current['unit'] == 'F'
            assert current['shortForecast'] == 'Sunny'
            assert current['isDaytime'] is True

            # Verify forecast periods
            assert len(data['periods']) >= 1

    def test_weather_upstream_failure(self, client):
        """GET /api/weather should return 502 when NWS API fails."""
        with patch('app.services.weather_service.requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection failed")

            response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
            assert response.status_code == 502
            data = json.loads(response.data)
            assert 'error' in data

    def test_weather_timeout(self, client):
        """GET /api/weather should return 502 when NWS API times out."""
        with patch('app.services.weather_service.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")

            response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
            assert response.status_code == 502
            data = json.loads(response.data)
            assert 'error' in data
            assert 'timeout' in data['error'].lower()

    def test_weather_no_forecast_url(self, client):
        """GET /api/weather should return 502 when NWS returns no forecast URL."""
        mock_points_response = MagicMock()
        mock_points_response.json.return_value = {
            'properties': {}  # No forecast URL
        }
        mock_points_response.raise_for_status = MagicMock()

        with patch('app.services.weather_service.requests.get') as mock_get:
            mock_get.return_value = mock_points_response

            response = client.get('/api/weather?lat=37.7749&lng=-122.4194')
            assert response.status_code == 502

    def test_weather_caching(self, client):
        """Repeated requests should use cached data."""
        mock_points_response = MagicMock()
        mock_points_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/MTR/84,105/forecast'
            }
        }
        mock_points_response.raise_for_status = MagicMock()

        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
            'properties': {
                'periods': [
                    {
                        'name': 'Today',
                        'temperature': 72,
                        'temperatureUnit': 'F',
                        'shortForecast': 'Sunny',
                        'icon': 'https://api.weather.gov/icons/land/day/few',
                        'isDaytime': True
                    }
                ]
            }
        }
        mock_forecast_response.raise_for_status = MagicMock()

        with patch('app.services.weather_service.requests.get') as mock_get:
            mock_get.side_effect = [mock_points_response, mock_forecast_response]

            # First request
            response1 = client.get('/api/weather?lat=40.7128&lng=-74.0060')
            assert response1.status_code == 200

            # Second request should use cache (no new API calls)
            response2 = client.get('/api/weather?lat=40.7128&lng=-74.0060')
            assert response2.status_code == 200

            # Should only have made 2 calls (points + forecast) for both requests
            assert mock_get.call_count == 2
