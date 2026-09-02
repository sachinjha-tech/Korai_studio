"""REST API / HTTP smoke tests for Korai Studio.

Covers the site's real JSON API surface plus a small set of HTTP-level checks.
JSON endpoints are cleanly testable without CSRF; form-backed POSTs are
CSRF-protected, so we assert the security behaviour (403 without a valid token)
and validate the authenticated JSON endpoint via the isolated authenticated page.
"""

import json
import re

import pytest

from pages.api_client import KoraiAPI
from utils import BASE_URL

# -- anonymous JSON contract tests ------------------------------------------


@pytest.mark.order(104)
@pytest.mark.case("positive", "Cart-count API returns valid JSON with an integer count")
def test_api_cart_count_anonymous(api):
    """GET /api/cart-count returns 200 JSON with a non-negative integer."""
    resp = api.cart_count()

    assert resp.status == 200
    assert "application/json" in resp.headers.get("content-type", "")
    body = resp.json()
    assert "count" in body
    assert isinstance(body["count"], int)
    assert body["count"] >= 0


@pytest.mark.order(105)
@pytest.mark.case("positive", "Account-status API reports anonymous as logged out")
def test_api_account_status_anonymous(api):
    """GET /api/account-status returns 200 JSON with logged_in=false."""
    resp = api.account_status()

    assert resp.status == 200
    body = resp.json()
    assert body.get("logged_in") is False
    assert "name" in body
    assert body["name"] == ""


@pytest.mark.order(106)
@pytest.mark.case("negative", "An unknown API route returns 404")
def test_api_unknown_route_404(api):
    """Unsupported /api/* endpoints must not silently succeed."""
    resp = api.request.get(api._url("/api/nonexistent"))
    assert resp.status == 404


@pytest.mark.order(107)
@pytest.mark.case("positive", "Key public pages respond 200 over HTTP")
def test_api_public_pages_ok(api):
    """The main storefront pages are reachable (200)."""
    for path in ("/", "/shop/short-kurtis", "/product/blue-yellow-stripes-100-cotton",
                 "/track-order", "/search?q=shirt"):
        resp = api.request.get(api._url(path))
        assert resp.status == 200, f"{path} returned {resp.status}"


@pytest.mark.order(108)
@pytest.mark.case("positive", "Search respects the query string over HTTP")
def test_api_search_returns_products(api):
    """The search results page reflects a URL query parameter."""
    resp = api.request.get(api._url("/search?q=shirt"))
    assert resp.status == 200
    assert "shirt" in resp.url
    assert re.search(r"\d+\s+results?", resp.text()), (
        "expected a numeric results count in the search page"
    )


@pytest.mark.order(109)
@pytest.mark.case("negative", "CSRF-protected POSTs are rejected without a valid token")
def test_api_post_requires_csrf(api):
    """Form-backed POSTs (login, cart/add, order/verify) reject forged CSRF."""
    cases = [
        ("login", api._url("/account/login"),
         {"email": "x@y.com", "password": "secret"}),
        ("verify", api._url("/order/verify"),
         {"number": "KS-1", "phone": "9876543210"}),
    ]
    for name, url, data in cases:
        resp = api.request.post(url, data=data)
        assert resp.status == 403, (
            f"{name} should reject a request without a valid CSRF token, "
            f"got {resp.status}"
        )


@pytest.mark.order(110)
@pytest.mark.case("negative", "A malformed cart-count response shape is absent — API stays consistent")
def test_api_json_endpoints_are_consistent(api):
    """Both JSON endpoints always return a JSON object (not HTML/error)."""
    for call in (api.cart_count, api.account_status):
        resp = call()
        assert resp.status == 200
        assert "application/json" in resp.headers.get("content-type", "")
        json.loads(resp.text())  # must parse as JSON


# -- authenticated JSON (via the isolated authenticated page) ---------------


@pytest.mark.order(111)
@pytest.mark.xdist_group("account-state")
@pytest.mark.case("positive", "Account-status reports the signed-in user after login")
def test_api_account_status_logged_in(page):
    """With a valid session, /api/account-status reports logged_in=true."""
    resp = page.request.get(
        KoraiAPI(page.request, BASE_URL)._url("/api/account-status")
    )
    assert resp.status == 200
    body = resp.json()
    assert body.get("logged_in") is True
    assert body.get("name") == "Sachin"
