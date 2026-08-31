"""Registration (create account) UI tests for Korai Studio.

Step 1 of the run — the registration flow is exercised exactly once. Covers the
page loading, field configuration, navigation reachability, and a mix of
positive, negative, edge and boundary cases (client-side native validation).
No real account is created on the live site; the account used for the rest of
the run is sachin's.
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
@pytest.mark.case("negative")
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


@pytest.mark.order(17)
@pytest.mark.case(
    "positive", "Registration form accepts a fully-filled, valid submission"
)
def test_register_positive_valid_form_passes_native_validation(register_page):
    """A valid name/email/password/confirm passes native form validation."""
    register_page.fill_form(
        name="Riya Sharma",
        email="riya.sharma@example.com",
        password="StrongPass1",
        confirm="StrongPass1",
    )
    assert register_page.form().evaluate("f => f.checkValidity()")
    assert register_page.email_field().evaluate("e => e.checkValidity()")
    assert register_page.password_field().evaluate("e => e.checkValidity()")
    assert register_page.confirm_field().evaluate("e => e.checkValidity()")


@pytest.mark.order(18)
@pytest.mark.case(
    "edge", "Password length boundary — exactly 8 chars is the minimum"
)
def test_register_edge_password_length_boundary(register_page):
    """A 7-character password fails minlength=8; 8 characters is accepted."""
    register_page.fill_form(
        name="Riya",
        email="riya@example.com",
        password="1234567",
        confirm="1234567",
    )
    assert not register_page.password_field().evaluate("e => e.checkValidity()")

    register_page.fill_password("12345678")
    register_page.fill_confirm_password("12345678")
    assert register_page.password_field().evaluate("e => e.checkValidity()")
    assert register_page.form().evaluate("f => f.checkValidity()")


@pytest.mark.order(19)
@pytest.mark.case(
    "negative", "Empty submission is blocked — no account created, no navigation"
)
def test_register_negative_empty_form_blocked_by_validation(register_page):
    """Submitting an empty form is blocked by required-field validation."""
    register_page.submit()
    assert not register_page.form().evaluate("f => f.checkValidity()")
    assert url_path(register_page.page.url) == "/account/register"


@pytest.mark.order(20)
@pytest.mark.case("negative", "Invalid email format is rejected by the input")
def test_register_negative_invalid_email_format_is_blocked(register_page):
    """An email that is not a valid address fails the type=email check."""
    register_page.fill_form(
        name="Riya",
        email="not-an-email",
        password="StrongPass1",
        confirm="StrongPass1",
    )
    assert not register_page.email_field().evaluate("e => e.checkValidity()")
    assert not register_page.form().evaluate("f => f.checkValidity()")


@pytest.mark.order(21)
@pytest.mark.case("edge", "Length limits enforced — input clamps at name=160, email=200, password=128")
def test_register_edge_field_length_boundaries(register_page):
    """Over-limit input is clamped to maxlength and the result stays valid."""
    # The browser clamps over-length input to each field's maxlength.
    register_page.fill_password("p" * 129)
    assert register_page.password_field().input_value() == "p" * 128
    register_page.fill_confirm_password("p" * 128)

    register_page.fill_full_name("R" * 161)
    assert register_page.title_field().input_value() == "R" * 160

    register_page.fill_email("a" * 189 + "@example.com")
    assert register_page.email_field().input_value() == ("a" * 189 + "@example.com")[:200]

    # Clamped values sit exactly on the limits and still pass native validation.
    assert register_page.password_field().evaluate("e => e.checkValidity()")
    assert register_page.email_field().evaluate("e => e.checkValidity()")
    assert register_page.form().evaluate("f => f.checkValidity()")


@pytest.mark.order(22)
@pytest.mark.case(
    "edge", "Valid email variants (plus-tag / mixed case) are accepted"
)
def test_register_positive_edge_email_variants_accepted(register_page):
    """Plus-addressed and mixed-case emails are valid at client side."""
    register_page.fill_form(
        name="Riya",
        email="Riya.Sharma+test@Example.COM",
        password="StrongPass1",
        confirm="StrongPass1",
    )
    assert register_page.email_field().evaluate("e => e.checkValidity()")
    assert register_page.form().evaluate("f => f.checkValidity()")