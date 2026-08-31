"""Lightweight HTTP client for the Korai Studio API / form endpoints.

Built on Playwright's APIRequestContext so it can share cookies with the UI
flow (login, cart) and assert on real status codes and JSON bodies.

The live site exposes a small API surface:

- GET  /api/cart-count      -> {"count": <int>}
- GET  /api/account-status  -> {"logged_in": <bool>, "name": <str>}

plus form-backed endpoints that return redirects and require a CSRF token for
state changes:

- POST /account/login       -> 303 on success (sets session cookie)
- POST /cart/add            -> 303 (adds a variant to the bag)
- POST /order/verify        -> 303 (track-order lookup)
"""

import re

from utils import BASE_URL, USER_EMAIL, USER_PASSWORD


class KoraiAPI:
    """A session-aware HTTP client with small, descriptive methods."""

    def __init__(self, request, base_url: str = BASE_URL):
        self.request = request
        self.base_url = base_url.rstrip("/")

    # -- internal helpers ---------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"

    @staticmethod
    def csrf_from(html: str) -> str:
        """Extract the csrf_token hidden-field value from an HTML form page."""
        m = re.search(
            r'name="csrf_token"\s+value="([^"]+)"', html
        )
        return m.group(1) if m else ""

    # -- JSON endpoints -----------------------------------------------------

    def cart_count(self):
        """GET /api/cart-count -> Response"""
        return self.request.get(self._url("/api/cart-count"))

    def account_status(self):
        """GET /api/account-status -> Response"""
        return self.request.get(self._url("/api/account-status"))

    # -- form-backed endpoints ----------------------------------------------

    def login(self, email: str = USER_EMAIL, password: str = USER_PASSWORD):
        """POST /account/login (form-encoded). Returns the Response."""
        return self.request.post(
            self._url("/account/login"),
            data={"email": email, "password": password},
        )

    def add_to_cart(self, variant_id: str = "98", quantity: str = "1"):
        """POST /cart/add for a product variant (S = variant 98)."""
        self.request.get(self._url("/product/blue-yellow-stripes"))
        resp = self.request.get(self._url("/account/login"))
        csrf = self.csrf_from(resp.text())
        return self.request.post(
            self._url("/cart/add"),
            data={
                "csrf_token": csrf,
                "variant_id": variant_id,
                "quantity": quantity,
            },
        )

    def verify_order(self, number: str, phone: str):
        """POST /order/verify (track-order). Requires a CSRF token."""
        page = self.request.get(self._url("/track-order")).text()
        csrf = self.csrf_from(page)
        return self.request.post(
            self._url("/order/verify"),
            data={"csrf_token": csrf, "number": number, "phone": phone},
        )
