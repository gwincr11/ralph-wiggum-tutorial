"""Weather views (routes).

Provides a backend proxy API endpoint for weather data.
The frontend calls this API with lat/lng coordinates,
and the backend fetches data from the National Weather Service API.

This proxy is necessary because:
- NWS API requires a custom User-Agent header
- Browsers block custom headers on cross-origin requests
- Enables server-side caching and error handling
"""
from flask import Blueprint, jsonify, request
from ..services import WeatherService
from ..services.weather_service import (
    InvalidCoordinatesError,
    UpstreamAPIError
)

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/api/weather', methods=['GET'])
def get_weather():  # type: ignore[no-untyped-def]
    """Get weather forecast for the given coordinates.

    Query Parameters:
        lat: Latitude (-90 to 90)
        lng: Longitude (-180 to 180)

    Returns:
        200: Weather data with current conditions and forecast
        400: Invalid or missing parameters
        502: Upstream NWS API error
    """
    lat_str = request.args.get('lat')
    lng_str = request.args.get('lng')

    # Validate presence of required parameters
    if lat_str is None or lng_str is None:
        return jsonify(error="Missing required parameters: lat and lng"), 400

    # Validate parameters are numeric
    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except ValueError:
        return jsonify(
            error="Invalid parameters: lat and lng must be numbers"
        ), 400

    # Fetch weather data from service
    try:
        weather_data = WeatherService.get_forecast(lat, lng)
        return jsonify(weather_data)
    except InvalidCoordinatesError as e:
        return jsonify(error=str(e)), 400
    except UpstreamAPIError as e:
        return jsonify(error=str(e)), 502
