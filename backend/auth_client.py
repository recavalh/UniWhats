import requests

BASE_URL = "https://2f0940df-cae2-4a25-adec-94b80d9762a7.preview.emergentagent.com"


def login(email: str, password: str, base_url: str = BASE_URL):
    """Send login request to the backend API."""
    return requests.post(
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
    )
