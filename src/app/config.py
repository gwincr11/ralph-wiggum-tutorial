"""Application configuration classes.

Configuration is loaded from environment variables with sensible defaults.
Each environment (development, testing, production) has its own class.
"""
import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Base configuration with shared settings."""

    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Vite dev server URL for template asset loading
    VITE_DEV_SERVER = os.environ.get('VITE_DEV_SERVER', 'http://localhost:5173')

    # Hugging Face API token for comic generation
    HF_API_TOKEN = os.environ.get('HF_API_TOKEN')


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/app'
    )
    # In development, load assets from Vite dev server
    VITE_DEV_MODE = True


class TestingConfig(Config):
    """Testing configuration with in-memory database."""

    TESTING = True
    DEBUG = True
    # Use SQLite in-memory for fast tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    VITE_DEV_MODE = False
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration with strict security settings."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # In production, load assets from built manifest
    VITE_DEV_MODE = False

    # Ensure critical settings are configured
    @classmethod
    def init_app(cls, app):  # type: ignore[no-untyped-def]
        """Production-specific initialization."""
        if not os.environ.get('FLASK_SECRET_KEY'):
            raise ValueError("FLASK_SECRET_KEY must be set in production")
        if not os.environ.get('DATABASE_URL'):
            raise ValueError("DATABASE_URL must be set in production")


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
