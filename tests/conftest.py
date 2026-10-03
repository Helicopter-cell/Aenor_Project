import os

import pytest

os.environ.setdefault("AENOR_TEST_MODE", "1")
os.environ.setdefault("SECRET_KEY", "pytest-secret-key-for-isolated-tests")
os.environ.setdefault("ADMIN_PASSWORD", "pytest-admin-password")

from app import create_app
from routes import admin as admin_routes
from routes import main as main_routes
from services import gemini_service
from modules.obsidian_vault import clear_obsidian_cache
from modules.utils import clear_cours_cache


@pytest.fixture
def app(tmp_path, monkeypatch):
    test_database = tmp_path / "test.sqlite3"
    monkeypatch.setattr(gemini_service, "DB_FILE", test_database)
    monkeypatch.setattr(main_routes, "DB_FILE", test_database)
    monkeypatch.setattr(admin_routes, "DB_FILE", test_database)

    application = create_app({
        "TESTING": True,
        "INITIALIZE_SERVICES": False,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "RATELIMIT_STORAGE_URI": "memory://",
    })
    gemini_service.init_db()
    clear_cours_cache()
    clear_obsidian_cache()
    yield application
    clear_cours_cache()
    clear_obsidian_cache()


@pytest.fixture
def client(app):
    return app.test_client()
