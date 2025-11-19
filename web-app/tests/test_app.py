# pylint: skip-file
"""Tests for the Flask app and MongoDB handler using mongomock."""

import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import mongomock
import pytest
from flask import url_for
from werkzeug.security import generate_password_hash

import app as app_module
from app import app as flask_app


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
    )
    assert b"Username already exists" in response.data

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post(
        "/login", data={"username": "testuser", "password": "wrongpassword"}
    )
    assert b"Incorrect password" in response.data

    response = client.post("/login", data={"username": "nouser", "password": "pass"})
    assert b"User not found" in response.data


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
