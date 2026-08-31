# Korai Studio — UI Automation (pytest + Playwright + Page Object Model)

Automated UI tests for the live storefront **https://www.thekoraistudio.com/**,
built with **pytest-playwright** and the **Page Object Model (POM)**.

## Project structure

```
Korai_studio/
├── conftest.py              # Session-scoped browser/page, run logger + screenshot hook
├── pytest.ini               # Pytest config: base_url, headed mode, HTML report
├── requirements.txt         # Python dependencies
├── .gitignore
├── screenshots/             # Per-test screenshots + final_results.txt (auto-generated)
├── reports/                 # HTML report + run logs (auto-generated)
│   └── logs/                # Timestamped per-run log files (+ test_cases.xlsx)
├── scripts/
│   └── generate_excel_report.py  # Builds reports/test_cases.xlsx inventory
├── pages/                   # Page Object Models
│   ├── __init__.py
│   ├── home_page.py         # HomePage — homepage + navigation + scroll/links
│   ├── login_page.py        # LoginPage — sign-in form
│   ├── register_page.py     # RegisterPage — create-account form
│   ├── shop_page.py         # ShopPage — product grid + filter & sort panel
│   ├── cart_page.py         # CartPage — shopping bag/line items
│   └── checkout_page.py     # CheckoutPage — address + payment form
└── tests/                   # Test suites
    ├── __init__.py
    ├── test_registration.py # Registration flow (step 1)
    ├── test_login.py        # Login as sachin (step 2)
    ├── test_homepage.py     # Homepage scroll + link validation (step 3)
    ├── test_shop.py         # Shop filter & sort checks (step 4)
    ├── test_navigation.py   # Main navigation + dropdown behaviour (step 5)
    ├── test_purchase_flow.py# Add to cart → checkout flow (step 6)
    ├── test_search.py      # Site search results (step 7)
    ├── test_wishlist.py    # Saved / wishlist flow (step 8)
    ├── test_product.py     # Product detail page (step 9)
    ├── test_track_order.py # Order tracking form (step 10)
    └── test_logout.py       # Sign-out flow (final step)
```

## Prerequisites

- Python 3.9+ (tested on 3.14)
- Git (optional)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the Playwright browser (Chromium)
python -m playwright install chromium
```

## Running the tests

```bash
# Run the whole suite
pytest

# Run a single test file
pytest tests/test_registration.py

# Run a single test
pytest tests/test_navigation.py::test_cart_link_goes_to_bag_not_checkout

