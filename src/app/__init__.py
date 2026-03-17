"""Flask application factory and initialization."""
import json
import os
from typing import Any, Callable
from flask import Flask
from .config import config
from .models.base import db
from .logging_config import configure_logging


def _load_vite_manifest(app: Flask) -> dict[str, Any]:
    """Load and cache the Vite manifest for production asset resolution."""
    manifest_path = os.path.join(app.static_folder or '', '.vite', 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            return json.load(f)  # type: ignore[no-any-return]
    return {}


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Uses the application factory pattern for flexibility in testing
    and deployment scenarios.

    Args:
        config_name: Configuration to use ('development', 'testing', 'production').
                    Defaults to FLASK_ENV environment variable or 'development'.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Configure logging before other initialization
    configure_logging(app)

    # Initialize extensions
    db.init_app(app)

    # Initialize Flask-Migrate
    from flask_migrate import Migrate
    Migrate(app, db)

    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Register blueprints
    from .views import register_blueprints
    register_blueprints(app)

    # Add Vite manifest helper to template context
    if not app.config.get('VITE_DEV_MODE'):
        manifest = _load_vite_manifest(app)

        @app.context_processor
        def vite_assets() -> dict[str, Callable[[str], dict[str, Any]]]:
            """Make vite_asset function available in templates."""
            def vite_asset(entry: str) -> dict[str, Any]:
                """Get asset paths for a Vite entry point.

                Args:
                    entry: Source file path (e.g., 'src/main.ts')

                Returns:
                    Dict with 'js' and 'css' keys containing asset paths
                """
                entry_data = manifest.get(entry, {})
                return {
                    'js': entry_data.get('file', ''),
                    'css': entry_data.get('css', [])
                }
            return {'vite_asset': vite_asset}

    return app
