import os
import tempfile
import pytest
from app import create_app, db

@pytest.fixture()
def app():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = "sqlite:///" + path.replace("\\", "/")
    os.environ["SECRET_KEY"] = "test-secret"
    application = create_app()
    application.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    yield application
    with application.app_context():
        db.drop_all()
    os.unlink(path)
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("SECRET_KEY", None)

def test_homepage_loads(app):
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"AchievX Scientist" in response.data

def test_health_endpoint(app):
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "running"