# Run headless (override the default headed mode)
pytest --headed=False
```

### Behaviour by default

- **Headed mode** — a visible browser window opens so you can watch the run.
- **HTML report** — generated automatically at `reports/report.html`
  (self-contained, open it in any browser).
- **Single session** — one browser window is opened and reused for the whole
  run via the session-scoped `context`/`page` fixtures.
- **Run log** — a timestamped log file (`reports/logs/korai_run_<timestamp>.log`)
  records each test start/end with scenario, result, duration and final URL,
  plus browser console errors/warnings and any failed HTTP responses
  (status ≥ 400).
- **Screenshots** — captured on **every** test (pass or fail), saved to
  `screenshots/<test_id>.png` and embedded inline (base64) into the HTML report,
  so `report.html` stays a single self-contained, shareable file.
- **Final results summary** — a per-test result recap is written to
  `screenshots/final_results.txt` after every run.
- **Deterministic execution order** — suites run in a fixed sequence
  (`registration → login → homepage → shop → navigation → purchase flow → search
  → wishlist → product → track order → logout`) via
  `pytest-order` markers.

All of the above are configured in `pytest.ini` and `conftest.py`:

```ini
[pytest]
base_url = https://www.thekoraistudio.com
addopts = --headed --html=reports/report.html --self-contained-html
```

## Page Object Model

Each page is encapsulated in a class under `pages/` so tests interact with
meaningful methods instead of raw CSS/text selectors:

- `pages/home_page.py` — `HomePage`
- `pages/login_page.py` — `LoginPage`
- `pages/register_page.py` — `RegisterPage`
- `pages/shop_page.py` — `ShopPage`
- `pages/cart_page.py` — `CartPage`
- `pages/checkout_page.py` — `CheckoutPage`

Page objects expose locators and actions (e.g. `goto()`, `click_nav()`,
`fill_form()`, `submit()`, `open_checkout()`, `clear_cart()`). Tests request a
ready page object via fixtures defined in `conftest.py` (`home_page`,
`login_page`, `register_page`, `cart_page`, `checkout_page`).

## Test flow

The suite runs as a single end-to-end journey (one browser session):

1. **Register** — the registration page is validated once (fields,
   constraints, cross-links); no real account is created.
2. **Login as sachin** — the sign-in form is validated, then sachin's
   credentials log the session in. The session stays signed in for the rest.
3. **Homepage** — while signed in, the page is scrolled top-to-bottom and
   back, and every link on the homepage is validated (well-formed hrefs and
   internal links resolving to a live page).
4. **Shop filters** — the shop filter & sort panel is exercised (sort by
   price, colour, design, price range) and the grid / querystring are verified.
5. **Purchase flow** — from the Short Kurtis catalogue (Newest sort), a product
   is opened, added to the bag, appears in the cart, and the checkout/payment
   page is reached. The order is **never placed** — the test stops at the
   payment form, then the cart is cleaned up.
6. **Search** — the site search is exercised (query submit, matching results,
   no-results, empty query, max length, result link validity).
7. **Wishlist** — items can be saved to the Saved page and removed again.
8. **Product detail** — title/price/sizes, info accordions, pincode delivery
   check and the size-guide modal.
9. **Track order** — the tracking form loads, handles unknown/empty numbers
   gracefully and enforces input length.
10. **Logout** — the signed-in session ends with a sign-out from the account
    page; afterwards the protected account page redirects back to sign-in.

## Test coverage

- **Homepage** — page loads, logo/title visible, announcement bar, hero
  carousel, featured products, signed-in header, full-page scroll, all-links
  validation.
- **Shop** — page loads signed in, filter panel widgets, sort by price
  (low/high), colour and design filters, price-range filter, reset to default.
- **Navigation** — primary nav links navigate to the correct pages, Collections
  dropdown (and its sub-group) reveal links, cart link goes to the bag — never
  into checkout/payment flows.
- **Purchase flow** — Short Kurtis page applies the Newest sort; a product opens
  with a size selector and Add-to-bag; adding redirects to the cart; the cart
  shows the item (name, size, qty, price) with a CHECKOUT link; the checkout
  page reaches the payment form (address fields + online payment) with a Place
  Order button, but the order is never submitted and the cart is cleaned up.
- **Registration** — page loads, field configuration, reachable from sign-in,
  mismatched passwords rejected; plus positive/negative/edge/boundary cases
  (valid form accepted, empty/invalid-email blocked, password min=8 boundary,
  field max-length clamping, email variants).
- **Login** — page loads, field configuration, sign-in button, forgot-password
  and create-account links, reachable from header/register, invalid credentials
  rejected, empty/malformed-email blocked, valid credential login (sachin).
- **Logout** — sign-out from the account page returns to the sign-in page and
  the header reverts to an anonymous state; the protected account page is no
  longer reachable afterwards (redirects to login).
- **Search** — query submit, matching results with links, no-results message,
  empty query, max-length clamping, and result name ↔ product page match.
- **Wishlist** — empty state, saving an item from the product page, the Saved
  page reflecting it, correct product, and removing it again.
- **Product detail** — title/price/size radios, fabric + delivery accordions,
  pincode delivery check, and the size-guide modal open/close.
- **Track order** — page loads with the two required fields, unknown and empty
  submissions are handled gracefully (not-found message), and input max-length
  is enforced.

## Reports & screenshots

After a run:

- `reports/report.html` — full HTML test report (self-contained: screenshots are
  inlined as base64, so this file alone is shareable with stakeholders).
- `reports/logs/korai_run_<timestamp>.log` — detailed run log (start/end of
  every test with scenario, result, duration, final URL; console errors;
  failed HTTP responses).
- `screenshots/*.png` — screenshot of the page at the end of every test.
- `screenshots/final_results.txt` — a scenario-aware report: each test listed
  as `# scenario result title` with test id + details, plus totals and a
  POSITIVE / NEGATIVE / EDGE scenario breakdown. Use the `@pytest.mark.case`
  marker to tag a test (e.g. `@pytest.mark.case("negative", "optional title")`);
  unmarked tests default to POSITIVE with their docstring as the title.
- `reports/test_cases.xlsx` — a section-wise Excel inventory of every test
  case. One sheet per section (Registration, Login, Homepage, Shop, Navigation,
  Purchase Flow, Search, Wishlist, Product Details, Track Order, Logout) plus a
  Summary sheet with per-section and overall counts split by scenario
  (Positive / Negative / Edge).

### Rebuilding the Excel inventory

The workbook is regenerated directly from the collected test suite:

```bash
.venv/Scripts/python.exe scripts/generate_excel_report.py
```

It writes `reports/test_cases.xlsx` with styling (section headers, scenario
colour-coding, frozen header rows) so it is ready to share with management.
Requires `openpyxl` (already added to `requirements.txt`).

Both are git-ignored (`reports/`) or git-tracked via `.gitkeep` (`screenshots/`)
as appropriate.
