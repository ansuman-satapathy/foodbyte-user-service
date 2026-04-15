from app.config import settings
from app.main import app

def test_settings_loaded_correctly():
    """Verify that pydantic settings load without errors and have an app name."""
    assert settings.app_name is not None
    assert isinstance(settings.app_name, str)

def test_app_title_matches_settings():
    """Verify that the FastAPI app instance uses the configured app name."""
    assert app.title == settings.app_name
