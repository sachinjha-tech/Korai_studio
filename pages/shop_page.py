"""Page Object Model for the Korai Studio shop (catalogue) page.

Encapsulates the selectors and behaviour for https://www.thekoraistudio.com/
shop — the product grid and the filter & sort panel — so tests interact with
the page through meaningful methods rather than raw CSS/text selectors.
"""

import re
from urllib.parse import parse_qsl, urlsplit

from playwright.sync_api import Page


class ShopPage:
    URL_PATH = "/shop"

    def __init__(self, page: Page):
        self.page = page

    # -- navigation ---------------------------------------------------------

    def goto(self):
        """Navigate to the shop page and wait for it to settle."""
        self.page.goto(self.URL_PATH)
        self.page.wait_for_load_state("networkidle")

    # -- selectors ----------------------------------------------------------

    def heading(self):
        """The primary <h1> of the shop page."""
        return self.page.locator("main h1").first

    def product_cards(self):
        """The product cards rendered in the grid."""
        return self.page.locator("a.card")

    def filters_panel(self):
        """The 'Filter & sort' sidebar panel."""
        return self.page.locator("aside.filters[data-filter-panel]")

    def filters_toggle(self):
        """The button that toggles the filter panel."""
        return self.page.locator("button[data-filter-toggle]")

    def filter_form(self):
        """The GET form carrying all the filter widgets."""
        return self.page.locator("form[data-filter-form]")

    def sort_select(self):
        return self.filter_form().locator('select[name="sort"]')

    def colour_select(self):
        return self.filter_form().locator('select[name="color"]')

    def design_select(self):
        return self.filter_form().locator('select[name="design"]')

    def price_min_input(self):
        return self.filter_form().locator('input[name="price_min"]')

    def price_max_input(self):
        return self.filter_form().locator('input[name="price_max"]')

    def apply_button(self):
        """The 'Apply' submit button for the filter form."""
        return self.filter_form().locator('button[type="submit"]')

    # -- helpers ------------------------------------------------------------

    def card_sale_price(self, card) -> int:
        """Extract the sale price (first rupee amount) from a product card."""
        text = card.locator(".card-price").inner_text().replace(",", "")
        match = re.search(r"\d{2,}", text)
        return int(match.group()) if match else 0

    def sale_prices(self):
        """The sale price of every product currently in the grid."""
        return [self.card_sale_price(c) for c in self.product_cards().all()]

    def query_param(self, name) -> str | None:
        """The value of a query parameter on the current URL (or None)."""
        params = dict(parse_qsl(urlsplit(self.page.url).query))
        return params.get(name)

    # -- actions ------------------------------------------------------------

    def open_filters(self):
        """Reveal the filter panel if it is not already visible."""
        if not self.filters_panel().count() or not self.filters_panel().is_visible():
            self.filters_toggle().click()
            self.filters_panel().wait_for(state="visible")

    def _submit_change(self, action):
        """Run an action that submits the filter form and awaits the reload."""
        try:
            with self.page.expect_navigation(wait_until="load", timeout=30000):
                action()
        except TimeoutError:
            pass  # some selections may not trigger a navigation
        self.page.wait_for_load_state("networkidle")

    def set_sort(self, value):
        self.open_filters()
        self._submit_change(lambda: self.sort_select().select_option(value))

    def set_colour(self, value):
        self.open_filters()
        self._submit_change(lambda: self.colour_select().select_option(value))

    def set_design(self, value):
        self.open_filters()
        self._submit_change(lambda: self.design_select().select_option(value))

    def apply_price(self, min_price="", max_price=""):
        """Fill the price range and click Apply."""
        self.open_filters()

        def do():
            self.price_min_input().fill(str(min_price))
            self.price_max_input().fill(str(max_price))
            self.apply_button().click()

        self._submit_change(do)