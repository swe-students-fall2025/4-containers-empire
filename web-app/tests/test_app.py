"""Tests for the Flask app and MongoDB handler using mongomock."""

# pylint: skip-file
import os
import sys
from unittest.mock import patch
import mongomock
import pytest
from werkzeug.security import generate_password_hash
from unittest.mock import patch
from bson.objectid import ObjectId

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app as flask_app
import app as app_module

patch("os.makedirs").start()


@pytest.fixture
def client(monkeypatch):
    """Provides a Flask test client with mocked MongoDB collections."""

    mock_client = mongomock.MongoClient()
    mock_db = mock_client["whos_that_animal"]
    monkeypatch.setattr(app_module, "users_collection", mock_db["users"])
    monkeypatch.setattr(app_module, "photos_collection", mock_db["photos"])

    flask_app.config.update(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test_secret"}
    )

    with flask_app.test_client() as test_client:
        yield test_client


def test_style_css_served(client, monkeypatch, tmp_path):
    """Covers /style.css route including successful file read."""

    fake_templates = tmp_path / "templates"
    fake_templates.mkdir()
    css_file = fake_templates / "styles.css"
    css_file.write_text("body { background: black; }")

    monkeypatch.setattr(app_module.app, "root_path", str(tmp_path))

    resp = client.get("/style.css")

    assert resp.status_code == 200
    assert b"background" in resp.data
    assert resp.headers["Content-Type"] == "text/css"


def test_register_and_login(client):
    """Test user registration and login flow."""

    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )
    assert b"Account created!" not in response.data

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post(
        "/login", data={"username": "testuser", "password": "wrongpassword"}
    )
    assert b"Invalid login." in response.data

    response = client.post("/login", data={"username": "nouser", "password": "pass"})
    assert b"Invalid login." in response.data


def test_protected_route_requires_login(client):
    """Index route should require login."""
    response = client.get("/", follow_redirects=True)
    assert b"login" in response.data.lower()


def test_user_in_db(client):
    """Direct database insertion works as expected."""
    users_collection = app_module.users_collection
    users_collection.insert_one(
        {
            "username": "mongo_user",
            "email": "mongo@example.com",
            "password_hash": generate_password_hash("pw"),
        }
    )

    user = users_collection.find_one({"username": "mongo_user"})
    assert user is not None
    assert user["email"] == "mongo@example.com"


def register_and_login(client, username="u1"):
    """Helper: register + login a user quickly."""
    client.post(
        "/register",
        data={"username": username, "email": "e@e.com", "password": "pw"},
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"username": username, "password": "pw"},
        follow_redirects=True,
    )


def test_login_get_page(client):
    """Covers GET /login (no form submission)."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_logout_route(client):
    """Covers /logout route."""
    register_and_login(client)

    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_home_page_authenticated(client):
    """Covers home() route."""
    register_and_login(client)

    resp = client.get("/", follow_redirects=True)
    assert resp.status_code == 200


def test_my_animals_empty(client):
    """Covers /my_animals with an empty database."""
    register_and_login(client)

    resp = client.get("/my_animals")
    assert resp.status_code == 200
    assert b"observations" in resp.data.lower()


def test_upload_get_page(client):
    """Covers GET /upload."""
    register_and_login(client)
    resp = client.get("/upload")
    assert resp.status_code == 200
