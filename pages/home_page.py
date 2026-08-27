"""Page Object Model for the Korai Studio homepage.

Encapsulates the selectors and behaviour for https://shop.thekoraistudio.com/
so tests interact with the page through meaningful methods rather than raw
CSS/text selectors.
"""


class HomePage:
    URL_PATH = "/"

    # Primary top-level navigation links (direct children of the <nav>).
    NAV_ITEMS = (
        ("Shop", "/shop"),
        ("Best Sellers", "/best-sellers"),
        ("New Arrivals", "/new-arrivals"),
    )

    def __init__(self, page):
        self.page = page

    # -- navigation ---------------------------------------------------------

    def goto(self):
        """Navigate to the homepage, resolving the path against base_url."""
        self.page.goto(self.URL_PATH)

    # -- selectors ----------------------------------------------------------

    def logo(self):
        """The wordmark/logo link and image (doubles as a home link)."""
        return self.page.locator("a.wordmark img")

    def main_heading(self):
        """The primary <h1> of the current page."""
        return self.page.locator("main h1").first

    def top_nav_links(self):
        """The top-level navigation anchors (direct <nav> children)."""
        return self.page.locator("nav.nav > a")

    def nav_link(self, text):
        """A specific top-level navigation anchor matched by visible text."""
        return self.page.locator("nav.nav > a", has_text=text).first

    def collections_trigger(self):
        """The button that toggles the Collections dropdown."""
        return self.page.locator("nav.nav .dropdown-trigger")

    def dropdown_panel(self):
        """The flyout panel revealed by the Collections dropdown."""
        return self.page.locator("nav.nav .dropdown-panel")

    def dropdown_links(self):
        """The links nested inside the Collections dropdown."""
        return self.page.locator("nav.nav .dropdown-panel a")

    def dropdown_group_links(self):
        """The top-level dropdown links (Short Kurtis, Shirts) — no subgroup."""
        return self.page.locator("nav.nav .dropdown-group > .dropdown-links > a")

    def dropdown_subgroup_toggle(self):
        """The 'Launching Soon' button that expands the nested subgroup."""
        return self.page.locator("nav.nav .dropdown-subheading")

    def dropdown_subgroup_links(self):
        """The links inside the 'Launching Soon' subgroup."""
        return self.page.locator("nav.nav .dropdown-subgroup .dropdown-links a")

    def cart_link(self):
        """The header 'Bag' link pointing at the cart page."""
        return self.page.locator("header .cart-link")

    def account_link(self):
        """The header account / sign-in link."""
        return self.page.locator("header .account-link")

    def menu_toggle(self):
        """The hamburger button used on mobile to open/close the menu."""
        return self.page.locator("header .menu-toggle")

    def announce_bar(self):
        """The scrolling announcement bar at the very top of the page."""
        return self.page.locator("div.announce")

    # -- actions ------------------------------------------------------------

    def click_nav(self, text):
        """Click a top-level navigation item and wait for the page to settle."""
        self.nav_link(text).click()
        self.page.wait_for_load_state("networkidle")

    def open_dropdown(self):
        """Hover the Collections trigger to reveal the dropdown panel."""
        self.collections_trigger().hover()
        self.dropdown_panel().wait_for(state="visible")

    def toggle_mobile_menu(self):
        """Open the mobile navigation menu."""
        self.menu_toggle().click()
        self.page.wait_for_load_state("networkidle")

    # -- readiness ----------------------------------------------------------

    def is_loaded(self):
        """Wait until the page has finished loading and the logo is visible."""
        self.page.wait_for_load_state("networkidle")
        self.logo().wait_for(state="visible")
        return True
