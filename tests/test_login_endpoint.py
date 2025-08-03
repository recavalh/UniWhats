import pytest
import requests

from backend.auth_client import login


class MockResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


def test_login_valid_credentials(monkeypatch):
    valid_users = [
        {"email": "admin@school.com", "password": "admin123", "expected_role": "Manager"},
        {"email": "maria@school.com", "password": "maria123", "expected_role": "Receptionist"},
        {"email": "carlos@school.com", "password": "carlos123", "expected_role": "Coordinator"},
        {"email": "ana@school.com", "password": "ana123", "expected_role": "Sales Rep"},
    ]

    def mock_post(url, json, headers):
        for user in valid_users:
            if json["email"] == user["email"] and json["password"] == user["password"]:
                return MockResponse(200, {"user": {"role": user["expected_role"]}})
        return MockResponse(401)

    monkeypatch.setattr(requests, "post", mock_post)

    for user in valid_users:
        response = login(user["email"], user["password"])
        assert response.status_code == 200
        assert response.json().get("user", {}).get("role") == user["expected_role"]


def test_login_invalid_credentials(monkeypatch):
    invalid_tests = [
        {"email": "admin@school.com", "password": "wrongpassword", "desc": "Wrong password"},
        {"email": "nonexistent@school.com", "password": "admin123", "desc": "Non-existent user"},
        {"email": "admin@school.com", "password": "", "desc": "Empty password"},
        {"email": "", "password": "admin123", "desc": "Empty email"},
        {"email": "admin@school.com", "password": "admin124", "desc": "Almost correct password"},
    ]

    def mock_post(url, json, headers):
        return MockResponse(401)

    monkeypatch.setattr(requests, "post", mock_post)

    for test in invalid_tests:
        response = login(test["email"], test["password"])
        assert response.status_code == 401
