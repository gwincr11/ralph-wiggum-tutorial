"""Weather views (routes).

Provides a JSON API endpoint for weather data that proxies requests
to the National Weather Service API. This proxy is necessary because
NWS requires a custom User-Agent header which browsers block.
"""
from flask import Blueprint, jsonify, request
from ..services import WeatherService
from ..services.weather_service import WeatherValidationError, WeatherAPIError

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/api/weather', methods=['GET'])
def api_weather():  # type: ignore[no-untyped-def]
    """Get weather forecast for a location.

    Query parameters:
        lat: Latitude (-90 to 90)
        lng: Longitude (-180 to 180)

    Returns:
        200: Weather forecast data with current conditions and 5-day forecast
        400: Missing or invalid parameters
        502: Upstream NWS API failure
    """
    # Validate required parameters
    lat_str = request.args.get('lat')
    lng_str = request.args.get('lng')

    if not lat_str or not lng_str:
        return jsonify(error="Missing required parameters: lat and lng"), 400

    # Parse coordinates
    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except ValueError:
        return jsonify(error="Invalid coordinates: lat and lng must be numbers"), 400

    # Fetch weather data
    try:
        forecast = WeatherService.get_forecast(lat, lng)
        return jsonify(forecast)
    except WeatherValidationError as e:
        return jsonify(error=str(e)), 400
    except WeatherAPIError as e:
        return jsonify(error=str(e)), 502
