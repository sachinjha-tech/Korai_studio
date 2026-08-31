"""Track-order UI tests for Korai Studio.

Exercise /track-order: the form loads, missing/invalid numbers are handled
gracefully, and the input constraints are enforced. No real order number is
used, so the 'not found' message is the expected outcome for submissions.
"""

import pytest
from playwright.sync_api import expect
from urllib.parse import urlparse


def url_path(url: str) -> str:
    return urlparse(url).path

TRACK_PATH = "/track-order"
ORDER_FORM = 'form[action="/order/verify"]'
NUMBER_INPUT = "#number"
PHONE_INPUT = "#phone"

# A synthetic order number (does not exist on the site).
UNKNOWN_ORDER = "KS-TEST-UNKNOWN"
UNKNOWN_PHONE = "9876543210"

NOT_FOUND_MSG = "couldn't find an order"


@pytest.mark.order(100)
@pytest.mark.case("positive", "Track-order page loads with number and phone fields")
def test_track_order_page_loads(page):
    """The tracking page shows the form and both required inputs."""
    page.goto(TRACK_PATH)
    page.wait_for_load_state("networkidle")

    expect(page.locator("main h1").first).to_contain_text("Track your order")
    expect(page.locator(NUMBER_INPUT)).to_be_visible()
    expect(page.locator(PHONE_INPUT)).to_be_visible()
    expect(page.locator(ORDER_FORM).locator('button[type="submit"]')).to_be_visible()

    # Constraints are configured on the inputs.
    assert page.locator(NUMBER_INPUT).get_attribute("maxlength")
    assert page.locator(PHONE_INPUT).get_attribute("maxlength")
    # Both fields must be required so an empty submission is blocked
    # client-side rather than being accepted and reported as "not found".
    assert page.locator(NUMBER_INPUT).get_attribute("required") is not None, (
        "order number input is missing the required attribute"
    )
    assert page.locator(PHONE_INPUT).get_attribute("required") is not None, (
        "phone input is missing the required attribute"
    )


@pytest.mark.order(101)
@pytest.mark.case("negative", "Submitting an unknown order shows a graceful message")
def test_track_order_unknown_order_handled(page):
    """A non-existent order number is handled without a crash."""
    page.goto(TRACK_PATH)
    page.wait_for_load_state("networkidle")

    page.locator(NUMBER_INPUT).fill(UNKNOWN_ORDER)
    page.locator(PHONE_INPUT).fill(UNKNOWN_PHONE)
    with page.expect_navigation(wait_until="load", timeout=30000):
        page.locator(ORDER_FORM).locator('button[type="submit"]').click()
    page.wait_for_load_state("networkidle")

    text = page.locator("main").inner_text()
    assert NOT_FOUND_MSG in text, "expected the order-not-found message"


@pytest.mark.order(102)
@pytest.mark.case("negative", "Empty submission is blocked — no navigation to /order/verify")
def test_track_order_empty_submission_handled(page):
    """Empty input should be blocked client-side, so the user stays put.

    The inputs are marked required (see the order-100 positive test), so an
    empty submit must not reach /order/verify. This currently fails on the
    live site, which lacks the required attributes and treats an empty submit
    as "order not found" — surfacing that validation defect.
    """
    page.goto(TRACK_PATH)
    page.wait_for_load_state("networkidle")

    with page.expect_navigation(wait_until="load", timeout=30000):
        page.locator(ORDER_FORM).locator('button[type="submit"]').click()
    page.wait_for_load_state("networkidle")

    # Correct behaviour: required fields block the submit, so we stay on the
    # track-order page rather than navigating to /order/verify with empty data.
    assert "/order/verify" not in page.url or url_path(page.url) == TRACK_PATH, (
        f"empty submit should be blocked, got navigation to {page.url}"
    )


@pytest.mark.order(103)
@pytest.mark.case("edge", "Phone and order number fields enforce a max length")
def test_track_order_inputs_clamp_to_max_length(page):
    """Very long input is clamped to the configured maxlength attributes."""
    page.goto(TRACK_PATH)
    page.wait_for_load_state("networkidle")

    number_max = int(page.locator(NUMBER_INPUT).get_attribute("maxlength"))
    phone_max = int(page.locator(PHONE_INPUT).get_attribute("maxlength"))

    page.locator(NUMBER_INPUT).fill("9" * 200)
    page.locator(PHONE_INPUT).fill("9" * 200)

    assert len(page.locator(NUMBER_INPUT).input_value()) == number_max
    assert len(page.locator(PHONE_INPUT).input_value()) == phone_max
