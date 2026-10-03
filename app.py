"""Application factory and WSGI entry point for Aënor."""

import os
from pathlib import Path

from flask import Flask
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import csrf, limiter
from modules.utils import clean_text, load_cours, render_cours_value, static_path
from routes.admin import admin_bp
from routes.audio import audio_bp
from routes.main import main_bp
from routes.scenario import scenario_bp
from routes.translation import translation_bp
from services import gemini_service


load_dotenv(Path(__file__).resolve().parent / ".env")


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    secret_key = (
        os.environ.get("SECRET_KEY")
        or os.environ.get("FLASK_SECRET_KEY")
    )
    if not secret_key:
        raise RuntimeError(
            "Set SECRET_KEY or FLASK_SECRET_KEY in the environment before starting Aënor."
        )

    app.config.update(
        SECRET_KEY=secret_key,
        DEBUG=False,
        PREFERRED_URL_SCHEME="https",
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_ENABLED=True,
        RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        RATELIMIT_HEADERS_ENABLED=True,
    )
    if config:
        app.config.update({key: value for key, value in config.items() if key != "SECRET_KEY"})
        app.config["SECRET_KEY"] = secret_key
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.jinja_env.filters["render_cours_value"] = render_cours_value
    app.jinja_env.filters["clean_text"] = clean_text
    app.jinja_env.globals["static_path"] = static_path

    csrf.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(translation_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(scenario_bp)
    app.register_blueprint(admin_bp)

    app.before_request(gemini_service.before_request_log_ip)
    app.before_request(gemini_service.ensure_user_uuid)
    app.register_error_handler(404, gemini_service.not_found)
    app.register_error_handler(500, gemini_service.internal_error)

    if app.config.get("INITIALIZE_SERVICES", not app.config.get("TESTING", False)):
        gemini_service.load_files_at_startup()
        load_cours()
    return app


app = (
    create_app({"TESTING": True, "INITIALIZE_SERVICES": False})
    if os.environ.get("AENOR_TEST_MODE") == "1"
    else create_app()
)


if __name__ == "__main__":
    app.run()
