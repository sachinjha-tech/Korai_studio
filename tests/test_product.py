"""Product detail page UI tests for Korai Studio.

Runs after the purchase flow (which already opened a product). These verify the
product page itself: title, price, size options, info accordions, delivery
pincode check and the size-guide modal.
"""

import re

import pytest
from playwright.sync_api import expect

PRODUCT = "/product/blue-yellow-stripes"
PRODUCT_NAME = "Blue & Yellow Stripes"

BUY_FORM = "#buy"
SIZE_RADIO = '#buy input[name="variant_id"]'
ADD_TO_BAG = '#buy button[type="submit"][name="next"][value="cart"]'
BUY_NOW = '#buy button[type="submit"][name="next"][value="checkout"]'
DELIVERY_PIN = "#delivery-pincode"
DELIVERY_CHECK = "[data-delivery-check-btn]"
SIZE_GUIDE_OPEN = "[data-open-size-guide]"
SIZE_GUIDE_CLOSE = "[data-close-size-guide]"


@pytest.mark.order(96)
@pytest.mark.case("positive", "The product page shows title, price and size options")
def test_product_page_shows_title_price_sizes(page):
    """Title, price and selectable sizes are all present."""
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")

    expect(page.locator("main h1").first).to_have_text(PRODUCT_NAME)

    # A well-formed price: a ₹ followed by digits (e.g. ₹799).
    assert re.search(r"₹\s*\d+", page.locator("main").inner_text()), (
        "expected a rupee-denominated price on the product page"
    )

    expect(page.locator(SIZE_RADIO).first).to_be_visible()
    assert page.locator(f"{SIZE_RADIO}:checked").count() > 0, (
        "expected a default size selected"
    )
    expect(page.locator(ADD_TO_BAG).first).to_be_visible()
    expect(page.locator(BUY_NOW).first).to_be_visible()


@pytest.mark.order(97)
@pytest.mark.case("positive", "Fabric and Delivery accordions are present and expandable")
def test_product_info_accordions_available(page):
    """The product page exposes FABRIC and DELIVERY & RETURNS accordions."""
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")

    summaries = page.locator("details summary")
    labels = [s.inner_text().strip() for s in summaries.all()]
    assert "FABRIC" in labels, f"expected a Fabric section, got {labels}"
    assert "DELIVERY & RETURNS" in labels, f"expected Delivery section, got {labels}"

    # Opening a Fabric accordion reveals its content.
    fabric = page.locator("details", has_text="FABRIC").first
    fabric.scroll_into_view_if_needed()
    fabric.locator("summary").click()
    page.wait_for_timeout(400)
    assert fabric.get_attribute("open") is not None, "fabric section did not open"


@pytest.mark.order(98)
@pytest.mark.case("positive", "Pincode check confirms delivery availability")
def test_product_delivery_pincode_check(page):
    """A valid pincode reports the area and dispatch timing."""
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")

    page.locator(DELIVERY_PIN).fill("110001")
    page.locator(DELIVERY_CHECK).click()
    page.wait_for_timeout(2000)

    text = page.locator("main").inner_text()
    assert "Delivers to" in text, "expected a delivery-area confirmation"
    # Dispatch timing must be concrete: e.g. "dispatched in 5–7 days".
    assert re.search(r"dispatched\s+in\s+\d+\s*[–-]\s*\d+\s*days", text, re.IGNORECASE), (
        "expected a concrete dispatch timing (e.g. 'dispatched in 5–7 days')"
    )


@pytest.mark.order(99)
@pytest.mark.case("positive", "The size guide modal opens and closes")
def test_product_size_guide_modal(page):
    """Size guide can be opened and closed from the product page."""
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")

    page.locator(SIZE_GUIDE_OPEN).first.click()
    page.wait_for_timeout(600)
    expect(page.locator(SIZE_GUIDE_CLOSE).first).to_be_visible(timeout=10000)

    page.locator(SIZE_GUIDE_CLOSE).first.click()
    page.wait_for_timeout(400)
    expect(page.locator(SIZE_GUIDE_CLOSE).first).not_to_be_visible(timeout=10000)
