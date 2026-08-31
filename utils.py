"""Central configuration and shared helpers for the Korai Studio test suite.

Keep the environment details in one place so both the UI (browser) and the API
layers read from the same source of truth:

- BASE_URL  — the live storefront host.
- USER      — the credentials used for sign-in and authenticated checks.

From the project root, import like:

    from utils import BASE_URL, USER, USER_EMAIL, USER_PASSWORD
"""

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Site under test (must match `base_url` in pytest.ini).
BASE_URL = "https://www.thekoraistudio.com"

# ---------------------------------------------------------------------------
# Test user
# ---------------------------------------------------------------------------

USER = {
    "first_name": "Sachin",
    "name": "Sachin Jha",
    "email": "sachinjha.765@gmail.com",
    "password": "Sachin@123",
}

USER_EMAIL = USER["email"]
USER_PASSWORD = USER["password"]
USER_NAME = USER["name"]
USER_FIRST_NAME = USER["first_name"]


def url(path: str = "/") -> str:
    """Join a path (or full URL) against BASE_URL."""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"
