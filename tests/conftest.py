"""Pytest configuration and fixtures.

Provides test fixtures for the Flask application including:
- Test app with testing configuration
- Test client for making HTTP requests
- Database setup/teardown per test
"""
import pytest
from app import create_app
from app.models import db


@pytest.fixture
def app():
    """Create application configured for testing.

    Uses SQLite in-memory database for fast, isolated tests.
    Yields the app within application context.
    """
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client for making HTTP requests.

    Use this fixture to test routes without running a server.
    """
    # Clear weather cache before each test
    from app.services import weather_service
    weather_service._cache.clear()

    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner for testing Flask commands."""
    return app.test_cli_runner()
