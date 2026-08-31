"""Login (sign in) UI tests for Korai Studio.

Step 2 of the run. Covers the login page loading, field configuration,
navigation reachability, helper links, plus positive, negative and edge cases.
The final test logs in with sachin's credentials and keeps that session signed
in for everything that follows (homepage, shop, navigation).
"""

from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage


def url_path(url):
    """Return the path component of a URL (ignoring query strings)."""
    return urlparse(url).path


@pytest.mark.order(30)
def test_login_page_loads(login_page):
    """The login page loads with the correct title, heading and form."""
    assert login_page.page.title() == "Sign in — Korai Studio"
    assert login_page.is_loaded()
    assert login_page.heading().inner_text() == "Sign in"


@pytest.mark.order(31)
def test_login_form_fields_visible_and_configured(login_page):
    """Both fields are present, visible and carry the right constraints."""
    email = login_page.email_field()
    password = login_page.password_field()

    assert email.is_visible()
    assert password.is_visible()

    assert email.get_attribute("type") == "email"
    assert email.get_attribute("required") is not None
    assert password.get_attribute("type") == "password"
    assert password.get_attribute("required") is not None


@pytest.mark.order(32)
def test_sign_in_button_visible_and_enabled(login_page):
    """The submit button is rendered, visible and clickable."""
    button = login_page.submit_button()
    assert button.is_visible()
    assert button.is_enabled()
    assert button.inner_text().strip().casefold() == "sign in"


@pytest.mark.order(33)
def test_forgot_password_link_present(login_page):
    """A 'Forgot your password?' link points at the reset flow."""
    link = login_page.forgot_password_link()
    assert link.is_visible()
    assert "/account/forgot-password" in link.get_attribute("href")


@pytest.mark.order(34)
def test_create_account_link_navigates_to_register(login_page):
    """'Create an account' on the sign-in page leads to registration."""
    login_page.create_account_link().click()
    login_page.page.wait_for_load_state("networkidle")
    assert url_path(login_page.page.url) == "/account/register"


@pytest.mark.order(35)
def test_login_page_reachable_from_header(login_page):
    """The header account link opens the sign-in page."""
    login_page.page.locator("header .account-link").first.click()
    login_page.page.wait_for_load_state("networkidle")
    assert url_path(login_page.page.url) == "/account/login"


@pytest.mark.order(36)
def test_login_page_reachable_from_register(login_page):
    """The 'Sign in' link on the register page opens login."""
    login_page.page.goto("/account/register")
    login_page.page.wait_for_load_state("networkidle")
    register_form = login_page.page.locator('form[action="/account/register"]')
    register_form.locator('a[href*="/account/login"]').click()
    login_page.page.wait_for_load_state("networkidle")
    assert url_path(login_page.page.url) == "/account/login"


@pytest.mark.order(37)
@pytest.mark.case(
    "negative", "Empty sign-in is blocked — required fields fire native validation"
)
def test_login_negative_empty_submission_is_blocked(login_page):
    """Submitting empty fields is blocked before any network request."""
    login_page.submit()
    assert not login_page.form().evaluate("f => f.checkValidity()")
    assert url_path(login_page.page.url) == "/account/login"


@pytest.mark.order(38)
@pytest.mark.case("negative", "Malformed email address is rejected by the input")
def test_login_negative_invalid_email_format_is_blocked(login_page):
    """A non-email string fails the type=email check on the sign-in form."""
    login_page.fill_form(email="not-an-email", password="whatever12")
    assert not login_page.email_field().evaluate("e => e.checkValidity()")
    assert not login_page.form().evaluate("f => f.checkValidity()")


@pytest.mark.order(39)
@pytest.mark.case("edge", "A correctly formatted email is accepted by the form")
def test_login_edge_valid_email_format_accepted(login_page):
    """A well-formed email address passes native validation."""
    login_page.fill_form(email="sachinjha.765@gmail.com", password="anything")
    assert login_page.email_field().evaluate("e => e.checkValidity()")
    assert login_page.form().evaluate("f => f.checkValidity()")


@pytest.mark.order(40)
@pytest.mark.case("negative", "Incorrect credentials are rejected — no login")
def test_submit_with_invalid_credentials_is_rejected(login_page):
    """Submitting wrong credentials must not log in or leave the login page."""
    login_page.fill_form(email="invalid@example.com", password="wrongpassword")
    login_page.submit()
    # The user is not logged in — no redirect away from the sign-in page.
    assert url_path(login_page.page.url) == "/account/login"


@pytest.mark.order(41)
@pytest.mark.case(
    "positive", "Sachin's valid credentials log in and land on the account page"
)
def test_submit_with_valid_credentials_logs_in(login_page):
    """A valid username/password logs the user in and lands on their account."""
    login_page.fill_form(email="sachinjha.765@gmail.com", password="Sachin@123")
    login_page.submit()
    # On success the app redirects to the account page and greets the user.
    assert url_path(login_page.page.url) == "/account"
    assert "account" in login_page.page.title().casefold()
    heading = login_page.page.locator("main h1").first.inner_text()
    assert "Hi" in heading or "Sachin" in heading
    header_account = login_page.page.locator("header .account-link").first
    # The header is rendered client-side after load, so use web-first
    # assertions that retry until it reflects the signed-in session.
    expect(header_account).to_have_attribute("href", "/account", timeout=15000)
    expect(header_account).to_contain_text("sachin", ignore_case=True, timeout=15000)
    # The sachin session is deliberately kept for the rest of the run so every
    # downstream suite (homepage, shop, navigation) executes while signed in.