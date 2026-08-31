"""Page Object Model for the Korai Studio cart (bag) page.

Encapsulates the selectors and behaviour for https://www.thekoraistudio.com/
cart so tests interact with the cart through meaningful methods rather than
raw CSS/text selectors.
"""

import re


class CartPage:
    URL_PATH = "/cart"

    def __init__(self, page):
        self.page = page

    # -- navigation ---------------------------------------------------------

    def goto(self):
        """Navigate to the cart page and wait for it to settle."""
        self.page.goto(self.URL_PATH)
        self.page.wait_for_load_state("networkidle")

    # -- selectors ----------------------------------------------------------

    def heading(self):
        """The cart page heading ('Your bag')."""
        return self.page.locator("main h1").first

    def item_rows(self):
        """All cart line items (one per product in the bag)."""
        return self.page.locator(".cart-layout .lines .line")

    def item_name(self, row):
        """The product name link inside a cart line item."""
        return row.locator("a.line-name").first

    def item_size(self, row):
        """The size label inside a cart line item (e.g. 'Size S')."""
        return row.locator(".line-meta").first

    def item_qty_select(self, row):
        """The quantity selector inside a cart line item."""
        return row.locator('select[name="quantity"]').first

    def item_price(self, row):
        """The line-item price element (a bare rupee amount)."""
        return row.locator("> p").first

    def remove_button(self, row):
        """The 'Remove' submit button inside a cart line item."""
        return row.locator('button.remove[type="submit"]').first

    def subtotal_value(self):
        """The Subtotal amount in the order summary."""
        return self.page.locator(".totals").locator("text=Subtotal").first

    def total_value(self):
        """The Total amount in the order summary."""
        return self.page.locator(".totals .grand").locator("text=Total").first

    def checkout_link(self):
        """The CHECKOUT anchor that proceeds to the checkout page."""
        return self.page.locator('a[href="/checkout"]')

    def bag_badge(self):
        """The numeric badge on the header BAG link showing item count."""
        return self.page.locator('[data-bag-count], .bag-count').first

    # -- helpers ------------------------------------------------------------

    def item_count(self) -> int:
        """Number of distinct line items currently in the cart."""
        return self.item_rows().count()

    def is_empty(self) -> bool:
        """True when the cart contains zero items."""
        return self.item_count() == 0

    def amount(self, locator) -> str:
        """The numeric/currency text of an amount locator, stripped."""
        return locator.inner_text().replace(",", "").strip()

    # -- actions ------------------------------------------------------------

    def clear_cart(self):
        """Remove every item from the cart until it is empty."""
        self.goto()
        while self.item_count() > 0:
            row = self.item_rows().first
            with self.page.expect_navigation(wait_until="load", timeout=30000):
                self.remove_button(row).click()
            self.page.wait_for_load_state("networkidle")

    def open_checkout(self):
        """Click the CHECKOUT link and wait for the checkout page to settle."""
        with self.page.expect_navigation(wait_until="load", timeout=30000):
            self.checkout_link().click()
        self.page.wait_for_load_state("networkidle")
