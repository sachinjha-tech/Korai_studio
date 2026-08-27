"""Registration (create account) UI tests for Korai Studio.

Covers the registration page loading, its field configuration, navigation
reachability from the sign-in page, and client-side validation behaviour —
without creating a real account on the live site.
"""

from urllib.parse import urlparse

import pytest

from pages.register_page import RegisterPage


def url_path(url):
    """Return the path component of a URL (ignoring query strings)."""
    return urlparse(url).path


@pytest.mark.order(10)
def test_register_page_loads(register_page):
    """The registration page loads with the correct title, heading and form."""
    assert register_page.page.title() == "Create an account — Korai Studio"
    assert register_page.is_loaded()
    assert register_page.heading().inner_text() == "Create an account"


@pytest.mark.order(11)
def test_registration_form_fields_visible_and_configured(register_page):
    """All required fields are present, visible and carry the right constraints."""
    name = register_page.title_field()
    email = register_page.email_field()
    password = register_page.password_field()
    confirm = register_page.confirm_field()

    assert name.is_visible()
    assert email.is_visible()
    assert password.is_visible()
    assert confirm.is_visible()

    assert name.get_attribute("required") is not None
    assert email.get_attribute("type") == "email"
    assert email.get_attribute("required") is not None
    assert password.get_attribute("type") == "password"
    assert password.get_attribute("required") is not None
    assert password.get_attribute("minlength") == "8"
    assert confirm.get_attribute("type") == "password"
    assert confirm.get_attribute("required") is not None


@pytest.mark.order(12)
def test_register_page_reachable_from_sign_in(register_page):
    """'Create an account' on the sign-in page navigates to registration."""
    register_page.page.goto("/account/login")
    register_page.page.wait_for_load_state("networkidle")
    register_page.page.get_by_role("link", name="Create an account").click()
    register_page.page.wait_for_load_state("networkidle")
    assert url_path(register_page.page.url) == "/account/register"


@pytest.mark.order(13)
def test_register_page_links_back_to_sign_in(register_page):
    """The 'Sign in' link on registration returns to the login page."""
    register_page.sign_in_link().click()
    register_page.page.wait_for_load_state("networkidle")
    assert url_path(register_page.page.url) == "/account/login"


@pytest.mark.order(14)
def test_create_account_button_visible_and_enabled(register_page):
    """The submit button is rendered, visible and clickable."""
    button = register_page.submit_button()
    assert button.is_visible()
    assert button.is_enabled()
    assert button.inner_text().strip().casefold() == "create account"


@pytest.mark.order(15)
def test_submit_with_mismatched_passwords_is_rejected(register_page):
    """Submitting with differing passwords must not create an account."""
    register_page.fill_form(
        name="QA Test User",
        email="qa@example.com",
        password="password123",
        confirm="password456",
    )
    register_page.submit()
    # The user stays on the registration page — no successful account creation.
    assert url_path(register_page.page.url) == "/account/register"


@pytest.mark.order(16)
def test_account_header_link_opens_sign_in(register_page):
    """The header account link leads to the sign-in page."""
    register_page.page.locator("header .account-link").first.click()
    register_page.page.wait_for_load_state("networkidle")
    assert url_path(register_page.page.url) == "/account/login"
