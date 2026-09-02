"""Logout (sign out) UI tests for Korai Studio.

These verify the sign-out flow from the account page and that the session is
genuinely cleared afterwards. Each test runs in its own isolated authenticated
page and signs itself out (no reliance on execution order).

Because they mutate sachin's LIVE session, they are pinned to a single worker
via @pytest.mark.xdist_group("account-state") + `--dist=loadgroup`.
"""
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

SIGN_OUT = 'a[href="/account/logout"]'
ACCOUNT_LINK = "header .account-link"
LOGIN_PATH = "/account/login"
ACCOUNT_PATH = "/account"


def url_path(url: str) -> str:
    return urlparse(url).path


@pytest.fixture
def account_page(page):
    page.goto(ACCOUNT_PATH)
    page.wait_for_load_state("networkidle")
    return page


@pytest.mark.order(112)
@pytest.mark.xdist_group("account-state")
@pytest.mark.case("positive", "Sign out from the account page returns to the sign-in page")
def test_logout_signs_out_from_account_page(account_page):
    """Clicking 'Sign out' ends the session and lands back on the sign-in page."""
    assert url_path(account_page.url) == ACCOUNT_PATH

    header_before = account_page.locator(ACCOUNT_LINK).first
    expect(header_before).to_contain_text("Hi, Sachin", ignore_case=True, timeout=15000)

    sign_out = account_page.locator(SIGN_OUT).first
    expect(sign_out).to_be_visible()
    with account_page.expect_navigation(wait_until="load", timeout=30000):
        sign_out.click()
    account_page.wait_for_load_state("networkidle")

    # Redirected to sign-in and the header swaps back to an anonymous state.
    assert url_path(account_page.url) == LOGIN_PATH
    header_after = account_page.locator(ACCOUNT_LINK).first
    assert header_after.get_attribute("href") == LOGIN_PATH
    expect(header_after).to_contain_text("Sign in", ignore_case=True, timeout=15000)


@pytest.mark.order(113)
@pytest.mark.xdist_group("account-state")
@pytest.mark.case("negative", "Protected account page is blocked after logout")
def test_session_cleared_after_logout(page):
    """After signing out, /account bounces to the login page with a next target.

    Runs in its own isolated authenticated page, so it signs itself out first
    (it does not depend on the order-112 test having run).
    """
    # Self-contained: end the session from the account page.
    page.goto(ACCOUNT_PATH)
    page.wait_for_load_state("networkidle")
    sign_out = page.locator(SIGN_OUT).first
    expect(sign_out).to_be_visible(timeout=15000)
    with page.expect_navigation(wait_until="load", timeout=30000):
        sign_out.click()
    page.wait_for_load_state("networkidle")

    # Now /account must bounce back to login with a next/last=account target.
    page.goto(ACCOUNT_PATH)
    page.wait_for_load_state("networkidle")

    assert url_path(page.url) == LOGIN_PATH
    assert "last=account" in page.url or "next=%2Faccount" in page.url

    header = page.locator(ACCOUNT_LINK).first
    assert header.get_attribute("href") == LOGIN_PATH
    expect(header).to_contain_text("Sign in", ignore_case=True, timeout=15000)