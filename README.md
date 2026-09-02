# Korai Studio — UI Automation (pytest + Playwright + Page Object Model)

Automated UI tests for the live storefront **https://www.thekoraistudio.com/**,
built with **pytest-playwright** and the **Page Object Model (POM)**.

## Project structure

```
Korai_studio/
├── conftest.py              # Isolated per-test browser/page, auth-state + run logging
├── utils.py                 # Central config: BASE_URL + login credentials/helpers
├── pytest.ini               # Pytest config: base_url, HTML report
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
│   ├── checkout_page.py     # CheckoutPage — address + payment form
│   └── api_client.py        # KoraiAPI — REST/JSON endpoint client
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
    ├── test_api.py         # REST / JSON API smoke layer (step 11)
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
# Run the whole suite sequentially (default)
pytest

# Run a single test file
pytest tests/test_registration.py

# Run a single test
pytest tests/test_navigation.py::test_cart_link_goes_to_bag_not_checkout

# Run in headed mode (visible browser window)
pytest --headed

# Run in parallel (opt-in, not the default)
pytest -n 4 --dist=loadgroup
```

Plain `pytest` runs the full suite **sequentially and headless** by default.
Parallel execution (`pytest -n 4 --dist=loadgroup`) is supported but not the
default, since several tests share live account state.

### Parallel execution (`pytest-xdist`)

Parallel execution is available but **opt-in** (`pytest -n 4 --dist=loadgroup`)
since several tests mutate sachin's live cart, wishlist or session state.
- **Isolated pages** — every test gets its own fresh browser context and page
  (function-scoped, per-test). No test shares a live page or session object,
  so the suites never interfere even when they run concurrently.
- **One authenticated login per worker** — the session-scoped `auth_state`
  fixture signs in as sachin once per worker process, captures the browser
  `storage_state`, and every authenticated test loads it as its starting state
  (no repeated logins, no shared live session).
- **Anonymous opt-in** — login, registration, anonymous-API and logout-over
  flows use dedicated anonymous contexts (`anon_page`), while the default
  `page` fixture is authenticated.
- **Shared-account safety** — tests that mutate sachin's LIVE cart, wishlist or
  session are tagged `@pytest.mark.xdist_group("account-state")`; with
  `--dist=loadgroup` all of them are pinned to a single worker, so they never
  race the same account state. Stateless tests stay ungrouped and spread across
  the remaining workers.
- Execution `order` markers now only categorise the report; correctness no
  longer depends on run order (the suites are order-independent by design).

### Behaviour by default

- **Headless mode** — no browser window is shown during the run (pass
  `--headed` to watch).
- **HTML report** — generated automatically at `reports/report.html`
  (self-contained, open it in any browser).
- **Sequential** — tests run one at a time in a single process. Pass
  `-n <workers> --dist=loadgroup` for parallel execution (see above).
- **Run log** — a timestamped log file (`reports/logs/korai_run_<timestamp>.log`)
  records each test start/end with scenario, result, duration and final URL,
  plus browser console errors/warnings and any failed HTTP responses
  (status ≥ 400).
- **Screenshots** — captured on **every** test (pass or fail), saved to
  `screenshots/<test_id>.png` and embedded inline (base64) into the HTML report,
  so `report.html` stays a single self-contained, shareable file.
- **Final results summary** — a per-test result recap is written to
  `screenshots/final_results.txt` after every run.

All of the above are configured in `pytest.ini` and `conftest.py`:

```ini
[pytest]
base_url = https://www.thekoraistudio.com
addopts = --html=reports/report.html --self-contained-html
```

## Configuration (`utils.py`)

Environment details live in one place (`utils.py`) so both the browser/UI and
API layers read the same source of truth:

```python
from utils import BASE_URL, USER_EMAIL, USER_PASSWORD, USER, url
```

- `BASE_URL` — the site under test (`https://www.thekoraistudio.com`).
- `USER` / `USER_EMAIL` / `USER_PASSWORD` / `USER_NAME` — the sign-in user.
- `url(path)` — join a path against `BASE_URL`.

To point the suite at another environment, update `BASE_URL` here (and the
matching `base_url` in `pytest.ini`); to change the sign-in user, update `USER`.
The API layer defaults its base URL and the login flow its credentials from
this module.

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
`fill_form()`, `submit()`, `open_checkout()`, `clear_cart()`). Tests request aready page object via fixtures defined in `conftest.py` (`home_page`,
`login_page`, `register_page`, `cart_page`, `checkout_page`).

## Test flow

Each test runs in its own isolated, authenticated browser context (authenticated
page by default, anonymous for login/registration/logout flows). The suites
cover the full journey:

1. **Register** — the registration page is validated once (fields,
   constraints, cross-links); no real account is created.
2. **Login as sachin** — the sign-in form is validated with data-driven
   cases (empty fields, invalid password, unregistered email, valid
   credentials). Authenticated tests downstream load sachin's session from
   the per-worker `storage_state` capture instead of sharing a live page.
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
10. **API layer** — the JSON API surface is verified (`/api/cart-count`,
    `/api/account-status`), unknown routes return 404, key pages return 200,
    CSRF-protected POSTs reject forged tokens (403), and the authenticated
    JSON endpoints reflect the signed-in session.
11. **Logout** — the signed-in session ends with a sign-out from the account
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
- **API layer** — `GET /api/cart-count` and `GET /api/account-status` return valid
  JSON (count int, logged_in/name), unknown API routes return 404, public pages
  respond 200, the search URL follows the query string, CSRF-protected POSTs
  (login/order-verify) return 403 without a valid token, and the authenticated
  account-status echoes the signed-in user.

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
